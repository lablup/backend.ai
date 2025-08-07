import tempfile
from pathlib import Path

from ai.backend.plugin.entrypoint import _glob


def test_basic_file_search():
    """Test basic file search without match patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "dir1").mkdir()
        (base / "dir2").mkdir()
        (base / "dir1" / "BUILD").touch()
        (base / "dir2" / "BUILD").touch()
        (base / "other.txt").touch()

        # Search for BUILD files
        results = [*_glob(base, "BUILD", excluded_patterns=[])]
        assert len(results) == 2
        assert all(r.name == "BUILD" for r in results)


def test_excluded_patterns():
    """Test exclusion patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "good").mkdir()
        (base / "good" / "BUILD").touch()
        (base / "tools").mkdir()
        (base / "tools" / "BUILD").touch()
        (base / "wheelhouse").mkdir()
        (base / "wheelhouse" / "BUILD").touch()

        # Search with exclusion patterns
        results = [*_glob(base, "BUILD", excluded_patterns=["tools", "wheelhouse"])]
        assert len(results) == 1
        assert results[0].parent.name == "good"


def test_hidden_and_pycache_exclusion():
    """Test automatic exclusion of hidden directories and __pycache__."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "visible").mkdir()
        (base / "visible" / "BUILD").touch()
        (base / ".hidden").mkdir()
        (base / ".hidden" / "BUILD").touch()
        (base / "__pycache__").mkdir()
        (base / "__pycache__" / "BUILD").touch()

        # Hidden and __pycache__ should be automatically excluded
        results = [*_glob(base, "BUILD", excluded_patterns=[])]
        assert len(results) == 1
        assert results[0].parent.name == "visible"


def test_search_from_upper_directory_with_match_pattern():
    """Test search starting from an upper directory with a match pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "project").mkdir()
        (base / "project" / "src").mkdir()
        (base / "project" / "src" / "ai").mkdir()
        (base / "project" / "src" / "ai" / "backend").mkdir()
        (base / "project" / "src" / "ai" / "backend" / "manager").mkdir()
        (base / "project" / "src" / "ai" / "backend" / "manager" / "BUILD").touch()
        (base / "project" / "src" / "ai" / "backend" / "manager" / "models").mkdir()
        (base / "project" / "src" / "ai" / "backend" / "manager" / "models" / "BUILD").touch()
        (base / "project" / "tests").mkdir()
        (base / "project" / "tests" / "BUILD").touch()

        # Search from project root with pattern
        # All files are found because directories are traversed until suffix match
        search_base = base / "project"
        results = [
            *_glob(
                search_base,
                "BUILD",
                excluded_patterns=[],
                match_patterns=["ai/backend/manager"],
            )
        ]
        assert len(results) == 1
        assert results[0].parent.name == "manager"


def test_search_from_exact_matching_directory():
    """Test search starting from a directory that already matches the pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "ai").mkdir()
        (base / "ai" / "backend").mkdir()
        (base / "ai" / "backend" / "manager").mkdir()
        (base / "ai" / "backend" / "manager" / "BUILD").touch()
        (base / "ai" / "backend" / "manager" / "subdir").mkdir()
        (base / "ai" / "backend" / "manager" / "subdir" / "BUILD").touch()

        # Search from the exact directory that matches the pattern
        # Only the direct BUILD file is found, not subdirectories
        search_base = base / "ai" / "backend"
        results = [*_glob(search_base, "BUILD", excluded_patterns=[], match_patterns=["manager"])]
        assert len(results) == 1
        assert results[0].parent.name == "manager"


def test_multiple_match_patterns():
    """Test multiple match patterns and their interaction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create complex structure
        (base / "ai").mkdir()
        (base / "ai" / "backend").mkdir()
        (base / "ai" / "backend" / "manager").mkdir()
        (base / "ai" / "backend" / "manager" / "BUILD").touch()
        (base / "ai" / "backend" / "agent").mkdir()
        (base / "ai" / "backend" / "agent" / "BUILD").touch()
        (base / "ai" / "backend" / "common").mkdir()
        (base / "ai" / "backend" / "common" / "BUILD").touch()
        (base / "ai" / "frontend").mkdir()
        (base / "ai" / "frontend" / "BUILD").touch()

        # Multiple patterns - all files are found because the function
        # traverses all directories until suffix match
        results = [
            *_glob(
                base,
                "BUILD",
                excluded_patterns=[],
                match_patterns=["ai/backend/manager", "ai/backend/agent"],
            )
        ]
        assert len(results) == 2  # Only BUILD files in the match patterns are found
        assert {result.parent.name for result in results} == {"manager", "agent"}


def test_wildcard_match_patterns():
    """Test wildcard match patterns and their interaction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        # Create complex structure
        (base / "ai").mkdir()
        (base / "ai" / "backend").mkdir()
        (base / "ai" / "backend" / "manager").mkdir()
        (base / "ai" / "backend" / "manager" / "BUILD").touch()
        (base / "ai" / "backend" / "agent").mkdir()
        (base / "ai" / "backend" / "agent" / "BUILD").touch()
        (base / "ai" / "backend" / "common").mkdir()
        (base / "ai" / "backend" / "common" / "BUILD").touch()
        (base / "ai" / "frontend").mkdir()
        (base / "ai" / "frontend" / "BUILD").touch()
        results = [
            *_glob(
                base,
                "BUILD",
                excluded_patterns=[],
                match_patterns=["ai/backend/*"],
            )
        ]
        assert len(results) == 3  # All BUILD files under ai/backend are found
        assert {result.parent.name for result in results} == {"manager", "agent", "common"}


def test_suffix_match_propagation_per_branch():
    """Test how suffix_match flag propagates through directory traversal.

    The propagation must be confined within the matching pattern.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        (base / "root").mkdir()
        (base / "root" / "ai").mkdir()
        (base / "root" / "ai" / "backend").mkdir()
        (base / "root" / "ai" / "backend" / "manager").mkdir()
        (base / "root" / "ai" / "backend" / "manager" / "BUILD").touch()
        (base / "root" / "ai" / "backend" / "manager" / "models").mkdir()
        (base / "root" / "ai" / "backend" / "manager" / "models" / "BUILD").touch()
        (base / "root" / "ai" / "backend" / "agent").mkdir()
        (base / "root" / "ai" / "backend" / "agent" / "BUILD").touch()

        results = [
            *_glob(
                base / "root",
                "BUILD",
                excluded_patterns=[],
                match_patterns=["ai/backend/manager"],
            )
        ]
        assert len(results) == 1
        assert "manager/BUILD" in str(results[0])


def test_empty_directory():
    """Test behavior with empty directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)

        results = [*_glob(base, "BUILD", excluded_patterns=[])]
        assert len(results) == 0


def test_file_at_root():
    """Test finding file at the root level."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "BUILD").touch()

        results = [*_glob(base, "BUILD", excluded_patterns=[])]
        assert len(results) == 1
        assert results[0].parent == base
