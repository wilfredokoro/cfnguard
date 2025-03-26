import os
import concurrent.futures
import subprocess
import shutil
import sys
from colorama import Fore, Style
from pydantic import BaseModel
from typing import List, Union

#################
# Classes
#################

class RuleTestResult(BaseModel):
    """
    Class to capture results of tests that are run
    """
    rule_name: str
    status: Union[bool, None] = None
    detail: Union[str, None] = None


class RuleTest:
    """
    Class to represent a rule and its correlated test
    """
    def __init__(self, rule_file: str) -> None:
        self._rule_file = rule_file

    @property
    def rule_name(self) -> str:
        return os.path.basename(self.rule_file).replace('guard', '')

    @property
    def rule_file(self) -> str:
        return self._rule_file

    @property
    def test_file(self) -> str:
        rule_file_parts = self.rule_file.split('/')
        rule_file_parts[-2] = f"{rule_file_parts[-2]}/tests"
        test = '/'.join(rule_file_parts)
        return test.replace('.guard', '_tests.yaml')

    @property
    def test_cmd(self) -> List:
        return [shutil.which('cfn-guard-validate'), 'test', '--rules-file', self.rule_file]

    def run(self) -> RuleTestResult:
        """
        Method to run a cfn-guard test
        :return: A rule test result object
        """
        if not os.path.isfile(self.test_file):
            return RuleTestResult(
                rule_name=self.rule_name,
                detail='Cannot find corresponding test file in `tests` directory'
            )
        test_run = subprocess.run(self.test_cmd, capture_output=True)
        return RuleTestResult(
            rule_name=self.rule_name,
            status=True if test_run.returncode == 0 else False,
            detail=test_run.stdout
        )


#################
# Main
#################

def main():
    print("Running CloudFormation Guard rule tests\n")

    rules_dir = f"{os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rules')}"
    guard_tests: List[RuleTest] = []

    for root, dirs, files in os.walk(rules_dir):
        for filename in files:
            if filename.endswith('guard'):
                guard_tests.append(RuleTest(os.path.join(root, filename)))

    print(f"Found {len(guard_tests)} rules to test\n")

    rules_passed: List[RuleTestResult] = []
    rules_failed: List[RuleTestResult] = []
    rules_skipped: List[RuleTestResult] = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        test_results: List[RuleTestResult] = []
        for test in guard_tests:
            test_results.append(executor.submit(test.run))

        for f in concurrent.futures.as_completed(test_results):
            result: RuleTestResult = f.result()
            if result.status is None:
                rules_skipped.append(result)
            elif result.status is True:
                if 'Error processing' in result.detail:
                    rules_failed.append(result)
                elif 'Parse error on ruleset file' in result.detail:
                    rules_failed.append(result)
                else:
                    rules_passed.append(result)
            elif result.status is False:
                rules_failed.append(result)

    print("Finished running CloudFormation Guard rule tests\n")
    print(f"{Fore.GREEN}{len(rules_passed)}{Style.RESET_ALL} rules passed, " +
          f"{Fore.RED}{len(rules_failed)}{Style.RESET_ALL} rules failed, " +
          f"{Fore.YELLOW}{len(rules_skipped)}{Style.RESET_ALL} rules skipped\n")

    if len(rules_skipped) > 0:
        print("The following rules failed to execute tests:")
        for rule in rules_skipped:
            print(f"{Fore.YELLOW}Rule: {rule.rule_name:<28}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Reason: {rule.detail}{Style.RESET_ALL}\n")

    if len(rules_failed) > 0:
        print("The following rules failed tests:")
        for rule in rules_failed:
            print(f"{Fore.RED}Rule: {rule.rule_name:<18}{Style.RESET_ALL}")
            print(f"{Fore.RED}Reason: (see below test case details) {Style.RESET_ALL}\n")
            print(rule.detail)

    if len(rules_skipped) == 0 and len(rules_failed) == 0:
        print("No rules failed or skipped tests.")

    print("Finished!")

    if len(rules_failed) != 0 or len(rules_skipped) != 0:
        print("Exiting code 1")
        sys.exit(1)


if __name__ == "__main__":
    main()
