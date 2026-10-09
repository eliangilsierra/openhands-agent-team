"""The single secret and private-data policy, and the scripts that refuse to publish findings (Issue #15)."""

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from helpers import DEVELOPMENT, ROOT, load

secret_scan = load(DEVELOPMENT, "secret_scan")
checkpoint = load(DEVELOPMENT, "checkpoint")
pr_body = load(DEVELOPMENT, "pr_body")
run_checks = load(DEVELOPMENT, "run_checks")
generate_runtime = load(ROOT / "scripts", "generate_runtime")

# Built by concatenation so no scanner sees a literal secret in this file.
TOKEN = "gh" + "p_" + "Q7w8E9r0T1y2U3i4O5p6A7s8D9f0G1h2J3k4L5z6"
AWS = "AK" + "IA" + "Q3EGRZ5LN6K2PXM7"
JWT = "ey" + "J" + "hbGciOiJIUzI1NiJ9.ey" + "J" + "zdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
EMAIL = "ana.perez" + "@" + "acme-corp.com"
CARD = "4111 1111 " + "1111 1111"


def rules(text, scopes=("secret", "private")):
    return {f.rule for f in secret_scan.scan(text, scopes)}


class Policy(unittest.TestCase):
    def test_secrets(self):
        self.assertEqual(rules(f"t = {TOKEN}"), {"github-token"})
        self.assertEqual(rules(f"key {AWS}"), {"aws-access-key"})
        self.assertEqual(rules(f"Authorization: Bearer {JWT}"), {"jwt"})
        self.assertIn("private-key", rules("-----BEGIN " + "OPENSSH PRIVATE KEY-----"))
        self.assertIn("credential-url", rules("postgres://app:" + "Hunt3r2Pass" + "@db.internal:5432/app"))
        self.assertIn("assigned-secret", rules('client_secret = "' + "q8Zt1LmN4vB7" + '"'))
        self.assertIn("env-secret", rules("GITHUB_TOKEN=" + "abc123def456ghi7"))

    def test_private_data(self):
        self.assertEqual(rules(f"by {EMAIL}"), {"email"})
        self.assertEqual(rules("call +34 612 345 678"), {"phone"})
        self.assertEqual(rules("server 192.168.10.4"), {"private-ip"})
        self.assertEqual(rules("C:" + "\\Users\\maria\\app"), {"home-path"})
        self.assertEqual(rules(f"card {CARD}"), {"card-number"})

    def test_allowed_values(self):
        clean = [
            "write to dev@example.org, noreply@github.com or 12345+bot@users.noreply.github.com",
            "postgres://app:test@localhost:5432/app and redis://:${REDIS_PASSWORD}@cache:6379",
            'password = "test-password-123" and api_key = "<your-key>"',
            "GITHUB_TOKEN=${{ secrets.GITHUB_TOKEN }} and GITHUB_TOKEN=<token>",
            "workspace /home/openhands/app, versions 22.11.0 and 3.12.10, order 1234 5678 9012 3456",
        ]
        for text in clean:
            with self.subTest(text=text[:40]):
                self.assertEqual(rules(text), set())

    def test_strict_rules_ignore_the_allow_list(self):
        self.assertEqual(rules("gh" + "p_" + "test" + "A" * 32), {"github-token"})

    def test_private_rules_do_not_apply_to_code(self):
        self.assertEqual(rules(f'SUPPORT = "{EMAIL}"', ("secret",)), set())

    def test_redact_and_findings_never_show_values(self):
        text = f"token {TOKEN} and key {AWS}"
        redacted = secret_scan.redact(text)
        self.assertNotIn(TOKEN, redacted)
        self.assertNotIn(AWS, redacted)
        self.assertIn("[REDACTED:github-token]", redacted)
        self.assertNotIn(TOKEN, secret_scan.describe(secret_scan.scan(text)))
        self.assertNotIn(TOKEN, run_checks.redact(text))

    def test_cli_exit_codes(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirty, clean = Path(tmp) / "dirty.md", Path(tmp) / "clean.md"
            dirty.write_text(f"mail {EMAIL}\n", encoding="utf-8")
            clean.write_text("all good\n", encoding="utf-8")
            with mock.patch("builtins.print"):
                self.assertEqual(secret_scan.main([str(dirty)]), 1)
                self.assertEqual(secret_scan.main(["--scope", "secret", str(dirty)]), 0)
                self.assertEqual(secret_scan.main([str(clean)]), 0)

    def test_policy_copies_match_the_canonical_file(self):
        canonical = (ROOT / "config" / "secret-patterns.tsv").read_text(encoding="utf-8")
        for copy in generate_runtime.POLICY_COPIES:
            self.assertEqual(copy.read_text(encoding="utf-8"), generate_runtime.POLICY_HEADER + canonical)

    def test_every_rule_compiles_in_the_shared_dialect(self):
        forbidden = ["\\b", "\\d", "\\s", "\\w", "(?", "*?", "+?"]
        for line in (ROOT / "config" / "secret-patterns.tsv").read_text(encoding="utf-8").splitlines():
            if line and not line.startswith("#"):
                regex = line.split("\t")[3]
                for token in forbidden:
                    self.assertNotIn(token, regex, f"{line.split(chr(9))[0]} uses {token}")


class PublishingRefusals(unittest.TestCase):
    def test_checkpoint_mirror_refuses_findings(self):
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(checkpoint, "mirror") as mirror:
            with self.assertRaises(SystemExit) as stop:
                checkpoint.main(["--item", "7", "--state-dir", tmp, "--goal", f"contact {EMAIL}", "--mirror"])
            self.assertIn("email", str(stop.exception))
            self.assertNotIn(EMAIL, str(stop.exception))
            mirror.assert_not_called()
            checkpoint.main(["--item", "8", "--state-dir", tmp, "--goal", "throttle logins", "--mirror"])
            mirror.assert_called_once()

    def test_pr_body_refuses_findings(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "pr.md"
            argv = ["--issue", "43", "--summary", f"Fix login; token {TOKEN}", "--branch", "feature/43-x", "--out", str(out)]
            with self.assertRaises(SystemExit):
                pr_body.main(argv)
            self.assertFalse(out.exists())
            argv[3] = "Fix login throttling."
            with mock.patch("builtins.print"):
                self.assertEqual(pr_body.main(argv), 0)
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
