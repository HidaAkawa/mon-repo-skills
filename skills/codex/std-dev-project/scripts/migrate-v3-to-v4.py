#!/usr/bin/env python3
"""Plan, apply, and finalize a non-destructive std-dev-project v3 migration."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
from typing import Any


V3_STATE = Path(".sdp/etat.json")
V4_STATE = Path(".sdp/state.json")
IGNORE_RULE = "/docs/reviews/"
STAGES = {
    0: "initiate-and-frame",
    0.5: "initiate-and-frame",
    1: "initiate-and-frame",
    2: "define",
    3: "define",
    4: "build",
    5: "verify",
    6: "release-and-improve",
    7: "release-and-improve",
}
COUNTER_REVIEW_BUDGETS = {"standard": 2, "elevated": 3, "critical": 4}

LEGACY_DOCUMENTS = {
    "docs/index.md": "docs/document-register.md",
    "docs/objectif.md": "docs/project-charter.md",
    "docs/brouillon-objectif.md": "docs/project-charter.md",
    "docs/spec-fonctionnelle.md": "docs/software-requirements-specification.md",
    "docs/spec-nf.md": "docs/software-requirements-specification.md",
    "docs/brouillon-spec-fonctionnelle.md": "docs/software-requirements-specification.md",
    "docs/brouillon-spec-nf.md": "docs/software-requirements-specification.md",
    "docs/architecture.md": "docs/software-development-plan.md",
    "docs/observabilite.md": "docs/software-development-plan.md",
    "docs/qualite/strategie-tests.md": "docs/software-development-plan.md",
    "docs/securite/modele-menaces.md": "docs/software-development-plan.md",
    "docs/journal-dev.md": "docs/verification/{version}.md",
    "docs/feedback.md": "docs/verification/{version}.md",
    "docs/qualite/rapport-tests.md": "docs/verification/{version}.md",
    "docs/qualite/validation-observabilite.md": "docs/verification/{version}.md",
    "docs/qualite/traceabilite.md": "docs/software-requirements-specification.md",
    "BACKLOG.md": "docs/releases/{version}.md",
    "DETTE.md": "docs/releases/{version}.md",
}

RETAINED_DOCUMENT_GLOBS = (
    "docs/adr/*.md",
    "docs/decisions/*.md",
    "docs/runbooks/*.md",
    "docs/releases/*.md",
)

DOCUMENT_SPECS = (
    ("DOC-REG-001", "docs/document-register.md"),
    ("PRJ-CHTR-001", "docs/project-charter.md"),
    ("SRS-001", "docs/software-requirements-specification.md"),
    ("SDP-001", "docs/software-development-plan.md"),
    ("VVR-{version}", "docs/verification/{version}.md"),
    ("REL-{version}", "docs/releases/{version}.md"),
)


class MigrationError(RuntimeError):
    pass


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise MigrationError(f"État absent : {path}") from exc
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MigrationError(f"État JSON illisible : {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise MigrationError("L'état doit être un objet JSON")
    return value


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(character for character in text if not unicodedata.combining(character)).lower().strip()


def _stage(value: Any) -> str:
    if _normalize(value).replace("_", "-") in {"0-bis", "0bis"}:
        return "initiate-and-frame"
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise MigrationError(f"Phase v3 invalide : {value!r}") from exc
    key: int | float = int(number) if number.is_integer() else number
    if key not in STAGES:
        raise MigrationError(f"Aucune correspondance v4 pour la phase {value!r}")
    return STAGES[key]


def _profile(legacy: dict[str, Any]) -> dict[str, str]:
    raw = legacy.get("profil") if isinstance(legacy.get("profil"), dict) else {}
    return {
        "development": {"non": "guided", "assiste": "collaborative", "oui": "autonomous"}.get(
            _normalize(raw.get("code")), "guided"
        ),
        "operations": {
            "debutant": "guided",
            "notion": "collaborative",
            "confirme": "autonomous",
        }.get(_normalize(raw.get("niveau_archi")), "guided"),
        "assurance": {
            "faible": "guided",
            "moyenne": "collaborative",
            "forte": "autonomous",
        }.get(_normalize(raw.get("discipline_process")), "guided"),
    }


def _guarantee(legacy: dict[str, Any]) -> tuple[str, list[Any], list[Any]]:
    raw = legacy.get("garantie_requise")
    if not isinstance(raw, dict):
        raw = legacy.get("assurance") if isinstance(legacy.get("assurance"), dict) else {}
    level = {"essentiel": "standard", "renforce": "elevated", "critique": "critical"}.get(
        _normalize(raw.get("niveau")), "standard"
    )
    reasons = raw.get("motifs") if isinstance(raw.get("motifs"), list) else []
    review_if = raw.get("reviser_si") if isinstance(raw.get("reviser_si"), list) else []
    return level, reasons, review_if


def _archetype(value: Any) -> str:
    normalized = _normalize(value)
    aliases = {
        "web": "web",
        "api": "api",
        "mobile": "mobile",
        "cli": "cli",
        "script": "cli",
        "bibliotheque": "library",
        "library": "library",
        "batch": "batch",
        "distributed": "distributed",
        "distribue": "distributed",
    }
    return aliases.get(normalized, "cli")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _legacy_documents(root: Path, version: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    mappings = dict(LEGACY_DOCUMENTS)
    for relative, target in sorted(mappings.items()):
        path = root / relative
        if path.is_file():
            items.append(
                {
                    "path": relative,
                    "sha256": _sha256(path),
                    "target": target.format(version=version),
                    "status": "pending-consolidation",
                }
            )
    inventoried = {item["path"] for item in items}
    for pattern in RETAINED_DOCUMENT_GLOBS:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if relative in inventoried:
                continue
            items.append(
                {
                    "path": relative,
                    "sha256": _sha256(path),
                    "target": relative,
                    "status": "retained-canonical" if relative.startswith("docs/releases/") else "retained-annex",
                }
            )
            inventoried.add(relative)
    return items


def _document_status(path: Path) -> str:
    if not path.is_file():
        return "planned"
    try:
        head = path.read_text(encoding="utf-8")[:4096]
    except (OSError, UnicodeError):
        return "in-review"
    match = re.search(r"(?m)^status:\s*[\"']?([a-z-]+)", head)
    if match and match.group(1) in {"draft", "in-review", "approved", "superseded"}:
        return match.group(1)
    return "in-review"


def _path_exists_at_commit(root: Path, commit: Any, relative: str) -> bool:
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit.strip()):
        return False
    try:
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{relative}"],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def _git_head(root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    value = result.stdout.strip()
    return value if result.returncode == 0 and re.fullmatch(r"[0-9a-fA-F]{40,64}", value) else None


def _document_register(root: Path, version: str, last_commit: Any) -> dict[str, dict[str, Any]]:
    documents: dict[str, dict[str, Any]] = {}
    for identifier, relative_template in DOCUMENT_SPECS:
        relative = relative_template.format(version=version)
        baseline = f"git:{last_commit}" if _path_exists_at_commit(root, last_commit, relative) else "git:pending"
        documents[identifier.format(version=version)] = {
            "path": relative,
            "status": _document_status(root / relative),
            "version": version,
            "baseline": baseline,
        }
    return documents


def _unmapped_fields(legacy: dict[str, Any]) -> dict[str, Any]:
    recognized = {
        "schema_version",
        "version",
        "phase",
        "phase_nom",
        "iteration",
        "profil",
        "type_projet",
        "origine",
        "garantie_requise",
        "assurance",
        "complexite",
        "observabilite",
        "hypotheses_ouvertes",
        "verrouille",
        "derogations",
        "dernier_commit",
        "maj",
    }
    return {key: value for key, value in legacy.items() if key not in recognized}


def _identified_items(values: list[Any], prefix: str, *, derogation: bool = False) -> list[dict[str, Any]]:
    pattern = re.compile(rf"^{re.escape(prefix)}-\d{{3,}}$")
    reserved = {
        str(item.get("id"))
        for item in values
        if isinstance(item, dict) and pattern.fullmatch(str(item.get("id", "")))
    }
    next_number = 1
    normalized: list[dict[str, Any]] = []
    for raw in values:
        item = dict(raw) if isinstance(raw, dict) else {"legacy_value": raw}
        old_id = item.get("id")
        if isinstance(old_id, str) and pattern.fullmatch(old_id):
            identifier = old_id
        else:
            while f"{prefix}-{next_number:03d}" in reserved:
                next_number += 1
            identifier = f"{prefix}-{next_number:03d}"
            reserved.add(identifier)
            next_number += 1
            if old_id is not None:
                item["legacy_id"] = old_id
        statement = next(
            (
                item[key]
                for key in ("statement", "decision", "description", "hypothese", "raison", "legacy_value")
                if key in item and item[key] not in (None, "")
            ),
            "À qualifier après migration",
        )
        item["id"] = identifier
        item.setdefault("statement", statement)
        item.setdefault("status", "open")
        item.setdefault("owner", item.get("proprietaire", "unassigned"))
        if derogation:
            item.setdefault("authority", item.get("autorite", "unassigned"))
        else:
            item.setdefault("source", "v3-migration")
        normalized.append(item)
    return normalized


def build_v4_state(root: Path, legacy: dict[str, Any]) -> dict[str, Any]:
    if legacy.get("schema_version") != 3:
        raise MigrationError(f"Schéma source non pris en charge : {legacy.get('schema_version')!r}; attendu : 3")
    stage = _stage(legacy.get("phase"))
    level, reasons, review_if = _guarantee(legacy)
    archetype = _archetype(legacy.get("type_projet"))
    version = str(legacy.get("version") or "v1")
    iteration = legacy.get("iteration", 1)
    if not isinstance(iteration, int) or iteration < 1:
        iteration = 1
    mode = "claude" if (root / ".codex/claude-review.json").is_file() else "external-prompt"
    legacy_documents = _legacy_documents(root, version)
    raw_assumptions = legacy.get("hypotheses_ouvertes") if isinstance(legacy.get("hypotheses_ouvertes"), list) else []
    raw_derogations = legacy.get("derogations") if isinstance(legacy.get("derogations"), list) else []
    assumptions = _identified_items(raw_assumptions, "ASM")
    derogations = _identified_items(raw_derogations, "DRG", derogation=True)
    return {
        "schema_version": 4,
        "method_version": "4.0",
        "project": {
            "name": root.name,
            "origin": "reconstruction" if _normalize(legacy.get("origine")) == "archeologie" else "new",
            "archetype": archetype,
        },
        "stage": {"id": stage, "status": "in-progress", "iteration": iteration, "gate": None},
        "profile": _profile(legacy),
        "guarantee": {"level": level, "reasons": reasons, "review_if": review_if},
        "baseline": {
            "id": f"BL-{archetype.upper()}-{level.upper()}-v1",
            "catalog_version": "1.0",
            "overrides": [],
        },
        "assumptions": assumptions,
        "risks": [],
        "derogations": derogations,
        "reviews": {
            "mode": mode,
            "authorization": {"source": "v3-migration", "version": version, "granted": False},
            "counter_reviews": {"maximum": COUNTER_REVIEW_BUDGETS[level], "used": 0},
            "milestones": [],
            "reports": [],
        },
        "delivery": {
            "working_version": version,
            "candidate_version": None,
            "forge": "none",
            "branch": None,
            "change_request_url": None,
            "ci_status": "not-configured",
        },
        "documents": _document_register(root, version, legacy.get("dernier_commit")),
        "last_commit": legacy.get("dernier_commit"),
        "updated_at": _today(),
        "migration": {
            "from_schema": 3,
            "status": "planned",
            "legacy_state_path": V3_STATE.as_posix(),
            "legacy_state_sha256": _sha256(root / V3_STATE),
            "legacy_documents": legacy_documents,
            "unmapped_fields": _unmapped_fields(legacy),
        },
    }


def _atomic_json(path: Path, value: dict[str, Any]) -> None:
    _atomic_bytes(
        path,
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    )


def _atomic_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _ensure_ignore(root: Path) -> bool:
    path = root / ".gitignore"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    lines = existing.splitlines()
    if IGNORE_RULE in lines:
        return False
    separator = "" if not existing or existing.endswith(("\n", "\r")) else "\n"
    _atomic_bytes(path, (existing + separator + IGNORE_RULE + "\n").encode("utf-8"))
    return True


def _restore_file(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        _atomic_bytes(path, previous)


def _tracked_reviews(root: Path) -> list[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--", "docs/reviews"],
            cwd=root,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    return [line for line in result.stdout.splitlines() if line]


def _validate_existing_v4(root: Path, state: dict[str, Any]) -> None:
    if state.get("schema_version") != 4:
        raise MigrationError(f"state.json existe avec un schéma inconnu : {state.get('schema_version')!r}")
    legacy_path = root / V3_STATE
    if not legacy_path.exists():
        return
    migration = state.get("migration")
    if not isinstance(migration, dict) or migration.get("from_schema") != 3:
        raise MigrationError("Conflit : les états v3 et v4 coexistent sans provenance de migration")
    if migration.get("legacy_state_sha256") != _sha256(legacy_path):
        raise MigrationError("Conflit : l'état v3 a divergé depuis la création de l'état v4")


def plan(root: Path) -> dict[str, Any]:
    state_path = root / V4_STATE
    if state_path.exists():
        state = _load_json(state_path)
        _validate_existing_v4(root, state)
        return {"status": "already-migrated", "state": V4_STATE.as_posix(), "stage": state.get("stage")}
    legacy = _load_json(root / V3_STATE)
    state = build_v4_state(root, legacy)
    return {
        "status": "planned",
        "state": V4_STATE.as_posix(),
        "stage": state["stage"],
        "profile": state["profile"],
        "guarantee": state["guarantee"],
        "baseline": state["baseline"],
        "legacy_documents": state["migration"]["legacy_documents"],
        "writes": [V4_STATE.as_posix(), ".gitignore"],
        "tracked_review_warning": _tracked_reviews(root),
    }


def apply(root: Path) -> dict[str, Any]:
    state_path = root / V4_STATE
    if state_path.exists():
        state = _load_json(state_path)
        _validate_existing_v4(root, state)
        changed_ignore = _ensure_ignore(root)
        return {
            "status": "already-migrated",
            "state": V4_STATE.as_posix(),
            "gitignore_updated": changed_ignore,
            "tracked_review_warning": _tracked_reviews(root),
        }
    legacy = _load_json(root / V3_STATE)
    state = build_v4_state(root, legacy)
    state["migration"]["status"] = "applied"
    gitignore_path = root / ".gitignore"
    old_gitignore = gitignore_path.read_bytes() if gitignore_path.exists() else None
    changed_ignore = _ensure_ignore(root)
    try:
        _atomic_json(state_path, state)
    except Exception:
        if changed_ignore:
            _restore_file(gitignore_path, old_gitignore)
        raise
    return {
        "status": "applied",
        "state": V4_STATE.as_posix(),
        "legacy_state_preserved": (root / V3_STATE).is_file(),
        "gitignore_updated": changed_ignore,
        "tracked_review_warning": _tracked_reviews(root),
    }


def _required_documents(state: dict[str, Any]) -> list[str]:
    required = ["docs/document-register.md", "docs/project-charter.md"]
    stage = state.get("stage", {}).get("id")
    if stage in {"define", "build", "verify", "release-and-improve"}:
        required.extend(["docs/software-requirements-specification.md", "docs/software-development-plan.md"])
    version = state.get("delivery", {}).get("working_version", "v1")
    if stage in {"verify", "release-and-improve"}:
        required.append(f"docs/verification/{version}.md")
    if stage == "release-and-improve":
        required.append(f"docs/releases/{version}.md")
    return required


def finalize(root: Path) -> dict[str, Any]:
    path = root / V4_STATE
    state = _load_json(path)
    _validate_existing_v4(root, state)
    migration = state.get("migration")
    if not isinstance(migration, dict) or migration.get("from_schema") != 3:
        raise MigrationError("Aucune migration v3 à finaliser")
    missing = [relative for relative in _required_documents(state) if not (root / relative).is_file()]
    if missing:
        raise MigrationError("Documents consolidés manquants : " + ", ".join(missing))
    if migration.get("status") == "completed":
        return {"status": "already-finalized", "state": V4_STATE.as_posix()}
    for item in migration.get("legacy_documents", []):
        if isinstance(item, dict):
            source = root / str(item.get("path", ""))
            if not source.is_file():
                raise MigrationError(f"Document historique absent avant finalisation : {item.get('path')}")
            if item.get("sha256") != _sha256(source):
                raise MigrationError(f"Document historique modifié depuis l'analyse : {item.get('path')}")
            if item.get("status") in {"retained-annex", "retained-canonical"}:
                item["status"] = "validated-retained"
            else:
                item["status"] = "superseded"
    candidate_commit = _git_head(root) or state.get("last_commit")
    state["last_commit"] = candidate_commit
    state["documents"] = _document_register(
        root,
        state.get("delivery", {}).get("working_version", "v1"),
        candidate_commit,
    )
    migration["status"] = "completed"
    migration["completed_at"] = _today()
    state["updated_at"] = _today()
    _atomic_json(path, state)
    return {
        "status": "finalized",
        "state": V4_STATE.as_posix(),
        "legacy_files_preserved": True,
        "superseded_count": sum(
            1 for item in migration.get("legacy_documents", []) if isinstance(item, dict) and item.get("status") == "superseded"
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--apply", action="store_true")
    action.add_argument("--finalize", action="store_true")
    arguments = parser.parse_args(argv)
    root = Path(arguments.project).resolve()
    if not root.is_dir():
        print(json.dumps({"status": "error", "error": f"Projet absent : {root}"}), file=sys.stderr)
        return 2
    try:
        result = finalize(root) if arguments.finalize else apply(root) if arguments.apply else plan(root)
    except (MigrationError, OSError, UnicodeError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
