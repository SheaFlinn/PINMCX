import os
import subprocess
import logging
from datetime import datetime
from typing import Dict, List
import sys

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
            "tests/test_coach_api.py",
        ]
        self.failures = 0
        self.test_results = {}

    def run_test(self, test_file: str) -> bool:
        """Run a single test file and return whether it passed."""
        print(f"\n🔍 Running: {test_file}")
        
        # Add project root to PYTHONPATH
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file, "-v"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            self.failures += 1
            self.test_results[test_file] = {"status": "failed", "output": result.stderr}
            return False
        else:
            self.test_results[test_file] = {"status": "passed", "output": result.stdout}
            return True

    def run_all_tests(self) -> Dict:
        """Run all test files and return summary of results."""
        print("\n🚀 Starting test suite run...")
        start_time = datetime.now()

        for test_file in self.test_files:
            if not os.path.exists(test_file):
                logger.error(f"Test file not found: {test_file}")
                self.failures += 1
                continue
            
            self.run_test(test_file)

        end_time = datetime.now()
        duration = end_time - start_time

        print(f"\n📊 Test Summary:")
        print(f"Total tests: {len(self.test_files)}")
        print(f"Passing tests: {len(self.test_files) - self.failures}")
        print(f"Failing tests: {self.failures}")
        print(f"Duration: {duration.seconds} seconds")

        if self.failures == 0:
            print("\n✅ ALL TESTS PASSED")
        else:
            print(f"\n❌ {self.failures} TESTS FAILED")
            print("\nFailed tests:")
            for test_file, result in self.test_results.items():
                if result["status"] == "failed":
                    print(f"- {test_file}")

        return self.test_results

    def generate_report(self) -> str:
        """Generate a detailed report of test results."""
        report = ["# Test Suite Report\n", 
                 f"## Run Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n",
                 f"## Summary\n",
                 f"- Total tests: {len(self.test_files)}\n",
                 f"- Passing tests: {len(self.test_files) - self.failures}\n",
                 f"- Failing tests: {self.failures}\n\n"]

        if self.failures > 0:
            report.append("## Failed Tests\n")
            for test_file, result in self.test_results.items():
                if result["status"] == "failed":
                    report.append(f"### {test_file}\n")
                    report.append(f"```
{result['output']}
```
\n")

        return "".join(report)

if __name__ == "__main__":
    runner = TestRunner()
    results = runner.run_all_tests()
    
    # Generate and save report
    report = runner.generate_report()
    with open("test_results.md", "w") as f:
        f.write(report)
    
    print("\n📝 Test report saved to test_results.md")
