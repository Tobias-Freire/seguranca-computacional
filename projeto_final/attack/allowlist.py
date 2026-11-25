"""Lista branca de alvos do laboratório (equivalente em Python de allowlist.sh)."""

import os
from pathlib import Path

DEFAULT_FILE = Path(__file__).resolve().parent.parent / "lab" / "allowed_targets.txt"


class TargetNotAllowedError(Exception):
    """O alvo não consta em lab/allowed_targets.txt."""


def load_allowed_targets(path: Path | None = None) -> set[str]:
    """Lê os alvos permitidos, ignorando linhas vazias e comentários."""
    path = path or Path(os.environ.get("LAB_ALLOWED_TARGETS", DEFAULT_FILE))
    lines = (line.strip() for line in path.read_text(encoding="utf-8").splitlines())
    return {line for line in lines if line and not line.startswith("#")}


def require_allowed_target(target: str, path: Path | None = None) -> None:
    """Levanta TargetNotAllowedError se o alvo não for exatamente um dos permitidos."""
    if target not in load_allowed_targets(path):
        raise TargetNotAllowedError(
            f"alvo '{target}' recusado. Só são permitidos os alvos de lab/allowed_targets.txt."
        )
