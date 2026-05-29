mod build_parser;

use build_parser::parse_visibility_private_component;
use std::collections::{HashMap, HashSet, VecDeque};
use std::env;
use std::ffi::OsStr;
use std::fmt;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::ExitCode;

const DEFAULT_BACKEND_ROOT: &str = "src/ai/backend";

fn main() -> ExitCode {
    match Config::parse(env::args().skip(1).collect()) {
        Ok(config) => match run(config) {
            Ok(()) => ExitCode::SUCCESS,
            Err(AppError::Violations(count)) => {
                eprintln!("visibility-checker: found {count} visibility violation(s)");
                ExitCode::from(1)
            }
            Err(err) => {
                eprintln!("visibility-checker: {err}");
                ExitCode::from(2)
            }
        },
        Err(err) => {
            eprintln!("{err}");
            print_usage();
            ExitCode::from(2)
        }
    }
}

#[derive(Debug, Clone)]
struct Config {
    root: PathBuf,
    backend_root: PathBuf,
    direct_only: bool,
    quiet: bool,
    max_violations: usize,
}

impl Config {
    fn parse(args: Vec<String>) -> Result<Self, String> {
        let mut root = PathBuf::from(".");
        let mut backend_root = PathBuf::from(DEFAULT_BACKEND_ROOT);
        let mut direct_only = false;
        let mut quiet = false;
        let mut max_violations = 200;
        let mut command_seen = false;
        let mut i = 0;
        while i < args.len() {
            match args[i].as_str() {
                "check" if !command_seen => {
                    command_seen = true;
                    i += 1;
                }
                "--root" => {
                    let value = args.get(i + 1).ok_or("--root requires a path")?;
                    root = PathBuf::from(value);
                    i += 2;
                }
                "--backend-root" => {
                    let value = args.get(i + 1).ok_or("--backend-root requires a path")?;
                    backend_root = PathBuf::from(value);
                    i += 2;
                }
                "--direct-only" => {
                    direct_only = true;
                    i += 1;
                }
                "--quiet" | "-q" => {
                    quiet = true;
                    i += 1;
                }
                "--max-violations" => {
                    let value = args.get(i + 1).ok_or("--max-violations requires a count")?;
                    max_violations = value
                        .parse()
                        .map_err(|_| "--max-violations requires a non-negative integer")?;
                    i += 2;
                }
                "--help" | "-h" => return Err(String::from("visibility-checker")),
                arg => return Err(format!("unknown argument: {arg}")),
            }
        }
        Ok(Self {
            root,
            backend_root,
            direct_only,
            quiet,
            max_violations,
        })
    }
}

fn print_usage() {
    eprintln!(
        "usage: visibility-checker check [--root PATH] [--backend-root PATH] [--direct-only] [--quiet] [--max-violations N]"
    );
}

#[derive(Debug)]
enum AppError {
    Io(PathBuf, io::Error),
    Parse(String),
    Violations(usize),
}

impl fmt::Display for AppError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io(path, err) => write!(f, "{}: {err}", path.display()),
            Self::Parse(message) => write!(f, "{message}"),
            Self::Violations(count) => write!(f, "found {count} visibility violation(s)"),
        }
    }
}

fn run(config: Config) -> Result<(), AppError> {
    let root = normalize_path(&config.root)?;
    let backend_root = normalize_rel(&config.backend_root);
    let abs_backend = root.join(&backend_root);
    let build_files = collect_build_files(&abs_backend, &root)?;
    let rules = RuleSet::from_build_files(&root, &backend_root, &build_files)?;
    let graph = ImportGraph::build(&root, &backend_root)?;
    let mut checker = Checker::new(&rules, &graph, config.direct_only, config.max_violations);
    let violations = checker.check();

    if !config.quiet {
        for violation in &violations {
            println!("{violation}");
        }
    }
    println!(
        "visibility-checker: checked {} Python files, {} import edge(s), {} component rule(s)",
        graph.files.len(),
        graph.edge_count(),
        rules.components.len(),
    );
    if config.max_violations > 0 && violations.len() >= config.max_violations {
        println!(
            "visibility-checker: report capped at {} violation(s); pass --max-violations 0 to disable the cap",
            config.max_violations
        );
    }

    if violations.is_empty() {
        Ok(())
    } else {
        Err(AppError::Violations(violations.len()))
    }
}

fn normalize_path(path: &Path) -> Result<PathBuf, AppError> {
    fs::canonicalize(path).map_err(|err| AppError::Io(path.to_path_buf(), err))
}

fn normalize_rel(path: &Path) -> PathBuf {
    let mut out = PathBuf::new();
    for part in path.components() {
        if let std::path::Component::Normal(name) = part {
            out.push(name);
        }
    }
    out
}

fn collect_build_files(abs_backend: &Path, root: &Path) -> Result<Vec<PathBuf>, AppError> {
    let mut files = Vec::new();
    visit_dirs(abs_backend, &mut |path| {
        if path.file_name() == Some(OsStr::new("BUILD")) {
            files.push(to_repo_path(root, path));
        }
    })?;
    files.sort();
    Ok(files)
}

fn visit_dirs(path: &Path, visit: &mut impl FnMut(&Path)) -> Result<(), AppError> {
    let entries = fs::read_dir(path).map_err(|err| AppError::Io(path.to_path_buf(), err))?;
    for entry in entries {
        let entry = entry.map_err(|err| AppError::Io(path.to_path_buf(), err))?;
        let child = entry.path();
        let file_type = entry
            .file_type()
            .map_err(|err| AppError::Io(child.clone(), err))?;
        if file_type.is_dir() {
            visit_dirs(&child, visit)?;
        } else if file_type.is_file() {
            visit(&child);
        }
    }
    Ok(())
}

fn to_repo_path(root: &Path, path: &Path) -> PathBuf {
    path.strip_prefix(root).unwrap_or(path).to_path_buf()
}

#[derive(Debug)]
struct RuleSet {
    components: Vec<ComponentRule>,
}

impl RuleSet {
    fn from_build_files(
        root: &Path,
        backend_root: &Path,
        build_files: &[PathBuf],
    ) -> Result<Self, AppError> {
        let mut components = Vec::new();
        for build in build_files {
            let text = fs::read_to_string(root.join(build))
                .map_err(|err| AppError::Io(root.join(build), err))?;
            let Some(visibility) = parse_visibility_private_component(&text)
                .map_err(|err| AppError::Parse(format!("{}: {err}", build.display())))?
            else {
                continue;
            };
            let dir = build
                .parent()
                .unwrap_or_else(|| Path::new(""))
                .to_path_buf();
            if !dir.starts_with(backend_root) {
                continue;
            }
            components.push(ComponentRule {
                dir,
                allowed_dependencies: visibility
                    .allowed_dependencies
                    .into_iter()
                    .map(AddressPattern::parse)
                    .collect(),
                allowed_dependents: visibility
                    .allowed_dependents
                    .into_iter()
                    .map(AddressPattern::parse)
                    .collect(),
            });
        }
        components.sort_by_key(|component| component.dir.as_os_str().len());
        Ok(Self { components })
    }

    fn component_for_path(&self, path: &Path) -> Option<usize> {
        let mut best = None;
        let mut best_len = 0;
        for (idx, component) in self.components.iter().enumerate() {
            if path.starts_with(&component.dir) {
                let len = component.dir.as_os_str().len();
                if len > best_len {
                    best = Some(idx);
                    best_len = len;
                }
            }
        }
        best
    }
}

#[derive(Debug)]
struct ComponentRule {
    dir: PathBuf,
    allowed_dependencies: Vec<AddressPattern>,
    allowed_dependents: Vec<AddressPattern>,
}

impl ComponentRule {
    fn permits_dependency(&self, dependency_path: &Path) -> bool {
        if dependency_path.starts_with(&self.dir) {
            return true;
        }
        first_matching_action(&self.allowed_dependencies, dependency_path).unwrap_or(false)
    }

    fn permits_dependent(&self, dependent_path: &Path) -> bool {
        if dependent_path.starts_with(&self.dir) {
            return true;
        }
        first_matching_action(&self.allowed_dependents, dependent_path).unwrap_or(false)
    }
}

fn first_matching_action(patterns: &[AddressPattern], path: &Path) -> Option<bool> {
    patterns
        .iter()
        .find(|pattern| pattern.matches(path))
        .map(|pattern| !pattern.negated)
}

#[derive(Debug, Clone)]
struct AddressPattern {
    negated: bool,
    path: String,
    any: bool,
}

impl AddressPattern {
    fn parse(raw: String) -> Self {
        let negated = raw.starts_with('!');
        let trimmed = raw.trim_start_matches('!');
        if trimmed == "*" {
            return Self {
                negated,
                path: String::new(),
                any: true,
            };
        }
        let without_slashes = trimmed.strip_prefix("//").unwrap_or(trimmed);
        let without_target = without_slashes.split(':').next().unwrap_or(without_slashes);
        let path = without_target.trim_end_matches("/**").to_string();
        Self {
            negated,
            path,
            any: false,
        }
    }

    fn matches(&self, path: &Path) -> bool {
        if self.any {
            return true;
        }
        let Some(path_str) = path.to_str() else {
            return false;
        };
        path_str == self.path || path_str.starts_with(&(self.path.clone() + "/"))
    }
}

#[derive(Debug)]
struct ImportGraph {
    files: Vec<SourceFile>,
    edges: Vec<Vec<usize>>,
}

impl ImportGraph {
    fn build(root: &Path, backend_root: &Path) -> Result<Self, AppError> {
        let abs_backend = root.join(backend_root);
        let mut paths = Vec::new();
        visit_dirs(&abs_backend, &mut |path| {
            if path.extension() == Some(OsStr::new("py")) {
                paths.push(to_repo_path(root, path));
            }
        })?;
        paths.sort();

        let mut files = Vec::new();
        let mut module_to_file = HashMap::new();
        for path in paths {
            let is_package = path.file_name() == Some(OsStr::new("__init__.py"));
            let module = module_name(backend_root, &path);
            let idx = files.len();
            module_to_file.insert(module.clone(), idx);
            files.push(SourceFile {
                path,
                module,
                is_package,
            });
        }

        let mut edges = vec![Vec::new(); files.len()];
        for (idx, file) in files.iter().enumerate() {
            let text = fs::read_to_string(root.join(&file.path))
                .map_err(|err| AppError::Io(root.join(&file.path), err))?;
            let imports = parse_python_imports(&text, &file.module, file.is_package);
            let mut seen = HashSet::new();
            for imported in imports {
                if let Some(dep) = resolve_module(&imported, &module_to_file) {
                    if dep != idx && seen.insert(dep) {
                        edges[idx].push(dep);
                    }
                }
            }
            edges[idx].sort();
        }

        Ok(Self { files, edges })
    }

    fn edge_count(&self) -> usize {
        self.edges.iter().map(Vec::len).sum()
    }
}

#[derive(Debug)]
struct SourceFile {
    path: PathBuf,
    module: String,
    is_package: bool,
}

fn module_name(backend_root: &Path, path: &Path) -> String {
    let rel = path.strip_prefix(backend_root).unwrap_or(path);
    let mut parts = vec!["ai".to_string(), "backend".to_string()];
    for component in rel.components() {
        let part = component.as_os_str().to_string_lossy();
        let part = part.strip_suffix(".py").unwrap_or(&part);
        if part != "__init__" {
            parts.push(part.to_string());
        }
    }
    parts.join(".")
}

fn resolve_module(module: &str, module_to_file: &HashMap<String, usize>) -> Option<usize> {
    let mut candidate = module;
    loop {
        if let Some(idx) = module_to_file.get(candidate) {
            return Some(*idx);
        }
        let (parent, _) = candidate.rsplit_once('.')?;
        candidate = parent;
    }
}

fn parse_python_imports(text: &str, current_module: &str, is_package: bool) -> Vec<String> {
    let mut imports = Vec::new();
    let logical_lines = join_logical_lines(text);
    for line in logical_lines {
        let trimmed = strip_comment(&line).trim().to_string();
        if trimmed.starts_with("import ") {
            parse_import_stmt(&trimmed, &mut imports);
        } else if trimmed.starts_with("from ") {
            parse_from_stmt(&trimmed, current_module, is_package, &mut imports);
        }
    }
    imports
}

fn join_logical_lines(text: &str) -> Vec<String> {
    let mut lines = Vec::new();
    let mut current = String::new();
    let mut paren_depth = 0isize;
    for raw in text.lines() {
        let line = raw.trim();
        if current.is_empty() {
            current.push_str(line);
        } else {
            current.push(' ');
            current.push_str(line);
        }
        paren_depth += paren_delta(line);
        if paren_depth <= 0 && !line.ends_with('\\') {
            lines.push(current.replace('\\', " "));
            current.clear();
            paren_depth = 0;
        }
    }
    if !current.is_empty() {
        lines.push(current);
    }
    lines
}

fn paren_delta(line: &str) -> isize {
    let mut delta = 0;
    let mut quote = None;
    let mut escaped = false;
    for c in line.chars() {
        if let Some(q) = quote {
            if escaped {
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == q {
                quote = None;
            }
            continue;
        }
        match c {
            '\'' | '"' => quote = Some(c),
            '(' | '[' | '{' => delta += 1,
            ')' | ']' | '}' => delta -= 1,
            _ => {}
        }
    }
    delta
}

fn strip_comment(line: &str) -> &str {
    let mut quote = None;
    let mut escaped = false;
    for (i, c) in line.char_indices() {
        if let Some(q) = quote {
            if escaped {
                escaped = false;
            } else if c == '\\' {
                escaped = true;
            } else if c == q {
                quote = None;
            }
        } else if c == '\'' || c == '"' {
            quote = Some(c);
        } else if c == '#' {
            return &line[..i];
        }
    }
    line
}

fn parse_import_stmt(line: &str, imports: &mut Vec<String>) {
    let rest = line.trim_start_matches("import ");
    for item in rest.split(',') {
        let module = item.trim().split_whitespace().next().unwrap_or("");
        if module.starts_with("ai.backend.") || module == "ai.backend" {
            imports.push(module.to_string());
        }
    }
}

fn parse_from_stmt(line: &str, current_module: &str, is_package: bool, imports: &mut Vec<String>) {
    let rest = line.trim_start_matches("from ");
    let Some((module_part, _names)) = rest.split_once(" import ") else {
        return;
    };
    let module = module_part.trim();
    let absolute = if module.starts_with('.') {
        resolve_relative_import(current_module, module, is_package)
    } else {
        module.to_string()
    };
    if absolute.starts_with("ai.backend.") || absolute == "ai.backend" {
        for name in imported_names(_names) {
            imports.push(format!("{absolute}.{name}"));
        }
        imports.push(absolute);
    }
}

fn imported_names(names: &str) -> Vec<String> {
    let trimmed = names.trim().trim_start_matches('(').trim_end_matches(')');
    trimmed
        .split(',')
        .filter_map(|item| {
            let name = item.trim().split_whitespace().next().unwrap_or("");
            if name.is_empty() || name == "*" {
                None
            } else {
                Some(name.to_string())
            }
        })
        .collect()
}

fn resolve_relative_import(current_module: &str, module: &str, is_package: bool) -> String {
    let dots = module.chars().take_while(|c| *c == '.').count();
    let suffix = module.trim_start_matches('.');
    let mut parts: Vec<&str> = current_module.split('.').collect();
    if !is_package && !parts.is_empty() {
        parts.pop();
    }
    for _ in 1..dots {
        if !parts.is_empty() {
            parts.pop();
        }
    }
    if !suffix.is_empty() {
        parts.extend(suffix.split('.'));
    }
    parts.join(".")
}

struct Checker<'a> {
    rules: &'a RuleSet,
    graph: &'a ImportGraph,
    direct_only: bool,
    max_violations: usize,
}

impl<'a> Checker<'a> {
    fn new(
        rules: &'a RuleSet,
        graph: &'a ImportGraph,
        direct_only: bool,
        max_violations: usize,
    ) -> Self {
        Self {
            rules,
            graph,
            direct_only,
            max_violations,
        }
    }

    fn check(&mut self) -> Vec<Violation> {
        let mut violations = Vec::new();
        for origin in 0..self.graph.files.len() {
            if self.direct_only {
                self.check_direct_edges(origin, &mut violations);
            } else {
                self.check_transitive_paths(origin, &mut violations);
            }
            if self.reached_limit(&violations) {
                break;
            }
        }
        violations.sort_by(|a, b| {
            a.origin
                .cmp(&b.origin)
                .then(a.dependency.cmp(&b.dependency))
        });
        violations.dedup_by(|a, b| a.origin == b.origin && a.dependency == b.dependency);
        violations
    }

    fn check_direct_edges(&self, origin: usize, violations: &mut Vec<Violation>) {
        for dep in &self.graph.edges[origin] {
            if let Some(reason) = self.check_edge(origin, *dep) {
                self.push_violation(violations, origin, *dep, reason, vec![origin, *dep]);
                if self.reached_limit(violations) {
                    return;
                }
            }
        }
    }

    fn check_transitive_paths(&self, origin: usize, violations: &mut Vec<Violation>) {
        let mut queue = VecDeque::from([origin]);
        let mut seen = HashSet::from([origin]);
        let mut prev: HashMap<usize, usize> = HashMap::new();

        while let Some(node) = queue.pop_front() {
            for next in &self.graph.edges[node] {
                if !seen.insert(*next) {
                    continue;
                }
                prev.insert(*next, node);
                let path = reconstruct_path(origin, *next, &prev);
                if let Some(reason) = self.check_edge(origin, *next) {
                    self.push_violation(violations, origin, *next, reason, path);
                    if self.reached_limit(violations) {
                        return;
                    }
                    continue;
                }
                queue.push_back(*next);
            }
        }
    }

    fn push_violation(
        &self,
        violations: &mut Vec<Violation>,
        origin: usize,
        dep: usize,
        reason: String,
        path: Vec<usize>,
    ) {
        violations.push(Violation {
            origin: self.graph.files[origin].path.clone(),
            dependency: self.graph.files[dep].path.clone(),
            reason,
            path: path
                .into_iter()
                .map(|idx| self.graph.files[idx].path.clone())
                .collect(),
        });
    }

    fn reached_limit(&self, violations: &[Violation]) -> bool {
        self.max_violations > 0 && violations.len() >= self.max_violations
    }

    fn check_edge(&self, origin: usize, dep: usize) -> Option<String> {
        let origin_path = &self.graph.files[origin].path;
        let dep_path = &self.graph.files[dep].path;
        let origin_component = self.rules.component_for_path(origin_path)?;
        let dep_component = self.rules.component_for_path(dep_path)?;
        let origin_rule = &self.rules.components[origin_component];
        let dep_rule = &self.rules.components[dep_component];
        if !origin_rule.permits_dependency(dep_path) {
            return Some(format!(
                "{} does not allow dependency {}",
                origin_rule.dir.display(),
                dep_rule.dir.display()
            ));
        }
        if !dep_rule.permits_dependent(origin_path) {
            return Some(format!(
                "{} does not allow dependent {}",
                dep_rule.dir.display(),
                origin_rule.dir.display()
            ));
        }
        None
    }
}

fn reconstruct_path(origin: usize, dep: usize, prev: &HashMap<usize, usize>) -> Vec<usize> {
    let mut path = vec![dep];
    let mut cur = dep;
    while cur != origin {
        let Some(parent) = prev.get(&cur) else {
            break;
        };
        path.push(*parent);
        cur = *parent;
    }
    path.reverse();
    path
}

#[derive(Debug, Clone)]
struct Violation {
    origin: PathBuf,
    dependency: PathBuf,
    reason: String,
    path: Vec<PathBuf>,
}

impl fmt::Display for Violation {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        writeln!(f, "visibility violation: {}", self.reason)?;
        writeln!(f, "  origin: {}", self.origin.display())?;
        writeln!(f, "  dependency: {}", self.dependency.display())?;
        write!(f, "  path:")?;
        for path in &self.path {
            write!(f, " {}", path.display())?;
        }
        writeln!(f)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    struct TestRepo {
        root: PathBuf,
    }

    impl TestRepo {
        fn new() -> Self {
            let unique = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos();
            let root = std::env::temp_dir().join(format!(
                "visibility-checker-test-{}-{unique}",
                std::process::id()
            ));
            fs::create_dir_all(&root).unwrap();
            Self { root }
        }

        fn write(&self, rel: &str, content: &str) {
            let path = self.root.join(rel);
            fs::create_dir_all(path.parent().unwrap()).unwrap();
            fs::write(path, content).unwrap();
        }
    }

    impl Drop for TestRepo {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.root);
        }
    }

    fn component(dir: &str, deps: &[&str], dependents: &[&str]) -> ComponentRule {
        ComponentRule {
            dir: PathBuf::from(dir),
            allowed_dependencies: deps
                .iter()
                .map(|pattern| AddressPattern::parse((*pattern).to_string()))
                .collect(),
            allowed_dependents: dependents
                .iter()
                .map(|pattern| AddressPattern::parse((*pattern).to_string()))
                .collect(),
        }
    }

    #[test]
    fn first_matching_visibility_rule_wins() {
        let component = component(
            "src/ai/backend/common",
            &["!//src/ai/backend/manager/**", "//src/ai/backend/**"],
            &[],
        );

        assert!(!component.permits_dependency(Path::new("src/ai/backend/manager/idle.py")));
        assert!(component.permits_dependency(Path::new("src/ai/backend/client/session.py")));
    }

    #[test]
    fn parses_absolute_and_relative_python_imports() {
        let imports = parse_python_imports(
            r#"
import ai.backend.common.types as common_types
from ai.backend.manager import idle
from . import local
from ..client import session
"#,
            "ai.backend.common.pkg.module",
            false,
        );

        assert!(imports.contains(&"ai.backend.common.types".to_string()));
        assert!(imports.contains(&"ai.backend.manager.idle".to_string()));
        assert!(imports.contains(&"ai.backend.common.pkg.local".to_string()));
        assert!(imports.contains(&"ai.backend.common.client.session".to_string()));
    }

    #[test]
    fn package_relative_import_stays_inside_package() {
        let imports = parse_python_imports("from . import local\n", "ai.backend.common.pkg", true);

        assert!(imports.contains(&"ai.backend.common.pkg.local".to_string()));
    }

    #[test]
    fn direct_check_reports_disallowed_dependency() {
        let repo = TestRepo::new();
        repo.write(
            "src/ai/backend/common/BUILD",
            r#"
python_sources(name="src")
visibility_private_component(
    allowed_dependencies=["//src/ai/backend/**"],
)
"#,
        );
        repo.write(
            "src/ai/backend/manager/BUILD",
            r#"
python_sources(name="src")
visibility_private_component()
"#,
        );
        repo.write(
            "src/ai/backend/common/__init__.py",
            "from ai.backend.manager import idle\n",
        );
        repo.write("src/ai/backend/manager/__init__.py", "");
        repo.write("src/ai/backend/manager/idle.py", "");

        let backend_root = PathBuf::from("src/ai/backend");
        let build_files = collect_build_files(&repo.root.join(&backend_root), &repo.root).unwrap();
        let rules = RuleSet::from_build_files(&repo.root, &backend_root, &build_files).unwrap();
        let graph = ImportGraph::build(&repo.root, &backend_root).unwrap();
        let mut checker = Checker::new(&rules, &graph, true, 10);
        let violations = checker.check();

        assert!(
            violations
                .iter()
                .any(|violation| violation.dependency
                    == PathBuf::from("src/ai/backend/manager/idle.py")),
            "expected manager/idle.py violation, got {violations:#?}",
        );
    }

    #[test]
    fn transitive_check_reports_first_disallowed_boundary() {
        let repo = TestRepo::new();
        repo.write(
            "src/ai/backend/web/BUILD",
            r#"
python_sources(name="src")
visibility_private_component(
    allowed_dependencies=["//src/ai/backend/**"],
)
"#,
        );
        repo.write(
            "src/ai/backend/common/BUILD",
            r#"
python_sources(name="src")
visibility_private_component(
    allowed_dependents=["//src/ai/backend/**"],
    allowed_dependencies=["//src/ai/backend/**"],
)
"#,
        );
        repo.write(
            "src/ai/backend/manager/BUILD",
            r#"
python_sources(name="src")
visibility_private_component()
"#,
        );
        repo.write(
            "src/ai/backend/web/server.py",
            "from ai.backend.common import bridge\n",
        );
        repo.write(
            "src/ai/backend/common/bridge.py",
            "from ai.backend.manager import idle\n",
        );
        repo.write("src/ai/backend/common/__init__.py", "");
        repo.write("src/ai/backend/manager/__init__.py", "");
        repo.write("src/ai/backend/manager/idle.py", "");

        let backend_root = PathBuf::from("src/ai/backend");
        let build_files = collect_build_files(&repo.root.join(&backend_root), &repo.root).unwrap();
        let rules = RuleSet::from_build_files(&repo.root, &backend_root, &build_files).unwrap();
        let graph = ImportGraph::build(&repo.root, &backend_root).unwrap();
        let mut checker = Checker::new(&rules, &graph, false, 10);
        let violations = checker.check();

        let violation = violations
            .iter()
            .find(|violation| {
                violation.origin == PathBuf::from("src/ai/backend/web/server.py")
                    && violation.dependency == PathBuf::from("src/ai/backend/manager/idle.py")
            })
            .unwrap_or_else(|| {
                panic!("expected transitive manager/idle.py violation, got {violations:#?}")
            });

        assert_eq!(
            violation.path,
            vec![
                PathBuf::from("src/ai/backend/web/server.py"),
                PathBuf::from("src/ai/backend/common/bridge.py"),
                PathBuf::from("src/ai/backend/manager/idle.py"),
            ]
        );
    }
}
