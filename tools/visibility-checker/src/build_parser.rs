use rustpython_ruff_python_ast::{Expr, Stmt};
use rustpython_ruff_python_parser::parse_module;

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct VisibilityPrivateComponent {
    pub allowed_dependencies: Vec<String>,
    pub allowed_dependents: Vec<String>,
}

pub fn parse_visibility_private_component(
    source: &str,
) -> Result<Option<VisibilityPrivateComponent>, String> {
    let module = parse_module(source)
        .map_err(|err| format!("failed to parse BUILD file as Python syntax: {err}"))?
        .into_syntax();

    for stmt in &module.body {
        let Stmt::Expr(expr_stmt) = stmt else {
            continue;
        };
        let Expr::Call(call) = expr_stmt.value.as_ref() else {
            continue;
        };
        if !matches_name(call.func.as_ref(), "visibility_private_component") {
            continue;
        }

        return Ok(Some(VisibilityPrivateComponent {
            allowed_dependencies: string_list_keyword(call, "allowed_dependencies")?
                .unwrap_or_default(),
            allowed_dependents: string_list_keyword(call, "allowed_dependents")?
                .unwrap_or_default(),
        }));
    }

    Ok(None)
}

fn matches_name(expr: &Expr, expected: &str) -> bool {
    match expr {
        Expr::Name(name) => name.id.as_str() == expected,
        _ => false,
    }
}

fn string_list_keyword(
    call: &rustpython_ruff_python_ast::ExprCall,
    keyword_name: &str,
) -> Result<Option<Vec<String>>, String> {
    let Some(keyword) = call.arguments.keywords.iter().find(|keyword| {
        keyword
            .arg
            .as_ref()
            .is_some_and(|arg| arg.id().as_str() == keyword_name)
    }) else {
        return Ok(None);
    };

    strings_from_list_expr(&keyword.value)
        .map(Some)
        .map_err(|err| format!("invalid {keyword_name}: {err}"))
}

fn strings_from_list_expr(expr: &Expr) -> Result<Vec<String>, String> {
    let elements = match expr {
        Expr::List(list) => list.elts.as_slice(),
        Expr::Tuple(tuple) => tuple.elts.as_slice(),
        _ => return Err("expected a list or tuple literal".to_string()),
    };

    elements.iter().map(string_from_expr).collect()
}

fn string_from_expr(expr: &Expr) -> Result<String, String> {
    match expr {
        Expr::StringLiteral(literal) => Ok(literal.value.to_str().to_string()),
        _ => Err("expected string literal elements".to_string()),
    }
}

#[cfg(test)]
mod tests {
    use super::parse_visibility_private_component;

    #[test]
    fn parses_visibility_macro_with_comments_and_layout_changes() {
        let parsed = parse_visibility_private_component(
            r#"
python_sources(name="src")

visibility_private_component(
    allowed_dependencies=[
        "//src/ai/backend/**",  # broad allow
        "!//src/ai/backend/manager/**",
    ],
    allowed_dependents=(
        "//tests/**",
    ),
)
"#,
        )
        .unwrap()
        .unwrap();

        assert_eq!(
            parsed.allowed_dependencies,
            vec![
                "//src/ai/backend/**".to_string(),
                "!//src/ai/backend/manager/**".to_string(),
            ]
        );
        assert_eq!(parsed.allowed_dependents, vec!["//tests/**".to_string()]);
    }

    #[test]
    fn returns_none_without_visibility_macro() {
        let parsed = parse_visibility_private_component(
            r#"
python_sources(
    name="src",
    sources=["**/*.py"],
)
"#,
        )
        .unwrap();

        assert_eq!(parsed, None);
    }

    #[test]
    fn rejects_non_literal_visibility_lists() {
        let err = parse_visibility_private_component(
            r#"
visibility_private_component(
    allowed_dependencies=SOME_SHARED_LIST,
)
"#,
        )
        .unwrap_err();

        assert!(err.contains("invalid allowed_dependencies"));
    }

    #[test]
    fn parses_implicitly_concatenated_string_literals() {
        let parsed = parse_visibility_private_component(
            r#"
visibility_private_component(
    allowed_dependencies=[
        "//src/ai/" "backend/**",
    ],
)
"#,
        )
        .unwrap()
        .unwrap();

        assert_eq!(
            parsed.allowed_dependencies,
            vec!["//src/ai/backend/**".to_string()]
        );
    }
}
