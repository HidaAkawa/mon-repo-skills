#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


MODULE_PATH = Path(__file__).with_name("migrate-v3-to-v4.py")
SPEC = importlib.util.spec_from_file_location("migrate_v3_to_v4", MODULE_PATH)
assert SPEC and SPEC.loader
migration = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = migration
SPEC.loader.exec_module(migration)


def legacy_state(phase=3, **extra):
    value = {
        "schema_version": 3,
        "version": "v2",
        "phase": phase,
        "phase_nom": "legacy",
        "iteration": 2,
        "profil": {"code": "assiste", "niveau_archi": "notion", "discipline_process": "forte"},
        "type_projet": "web",
        "origine": "neuf",
        "garantie_requise": {"niveau": "renforce", "motifs": ["partagé"], "reviser_si": []},
        "hypotheses_ouvertes": [{"id": "ASM-001"}],
        "derogations": [],
        "dernier_commit": "abc123",
    }
    value.update(extra)
    return value


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


class MigrationTests(unittest.TestCase):
    def project(self, container: str, phase=3, **extra) -> Path:
        root = Path(container) / "project"
        root.mkdir()
        write_json(root / ".sdp/etat.json", legacy_state(phase, **extra))
        return root

    def test_maps_every_v3_phase(self):
        expected = {
            0: "initiate-and-frame",
            "0-bis": "initiate-and-frame",
            0.5: "initiate-and-frame",
            1: "initiate-and-frame",
            2: "define",
            3: "define",
            4: "build",
            5: "verify",
            6: "release-and-improve",
            7: "release-and-improve",
        }
        for phase, stage in expected.items():
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as container:
                root = self.project(container, phase)
                state = migration.build_v4_state(root, legacy_state(phase))
                self.assertEqual(state["stage"]["id"], stage)

    def test_plan_is_read_only_and_maps_profile_guarantee(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container)
            result = migration.plan(root)
            self.assertEqual(result["status"], "planned")
            self.assertEqual(result["profile"], {
                "development": "collaborative",
                "operations": "collaborative",
                "assurance": "autonomous",
            })
            self.assertEqual(result["guarantee"]["level"], "elevated")
            self.assertFalse((root / ".sdp/state.json").exists())
            self.assertFalse((root / ".gitignore").exists())

    def test_normalizes_v3_assumptions_and_derogations_without_losing_fields(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(
                container,
                hypotheses_ouvertes=[
                    {
                        "id": "HYP-007",
                        "decision": "Le fournisseur répond en moins de 2 s",
                        "raison": "SLA inconnu",
                        "confiance": "faible",
                    },
                    "Le volume reste inférieur à 1000 éléments",
                ],
                derogations=[{"id": "OLD-2", "description": "Scan différé", "autorite": "Alice"}],
            )

            state = migration.build_v4_state(root, migration._load_json(root / ".sdp/etat.json"))

            first, second = state["assumptions"]
            self.assertEqual(first["id"], "ASM-001")
            self.assertEqual(first["legacy_id"], "HYP-007")
            self.assertEqual(first["statement"], "Le fournisseur répond en moins de 2 s")
            self.assertEqual(first["confiance"], "faible")
            self.assertEqual(second["id"], "ASM-002")
            self.assertEqual(second["legacy_value"], "Le volume reste inférieur à 1000 éléments")
            derogation = state["derogations"][0]
            self.assertEqual(derogation["id"], "DRG-001")
            self.assertEqual(derogation["legacy_id"], "OLD-2")
            self.assertEqual(derogation["authority"], "Alice")
            for item in (*state["assumptions"], *state["derogations"]):
                self.assertTrue({"id", "statement", "status", "owner"} <= set(item))

    def test_apply_is_atomic_idempotent_and_preserves_legacy(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container, custom_extension={"keep": True})
            first = migration.apply(root)
            self.assertEqual(first["status"], "applied")
            self.assertTrue((root / ".sdp/etat.json").exists())
            state = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["migration"]["unmapped_fields"]["custom_extension"], {"keep": True})
            self.assertEqual(state["reviews"]["counter_reviews"]["maximum"], 3)
            self.assertIsNone(state["stage"]["gate"])
            self.assertEqual(len(state["documents"]), 6)
            self.assertEqual(state["documents"]["SRS-001"]["status"], "planned")
            self.assertEqual((root / ".gitignore").read_text(encoding="utf-8"), "/docs/reviews/\n")
            second = migration.apply(root)
            self.assertEqual(second["status"], "already-migrated")
            self.assertEqual((root / ".gitignore").read_text(encoding="utf-8"), "/docs/reviews/\n")

    def test_atomic_failure_leaves_no_state(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container)
            with mock.patch.object(migration, "_atomic_json", side_effect=OSError("fixture interruption")):
                with self.assertRaisesRegex(OSError, "fixture interruption"):
                    migration.apply(root)
            self.assertFalse((root / ".sdp/state.json").exists())
            self.assertFalse((root / ".gitignore").exists())
            self.assertTrue((root / ".sdp/etat.json").exists())

    def test_rejects_divergent_coexisting_states(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container)
            migration.apply(root)
            state_path = root / ".sdp/state.json"
            legacy_path = root / ".sdp/etat.json"
            legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
            legacy["iteration"] = 99
            write_json(legacy_path, legacy)
            with self.assertRaisesRegex(migration.MigrationError, "divergé"):
                migration.plan(root)
            self.assertTrue(state_path.exists())

    def test_rejects_invalid_or_unknown_source(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container, schema_version=2)
            with self.assertRaisesRegex(migration.MigrationError, "Schéma source"):
                migration.plan(root)
            (root / ".sdp/etat.json").write_text("not-json", encoding="utf-8")
            with self.assertRaisesRegex(migration.MigrationError, "JSON illisible"):
                migration.plan(root)

    def test_finalize_requires_documents_then_preserves_sources(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container, phase=3)
            (root / "docs").mkdir()
            (root / "docs/objectif.md").write_text("legacy objective\n", encoding="utf-8")
            migration.apply(root)
            with self.assertRaisesRegex(migration.MigrationError, "manquants"):
                migration.finalize(root)
            for relative in (
                "docs/document-register.md",
                "docs/project-charter.md",
                "docs/software-requirements-specification.md",
                "docs/software-development-plan.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("consolidated\n", encoding="utf-8")
            result = migration.finalize(root)
            self.assertEqual(result["status"], "finalized")
            self.assertTrue((root / "docs/objectif.md").exists())
            state = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(state["migration"]["status"], "completed")
            self.assertEqual(state["migration"]["legacy_documents"][0]["status"], "superseded")
            self.assertEqual(migration.finalize(root)["status"], "already-finalized")

    def test_finalize_refuses_modified_or_missing_legacy_documents(self):
        for action, message in (("modify", "modifié"), ("remove", "absent")):
            with self.subTest(action=action), tempfile.TemporaryDirectory() as container:
                root = self.project(container, phase=1)
                legacy_doc = root / "docs/objectif.md"
                legacy_doc.parent.mkdir()
                legacy_doc.write_text("original\n", encoding="utf-8")
                migration.apply(root)
                for relative in ("docs/document-register.md", "docs/project-charter.md"):
                    target = root / relative
                    target.write_text("consolidated\n", encoding="utf-8")
                if action == "modify":
                    legacy_doc.write_text("changed\n", encoding="utf-8")
                else:
                    legacy_doc.unlink()
                with self.assertRaisesRegex(migration.MigrationError, message):
                    migration.finalize(root)

    def test_inventories_documented_v3_debt_traceability_and_annexes(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container, phase=3)
            paths = (
                "BACKLOG.md",
                "DETTE.md",
                "docs/qualite/traceabilite.md",
                "docs/adr/ADR-0001.md",
                "docs/decisions/ADR-0002.md",
                "docs/runbooks/outage.md",
                "docs/releases/v1.md",
            )
            for relative in paths:
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative + "\n", encoding="utf-8")

            result = migration.plan(root)

            inventoried = {item["path"]: item for item in result["legacy_documents"]}
            self.assertEqual(set(inventoried), set(paths))
            self.assertEqual(inventoried["docs/adr/ADR-0001.md"]["status"], "retained-annex")
            self.assertEqual(inventoried["docs/releases/v1.md"]["status"], "retained-canonical")

    @unittest.skipUnless(shutil.which("git"), "git absent")
    def test_document_baseline_only_claims_paths_present_in_legacy_commit(self):
        with tempfile.TemporaryDirectory() as container:
            root = self.project(container, phase=1)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
            legacy_charter = root / "docs/project-charter.md"
            legacy_charter.parent.mkdir()
            legacy_charter.write_text("legacy canonical\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "legacy"], cwd=root, check=True)
            commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=root, check=True, capture_output=True, text=True
            ).stdout.strip()
            legacy = migration._load_json(root / ".sdp/etat.json")
            legacy["dernier_commit"] = commit
            write_json(root / ".sdp/etat.json", legacy)

            state = migration.build_v4_state(root, legacy)

            self.assertEqual(state["documents"]["PRJ-CHTR-001"]["baseline"], f"git:{commit}")
            self.assertEqual(state["documents"]["DOC-REG-001"]["baseline"], "git:pending")


if __name__ == "__main__":
    unittest.main(verbosity=2)
