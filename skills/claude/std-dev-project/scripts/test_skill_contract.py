#!/usr/bin/env python3
"""Static contract checks for std-dev-project v4."""

from __future__ import annotations

import json
from pathlib import Path
import re
import unittest


SKILL_ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = SKILL_ROOT.parents[2]
REQUIRED_REFERENCES = {
    "workflow.md",
    "baselines.md",
    "independent-reviews.md",
    "migration-v4.md",
    "standards-profile.md",
}
REQUIRED_TEMPLATES = {
    "document-register.md",
    "project-charter.md",
    "software-requirements-specification.md",
    "software-development-plan.md",
    "verification-report.md",
    "release-record.md",
}
COMMON_METADATA = {
    "document_id",
    "document_type",
    "status",
    "version",
    "owner",
    "approvers",
    "created_at",
    "updated_at",
    "baseline",
    "applicable_standards",
}
ARCHETYPES = {"web", "api", "mobile", "cli", "library", "batch", "distributed"}
GUARANTEES = {"standard", "elevated", "critical"}
STAGES = {
    "initiate-and-frame",
    "define",
    "build",
    "verify",
    "release-and-improve",
}


def frontmatter(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise AssertionError(f"frontmatter absent : {path}")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise AssertionError(f"frontmatter non fermé : {path}") from exc
    values: dict[str, object] = {}
    for number, line in enumerate(lines[1:end], start=2):
        if not line.strip() or line.startswith((" ", "\t")):
            raise AssertionError(f"frontmatter non plat à {path}:{number}")
        if ":" not in line:
            raise AssertionError(f"entrée YAML invalide à {path}:{number}")
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        if not re.fullmatch(r"[a-z][a-z0-9_]*", key) or not raw:
            raise AssertionError(f"métadonnée invalide à {path}:{number}")
        if raw.startswith("["):
            try:
                values[key] = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise AssertionError(f"liste YAML/JSON invalide à {path}:{number}") from exc
        else:
            values[key] = raw.strip('"')
    return values


def local_links(path: Path):
    text = path.read_text(encoding="utf-8")
    for match in re.finditer(r"\[[^\]]+\]\(([^)]+)\)", text):
        target = match.group(1).strip().strip("<>").split("#", 1)[0]
        if not target or re.match(r"^[a-z][a-z0-9+.-]*://", target, re.IGNORECASE):
            continue
        yield target


class SkillContractTests(unittest.TestCase):
    def test_exact_reference_and_template_sets(self):
        references = {path.name for path in (SKILL_ROOT / "references").glob("*.md")}
        templates = {path.name for path in (SKILL_ROOT / "templates").glob("*.md")}
        self.assertEqual(references, REQUIRED_REFERENCES)
        self.assertEqual(templates, REQUIRED_TEMPLATES)

    def test_skill_and_templates_have_valid_frontmatter(self):
        skill_metadata = frontmatter(SKILL_ROOT / "SKILL.md")
        self.assertEqual(skill_metadata["name"], "std-dev-project")
        self.assertIn("description", skill_metadata)

        fixed_ids: list[str] = []
        for name in sorted(REQUIRED_TEMPLATES):
            path = SKILL_ROOT / "templates" / name
            self.assertTrue(name.isascii())
            self.assertRegex(name, r"^[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
            metadata = frontmatter(path)
            self.assertEqual(set(metadata), COMMON_METADATA)
            identifier = str(metadata["document_id"])
            if "{{" not in identifier:
                fixed_ids.append(identifier)
        self.assertEqual(len(fixed_ids), len(set(fixed_ids)))

    def test_all_local_markdown_links_resolve(self):
        markdown = [REPOSITORY_ROOT / "README.md"]
        markdown.extend(SKILL_ROOT.rglob("*.md"))
        reviewer = REPOSITORY_ROOT / "skills/claude/codex-independent-review"
        markdown.extend(reviewer.rglob("*.md"))
        broken = []
        for path in markdown:
            for target in local_links(path):
                if not (path.parent / target).resolve().exists():
                    broken.append(f"{path.relative_to(REPOSITORY_ROOT)} -> {target}")
        self.assertEqual(broken, [])

    def test_baseline_matrix_covers_all_twenty_one_profiles(self):
        text = (SKILL_ROOT / "references/baselines.md").read_text(encoding="utf-8")
        found_archetypes = {
            match.group(1)
            for match in re.finditer(r"^\| `([a-z]+)` \|", text, re.MULTILINE)
            if match.group(1) in ARCHETYPES
        }
        self.assertEqual(found_archetypes, ARCHETYPES)
        for guarantee in GUARANTEES:
            self.assertIn(f"`{guarantee}`", text)
        profiles = {f"BL-{a.upper()}-{g.upper()}-v1" for a in ARCHETYPES for g in GUARANTEES}
        self.assertEqual(len(profiles), 21)
        for domain in ("Sécurité", "Tests", "Performance", "Observabilité", "Revue"):
            self.assertRegex(text, rf"(?m)^\| {domain} \|")

    def test_workflow_declares_five_gates_six_documents_and_same_pr_rule(self):
        text = (SKILL_ROOT / "references/workflow.md").read_text(encoding="utf-8")
        normalized = " ".join(text.split())
        for stage in STAGES:
            self.assertIn(f"`{stage}`", text)
        self.assertEqual(text.count("**Gate :**"), 5)
        for document_path in (
            "docs/document-register.md",
            "docs/project-charter.md",
            "docs/software-requirements-specification.md",
            "docs/software-development-plan.md",
            "docs/verification/<version>.md",
            "docs/releases/<version>.md",
        ):
            self.assertIn(document_path, text)
        self.assertIn("chaque push actualise la même demande", normalized)
        self.assertIn("Ne jamais supprimer une branche non fusionnée", normalized)
        self.assertIn("committer le candidat", normalized)
        self.assertIn("vérifier que les chemins évalués sont propres", normalized)
        self.assertIn("ne se référence jamais lui-même", normalized)

    def test_review_and_migration_invariants_are_explicit(self):
        reviews = (SKILL_ROOT / "references/independent-reviews.md").read_text(encoding="utf-8")
        for budget in (2, 3, 4):
            self.assertRegex(reviews, rf"(?m)\| `(?:standard|elevated|critical)` .*\| {budget} \|")
        self.assertIn("/docs/reviews/", reviews)
        self.assertIn("SHA-256", reviews)
        self.assertIn("aucun P0–P2 retenu", reviews)

        migration = (SKILL_ROOT / "references/migration-v4.md").read_text(encoding="utf-8")
        self.assertIn("`0`, `0-bis`", migration)
        self.assertIn("`0.5`", migration)
        self.assertIn("--apply", migration)
        self.assertIn("--finalize", migration)
        self.assertIn("Aucun mode ne supprime", migration)

    def test_review_summary_and_id_register_follow_the_closed_contract(self):
        verification = (SKILL_ROOT / "templates/verification-report.md").read_text(encoding="utf-8")
        self.assertIn("| ID | Result | Decision | SHA-256 |", verification)
        self.assertNotIn("Archive reference", verification)
        workflow = (SKILL_ROOT / "references/workflow.md").read_text(encoding="utf-8")
        self.assertIn("`archive_reference`", workflow)
        register = (SKILL_ROOT / "templates/document-register.md").read_text(encoding="utf-8")
        for prefix in ("STK", "ADR"):
            self.assertRegex(register, rf"(?m)^\| {prefix} \|")


if __name__ == "__main__":
    unittest.main(verbosity=2)
