import os
import subprocess
import logging
import sys
from datetime import datetime
from typing import Dict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.test_files = [
            "tests/test_xp_service.py",
            "tests/test_amm_service.py",
            "tests/test_liquidity_service.py",
            "tests/test_prediction_service.py",
            "tests/test_scraper_api.py",
            "tests/test_coach_api.py"
        ]
        self.failures = 0
        self.test_results = {}

    def run_test(self, test_file: str) -> bool:
        print(f"\n🔍 Running: {test_file}")
        env = os.environ.copy()
        python_path = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = f"{python_path}:." if python_path else "."

        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            env=env,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.failures += 1
            self.test_results[test_file] = {"status": "failed", "output": result.stdout + result.stderr}
            return False
        else:
            self.test_results[test_file] = {"status": "passed", "output": result.stdout}
            return True

    def run_all_tests(self) -> Dict:
        print("\n🚀 Starting test suite run...")
        start_time = datetime.now()

        for test_file in self.test_files:
            if not os.path.exists(test_file):
                logger.error(f"❌ Test file not found: {test_file}")
                self.failures += 1
                continue
            self.run_test(test_file)

        duration = datetime.now() - start_time

        print("\n📊 Test Summary:")
        print(f"Total: {len(self.test_files)} | Passed: {len(self.test_files) - self.failures} | Failed: {self.failures} | Time: {duration.total_seconds():.2f}s")

        if self.failures:
            print("\n❌ FAILED TESTS:")
            for test, result in self.test_results.items():
                if result["status"] == "failed":
                    print(f"- {test}")

        else:
            print("\n✅ ALL TESTS PASSED!")

        return self.test_results

    def generate_report(self) -> str:
        report = [
            "# Test Report\n",
            f"Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
            f"## Summary\n",
            f"- Total tests: {len(self.test_files)}\n",
            f"- Passed: {len(self.test_files) - self.failures}\n",
            f"- Failed: {self.failures}\n\n"
        ]

        if self.failures:
            report.append("## Failed Tests:\n")
            for test, result in self.test_results.items():
                if result["status"] == "failed":
                    report.append(f"### {test}\n```\n{result['output']}\n```\n")

        return ''.join(report)

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_all_tests()
    with open("test_results.md", "w") as f:
        f.write(runner.generate_report())
    print("\n📝 Report saved to test_results.md")

