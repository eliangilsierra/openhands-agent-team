import unittest

from helpers import DEVELOPMENT, git, load, temp_repo

diff_guard = load(DEVELOPMENT, "diff_guard")


def diff(path: str, *added: str, status: str = "") -> str:
    header = f"diff --git a/{path} b/{path}\n"
    if status == "added":
        header += "new file mode 100644\n--- /dev/null\n"
    elif status == "deleted":
        return header + f"deleted file mode 100644\n--- a/{path}\n+++ /dev/null\n@@ -1 +0,0 @@\n-x\n"
    else:
        header += f"--- a/{path}\n"
    body = f"+++ b/{path}\n@@ -0,0 +1,{len(added)} @@\n" + "".join(f"+{line}\n" for line in added)
    return header + body


def rules(text: str, touches=None, sizes=None) -> dict:
    found = diff_guard.scan(diff_guard.parse_diff(text), touches or [], sizes)
    return {(f.rule, f.severity) for f in found}


class DiffGuard(unittest.TestCase):
    def test_secret_is_blocked_without_printing_it(self):
        token = "ghp_" + "b" * 36
        found = diff_guard.scan(diff_guard.parse_diff(diff("src/config.ts", f"const t = '{token}';")), [])
        self.assertEqual(found[0].rule, "secret")
        self.assertEqual(found[0].line, 1)
        self.assertNotIn(token, found[0].message)

    def test_hard_coded_credential(self):
        self.assertIn(("secret", "block"), rules(diff("app/settings.py", "API_KEY = " + repr("s3cr3t-value-123"))))

    def test_secret_file(self):
        self.assertIn(("secret-file", "block"), rules(diff(".env.production", "X=1", status="added")))
        self.assertEqual(rules(diff(".env.example", "X=", status="added")), set())

    def test_weakened_tests_are_blocked(self):
        self.assertIn(("focused-test", "block"), rules(diff("src/a.test.ts", "it.only('works', () => {});")))
        self.assertIn(("skipped-test", "block"), rules(diff("src/a.test.ts", "it.skip('works', () => {});")))
        self.assertIn(("skipped-test", "block"), rules(diff("src/test/java/AT.java", "    @Disabled")))
        self.assertIn(("skipped-test", "block"), rules(diff("tests/test_a.py", "@pytest.mark.skip(reason='flaky')")))
        self.assertIn(("skipped-test", "block"), rules(diff("a_test.go", "\tt.Skip(\"later\")")))
        self.assertIn(("test-deleted", "block"), rules(diff("src/a.spec.ts", status="deleted")))

    def test_conflict_marker(self):
        self.assertIn(("conflict-marker", "block"), rules(diff("README.md", "<" * 7 + " HEAD")))

    def test_scope_and_workflows(self):
        text = diff("src/orders/a.ts", "export const a = 1;") + diff("src/billing/b.ts", "export const b = 2;")
        found = rules(text, touches=["src/orders/**"])
        self.assertIn(("out-of-scope", "block"), found)
        self.assertEqual(len([r for r in found if r[0] == "out-of-scope"]), 1)
        self.assertIn(("workflow-change", "block"), rules(diff(".github/workflows/ci.yml", "on: push")))

    def test_debug_output_warns_outside_tests_only(self):
        self.assertIn(("debug-statement", "warn"), rules(diff("src/a.ts", "console.log(order);")))
        self.assertIn(("debug-statement", "warn"), rules(diff("src/main/java/A.java", "System.out.println(x);")))
        self.assertNotIn(("debug-statement", "warn"), rules(diff("src/a.test.ts", "console.log(order);")))

    def test_large_and_lockfile_only(self):
        self.assertIn(("large-file", "block"), rules(diff("assets/big.bin", "x"), sizes={"assets/big.bin": 5_000_000}))
        self.assertIn(("lockfile-only", "warn"), rules(diff("package-lock.json", "{}")))
        self.assertNotIn(("lockfile-only", "warn"), rules(diff("package-lock.json", "{}") + diff("package.json", "{}")))

    def test_clean_change(self):
        self.assertEqual(rules(diff("src/orders/total.ts", "export const total = (a: number[]) => a.length;"),
                               touches=["src/orders/**"]), set())

    def test_cli_on_a_real_branch_and_allow(self):
        holder, root = temp_repo({"src/a.ts": "export const a = 1;\n"})
        self.addCleanup(holder.cleanup)
        git(root, "switch", "-q", "-c", "feature/1-x")
        (root / "src/b.ts").write_text("export const b = 2;\n", encoding="utf-8")
        git(root, "add", ".")
        git(root, "commit", "-q", "--no-verify", "-m", "feat: add b")
        import os
        cwd = os.getcwd()
        os.chdir(root)
        try:
            self.assertEqual(diff_guard.main(["--base", "main", "--touches", "src/a.ts"]), 1)
            self.assertEqual(diff_guard.main(["--base", "main", "--touches", "src/a.ts", "--allow", "out-of-scope"]), 0)
            self.assertEqual(diff_guard.main(["--base", "main", "--touches", "src/**"]), 0)
        finally:
            os.chdir(cwd)


if __name__ == "__main__":
    unittest.main()
