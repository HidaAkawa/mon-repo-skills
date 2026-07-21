#!/usr/bin/env python3
"""Run isolated, read-only Claude reviews with durable audit evidence."""

from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fnmatch
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import textwrap
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Sequence


SCHEMA_VERSION = 1
CONFIG_RELATIVE = Path(".codex/claude-review.json")
AGENTS_START = "<!-- claude-independent-review:start -->"
AGENTS_END = "<!-- claude-independent-review:end -->"
EVIDENCE_DIRNAME = ".independent-review-evidence"
MAX_DIFF_BYTES = 25 * 1024 * 1024
ALLOWED_REVIEW_TYPES = {"code", "architecture", "security", "design", "content", "general"}
ALLOWED_EFFORTS = {"low", "medium", "high", "xhigh", "max"}
SAFE_ENV_SUFFIXES = (".example", ".sample", ".template")
HARD_SECRET_NAMES = {
    ".npmrc",
    ".pypirc",
    ".netrc",
    "credentials.json",
    "application_default_credentials.json",
}
HARD_SECRET_EXTENSIONS = {".pem", ".key", ".p12", ".pfx"}
DEFAULT_EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".codex",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".cache",
    ".next",
    ".nuxt",
    ".turbo",
    "dist",
    "build",
    "target",
    "coverage",
}
REQUIRED_HELP_FLAGS = {
    "--safe-mode",
    "--tools",
    "--permission-mode",
    "--strict-mcp-config",
    "--disable-slash-commands",
    "--no-chrome",
    "--no-session-persistence",
    "--output-format",
    "--model",
    "--effort",
    "--append-system-prompt",
}


class ReviewError(RuntimeError):
    """Expected failure that must not leave project artifacts."""


class ScopeTooLarge(ReviewError):
    """Snapshot scope exceeds the approved policy."""

    def __init__(self, file_count: int, byte_count: int, largest: list[tuple[str, int]]) -> None:
        self.file_count = file_count
        self.byte_count = byte_count
        self.largest = largest
        detail = ", ".join(f"{name}: {size} octets" for name, size in largest) or "indisponible"
        super().__init__(
            f"Snapshot trop volumineux ({file_count} fichiers, {byte_count} octets). "
            f"Faire valider un cadrage --include. Principaux répertoires : {detail}"
        )


@dataclass(frozen=True)
class Milestone:
    identifier: str
    condition: str
    review_types: tuple[str, ...]
    focus_paths: tuple[str, ...]
    git_baseline: str | None


@dataclass(frozen=True)
class Policy:
    project_name: str
    language: str
    model: str
    effort: str
    timeout_minutes: int
    max_turns: int
    report_directory: str
    context_files: tuple[str, ...]
    max_files: int
    max_bytes: int
    extra_excludes: tuple[str, ...]
    milestones: tuple[Milestone, ...]


@dataclass
class Candidate:
    relative: str
    source: Path
    size: int
    kind: str = "file"
    link_target: str | None = None


@dataclass
class Snapshot:
    root: Path
    manifest: dict[str, Any]
    git_mode: bool
    git_commit: str | None
    git_baseline: str | None
    git_state: str | None
    diff_text: str | None
    excluded: list[dict[str, str]] = field(default_factory=list)


def _reject_duplicate_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ReviewError(f"Clé JSON dupliquée : {key}")
        result[key] = value
    return result


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_reject_duplicate_pairs)
    except FileNotFoundError as exc:
        raise ReviewError(f"Fichier absent : {path}") from exc
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewError(f"JSON invalide dans {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReviewError(f"La racine JSON de {path} doit être un objet")
    return value


def _expect_keys(value: dict[str, Any], expected: set[str], context: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        raise ReviewError(f"{context}: clés manquantes : {', '.join(sorted(missing))}")
    if unknown:
        raise ReviewError(f"{context}: clés inconnues : {', '.join(sorted(unknown))}")


def _string(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReviewError(f"{context} doit être une chaîne non vide")
    return value.strip()


def _integer(value: Any, context: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise ReviewError(f"{context} doit être un entier entre {minimum} et {maximum}")
    return value


def _relative_path(value: Any, context: str, allow_glob: bool = False) -> str:
    raw = _string(value, context).replace("\\", "/")
    if raw.startswith("/") or re.match(r"^[A-Za-z]:/", raw):
        raise ReviewError(f"{context} doit être relatif à la racine du projet")
    parts = PurePosixPath(raw).parts
    if ".." in parts or "." == raw:
        raise ReviewError(f"{context} ne peut pas contenir '..' ni désigner la racine")
    if not allow_glob and any(char in raw for char in "*?[]"):
        raise ReviewError(f"{context} ne peut pas contenir de glob")
    return raw.rstrip("/")


def _string_list(value: Any, context: str, *, paths: bool = False, globs: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ReviewError(f"{context} doit être une liste")
    items: list[str] = []
    for index, item in enumerate(value):
        if paths:
            parsed = _relative_path(item, f"{context}[{index}]", allow_glob=globs)
        else:
            parsed = _string(item, f"{context}[{index}]")
        if parsed in items:
            raise ReviewError(f"{context}: valeur dupliquée : {parsed}")
        items.append(parsed)
    return tuple(items)


def validate_policy(data: dict[str, Any]) -> Policy:
    _expect_keys(
        data,
        {"schema_version", "project", "claude", "reports", "context_files", "snapshot", "milestones"},
        "configuration",
    )
    if data["schema_version"] != SCHEMA_VERSION:
        raise ReviewError(
            f"schema_version {data['schema_version']!r} non pris en charge ; attendu : {SCHEMA_VERSION}. "
            "Aucune migration implicite n'est autorisée."
        )

    project = data["project"]
    claude = data["claude"]
    reports = data["reports"]
    snapshot = data["snapshot"]
    milestones = data["milestones"]
    for value, context in ((project, "project"), (claude, "claude"), (reports, "reports"), (snapshot, "snapshot")):
        if not isinstance(value, dict):
            raise ReviewError(f"{context} doit être un objet")

    _expect_keys(project, {"name", "language"}, "project")
    _expect_keys(claude, {"model", "effort", "timeout_minutes", "max_turns"}, "claude")
    _expect_keys(reports, {"directory"}, "reports")
    _expect_keys(snapshot, {"max_files", "max_bytes", "extra_excludes"}, "snapshot")

    effort = _string(claude["effort"], "claude.effort")
    if effort not in ALLOWED_EFFORTS:
        raise ReviewError(f"claude.effort doit être dans : {', '.join(sorted(ALLOWED_EFFORTS))}")
    model = _string(claude["model"], "claude.model")
    if model in {"sonnet", "opus", "haiku"}:
        raise ReviewError("claude.model doit être un identifiant exact, pas un alias mouvant")

    context_files = _string_list(data["context_files"], "context_files", paths=True)
    extra_excludes = _string_list(snapshot["extra_excludes"], "snapshot.extra_excludes", paths=True, globs=True)
    report_directory = _relative_path(reports["directory"], "reports.directory")
    if report_directory == ".codex" or report_directory.startswith(".codex/"):
        raise ReviewError("reports.directory ne peut pas se trouver dans .codex")

    if not isinstance(milestones, list) or not milestones:
        raise ReviewError("milestones doit être une liste non vide")
    parsed_milestones: list[Milestone] = []
    identifiers: set[str] = set()
    for index, value in enumerate(milestones):
        context = f"milestones[{index}]"
        if not isinstance(value, dict):
            raise ReviewError(f"{context} doit être un objet")
        _expect_keys(value, {"id", "condition", "review_types", "focus_paths", "git_baseline"}, context)
        identifier = _string(value["id"], f"{context}.id")
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,63}", identifier):
            raise ReviewError(f"{context}.id doit être un identifiant minuscule sûr")
        if identifier in identifiers:
            raise ReviewError(f"Identifiant de jalon dupliqué : {identifier}")
        identifiers.add(identifier)
        review_types = _string_list(value["review_types"], f"{context}.review_types")
        if not review_types or not set(review_types) <= ALLOWED_REVIEW_TYPES:
            raise ReviewError(
                f"{context}.review_types doit utiliser : {', '.join(sorted(ALLOWED_REVIEW_TYPES))}"
            )
        baseline = value["git_baseline"]
        if baseline is not None:
            baseline = _string(baseline, f"{context}.git_baseline")
        parsed_milestones.append(
            Milestone(
                identifier=identifier,
                condition=_string(value["condition"], f"{context}.condition"),
                review_types=review_types,
                focus_paths=_string_list(value["focus_paths"], f"{context}.focus_paths", paths=True, globs=True),
                git_baseline=baseline,
            )
        )

    return Policy(
        project_name=_string(project["name"], "project.name"),
        language=_string(project["language"], "project.language"),
        model=model,
        effort=effort,
        timeout_minutes=_integer(claude["timeout_minutes"], "claude.timeout_minutes", 1, 120),
        max_turns=_integer(claude["max_turns"], "claude.max_turns", 1, 200),
        report_directory=report_directory,
        context_files=context_files,
        max_files=_integer(snapshot["max_files"], "snapshot.max_files", 1, 1_000_000),
        max_bytes=_integer(snapshot["max_bytes"], "snapshot.max_bytes", 1, 100 * 1024**3),
        extra_excludes=extra_excludes,
        milestones=tuple(parsed_milestones),
    )


def migrate_policy(data: dict[str, Any]) -> dict[str, Any]:
    """Explicitly migrate the only legacy draft schema to version 1."""
    version = data.get("schema_version")
    if version == SCHEMA_VERSION:
        validate_policy(data)
        return json.loads(json.dumps(data))
    if version != 0:
        raise ReviewError(f"Aucune migration explicite disponible depuis schema_version {version!r}")
    migrated = json.loads(json.dumps(data))
    migrated["schema_version"] = SCHEMA_VERSION
    claude = migrated.get("claude")
    snapshot = migrated.get("snapshot")
    if not isinstance(claude, dict) or not isinstance(snapshot, dict):
        raise ReviewError("Le brouillon version 0 doit contenir les objets claude et snapshot")
    claude.setdefault("max_turns", 40)
    snapshot.setdefault("max_files", 20_000)
    snapshot.setdefault("max_bytes", 262_144_000)
    validate_policy(migrated)
    return migrated


def load_policy(project_root: Path) -> tuple[dict[str, Any], Policy]:
    raw = load_json(project_root / CONFIG_RELATIVE)
    return raw, validate_policy(raw)


def _agents_block(language: str) -> str:
    if language.lower().startswith("fr"):
        body = (
            "## Revue indépendante Claude\n\n"
            "Lorsque `.codex/claude-review.json` existe, utiliser `$claude-independent-review` aux jalons applicables "
            "avant de livrer le résultat. Les revues initiales configurées sont préautorisées après annonce ; "
            "toute contre-revue exige une confirmation explicite."
        )
    else:
        body = (
            "## Independent Claude review\n\n"
            "When `.codex/claude-review.json` exists, use `$claude-independent-review` at applicable milestones "
            "before handing off the result. Configured initial reviews are pre-authorized after an announcement; "
            "every counter-review requires explicit confirmation."
        )
    return f"{AGENTS_START}\n{body}\n{AGENTS_END}"


def render_agents(existing: str | None, language: str) -> str:
    block = _agents_block(language)
    if existing is None or not existing.strip():
        return block + "\n"
    has_start = AGENTS_START in existing
    has_end = AGENTS_END in existing
    if has_start != has_end:
        raise ReviewError("Bloc claude-independent-review incomplet dans AGENTS.md ; arbitrage manuel requis")
    if has_start:
        if existing.count(AGENTS_START) != 1 or existing.count(AGENTS_END) != 1:
            raise ReviewError("Plusieurs blocs claude-independent-review dans AGENTS.md ; arbitrage manuel requis")
        start = existing.index(AGENTS_START)
        end = existing.index(AGENTS_END, start) + len(AGENTS_END)
        return existing[:start] + block + existing[end:]
    separator = "" if existing.endswith("\n\n") else "\n" if existing.endswith("\n") else "\n\n"
    return existing + separator + block + "\n"


def _atomic_write(path: Path, content: bytes, *, replace: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise ReviewError(f"Refus d'écraser un fichier existant : {path}")
    temporary: Path | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        temporary = Path(temporary_name)
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        if not replace and path.exists():
            raise ReviewError(f"Refus d'écraser un fichier existant : {path}")
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _ensure_output_within(project_root: Path, path: Path, context: str) -> None:
    if path.is_symlink():
        raise ReviewError(f"{context} ne peut pas être un lien symbolique : {path}")
    resolved = path.resolve(strict=False)
    try:
        resolved.relative_to(project_root.resolve())
    except ValueError as exc:
        raise ReviewError(f"{context} sortirait de la racine du projet : {path}") from exc


def install_policy(project_root: Path, proposal_path: Path, replace: bool) -> None:
    raw = load_json(proposal_path)
    policy = validate_policy(raw)
    project_root.mkdir(parents=True, exist_ok=True)
    config_path = project_root / CONFIG_RELATIVE
    agents_path = project_root / "AGENTS.md"
    _ensure_output_within(project_root, config_path, "Politique")
    _ensure_output_within(project_root, agents_path, "Pointeur AGENTS.md")
    if config_path.exists() and not replace:
        raise ReviewError("Une politique existe déjà ; présenter les différences puis utiliser --replace")
    old_config = config_path.read_bytes() if config_path.exists() else None
    old_agents = agents_path.read_bytes() if agents_path.exists() else None
    existing_agents = old_agents.decode("utf-8") if old_agents is not None else None
    rendered_agents = render_agents(existing_agents, policy.language).encode("utf-8")
    rendered_config = (json.dumps(raw, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    try:
        _atomic_write(config_path, rendered_config, replace=True)
        _atomic_write(agents_path, rendered_agents, replace=True)
    except Exception:
        try:
            if old_config is None:
                config_path.unlink(missing_ok=True)
            else:
                _atomic_write(config_path, old_config, replace=True)
            if old_agents is None:
                agents_path.unlink(missing_ok=True)
            else:
                _atomic_write(agents_path, old_agents, replace=True)
        finally:
            codex_directory = project_root / ".codex"
            if codex_directory.exists() and not any(codex_directory.iterdir()):
                codex_directory.rmdir()
        raise


def _run(command: Sequence[str], cwd: Path, *, check: bool = True, timeout: int = 30) -> subprocess.CompletedProcess[bytes]:
    try:
        completed = subprocess.run(
            list(command), cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ReviewError(f"Commande de diagnostic impossible : {command[0]}: {exc}") from exc
    if check and completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        raise ReviewError(f"Commande échouée ({command[0]}): {stderr or completed.returncode}")
    return completed


def git_root(project_root: Path) -> Path | None:
    if shutil.which("git") is None:
        return None
    completed = _run(["git", "rev-parse", "--show-toplevel"], project_root, check=False)
    if completed.returncode != 0:
        return None
    root = Path(completed.stdout.decode("utf-8", errors="strict").strip()).resolve()
    if root != project_root.resolve():
        raise ReviewError(f"Utiliser la racine Git comme --project : {root}")
    return root


def _normalize(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _matches(path: str, patterns: Iterable[str]) -> bool:
    normalized = _normalize(path)
    parts = PurePosixPath(normalized).parts
    for raw in patterns:
        pattern = _normalize(raw).rstrip("/")
        if not pattern:
            continue
        if "/" not in pattern and not any(char in pattern for char in "*?["):
            if pattern in parts:
                return True
        if fnmatch.fnmatchcase(normalized, pattern) or fnmatch.fnmatchcase(normalized, f"{pattern}/**"):
            return True
        if normalized == pattern or normalized.startswith(pattern + "/"):
            return True
    return False


def _hard_secret(path: str) -> bool:
    normalized = _normalize(path)
    lower = normalized.lower()
    name = PurePosixPath(lower).name
    if name == ".env" or name.startswith(".env."):
        return not name.endswith(SAFE_ENV_SUFFIXES)
    if name in HARD_SECRET_NAMES or PurePosixPath(name).suffix in HARD_SECRET_EXTENSIONS:
        return True
    if re.fullmatch(r"id_(rsa|dsa|ecdsa|ed25519)(\..*)?", name):
        return True
    if name.startswith("service-account") and name.endswith(".json"):
        return True
    if name.startswith("secrets.") or name == "secrets":
        return True
    return lower.endswith("/.aws/credentials") or lower.endswith("/.azure/accesstokens.json")


def _included(path: str, include_patterns: Sequence[str]) -> bool:
    if not include_patterns:
        return True
    return _matches(path, include_patterns)


def _candidate_from_path(project_root: Path, relative: str) -> Candidate | None:
    source = project_root / Path(relative)
    try:
        mode = source.lstat().st_mode
    except FileNotFoundError:
        return Candidate(relative=relative, source=source, size=0, kind="missing")
    if stat.S_ISLNK(mode):
        target_text = os.readlink(source)
        resolved = source.resolve(strict=False)
        try:
            resolved.relative_to(project_root)
        except ValueError:
            return Candidate(relative=relative, source=source, size=0, kind="external_symlink", link_target=target_text)
        if resolved.is_file():
            return Candidate(
                relative=relative,
                source=resolved,
                size=resolved.stat().st_size,
                kind="materialized_symlink",
                link_target=target_text,
            )
        return Candidate(relative=relative, source=source, size=0, kind="directory_symlink", link_target=target_text)
    if stat.S_ISREG(mode):
        return Candidate(relative=relative, source=source, size=source.stat().st_size)
    return Candidate(relative=relative, source=source, size=0, kind="special")


def _git_paths(project_root: Path) -> list[str]:
    completed = _run(["git", "ls-files", "-co", "--exclude-standard", "-z"], project_root)
    return sorted({_normalize(item.decode("utf-8", errors="replace")) for item in completed.stdout.split(b"\0") if item})


def _walk_paths(project_root: Path, report_directory: str) -> list[str]:
    paths: list[str] = []
    report_parts = PurePosixPath(report_directory).parts
    for current, directories, files in os.walk(project_root, topdown=True, followlinks=False):
        current_path = Path(current)
        relative_current = current_path.relative_to(project_root).as_posix()
        kept: list[str] = []
        for directory in directories:
            relative = directory if relative_current == "." else f"{relative_current}/{directory}"
            if directory in DEFAULT_EXCLUDED_DIRS or _matches(relative, [report_directory]):
                continue
            if (current_path / directory).is_symlink():
                paths.append(relative)
                continue
            kept.append(directory)
        directories[:] = kept
        for filename in files:
            relative = filename if relative_current == "." else f"{relative_current}/{filename}"
            if report_parts and _matches(relative, [report_directory]):
                continue
            paths.append(relative)
    return sorted(set(paths))


def _largest_directories(candidates: Sequence[Candidate]) -> list[tuple[str, int]]:
    totals: dict[str, int] = {}
    for candidate in candidates:
        head = PurePosixPath(candidate.relative).parts[0] if PurePosixPath(candidate.relative).parts else "."
        totals[head] = totals.get(head, 0) + candidate.size
    return sorted(totals.items(), key=lambda item: item[1], reverse=True)[:8]


def _select_candidates(
    project_root: Path,
    policy: Policy,
    git_mode: bool,
    include_patterns: Sequence[str],
) -> tuple[list[Candidate], list[dict[str, str]]]:
    raw_paths = _git_paths(project_root) if git_mode else _walk_paths(project_root, policy.report_directory)
    candidates: list[Candidate] = []
    excluded: list[dict[str, str]] = []
    default_patterns = [policy.report_directory, ".codex"] if git_mode else [*DEFAULT_EXCLUDED_DIRS, policy.report_directory]
    for relative in raw_paths:
        if _hard_secret(relative):
            excluded.append({"path": relative, "reason": "hard_secret"})
            continue
        if _matches(relative, default_patterns):
            excluded.append({"path": relative, "reason": "default_exclusion"})
            continue
        if _matches(relative, policy.extra_excludes):
            excluded.append({"path": relative, "reason": "policy_exclusion"})
            continue
        context_match = relative in policy.context_files
        if not context_match and not _included(relative, include_patterns):
            excluded.append({"path": relative, "reason": "approved_scope"})
            continue
        candidate = _candidate_from_path(project_root, relative)
        if candidate is not None:
            candidates.append(candidate)

    included_paths = {candidate.relative for candidate in candidates if candidate.kind not in {"missing", "special", "external_symlink", "directory_symlink"}}
    missing_context = [path for path in policy.context_files if path not in included_paths]
    if missing_context:
        raise ReviewError(
            "Sources de vérité absentes ou exclues du snapshot : " + ", ".join(missing_context)
        )
    count = sum(candidate.kind in {"file", "materialized_symlink"} for candidate in candidates)
    byte_count = sum(candidate.size for candidate in candidates if candidate.kind in {"file", "materialized_symlink"})
    if count > policy.max_files or byte_count > policy.max_bytes:
        raise ScopeTooLarge(count, byte_count, _largest_directories(candidates))
    return candidates, excluded


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _untracked_patch(project_root: Path, included_paths: set[str]) -> str:
    result = _run(["git", "ls-files", "--others", "--exclude-standard", "-z"], project_root)
    fragments: list[str] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = _normalize(raw.decode("utf-8", errors="replace"))
        if relative not in included_paths:
            continue
        source = project_root / relative
        try:
            content = source.read_bytes()
        except OSError:
            continue
        if b"\0" in content[:8192]:
            fragments.append(f"diff --git a/{relative} b/{relative}\nnew file mode 100644\nBinary file {relative} added\n")
            continue
        text = content.decode("utf-8", errors="replace").splitlines(keepends=True)
        fragments.extend(
            difflib.unified_diff([], text, fromfile="/dev/null", tofile=f"b/{relative}", n=80)
        )
    return "".join(fragments)


def _git_diff(project_root: Path, baseline: str, included_paths: set[str]) -> str:
    _run(["git", "rev-parse", "--verify", f"{baseline}^{{commit}}"], project_root)
    changed_result = _run(["git", "diff", "--name-only", "-z", baseline, "--"], project_root)
    changed = [
        _normalize(item.decode("utf-8", errors="surrogateescape"))
        for item in changed_result.stdout.split(b"\0")
        if item
    ]
    selected = sorted({path for path in changed if path in included_paths})
    fragments: list[bytes] = []
    total = 0
    for offset in range(0, len(selected), 100):
        batch = selected[offset : offset + 100]
        completed = _run(
            ["git", "diff", "--no-ext-diff", "--no-textconv", "--unified=80", baseline, "--", *batch],
            project_root,
            timeout=120,
        )
        fragments.append(completed.stdout)
        total += len(completed.stdout)
        if total > MAX_DIFF_BYTES:
            raise ScopeTooLarge(len(selected), total, [("diff.patch", total)])
    tracked_patch = b"".join(fragments).decode("utf-8", errors="replace")
    combined = tracked_patch + _untracked_patch(project_root, included_paths)
    if len(combined.encode("utf-8")) > MAX_DIFF_BYTES:
        raise ScopeTooLarge(len(selected), len(combined.encode("utf-8")), [("diff.patch", len(combined.encode("utf-8")))])
    return combined


def build_snapshot(
    project_root: Path,
    policy: Policy,
    temporary_root: Path,
    include_patterns: Sequence[str],
    baseline: str | None,
    audit_context: Sequence[Path],
    test_evidence: Sequence[Path],
) -> Snapshot:
    detected_git_root = git_root(project_root)
    git_mode = detected_git_root is not None
    candidates, excluded = _select_candidates(project_root, policy, git_mode, include_patterns)
    snapshot_root = temporary_root / "snapshot"
    snapshot_root.mkdir()
    entries: list[dict[str, Any]] = []
    fingerprint = hashlib.sha256()
    included_paths: set[str] = set()
    for candidate in sorted(candidates, key=lambda item: item.relative):
        entry: dict[str, Any] = {"path": candidate.relative, "status": candidate.kind, "size": candidate.size}
        if candidate.link_target is not None:
            entry["link_target"] = candidate.link_target
        fingerprint.update(candidate.relative.encode("utf-8", errors="surrogateescape"))
        fingerprint.update(b"\0")
        fingerprint.update(candidate.kind.encode("ascii"))
        fingerprint.update(b"\0")
        if candidate.kind in {"file", "materialized_symlink"}:
            destination = snapshot_root / Path(candidate.relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(candidate.source, destination)
            digest = _sha256_file(destination)
            entry["sha256"] = digest
            fingerprint.update(digest.encode("ascii"))
            fingerprint.update(b"\0")
        if candidate.kind not in {"special", "external_symlink", "directory_symlink"}:
            included_paths.add(candidate.relative)
        entries.append(entry)

    git_commit: str | None = None
    git_state: str | None = None
    effective_baseline: str | None = None
    diff_text: str | None = None
    if git_mode:
        git_commit = _run(["git", "rev-parse", "HEAD"], project_root).stdout.decode("ascii", errors="replace").strip()
        git_state = _run(["git", "status", "--porcelain=v1", "--untracked-files=all"], project_root).stdout.decode(
            "utf-8", errors="replace"
        )
        effective_baseline = baseline or "HEAD"
        diff_text = _git_diff(project_root, effective_baseline, included_paths)

    evidence_root = snapshot_root / EVIDENCE_DIRNAME
    evidence_root.mkdir()
    audit_items: list[str] = []
    audit_total = 0
    for index, source in enumerate(audit_context, start=1):
        resolved = source.resolve()
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise ReviewError(f"Contexte d'audit hors projet : {source}") from exc
        if _hard_secret(resolved.relative_to(project_root).as_posix()) or not resolved.is_file():
            raise ReviewError(f"Contexte d'audit interdit ou absent : {source}")
        audit_total += resolved.stat().st_size
        if resolved.stat().st_size > 10 * 1024 * 1024 or audit_total > 50 * 1024 * 1024:
            raise ReviewError("Contexte d'audit trop volumineux (10 Mio par fichier, 50 Mio au total)")
        destination = evidence_root / "audit-context" / f"{index:02d}-{resolved.name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolved, destination)
        audit_items.append(destination.relative_to(snapshot_root).as_posix())

    test_items: list[str] = []
    test_total = 0
    for index, source in enumerate(test_evidence, start=1):
        resolved = source.resolve()
        if not resolved.is_file():
            raise ReviewError(f"Preuve de test absente : {source}")
        if resolved.stat().st_size > 5 * 1024 * 1024:
            raise ReviewError(f"Preuve de test trop volumineuse (> 5 Mio) : {source}")
        test_total += resolved.stat().st_size
        if test_total > 20 * 1024 * 1024:
            raise ReviewError("Preuves de test trop volumineuses (> 20 Mio au total)")
        destination = evidence_root / "test-evidence" / f"{index:02d}-{resolved.name}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(resolved, destination)
        test_items.append(destination.relative_to(snapshot_root).as_posix())

    manifest = {
        "schema_version": 1,
        "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project": policy.project_name,
        "repository_type": "git" if git_mode else "directory",
        "snapshot_sha256": fingerprint.hexdigest(),
        "file_count": sum(entry["status"] in {"file", "materialized_symlink"} for entry in entries),
        "total_bytes": sum(entry["size"] for entry in entries if entry["status"] in {"file", "materialized_symlink"}),
        "include_patterns": list(include_patterns),
        "files": entries,
        "excluded": excluded,
        "audit_context": audit_items,
        "test_evidence": test_items,
        "git": {
            "commit": git_commit,
            "baseline": effective_baseline,
            "status_porcelain": git_state,
        }
        if git_mode
        else None,
    }
    (evidence_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if diff_text:
        (evidence_root / "diff.patch").write_text(diff_text, encoding="utf-8")
    return Snapshot(
        root=snapshot_root,
        manifest=manifest,
        git_mode=git_mode,
        git_commit=git_commit,
        git_baseline=effective_baseline,
        git_state=git_state,
        diff_text=diff_text,
        excluded=excluded,
    )


def _milestones(policy: Policy, identifiers: Sequence[str]) -> list[Milestone]:
    mapping = {milestone.identifier: milestone for milestone in policy.milestones}
    missing = [identifier for identifier in identifiers if identifier not in mapping]
    if missing:
        raise ReviewError("Jalons inconnus : " + ", ".join(missing))
    return [mapping[identifier] for identifier in identifiers]


def _read_mission(path: str | None, direct: str | None) -> str:
    if direct is not None:
        mission = direct
    elif path == "-":
        mission = sys.stdin.read()
    elif path:
        try:
            mission = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            raise ReviewError(f"Mission illisible : {path}: {exc}") from exc
    else:
        raise ReviewError("Fournir --mission ou --mission-file")
    if not mission.strip():
        raise ReviewError("La mission de revue est vide")
    if len(mission.encode("utf-8")) > 2 * 1024 * 1024:
        raise ReviewError("La mission dépasse 2 Mio")
    return mission


def compose_prompt(
    mission: str,
    policy: Policy,
    snapshot: Snapshot,
    review_kind: str,
    review_types: Sequence[str],
    milestone_ids: Sequence[str],
    focus_paths: Sequence[str],
) -> str:
    audit_paths = snapshot.manifest["audit_context"]
    test_paths = snapshot.manifest["test_evidence"]
    diff_path = f"{EVIDENCE_DIRNAME}/diff.patch" if snapshot.diff_text else "aucun diff Git disponible"
    return textwrap.dedent(
        f"""
        Tu réalises une {'contre-revue' if review_kind == 'counter' else 'revue initiale'} indépendante.

        Projet : {policy.project_name}
        Langue de réponse : {policy.language}
        Angles : {', '.join(review_types)}
        Jalons : {', '.join(milestone_ids) if milestone_ids else 'demande ponctuelle'}
        Focalisation : {', '.join(focus_paths) if focus_paths else 'ensemble du projet filtré'}
        Sources de vérité déclarées : {', '.join(policy.context_files) if policy.context_files else 'aucune'}

        Mission exacte de l'utilisateur ou de Codex :
        ---
        {mission.rstrip()}
        ---

        Le snapshot est figé et filtré. Son manifeste se trouve dans `{EVIDENCE_DIRNAME}/manifest.json`.
        Diff examiné : `{diff_path}`.
        Contexte d'audit explicitement fourni : {', '.join(audit_paths) if audit_paths else 'aucun'}.
        Preuves brutes de tests déjà exécutés par Codex : {', '.join(test_paths) if test_paths else 'aucune'}.

        Applique le mandat de contrôleur indépendant. Inspecte toi-même les fichiers utiles. Retourne uniquement
        le rapport Markdown ; n'offre pas d'appliquer les corrections et ne demande aucune permission supplémentaire.
        """
    ).strip() + "\n"


def doctor(claude_command: str) -> dict[str, str]:
    resolved = shutil.which(claude_command)
    if not resolved:
        raise ReviewError("Claude Code est introuvable dans PATH. Installer Claude Code puis exécuter `claude auth login`.")
    executable = str(Path(resolved).resolve())
    base = Path.cwd()
    version = _run([executable, "--version"], base).stdout.decode("utf-8", errors="replace").strip()
    auth = _run([executable, "auth", "status", "--text"], base).stdout.decode("utf-8", errors="replace").strip()
    help_text = _run([executable, "--help"], base).stdout.decode("utf-8", errors="replace")
    missing = sorted(flag for flag in REQUIRED_HELP_FLAGS if flag not in help_text)
    if missing:
        raise ReviewError("Claude Code ne prend pas en charge les verrous requis : " + ", ".join(missing))
    return {"claude": executable, "version": version, "auth": auth}


def invoke_claude(
    claude_command: str,
    snapshot: Snapshot,
    policy: Policy,
    prompt: str,
    mandate_path: Path,
) -> tuple[str, dict[str, Any], str]:
    diagnostic = doctor(claude_command)
    mandate = mandate_path.read_text(encoding="utf-8")
    command = [
        diagnostic["claude"],
        "-p",
        "--safe-mode",
        "--model",
        policy.model,
        "--effort",
        policy.effort,
        "--permission-mode",
        "dontAsk",
        "--tools",
        "Read,Glob,Grep",
        "--strict-mcp-config",
        "--disable-slash-commands",
        "--no-chrome",
        "--no-session-persistence",
        "--max-turns",
        str(policy.max_turns),
        "--output-format",
        "json",
        "--append-system-prompt",
        mandate,
    ]
    execution_environment = os.environ.copy()
    execution_environment["CLAUDE_CODE_EFFORT_LEVEL"] = policy.effort
    try:
        completed = subprocess.run(
            command,
            cwd=snapshot.root,
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=policy.timeout_minutes * 60,
            check=False,
            env=execution_environment,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReviewError(f"La revue Claude a dépassé {policy.timeout_minutes} minutes ; aucun artefact créé") from exc
    except OSError as exc:
        raise ReviewError(f"Impossible de lancer Claude Code : {exc}") from exc
    if completed.returncode != 0:
        stderr = completed.stderr.decode("utf-8", errors="replace").strip()
        if len(stderr) > 4000:
            stderr = stderr[-4000:]
        raise ReviewError(f"Claude Code a échoué ({completed.returncode}) : {stderr or 'aucun détail'}")
    try:
        envelope = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ReviewError("Claude Code n'a pas renvoyé une enveloppe JSON UTF-8 valide") from exc
    if not isinstance(envelope, dict) or not isinstance(envelope.get("result"), str) or not envelope["result"].strip():
        raise ReviewError("Claude Code n'a produit aucun rapport Markdown exploitable")
    usage = {
        key: envelope[key]
        for key in ("total_cost_usd", "duration_ms", "duration_api_ms", "num_turns", "usage", "modelUsage")
        if key in envelope
    }
    return envelope["result"], usage, diagnostic["version"]


def _slug(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized[:80] or "review"


def _fence(content: str) -> str:
    longest = max((len(match.group(0)) for match in re.finditer(r"`+", content)), default=0)
    marker = "`" * max(3, longest + 1)
    return f"{marker}text\n{content}{'' if content.endswith(chr(10)) else chr(10)}{marker}"


def render_report(
    policy: Policy,
    snapshot: Snapshot,
    prompt: str,
    response: str,
    usage: dict[str, Any],
    claude_version: str,
    review_kind: str,
    review_types: Sequence[str],
    milestone_ids: Sequence[str],
    report_stem: str,
) -> str:
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    evidence_base = f"evidence/{report_stem}"
    fields: list[tuple[str, Any]] = [
        ("document_type", "independent_review"),
        ("reviewer", "anthropic/claude-code"),
        ("review_kind", review_kind),
        ("review_types", list(review_types)),
        ("milestones", list(milestone_ids)),
        ("reviewed_at", timestamp),
        ("project", policy.project_name),
        ("language", policy.language),
        ("claude_model", policy.model),
        ("claude_effort", policy.effort),
        ("claude_code_version", claude_version),
        ("repository_type", "git" if snapshot.git_mode else "directory"),
        ("repository_commit", snapshot.git_commit or "unavailable"),
        ("repository_state", "dirty" if snapshot.git_state else "clean" if snapshot.git_mode else "unavailable"),
        ("git_baseline", snapshot.git_baseline or "unavailable"),
        ("snapshot_sha256", snapshot.manifest["snapshot_sha256"]),
        ("snapshot_file_count", snapshot.manifest["file_count"]),
        ("snapshot_bytes", snapshot.manifest["total_bytes"]),
        ("mission_sha256", hashlib.sha256(prompt.encode("utf-8")).hexdigest()),
        ("evidence_manifest", f"{evidence_base}/manifest.json"),
        ("evidence_diff", f"{evidence_base}/diff.patch" if snapshot.diff_text else "unavailable"),
        ("claude_usage", usage),
    ]
    frontmatter_lines = ["---"]
    for key, value in fields:
        if isinstance(value, (list, dict)):
            rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        elif isinstance(value, (int, float)):
            rendered = str(value)
        else:
            rendered = json.dumps(str(value), ensure_ascii=False)
        frontmatter_lines.append(f"{key}: {rendered}")
    frontmatter_lines.extend(["---", ""])
    french = policy.language.lower().startswith("fr")
    title = "Revue indépendante Claude" if french else "Independent Claude review"
    mission_heading = "Mission exacte transmise à Claude" if french else "Exact mission sent to Claude"
    response_heading = "Rapport original de Claude" if french else "Original Claude report"
    body = "\n".join(frontmatter_lines)
    body += f"# {title}\n\n## {mission_heading}\n\n{_fence(prompt)}\n\n## {response_heading}\n\n"
    body += response
    if not body.endswith("\n"):
        body += "\n"
    return body


def _unique_report_target(report_root: Path, base_slug: str) -> tuple[Path, Path, str]:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d-%H%M%S")
    base = f"{stamp}-{_slug(base_slug)}-claude"
    for index in range(1, 1000):
        stem = base if index == 1 else f"{base}-{index}"
        report = report_root / f"{stem}.md"
        evidence = report_root / "evidence" / stem
        if not report.exists() and not evidence.exists():
            return report, evidence, stem
    raise ReviewError("Impossible de réserver un nom de rapport unique")


def _missing_directories(path: Path, stop: Path) -> list[Path]:
    missing: list[Path] = []
    current = path
    while current != stop and not current.exists():
        missing.append(current)
        current = current.parent
    return missing


def _cleanup_empty(directories: Sequence[Path]) -> None:
    for directory in directories:
        try:
            directory.rmdir()
        except OSError:
            pass


def persist_audit(
    project_root: Path,
    policy: Policy,
    snapshot: Snapshot,
    prompt: str,
    response: str,
    usage: dict[str, Any],
    claude_version: str,
    review_kind: str,
    review_types: Sequence[str],
    milestone_ids: Sequence[str],
    slug: str,
) -> tuple[Path, Path]:
    report_root = project_root / Path(policy.report_directory)
    _ensure_output_within(project_root, report_root, "Répertoire de rapports")
    created_directories = _missing_directories(report_root, project_root)
    report_path, evidence_path, stem = _unique_report_target(report_root, slug)
    report_content = render_report(
        policy,
        snapshot,
        prompt,
        response,
        usage,
        claude_version,
        review_kind,
        review_types,
        milestone_ids,
        stem,
    ).encode("utf-8")
    with tempfile.TemporaryDirectory(prefix="claude-review-audit-") as staging_name:
        staging = Path(staging_name)
        staging_report = staging / report_path.name
        staging_evidence = staging / "evidence"
        staging_report.write_bytes(report_content)
        staging_evidence.mkdir()
        source_manifest = snapshot.root / EVIDENCE_DIRNAME / "manifest.json"
        shutil.copyfile(source_manifest, staging_evidence / "manifest.json")
        if snapshot.diff_text:
            shutil.copyfile(snapshot.root / EVIDENCE_DIRNAME / "diff.patch", staging_evidence / "diff.patch")
        report_created = False
        evidence_created = False
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            descriptor = os.open(report_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(staging_report.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            report_created = True
            evidence_path.parent.mkdir(parents=True, exist_ok=True)
            evidence_path.mkdir()
            evidence_created = True
            for source in staging_evidence.iterdir():
                _atomic_write(evidence_path / source.name, source.read_bytes(), replace=False)
        except Exception as exc:
            if evidence_created:
                shutil.rmtree(evidence_path, ignore_errors=True)
            if report_created:
                report_path.unlink(missing_ok=True)
            _cleanup_empty([evidence_path.parent, *created_directories])
            if isinstance(exc, ReviewError):
                raise
            raise ReviewError(f"Impossible de persister les artefacts d'audit : {exc}") from exc
    return report_path, evidence_path


def command_review(arguments: argparse.Namespace, skill_root: Path) -> dict[str, Any]:
    project_root = Path(arguments.project).resolve()
    if not project_root.is_dir():
        raise ReviewError(f"Racine de projet absente : {project_root}")
    _, policy = load_policy(project_root)
    selected_milestones = _milestones(policy, arguments.milestone)
    configured_types = [item for milestone in selected_milestones for item in milestone.review_types]
    review_types = list(dict.fromkeys(arguments.review_type or configured_types or ["general"]))
    if not set(review_types) <= ALLOWED_REVIEW_TYPES:
        raise ReviewError("Type de revue inconnu")
    focus_paths = list(dict.fromkeys(path for milestone in selected_milestones for path in milestone.focus_paths))
    baseline_values = {milestone.git_baseline for milestone in selected_milestones if milestone.git_baseline}
    if arguments.baseline:
        baseline = arguments.baseline
    elif len(baseline_values) == 1:
        baseline = next(iter(baseline_values))
    elif len(baseline_values) > 1:
        raise ReviewError("Les jalons combinés ont des bases Git incompatibles ; fournir --baseline")
    else:
        baseline = None
    mission = _read_mission(arguments.mission_file, arguments.mission)
    audit_context = [Path(value).resolve() if Path(value).is_absolute() else project_root / value for value in arguments.audit_context]
    test_evidence = [Path(value).resolve() if Path(value).is_absolute() else project_root / value for value in arguments.test_evidence]
    if arguments.kind == "counter" and not audit_context:
        raise ReviewError("Une contre-revue exige au moins un --audit-context")
    with tempfile.TemporaryDirectory(prefix="claude-independent-review-") as temporary_name:
        snapshot = build_snapshot(
            project_root,
            policy,
            Path(temporary_name),
            arguments.include,
            baseline,
            audit_context,
            test_evidence,
        )
        prompt = compose_prompt(
            mission,
            policy,
            snapshot,
            arguments.kind,
            review_types,
            arguments.milestone,
            focus_paths,
        )
        response, usage, claude_version = invoke_claude(
            arguments.claude,
            snapshot,
            policy,
            prompt,
            skill_root / "references/reviewer-mandate.md",
        )
        slug = arguments.slug or "-".join(arguments.milestone) or "independent-review"
        if arguments.kind == "counter" and "counter" not in slug:
            slug += "-counter-review"
        report_path, evidence_path = persist_audit(
            project_root,
            policy,
            snapshot,
            prompt,
            response,
            usage,
            claude_version,
            arguments.kind,
            review_types,
            arguments.milestone,
            slug,
        )
    return {
        "status": "created",
        "report": str(report_path),
        "evidence": str(evidence_path),
        "snapshot_sha256": snapshot.manifest["snapshot_sha256"],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor_parser = subparsers.add_parser("doctor", help="Vérifier Claude Code et ses verrous")
    doctor_parser.add_argument("--claude", default="claude")

    validate_parser = subparsers.add_parser("validate-config", help="Valider la politique d'un projet")
    validate_parser.add_argument("--project", required=True)

    install_parser = subparsers.add_parser("install-policy", help="Installer une politique validée et son pointeur")
    install_parser.add_argument("--project", required=True)
    install_parser.add_argument("--config", required=True)
    install_parser.add_argument("--replace", action="store_true")

    migrate_parser = subparsers.add_parser("migrate-config", help="Migrer explicitement un ancien brouillon")
    migrate_parser.add_argument("--input", required=True)
    migrate_parser.add_argument("--output", required=True)

    review_parser = subparsers.add_parser("review", help="Créer une revue Claude et ses preuves d'audit")
    review_parser.add_argument("--project", required=True)
    mission_group = review_parser.add_mutually_exclusive_group(required=True)
    mission_group.add_argument("--mission")
    mission_group.add_argument("--mission-file")
    review_parser.add_argument("--kind", choices=("initial", "counter"), default="initial")
    review_parser.add_argument("--review-type", action="append", choices=sorted(ALLOWED_REVIEW_TYPES), default=[])
    review_parser.add_argument("--milestone", action="append", default=[])
    review_parser.add_argument("--baseline")
    review_parser.add_argument("--include", action="append", default=[])
    review_parser.add_argument("--test-evidence", action="append", default=[])
    review_parser.add_argument("--audit-context", action="append", default=[])
    review_parser.add_argument("--slug")
    review_parser.add_argument("--claude", default="claude")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    skill_root = Path(__file__).resolve().parents[1]
    try:
        if arguments.command == "doctor":
            result: Any = {"status": "ready", **doctor(arguments.claude)}
        elif arguments.command == "validate-config":
            project_root = Path(arguments.project).resolve()
            _, policy = load_policy(project_root)
            result = {
                "status": "valid",
                "project": policy.project_name,
                "schema_version": SCHEMA_VERSION,
                "milestones": [milestone.identifier for milestone in policy.milestones],
            }
        elif arguments.command == "install-policy":
            project_root = Path(arguments.project).resolve()
            install_policy(project_root, Path(arguments.config).resolve(), arguments.replace)
            result = {
                "status": "installed",
                "config": str(project_root / CONFIG_RELATIVE),
                "agents": str(project_root / "AGENTS.md"),
            }
        elif arguments.command == "migrate-config":
            migrated = migrate_policy(load_json(Path(arguments.input).resolve()))
            output_path = Path(arguments.output).resolve()
            _atomic_write(
                output_path,
                (json.dumps(migrated, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
                replace=False,
            )
            result = {"status": "migrated", "schema_version": SCHEMA_VERSION, "output": str(output_path)}
        else:
            result = command_review(arguments, skill_root)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ScopeTooLarge as exc:
        print(
            json.dumps(
                {
                    "status": "scope_too_large",
                    "error": str(exc),
                    "file_count": exc.file_count,
                    "byte_count": exc.byte_count,
                    "largest_directories": exc.largest,
                },
                ensure_ascii=False,
                indent=2,
            ),
            file=sys.stderr,
        )
        return 78
    except ReviewError as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    except (OSError, UnicodeError) as exc:
        print(
            json.dumps({"status": "error", "error": f"Erreur d'entrée-sortie : {exc}"}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
