#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("claude_review.py")
SPEC = importlib.util.spec_from_file_location("claude_review", MODULE_PATH)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


def policy_data(**overrides):
    data = {
        "schema_version": 1,
        "project": {"name": "Fixture", "language": "fr"},
        "claude": {
            "model": "claude-sonnet-5",
            "effort": "high",
            "timeout_minutes": 1,
            "max_turns": 40,
        },
        "reports": {"directory": "docs/reviews"},
        "context_files": ["AGENTS.md"],
        "snapshot": {"max_files": 20000, "max_bytes": 262144000, "extra_excludes": []},
        "milestones": [
            {
                "id": "lot-ready",
                "condition": "Le lot est prêt.",
                "review_types": ["code"],
                "focus_paths": ["src/**"],
                "git_baseline": "HEAD",
            }
        ],
    }
    data.update(overrides)
    return data


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def make_fake_claude(directory: Path) -> Path:
    executable = directory / "fake-claude"
    executable.write_text(
        """#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
log = os.environ.get('FAKE_CLAUDE_LOG')
if log:
    with open(log, 'w', encoding='utf-8') as stream:
        json.dump(args, stream)
if args == ['--version']:
    print('9.9.9 (Fake Claude Code)')
elif args == ['auth', 'status', '--text']:
    print('Login method: fixture')
elif args == ['--help']:
    print('--safe-mode --tools --permission-mode --strict-mcp-config --disable-slash-commands --no-chrome --no-session-persistence --output-format --model --effort --append-system-prompt')
else:
    prompt = sys.stdin.read()
    mode = os.environ.get('FAKE_CLAUDE_MODE', 'success')
    if mode == 'failure':
        print('fixture failure', file=sys.stderr)
        raise SystemExit(75)
    if mode == 'invalid-json':
        print('not-json')
    elif mode == 'empty':
        print(json.dumps({'result': '   '}))
    else:
        result = os.environ.get('FAKE_CLAUDE_RESULT', '# Revue\\n\\n## Verdict\\nPASS')
        print(json.dumps({'result': result, 'num_turns': 3, 'usage': {'input_tokens': 10}, 'prompt_seen': bool(prompt)}))
""",
        encoding="utf-8",
    )
    executable.chmod(0o755)
    return executable


@contextlib.contextmanager
def temporary_environment(**values):
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update({key: str(value) for key, value in values.items()})
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


class ConfigurationTests(unittest.TestCase):
    def test_validates_version_one_and_rejects_aliases(self):
        parsed = review.validate_policy(policy_data())
        self.assertEqual(parsed.model, "claude-sonnet-5")
        invalid = policy_data()
        invalid["claude"]["model"] = "sonnet"
        with self.assertRaisesRegex(review.ReviewError, "alias mouvant"):
            review.validate_policy(invalid)

    def test_rejects_unknown_schema_without_implicit_migration(self):
        invalid = policy_data(schema_version=2)
        with self.assertRaisesRegex(review.ReviewError, "Aucune migration implicite"):
            review.validate_policy(invalid)

    def test_explicitly_migrates_legacy_draft_without_mutating_source(self):
        legacy = policy_data(schema_version=0)
        del legacy["claude"]["max_turns"]
        del legacy["snapshot"]["max_files"]
        del legacy["snapshot"]["max_bytes"]
        migrated = review.migrate_policy(legacy)
        self.assertEqual(legacy["schema_version"], 0)
        self.assertEqual(migrated["schema_version"], 1)
        self.assertEqual(migrated["claude"]["max_turns"], 40)
        self.assertEqual(migrated["snapshot"]["max_files"], 20000)
        review.validate_policy(migrated)

    def test_installs_pointer_idempotently_and_preserves_agents(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            proposal = root.parent / f"{root.name}-proposal.json"
            write_json(proposal, policy_data())
            (root / "AGENTS.md").write_text("# Existing\n\nKeep me.\n", encoding="utf-8")
            review.install_policy(root, proposal, replace=False)
            first = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn("Keep me.", first)
            self.assertEqual(first.count(review.AGENTS_START), 1)
            with self.assertRaisesRegex(review.ReviewError, "existe déjà"):
                review.install_policy(root, proposal, replace=False)
            review.install_policy(root, proposal, replace=True)
            second = (root / "AGENTS.md").read_text(encoding="utf-8")
            self.assertEqual(second.count(review.AGENTS_START), 1)
            self.assertIn("Keep me.", second)
            proposal.unlink()

    def test_rejects_partial_agents_marker_before_writing(self):
        with tempfile.TemporaryDirectory() as root_name:
            root = Path(root_name)
            proposal = root.parent / f"{root.name}-proposal.json"
            write_json(proposal, policy_data())
            (root / "AGENTS.md").write_text(review.AGENTS_START + "\n", encoding="utf-8")
            with self.assertRaisesRegex(review.ReviewError, "incomplet"):
                review.install_policy(root, proposal, replace=False)
            self.assertFalse((root / review.CONFIG_RELATIVE).exists())
            proposal.unlink()

    def test_rejects_duplicate_agents_blocks(self):
        block = review.render_agents(None, "fr")
        with self.assertRaisesRegex(review.ReviewError, "Plusieurs blocs"):
            review.render_agents(block + "\n" + block, "fr")

    def test_rejects_policy_directory_symlink_outside_project(self):
        with tempfile.TemporaryDirectory() as root_name, tempfile.TemporaryDirectory() as outside_name:
            root = Path(root_name)
            proposal = root.parent / f"{root.name}-proposal.json"
            write_json(proposal, policy_data())
            (root / ".codex").symlink_to(Path(outside_name), target_is_directory=True)
            with self.assertRaisesRegex(review.ReviewError, "sortirait"):
                review.install_policy(root, proposal, replace=False)
            self.assertEqual(list(Path(outside_name).iterdir()), [])
            proposal.unlink()


class SnapshotTests(unittest.TestCase):
    def _installed_project(self, root: Path):
        proposal = root.parent / f"{root.name}-proposal.json"
        write_json(proposal, policy_data())
        review.install_policy(root, proposal, replace=False)
        proposal.unlink()
        return review.load_policy(root)[1]

    def test_non_git_snapshot_filters_secrets_reports_and_external_links(self):
        with tempfile.TemporaryDirectory() as root_name, tempfile.TemporaryDirectory() as temporary_name:
            root = Path(root_name)
            policy = self._installed_project(root)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("print('ok')\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            (root / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
            (root / "docs/reviews").mkdir(parents=True)
            (root / "docs/reviews/old.md").write_text("old\n", encoding="utf-8")
            outside = root.parent / f"{root.name}-outside.txt"
            outside.write_text("outside\n", encoding="utf-8")
            try:
                (root / "outside-link").symlink_to(outside)
                snapshot = review.build_snapshot(root, policy, Path(temporary_name), [], None, [], [])
            finally:
                outside.unlink(missing_ok=True)
            copied = {entry["path"]: entry for entry in snapshot.manifest["files"]}
            self.assertIn("src/app.py", copied)
            self.assertIn(".env.example", copied)
            self.assertNotIn(".env", copied)
            self.assertNotIn("docs/reviews/old.md", copied)
            self.assertEqual(copied["outside-link"]["status"], "external_symlink")
            self.assertFalse((snapshot.root / "outside-link").exists())

    def test_threshold_stops_before_copying(self):
        with tempfile.TemporaryDirectory() as root_name, tempfile.TemporaryDirectory() as temporary_name:
            root = Path(root_name)
            data = policy_data()
            data["snapshot"]["max_files"] = 1
            proposal = root.parent / f"{root.name}-proposal.json"
            write_json(proposal, data)
            review.install_policy(root, proposal, replace=False)
            proposal.unlink()
            (root / "one.txt").write_text("1", encoding="utf-8")
            (root / "two.txt").write_text("2", encoding="utf-8")
            with self.assertRaises(review.ScopeTooLarge):
                review.build_snapshot(root, review.load_policy(root)[1], Path(temporary_name), [], None, [], [])

    @unittest.skipUnless(shutil.which("git"), "git absent")
    def test_git_snapshot_keeps_filtered_tracked_and_untracked_diff(self):
        with tempfile.TemporaryDirectory() as root_name, tempfile.TemporaryDirectory() as temporary_name:
            root = Path(root_name)
            subprocess.run(["git", "init", "-q"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.email", "fixture@example.test"], cwd=root, check=True)
            subprocess.run(["git", "config", "user.name", "Fixture"], cwd=root, check=True)
            policy = self._installed_project(root)
            (root / "src").mkdir()
            (root / "src/app.py").write_text("value = 1\n", encoding="utf-8")
            (root / ".gitignore").write_text("ignored.txt\n.env\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=root, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
            (root / "src/app.py").write_text("value = 2\n", encoding="utf-8")
            (root / "src/new.py").write_text("new_value = 3\n", encoding="utf-8")
            (root / "ignored.txt").write_text("ignored\n", encoding="utf-8")
            (root / ".env").write_text("TOKEN=secret\n", encoding="utf-8")
            snapshot = review.build_snapshot(root, policy, Path(temporary_name), [], "HEAD", [], [])
            self.assertTrue(snapshot.git_mode)
            self.assertIn("-value = 1", snapshot.diff_text)
            self.assertIn("+value = 2", snapshot.diff_text)
            self.assertIn("new_value = 3", snapshot.diff_text)
            self.assertNotIn("TOKEN=secret", snapshot.diff_text)
            self.assertNotIn("ignored.txt", {entry["path"] for entry in snapshot.manifest["files"]})


class ReviewExecutionTests(unittest.TestCase):
    def _project_and_fake(self, container: Path):
        root = container / "project"
        root.mkdir()
        proposal = container / "proposal.json"
        write_json(proposal, policy_data())
        review.install_policy(root, proposal, replace=False)
        proposal.unlink()
        (root / "src").mkdir()
        (root / "src/app.py").write_text("def total(values):\n    return sum(values)\n", encoding="utf-8")
        fake = make_fake_claude(container)
        return root, fake

    def _invoke(self, root: Path, fake: Path, extra=None):
        arguments = [
            "review",
            "--project",
            str(root),
            "--mission",
            "Examiner le lot sans supposer qu'il est correct.",
            "--milestone",
            "lot-ready",
            "--claude",
            str(fake),
        ]
        if extra:
            arguments.extend(extra)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = review.main(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_success_preserves_exact_markdown_and_security_arguments(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            log = container / "claude-args.json"
            result = "# Rapport libre\n\n### [P2] Exemple\nPreuve exacte.\n"
            with temporary_environment(FAKE_CLAUDE_LOG=log, FAKE_CLAUDE_RESULT=result):
                status, output, error = self._invoke(root, fake)
            self.assertEqual(status, 0, error)
            payload = json.loads(output)
            report_path = Path(payload["report"])
            evidence_path = Path(payload["evidence"])
            report_text = report_path.read_text(encoding="utf-8")
            self.assertTrue(report_text.endswith(result))
            self.assertIn("Mission exacte transmise", report_text)
            self.assertTrue((evidence_path / "manifest.json").is_file())
            args = json.loads(log.read_text(encoding="utf-8"))
            for expected in [
                "--safe-mode",
                "--permission-mode",
                "dontAsk",
                "Read,Glob,Grep",
                "--strict-mcp-config",
                "--disable-slash-commands",
                "--no-chrome",
                "--no-session-persistence",
                "claude-sonnet-5",
                "high",
            ]:
                self.assertIn(expected, args)
            self.assertEqual(args[args.index("--tools") + 1], "Read,Glob,Grep")
            self.assertNotIn("--fallback-model", args)
            self.assertNotIn("--dangerously-skip-permissions", args)
            self.assertNotIn("Bash", args)
            project_names = {path.name for path in root.rglob("*")}
            self.assertNotIn(review.EVIDENCE_DIRNAME, project_names)
            self.assertFalse(any(name.startswith(".claude-review") for name in project_names))

    def test_failure_modes_leave_no_report_or_evidence(self):
        for mode in ("failure", "invalid-json", "empty"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as container_name:
                container = Path(container_name)
                root, fake = self._project_and_fake(container)
                with temporary_environment(FAKE_CLAUDE_MODE=mode):
                    status, _, _ = self._invoke(root, fake)
                self.assertNotEqual(status, 0)
                self.assertFalse((root / "docs/reviews").exists())
                self.assertFalse(any(path.name.startswith(".claude-review") for path in root.rglob("*")))

    def test_two_successes_never_overwrite(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            first, output_one, error_one = self._invoke(root, fake)
            second, output_two, error_two = self._invoke(root, fake)
            self.assertEqual(first, 0, error_one)
            self.assertEqual(second, 0, error_two)
            self.assertNotEqual(json.loads(output_one)["report"], json.loads(output_two)["report"])

    def test_counter_review_requires_audit_context(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            status, _, error = self._invoke(root, fake, ["--kind", "counter"])
            self.assertNotEqual(status, 0)
            self.assertIn("audit-context", error)
            self.assertFalse((root / "docs/reviews").exists())


@unittest.skipUnless(os.environ.get("RUN_LIVE_CLAUDE") == "1", "live Claude smoke test disabled")
class LiveClaudeSmokeTests(unittest.TestCase):
    def test_real_claude_reviews_disposable_fixture_without_leaks(self):
        container_path: Path | None = None
        with tempfile.TemporaryDirectory(prefix="claude-review-live-fixture-") as container_name:
            container = Path(container_name)
            container_path = container
            root = container / "project"
            root.mkdir()
            data = policy_data()
            data["context_files"] = ["AGENTS.md", "SPEC.md"]
            data["claude"]["timeout_minutes"] = 5
            proposal = container / "proposal.json"
            write_json(proposal, data)
            review.install_policy(root, proposal, replace=False)
            proposal.unlink()
            (root / "SPEC.md").write_text(
                "# Access policy\n\nGrant access only when the account is active and its role exactly matches the required role.\n",
                encoding="utf-8",
            )
            (root / "src").mkdir()
            (root / "src/access.py").write_text(
                "def is_allowed(user, required_role):\n    return user.active or user.role == required_role\n",
                encoding="utf-8",
            )
            (root / "tests").mkdir()
            (root / "tests/test_access.py").write_text(
                "from src.access import is_allowed\n\n\ndef test_matching_active_user():\n    user = type('User', (), {'active': True, 'role': 'admin'})()\n    assert is_allowed(user, 'admin')\n",
                encoding="utf-8",
            )
            stdout = io.StringIO()
            stderr = io.StringIO()
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                status = review.main(
                    [
                        "review",
                        "--project",
                        str(root),
                        "--mission",
                        "Review the current implementation against the specification. Report concrete correctness or security defects and material test gaps.",
                        "--milestone",
                        "lot-ready",
                    ]
                )
            self.assertEqual(status, 0, stderr.getvalue())
            payload = json.loads(stdout.getvalue())
            report_text = Path(payload["report"]).read_text(encoding="utf-8")
            self.assertIn("src/access.py", report_text)
            print("LIVE_CLAUDE_REPORT_START")
            print(report_text[-5000:])
            print("LIVE_CLAUDE_REPORT_END")
        assert container_path is not None
        self.assertFalse(container_path.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
