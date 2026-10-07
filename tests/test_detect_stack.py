import json
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURES, ROUTING, load, write_tree

detect_stack = load(ROUTING, "detect_stack")


def modules(name: str) -> dict:
    profile = detect_stack.detect(FIXTURES / name)
    return {m["path"]: m for m in profile["modules"]}


class DetectStackFixtures(unittest.TestCase):
    def test_nextjs_with_pnpm_and_vitest(self):
        module = modules("nextjs")["."]
        self.assertEqual(module["specialist"], "developer-nextjs")
        self.assertEqual(module["stacks"][:2], ["nextjs", "react"])
        self.assertEqual(module["package_manager"], "pnpm")
        self.assertEqual(module["commands"]["install"], "pnpm install --frozen-lockfile")
        self.assertEqual(module["commands"]["test"], "pnpm test --run")  # vitest must not watch
        self.assertEqual(module["versions"]["node"], "22")

    def test_angular_test_runs_once(self):
        module = modules("angular")["."]
        self.assertEqual(module["specialist"], "developer-angular")
        self.assertEqual(module["commands"]["install"], "npm ci")
        self.assertEqual(module["commands"]["test"], "npm test -- --watch=false")

    def test_spring_boot_maven(self):
        found = modules("spring-maven")
        self.assertEqual(list(found), ["."], "nested Maven modules fold into the root build")
        module = found["."]
        self.assertEqual(module["specialist"], "developer-java-spring")
        self.assertEqual(module["versions"], {"java": "21", "spring-boot": "3.3.4"})
        self.assertEqual(module["commands"]["test"], "./mvnw -B test")
        self.assertEqual(module["commands"]["format"], "./mvnw -B spotless:check")
        self.assertIn("testcontainers", module["tools"])

    def test_android_gradle_kts(self):
        module = modules("android")["."]
        self.assertEqual(module["specialist"], "developer-kotlin-android")
        self.assertEqual(module["stacks"], ["android", "kotlin"])
        self.assertIn("jetpack-compose", module["frameworks"])
        self.assertEqual(module["commands"]["test"], "./gradlew testDebugUnitTest")
        self.assertEqual(module["commands"]["format"], "./gradlew ktlintCheck")
        self.assertEqual(module["versions"]["android-min-sdk"], "26")

    def test_python_uv(self):
        module = modules("python")["."]
        self.assertEqual(module["specialist"], "developer-python")
        self.assertEqual(module["commands"]["install"], "uv sync --frozen")
        self.assertEqual(module["commands"]["test"], "uv run pytest -q")
        self.assertEqual(module["commands"]["typecheck"], "uv run mypy .")
        self.assertIn("fastapi", module["frameworks"])

    def test_go_with_golangci(self):
        module = modules("go")["."]
        self.assertEqual(module["specialist"], "developer-go")
        self.assertEqual(module["commands"]["lint"], "golangci-lint run")
        self.assertEqual(module["versions"], {"go": "1.23"})

    def test_dotnet_solution(self):
        found = modules("dotnet")
        self.assertEqual(list(found), ["."], "projects fold into the solution")
        module = found["."]
        self.assertEqual(module["specialist"], "developer-dotnet")
        self.assertEqual(module["commands"]["test"], "dotnet test Orders.sln --no-restore")
        self.assertIn("aspnetcore", module["frameworks"])
        self.assertIn("xunit", module["tools"])

    def test_monorepo_modules_and_ci(self):
        profile = detect_stack.detect(FIXTURES / "monorepo")
        found = {m["path"]: m for m in profile["modules"]}
        self.assertEqual(found["apps/web"]["specialist"], "developer-nextjs")
        self.assertEqual(found["apps/admin"]["specialist"], "developer-vue")
        self.assertEqual(found["services/orders"]["specialist"], "developer-java-spring")
        self.assertNotIn("install", found["apps/web"]["commands"], "workspace members install from the root")
        self.assertEqual(found["."]["commands"]["install"], "npm ci")
        runs = [c["run"] for c in profile["ci_commands"]]
        self.assertIn("npm run lint --workspace web && npm test --workspace web", runs)
        self.assertIn("mvn -B verify", runs)


class DetectStackEdgeCases(unittest.TestCase):
    def detect(self, files: dict) -> list:
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(Path(tmp), files)
            return detect_stack.detect(Path(tmp))["modules"]

    def test_react_native_routes_to_react(self):
        found = self.detect({"package.json": json.dumps({"dependencies": {"react": "18", "react-native": "0.76"}})})
        self.assertEqual(found[0]["specialist"], "developer-react")

    def test_express_service_routes_to_typescript(self):
        found = self.detect({"package.json": json.dumps({"dependencies": {"express": "4"}, "scripts": {
            "test": 'echo "Error: no test specified" && exit 1'}}), "tsconfig.json": "{}"})
        self.assertEqual(found[0]["specialist"], "developer-typescript")
        self.assertNotIn("test", found[0]["commands"], "the npm placeholder test script is not a test")
        self.assertEqual(found[0]["commands"]["typecheck"], "npx tsc --noEmit")

    def test_ktor_routes_to_kotlin(self):
        found = self.detect({"build.gradle.kts": 'plugins { kotlin("jvm") }\ndependencies { implementation("io.ktor:ktor-server-core") }\n'})
        self.assertEqual(found[0]["specialist"], "developer-kotlin-android")
        self.assertIn("ktor", found[0]["frameworks"])

    def test_spring_kotlin_routes_to_spring(self):
        found = self.detect({"build.gradle.kts": 'plugins { id("org.springframework.boot") version "3.3.4"\n kotlin("jvm") }\n'})
        self.assertEqual(found[0]["specialist"], "developer-java-spring")

    def test_django_requirements(self):
        found = self.detect({"requirements.txt": "Django==5.1\npytest-django==4.9\n", "manage.py": "import django\n"})
        self.assertEqual(found[0]["commands"]["install"], "python -m pip install -r requirements.txt")
        self.assertIn("django", found[0]["frameworks"])

    def test_unknown_repository_falls_back(self):
        profile_modules = self.detect({"README.md": "docs only\n"})
        self.assertEqual(profile_modules, [])

    def test_vendored_directories_are_skipped(self):
        found = self.detect({"package.json": "{}", "node_modules/x/package.json": json.dumps({"dependencies": {"vue": "3"}})})
        self.assertEqual([m["path"] for m in found], ["."])

    def test_invalid_package_json_is_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_tree(Path(tmp), {"package.json": "{ not json"})
            profile = detect_stack.detect(Path(tmp))
        self.assertEqual(profile["modules"], [])
        self.assertIn("invalid JSON", profile["errors"][0])

    def test_markdown_project_facts(self):
        text = detect_stack.to_markdown(detect_stack.detect(FIXTURES / "spring-maven"))
        self.assertIn("## Project facts", text)
        self.assertIn("- Test: `./mvnw -B test`", text)
        self.assertIn("`developer-java-spring`", text)


if __name__ == "__main__":
    unittest.main()
