import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from allowlist import TargetNotAllowedError, load_allowed_targets, require_allowed_target  # noqa: E402


@pytest.fixture
def allowlist(tmp_path: Path) -> Path:
    path = tmp_path / "allowed.txt"
    path.write_text("# comentário\nhoneypot\n\n  hardened-ssh  \n", encoding="utf-8")
    return path


def test_load_ignores_comments_blank_lines_and_whitespace(allowlist):
    assert load_allowed_targets(allowlist) == {"honeypot", "hardened-ssh"}


def test_allowed_target_passes(allowlist):
    require_allowed_target("honeypot", allowlist)


@pytest.mark.parametrize("target", ["8.8.8.8", "example.com", "honeypot.evil.com", "honey", "", "# comentário"])
def test_other_targets_are_refused(allowlist, target):
    with pytest.raises(TargetNotAllowedError):
        require_allowed_target(target, allowlist)


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_allowed_targets(tmp_path / "nao_existe.txt")


def test_repository_allowlist_contains_lab_hosts():
    assert {"honeypot", "hardened-ssh"} <= load_allowed_targets()
