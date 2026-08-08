#!/usr/bin/env python3

from __future__ import annotations

import contextlib
import concurrent.futures
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("codex_review.py")
SPEC = importlib.util.spec_from_file_location("codex_review", MODULE_PATH)
assert SPEC and SPEC.loader
review = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = review
SPEC.loader.exec_module(review)


def policy_data(**overrides):
    data = {
        "schema_version": 1,
        "project": {"name": "Fixture", "language": "fr"},
        "codex": {
            "model": "gpt-5.6-terra",
            "effort": "high",
            "timeout_minutes": 1,
        },
        "reports": {"directory": "docs/reviews"},
        "context_files": ["CLAUDE.md"],
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


def sdp_state_data(*, level="standard", maximum=2, used=0, version="v1", milestone="lot-ready", mode="codex"):
    return {
        "schema_version": 4,
        "project": {"name": "Fixture", "origin": "new", "archetype": "api"},
        "stage": {"id": "verify", "status": "in-progress", "iteration": 1},
        "profile": {"development": "guided", "operations": "guided", "assurance": "guided"},
        "guarantee": {"level": level, "reasons": [], "review_if": []},
        "baseline": {"id": f"BL-API-{level.upper()}-v1", "catalog_version": "1.0", "overrides": []},
        "assumptions": [],
        "risks": [],
        "derogations": [],
        "reviews": {
            "mode": mode,
            "authorization": {"source": "std-dev-project-v4", "version": version, "granted": True},
            "counter_reviews": {"maximum": maximum, "used": used},
            "milestones": [{"id": milestone, "status": "open"}],
            "reports": [],
        },
        "delivery": {
            "working_version": version,
            "candidate_version": None,
            "forge": "none",
            "branch": None,
            "change_request_url": None,
            "ci_status": "local-green",
        },
        "documents": {},
        "last_commit": None,
        "updated_at": "2026-08-08",
    }


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


FAKE_CODEX_SOURCE = """#!/usr/bin/env python3
import json, os, sys, time
args = sys.argv[1:]
log = os.environ.get('FAKE_CODEX_LOG')
if log:
    with open(log, 'w', encoding='utf-8') as stream:
        json.dump(args, stream)
if args == ['--version']:
    print('codex-cli 9.9.9 (fixture)')
elif args == ['login', 'status']:
    print('Logged in: fixture')
elif args[:2] == ['exec', '--help']:
    flags = ['--sandbox', '--ephemeral', '--ignore-user-config', '--ignore-rules',
             '--strict-config', '--skip-git-repo-check', '--output-last-message',
             '--json', '--cd', '--model', '--config', '--color']
    if os.environ.get('FAKE_CODEX_DROP_FLAG'):
        flags.remove(os.environ['FAKE_CODEX_DROP_FLAG'])
    suffix = '' if os.environ.get('FAKE_CODEX_NO_SANDBOX') else ' read-only workspace-write'
    print(' '.join(flags) + suffix)
else:
    # The runner writes UTF-8 bytes; decode them as such rather than through
    # whatever the local console code page happens to be.
    prompt = sys.stdin.buffer.read().decode('utf-8')
    count = os.environ.get('FAKE_CODEX_COUNT')
    if count:
        with open(count, 'a', encoding='utf-8') as stream:
            stream.write('1\\n')
    if os.environ.get('FAKE_CODEX_PROMPT'):
        with open(os.environ['FAKE_CODEX_PROMPT'], 'w', encoding='utf-8') as stream:
            stream.write(prompt)
    mode = os.environ.get('FAKE_CODEX_MODE', 'success')
    delay = float(os.environ.get('FAKE_CODEX_DELAY', '0'))
    if delay:
        time.sleep(delay)
    if mode == 'failure':
        print('fixture failure', file=sys.stderr)
        raise SystemExit(75)
    if mode == 'large-stderr-failure':
        print('x' * 5000 + ' fixture tail', file=sys.stderr)
        raise SystemExit(76)
    target = None
    if '--output-last-message' in args:
        target = args[args.index('--output-last-message') + 1]
    print(json.dumps({'type': 'task_started'}), flush=True)
    print('not-json-at-all', flush=True)
    print(json.dumps({'type': 'exec_command_begin', 'command': 'rg secret'}), flush=True)
    print(json.dumps({'type': 'agent_message', 'message': 'draft content must stay private'}), flush=True)
    if mode == 'empty':
        payload = '   '
    else:
        payload = os.environ.get('FAKE_CODEX_RESULT', '# Revue\\n\\n## Verdict\\nPASS')
    if mode != 'no-output' and target:
        with open(target, 'w', encoding='utf-8') as stream:
            stream.write(payload)
"""


def make_fake_codex(directory: Path) -> Path:
    script = directory / "fake-codex.py"
    script.write_text(FAKE_CODEX_SOURCE, encoding="utf-8")
    if os.name == "nt":
        executable = directory / "fake-codex.cmd"
        executable.write_text(f'@"{sys.executable}" "{script}" %*\r\n', encoding="utf-8")
    else:
        executable = directory / "fake-codex"
        executable.write_text(f'#!/bin/sh\nexec "{sys.executable}" "{script}" "$@"\n', encoding="utf-8")
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
        policy = review.validate_policy(policy_data())
        self.assertEqual(policy.model, "gpt-5.6-terra")
        self.assertEqual(policy.effort, "high")
        self.assertEqual(policy.timeout_minutes, 1)
        for alias in ("codex", "gpt-5.6", "terra", "best"):
            with self.assertRaises(review.ReviewError):
                review.validate_policy(policy_data(codex={"model": alias, "effort": "high", "timeout_minutes": 20}))

    def test_rejects_max_turns_key_that_only_exists_in_the_claude_mirror(self):
        with self.assertRaises(review.ReviewError) as caught:
            review.validate_policy(
                policy_data(codex={"model": "gpt-5.6-terra", "effort": "high", "timeout_minutes": 20, "max_turns": 40})
            )
        self.assertIn("max_turns", str(caught.exception))

    def test_rejects_effort_outside_the_allowed_set(self):
        with self.assertRaises(review.ReviewError):
            review.validate_policy(
                policy_data(codex={"model": "gpt-5.6-terra", "effort": "ultra", "timeout_minutes": 20})
            )

    def test_rejects_unknown_schema_without_implicit_migration(self):
        with self.assertRaises(review.ReviewError):
            review.validate_policy(policy_data(schema_version=2))

    def test_explicitly_migrates_legacy_draft_dropping_max_turns(self):
        draft = policy_data(schema_version=0)
        draft["codex"] = {"model": "gpt-5.6-terra", "effort": "high", "max_turns": 40}
        draft["snapshot"] = {"extra_excludes": []}
        original = json.loads(json.dumps(draft))
        migrated = review.migrate_policy(draft)
        self.assertEqual(migrated["schema_version"], 1)
        self.assertNotIn("max_turns", migrated["codex"])
        self.assertEqual(migrated["codex"]["timeout_minutes"], 20)
        self.assertEqual(migrated["snapshot"]["max_files"], 20000)
        self.assertEqual(draft, original, "la migration ne doit jamais muter la source")

    def test_installs_pointer_in_claude_md_and_preserves_existing_content(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container) / "project"
            root.mkdir()
            (root / "CLAUDE.md").write_text("# Projet\n\nInstructions existantes.\n", encoding="utf-8")
            proposal = Path(container) / "proposal.json"
            write_json(proposal, policy_data())
            review.install_policy(root, proposal, replace=False)
            pointer = (root / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("Instructions existantes.", pointer)
            self.assertIn(review.POINTER_START, pointer)
            self.assertIn(".claude/codex-review.json", pointer)
            self.assertTrue((root / ".claude/codex-review.json").is_file())
            self.assertIn("/docs/reviews/", (root / ".gitignore").read_text(encoding="utf-8"))
            review.install_policy(root, proposal, replace=True)
            self.assertEqual((root / "CLAUDE.md").read_text(encoding="utf-8").count(review.POINTER_START), 1)

    def test_gitignore_rendering_is_idempotent(self):
        first = review.render_gitignore("build/\n", ("/docs/reviews/", "/audits/"))
        self.assertEqual(review.render_gitignore(first, ("/docs/reviews/", "/audits/")), first)

    def test_rejects_partial_pointer_marker_before_writing(self):
        with self.assertRaises(review.ReviewError):
            review.render_pointer(f"{review.POINTER_START}\nbloc tronqué\n", "fr")
        with self.assertRaises(review.ReviewError):
            review.render_pointer_without_block(f"{review.POINTER_START}\nbloc tronqué\n")

    def test_rejects_duplicate_pointer_blocks(self):
        doubled = review.render_pointer(None, "fr") + review.render_pointer(None, "fr")
        with self.assertRaises(review.ReviewError):
            review.render_pointer(doubled, "fr")

    def test_disables_policy_idempotently_without_touching_audit_artifacts(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container) / "project"
            root.mkdir()
            (root / "CLAUDE.md").write_text("# Projet\n\nÀ conserver.\n", encoding="utf-8")
            proposal = Path(container) / "proposal.json"
            write_json(proposal, policy_data())
            review.install_policy(root, proposal, replace=False)
            report = root / "docs/reviews/2026-01-01-lot-ready-codex.md"
            report.parent.mkdir(parents=True, exist_ok=True)
            report.write_text("rapport conservé", encoding="utf-8")

            first = review.disable_policy(root)
            self.assertEqual(first["status"], "disabled")
            self.assertTrue(first["reports_preserved"])
            self.assertFalse((root / ".claude/codex-review.json").exists())
            self.assertNotIn(review.POINTER_START, (root / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertIn("À conserver.", (root / "CLAUDE.md").read_text(encoding="utf-8"))
            self.assertEqual(report.read_text(encoding="utf-8"), "rapport conservé")
            self.assertIn("/docs/reviews/", (root / ".gitignore").read_text(encoding="utf-8"))

            second = review.disable_policy(root)
            self.assertEqual(second["status"], "already_disabled")
            self.assertTrue(second["reports_preserved"])
            self.assertTrue(report.is_file())

    def test_install_warns_without_untracking_existing_reviews(self):
        if not shutil_which("git"):
            self.skipTest("git indisponible")
        with tempfile.TemporaryDirectory() as container:
            root = Path(container) / "project"
            root.mkdir()
            run_git(root, "init")
            tracked = root / "docs/reviews/old.md"
            tracked.parent.mkdir(parents=True, exist_ok=True)
            tracked.write_text("ancien audit", encoding="utf-8")
            run_git(root, "add", "docs/reviews/old.md")
            proposal = Path(container) / "proposal.json"
            write_json(proposal, policy_data())
            result = review.install_policy(root, proposal, replace=False)
            self.assertTrue(result["warnings"])
            self.assertIn("docs/reviews/old.md", result["warnings"][0])
            self.assertTrue(tracked.is_file())

    def test_report_directory_cannot_hide_inside_dot_claude(self):
        with self.assertRaises(review.ReviewError):
            review.validate_policy(policy_data(reports={"directory": ".claude/reviews"}))


class ModelDiscoveryTests(unittest.TestCase):
    def test_embedded_catalog_recommends_terra_and_never_uses_the_network(self):
        result = review.discover_models(allow_cache=False)
        self.assertEqual(result["source"], "embedded_catalog")
        identifiers = [item["id"] for item in result["models"]]
        self.assertIn("gpt-5.6-terra", identifiers)
        self.assertIn("gpt-5.6-sol", identifiers)
        recommended = [item["id"] for item in result["models"] if item["recommended"]]
        self.assertEqual(recommended, ["gpt-5.6-terra"])

    def test_local_cache_is_preferred_and_hidden_models_are_dropped(self):
        with tempfile.TemporaryDirectory() as container:
            home = Path(container) / "codex-home"
            home.mkdir()
            write_json(
                home / "models_cache.json",
                {
                    "fetched_at": "2026-08-08T00:00:00Z",
                    "models": [
                        {
                            "slug": "gpt-5.6-terra",
                            "display_name": "GPT-5.6-Terra",
                            "visibility": "list",
                            "supported_reasoning_levels": [{"effort": "high"}],
                        },
                        {"slug": "secret-internal", "display_name": "Hidden", "visibility": "hide"},
                        {
                            "slug": "gpt-9-future",
                            "display_name": "GPT-9",
                            "description": "Modèle inconnu du catalogue.",
                            "visibility": "list",
                        },
                    ],
                },
            )
            with temporary_environment(CODEX_HOME=str(home)):
                result = review.discover_models()
            self.assertEqual(result["source"], "codex_models_cache")
            identifiers = [item["id"] for item in result["models"]]
            self.assertEqual(identifiers, ["gpt-5.6-terra", "gpt-9-future"])
            self.assertNotIn("secret-internal", identifiers)

    def test_missing_cache_falls_back_without_leaking_paths_into_models(self):
        with tempfile.TemporaryDirectory() as container:
            with temporary_environment(CODEX_HOME=str(Path(container) / "absent")):
                result = review.discover_models()
        self.assertEqual(result["source"], "embedded_catalog")
        self.assertTrue(result["warnings"])

    def test_discover_models_cli_can_force_offline_catalog(self):
        completed = subprocess.run(
            [sys.executable, str(MODULE_PATH), "discover-models", "--offline"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout.decode("utf-8"))
        self.assertEqual(payload["source"], "embedded_catalog")


class StdDevAuthorizationTests(unittest.TestCase):
    def test_budget_is_bound_to_guarantee_and_consumed_atomically(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container)
            write_json(root / ".sdp/state.json", sdp_state_data(level="elevated", maximum=3))
            granted = review.validate_sdp_authorization(root, ["lot-ready"], consume=True)
            self.assertEqual(granted["used"], 1)
            self.assertEqual(granted["maximum"], 3)
            stored = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["reviews"]["counter_reviews"]["used"], 1)

    def test_rejects_claude_mode_state(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container)
            write_json(root / ".sdp/state.json", sdp_state_data(mode="claude"))
            with self.assertRaises(review.ReviewError) as caught:
                review.validate_sdp_authorization(root, ["lot-ready"])
            self.assertIn("Codex", str(caught.exception))

    def test_rejects_wrong_version_budget_milestone_and_exhaustion(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container)
            write_json(root / ".sdp/state.json", sdp_state_data(used=2, maximum=2))
            with self.assertRaises(review.ReviewError):
                review.validate_sdp_authorization(root, ["lot-ready"])
            write_json(root / ".sdp/state.json", sdp_state_data(level="standard", maximum=4))
            with self.assertRaises(review.ReviewError):
                review.validate_sdp_authorization(root, ["lot-ready"])
            write_json(root / ".sdp/state.json", sdp_state_data())
            with self.assertRaises(review.ReviewError):
                review.validate_sdp_authorization(root, ["autre-jalon"])
            with self.assertRaises(review.ReviewError):
                review.validate_sdp_authorization(root, [])

    def test_concurrent_consumption_is_serialized(self):
        with tempfile.TemporaryDirectory() as container:
            root = Path(container)
            write_json(root / ".sdp/state.json", sdp_state_data(level="critical", maximum=4))

            def consume():
                try:
                    return review.validate_sdp_authorization(root, ["lot-ready"], consume=True)["used"]
                except review.ReviewError:
                    return None

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                results = [value for value in pool.map(lambda _: consume(), range(4)) if value is not None]
            self.assertEqual(sorted(results), [1, 2, 3, 4])
            stored = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["reviews"]["counter_reviews"]["used"], 4)


class SnapshotTests(unittest.TestCase):
    def _project(self, container: Path) -> Path:
        root = container / "project"
        (root / "src").mkdir(parents=True)
        (root / "docs/reviews").mkdir(parents=True)
        (root / ".claude").mkdir(parents=True)
        (root / "CLAUDE.md").write_text("# Projet\n", encoding="utf-8")
        (root / "src/main.py").write_text("print('hello')\n", encoding="utf-8")
        (root / ".env").write_text("TOKEN=secret-value\n", encoding="utf-8")
        (root / ".env.example").write_text("TOKEN=\n", encoding="utf-8")
        (root / "server.key").write_text("-----BEGIN PRIVATE KEY-----\n", encoding="utf-8")
        (root / "auth.json").write_text('{"token": "secret"}\n', encoding="utf-8")
        (root / ".claude/codex-review.json").write_text("{}\n", encoding="utf-8")
        (root / "docs/reviews/previous.md").write_text("ancien audit\n", encoding="utf-8")
        return root

    def test_non_git_snapshot_filters_secrets_reports_and_policy(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root = self._project(container)
            policy = review.validate_policy(policy_data())
            with tempfile.TemporaryDirectory() as staging:
                snapshot = review.build_snapshot(root, policy, Path(staging), [], None, [], [])
                copied = {
                    path.relative_to(snapshot.root).as_posix()
                    for path in snapshot.root.rglob("*")
                    if path.is_file()
                }
            self.assertIn("src/main.py", copied)
            self.assertIn("CLAUDE.md", copied)
            self.assertIn(".env.example", copied)
            self.assertNotIn(".env", copied)
            self.assertNotIn("server.key", copied)
            self.assertNotIn("auth.json", copied)
            self.assertNotIn("docs/reviews/previous.md", copied)
            self.assertNotIn(".claude/codex-review.json", copied)
            reasons = {item["path"]: item["reason"] for item in snapshot.excluded}
            self.assertEqual(reasons[".env"], "hard_secret")
            self.assertEqual(reasons["auth.json"], "hard_secret")

    def test_external_symlinks_are_recorded_but_never_copied(self):
        if os.name == "nt":
            self.skipTest("création de liens symboliques non garantie sous Windows")
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root = self._project(container)
            outside = container / "outside.txt"
            outside.write_text("hors projet\n", encoding="utf-8")
            (root / "link.txt").symlink_to(outside)
            policy = review.validate_policy(policy_data())
            with tempfile.TemporaryDirectory() as staging:
                snapshot = review.build_snapshot(root, policy, Path(staging), [], None, [], [])
                self.assertFalse((snapshot.root / "link.txt").exists())
            statuses = {entry["path"]: entry["status"] for entry in snapshot.manifest["files"]}
            self.assertEqual(statuses["link.txt"], "external_symlink")

    def test_threshold_stops_before_copying(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root = self._project(container)
            policy = review.validate_policy(
                policy_data(snapshot={"max_files": 1, "max_bytes": 262144000, "extra_excludes": []})
            )
            with tempfile.TemporaryDirectory() as staging:
                with self.assertRaises(review.ScopeTooLarge):
                    review.build_snapshot(root, policy, Path(staging), [], None, [], [])

    def test_missing_context_file_is_refused(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root = self._project(container)
            (root / "CLAUDE.md").unlink()
            policy = review.validate_policy(policy_data())
            with tempfile.TemporaryDirectory() as staging:
                with self.assertRaises(review.ReviewError):
                    review.build_snapshot(root, policy, Path(staging), [], None, [], [])


class ReviewExecutionTests(unittest.TestCase):
    def _project_and_fake(self, container: Path):
        root = container / "project"
        (root / "src").mkdir(parents=True)
        (root / "CLAUDE.md").write_text("# Projet\n", encoding="utf-8")
        (root / "src/main.py").write_text("print('hello')\n", encoding="utf-8")
        write_json(root / ".claude/codex-review.json", policy_data())
        fake = make_fake_codex(container)
        return root, fake

    def _invoke(self, root: Path, fake: Path, extra=None):
        mission = root.parent / "mission.txt"
        mission.write_text("Contrôler le lot livré.\n", encoding="utf-8")
        command = [
            sys.executable,
            str(MODULE_PATH),
            "review",
            "--project",
            str(root),
            "--mission-file",
            str(mission),
            "--milestone",
            "lot-ready",
            "--codex",
            str(fake),
            *(extra or []),
        ]
        completed = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        return (
            completed.returncode,
            completed.stdout.decode("utf-8", errors="replace"),
            completed.stderr.decode("utf-8", errors="replace"),
        )

    def test_success_preserves_exact_markdown_and_locks_every_security_flag(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            log = container / "args.json"
            with temporary_environment(FAKE_CODEX_LOG=str(log)):
                status, output, error = self._invoke(root, fake)
            self.assertEqual(status, 0, error)
            payload = json.loads(output)
            self.assertEqual(payload["status"], "created")
            report = Path(payload["report"])
            self.assertTrue(report.is_file())
            content = report.read_text(encoding="utf-8")
            self.assertIn("## Verdict\nPASS", content)
            self.assertIn('reviewer: "openai/codex"', content)
            self.assertIn('codex_model: "gpt-5.6-terra"', content)
            self.assertNotIn("draft content must stay private", content)

            arguments = json.loads(log.read_text(encoding="utf-8"))
            self.assertEqual(arguments[0], "exec")
            for flag in (
                "--sandbox",
                "--ephemeral",
                "--ignore-user-config",
                "--ignore-rules",
                "--strict-config",
                "--skip-git-repo-check",
                "--json",
                "--output-last-message",
                "--cd",
            ):
                self.assertIn(flag, arguments)
            self.assertEqual(arguments[arguments.index("--sandbox") + 1], "read-only")
            self.assertEqual(arguments[arguments.index("--model") + 1], "gpt-5.6-terra")
            self.assertIn('model_reasoning_effort="high"', arguments)
            self.assertIn('web_search="disabled"', arguments)
            self.assertIn('approval_policy="never"', arguments)
            self.assertNotIn("--dangerously-bypass-approvals-and-sandbox", arguments)
            self.assertNotIn("--dangerously-bypass-hook-trust", arguments)
            self.assertNotIn("--max-turns", arguments)

    def test_mandate_travels_in_band_ahead_of_the_mission(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            prompt_file = container / "prompt.txt"
            with temporary_environment(FAKE_CODEX_PROMPT=str(prompt_file)):
                status, _, error = self._invoke(root, fake)
            self.assertEqual(status, 0, error)
            prompt = prompt_file.read_text(encoding="utf-8")
            self.assertIn("Mandat de contrôleur indépendant", prompt)
            self.assertIn("Contrôler le lot livré.", prompt)
            self.assertLess(prompt.index("Mandat de contrôleur"), prompt.index("Contrôler le lot livré."))

    def test_progress_is_jsonl_sanitized_and_keeps_stdout_parseable(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            status, output, error = self._invoke(root, fake, ["--progress"])
            self.assertEqual(status, 0, error)
            json.loads(output)
            events = [json.loads(line) for line in error.splitlines() if line.strip()]
            self.assertTrue(events)
            phases = {event["phase"] for event in events}
            self.assertIn("snapshot", phases)
            self.assertIn("codex", phases)
            serialized = json.dumps(events, ensure_ascii=False)
            self.assertNotIn("draft content must stay private", serialized)
            self.assertNotIn("TOKEN", serialized)

    def test_unparsable_events_are_counted_but_never_fail_the_review(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            status, output, error = self._invoke(root, fake)
            self.assertEqual(status, 0, error)
            report = Path(json.loads(output)["report"]).read_text(encoding="utf-8")
            self.assertIn('"unparsed_events":1', report.replace(" ", ""))

    def test_doctor_rejects_a_cli_missing_a_required_lock(self):
        with tempfile.TemporaryDirectory() as container_name:
            fake = make_fake_codex(Path(container_name))
            with temporary_environment(FAKE_CODEX_DROP_FLAG="--ignore-user-config"):
                with self.assertRaises(review.ReviewError) as caught:
                    review.doctor(str(fake))
            self.assertIn("--ignore-user-config", str(caught.exception))

    def test_doctor_rejects_a_cli_without_read_only_sandbox(self):
        with tempfile.TemporaryDirectory() as container_name:
            fake = make_fake_codex(Path(container_name))
            with temporary_environment(FAKE_CODEX_NO_SANDBOX="1"):
                with self.assertRaises(review.ReviewError):
                    review.doctor(str(fake))

    def test_failure_modes_leave_no_report_or_evidence(self):
        for mode in ("failure", "empty", "no-output"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as container_name:
                container = Path(container_name)
                root, fake = self._project_and_fake(container)
                with temporary_environment(FAKE_CODEX_MODE=mode):
                    status, _, _ = self._invoke(root, fake)
                self.assertEqual(status, 1)
                self.assertFalse((root / "docs/reviews").exists())

    def test_failure_keeps_only_a_bounded_stderr_tail(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            with temporary_environment(FAKE_CODEX_MODE="large-stderr-failure"):
                status, _, error = self._invoke(root, fake)
            self.assertEqual(status, 1)
            self.assertIn("fixture tail", error)
            self.assertLess(len(error), 6000)

    def test_timeout_stops_codex_without_artifacts(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            write_json(
                root / ".claude/codex-review.json",
                policy_data(codex={"model": "gpt-5.6-terra", "effort": "high", "timeout_minutes": 1}),
            )
            with temporary_environment(FAKE_CODEX_DELAY="90"):
                status, _, error = self._invoke(root, fake, ["--progress"])
            self.assertEqual(status, 1)
            self.assertIn("dépassé", error)
            self.assertFalse((root / "docs/reviews").exists())

    def test_two_successes_never_overwrite(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            first_status, first_output, _ = self._invoke(root, fake)
            second_status, second_output, _ = self._invoke(root, fake)
            self.assertEqual((first_status, second_status), (0, 0))
            self.assertNotEqual(json.loads(first_output)["report"], json.loads(second_output)["report"])

    def test_counter_review_requires_audit_context_and_confirmation(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            status, _, error = self._invoke(root, fake, ["--kind", "counter"])
            self.assertEqual(status, 1)
            self.assertIn("audit-context", error)

            audit = root / "docs/reviews/previous.md"
            audit.parent.mkdir(parents=True, exist_ok=True)
            audit.write_text("rapport précédent\n", encoding="utf-8")
            status, _, error = self._invoke(root, fake, ["--kind", "counter", "--audit-context", str(audit)])
            self.assertEqual(status, 1)
            self.assertIn("--confirm-counter-review", error)

    def test_sdp_authorization_is_consumed_only_after_the_report_lands(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            write_json(root / ".sdp/state.json", sdp_state_data())
            audit = root / "docs/reviews/previous.md"
            audit.parent.mkdir(parents=True, exist_ok=True)
            audit.write_text("rapport précédent\n", encoding="utf-8")

            with temporary_environment(FAKE_CODEX_MODE="failure"):
                status, _, _ = self._invoke(
                    root, fake, ["--kind", "counter", "--audit-context", str(audit), "--sdp-authorized"]
                )
            self.assertEqual(status, 1)
            stored = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["reviews"]["counter_reviews"]["used"], 0)

            status, output, error = self._invoke(
                root, fake, ["--kind", "counter", "--audit-context", str(audit), "--sdp-authorized"]
            )
            self.assertEqual(status, 0, error)
            stored = json.loads((root / ".sdp/state.json").read_text(encoding="utf-8"))
            self.assertEqual(stored["reviews"]["counter_reviews"]["used"], 1)
            self.assertEqual(json.loads(output)["authorization"]["used"], 1)

    def test_sdp_authorization_is_refused_outside_a_counter_review(self):
        with tempfile.TemporaryDirectory() as container_name:
            container = Path(container_name)
            root, fake = self._project_and_fake(container)
            write_json(root / ".sdp/state.json", sdp_state_data())
            status, _, error = self._invoke(root, fake, ["--sdp-authorized"])
            self.assertEqual(status, 1)
            self.assertIn("contre-revue", error)


def shutil_which(name: str):
    import shutil

    return shutil.which(name)


def run_git(root: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"},
    )


if __name__ == "__main__":
    unittest.main(verbosity=2)
