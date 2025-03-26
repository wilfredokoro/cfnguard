# import os
# import concurrent.futures
# import subprocess
# import shutil
# import sys
# from colorama import Fore, Style
# from pydantic import BaseModel
# from typing import List, Union

# #################
# # Classes
# #################

# class RuleTestResult(BaseModel):
#     """
#     Class to capture results of tests that are run
#     """
#     rule_name: str
#     status: Union[bool, None] = None
#     detail: Union[str, None] = None


# class RuleTest:
#     """
#     Class to represent a rule and its correlated test
#     """
#     def __init__(self, rule_file: str) -> None:
#         self._rule_file = rule_file
#         self._guard_binary = self._find_guard_binary()

#     def _find_guard_binary(self) -> str:
#         """Find the correct guard binary path"""
#         # Try different possible binary names and paths
#         for binary in ['cfn-guard', 'cfn-guard-validate', 'guard']:
#             path = shutil.which(binary)
#             if path:
#                 return path
#         # Fallback to direct path if not found in PATH
#         return '/usr/local/bin/cfn-guard'

#     @property
#     def rule_name(self) -> str:
#         return os.path.basename(self.rule_file).replace('.guard', '')

#     @property
#     def rule_file(self) -> str:
#         return self._rule_file

#     @property
#     def test_file(self) -> str:
#         rule_dir = os.path.dirname(self.rule_file)
#         test_dir = os.path.join(rule_dir, 'tests')
#         test_file = os.path.basename(self.rule_file).replace('.guard', '_tests.yaml')
#         return os.path.join(test_dir, test_file)

#     @property
#     def test_cmd(self) -> List:
#         return [self._guard_binary, 'test', '--rules-file', self.rule_file, '--test-data', self.test_file]

#     def run(self) -> RuleTestResult:
#         """
#         Method to run a cfn-guard test
#         :return: A rule test result object
#         """
#         if not os.path.isfile(self.test_file):
#             return RuleTestResult(
#                 rule_name=self.rule_name,
#                 detail=f'Cannot find corresponding test file: {self.test_file}'
#             )
        
#         try:
#             test_run = subprocess.run(
#                 self.test_cmd,
#                 capture_output=True,
#                 text=True
#             )
            
#             detail = test_run.stdout or test_run.stderr
            
#             return RuleTestResult(
#                 rule_name=self.rule_name,
#                 status=test_run.returncode == 0,
#                 detail=detail
#             )
#         except Exception as e:
#             return RuleTestResult(
#                 rule_name=self.rule_name,
#                 detail=f'Error executing test: {str(e)}'
#             )

# #################
# # Main
# #################

# def main():
#     print("Running CloudFormation Guard rule tests\n")

#     # Find rules directory relative to script location
#     script_dir = os.path.dirname(os.path.realpath(__file__))
#     rules_dir = os.path.join(script_dir, 'rules')
    
#     if not os.path.exists(rules_dir):
#         print(f"{Fore.RED}Error: Rules directory not found at {rules_dir}{Style.RESET_ALL}")
#         sys.exit(1)

#     guard_tests: List[RuleTest] = []

#     for root, dirs, files in os.walk(rules_dir):
#         for filename in files:
#             if filename.endswith('.guard'):
#                 guard_tests.append(RuleTest(os.path.join(root, filename)))

#     print(f"Found {len(guard_tests)} rules to test\n")

#     rules_passed: List[RuleTestResult] = []
#     rules_failed: List[RuleTestResult] = []
#     rules_skipped: List[RuleTestResult] = []

#     with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
#         test_results = []
#         for test in guard_tests:
#             test_results.append(executor.submit(test.run))

#         for f in concurrent.futures.as_completed(test_results):
#             result: RuleTestResult = f.result()
#             if result.status is None:
#                 rules_skipped.append(result)
#             elif result.status is True:
#                 if 'Error processing' in (result.detail or ''):
#                     rules_failed.append(result)
#                 elif 'Parse error' in (result.detail or ''):
#                     rules_failed.append(result)
#                 else:
#                     rules_passed.append(result)
#             else:
#                 rules_failed.append(result)

#     print("\nFinished running CloudFormation Guard rule tests\n")
#     print(f"{Fore.GREEN}{len(rules_passed)} passed{Style.RESET_ALL}, "
#           f"{Fore.RED}{len(rules_failed)} failed{Style.RESET_ALL}, "
#           f"{Fore.YELLOW}{len(rules_skipped)} skipped{Style.RESET_ALL}\n")

#     if rules_skipped:
#         print(f"{Fore.YELLOW}Skipped tests:{Style.RESET_ALL}")
#         for rule in rules_skipped:
#             print(f"- {rule.rule_name}: {rule.detail}")

#     if rules_failed:
#         print(f"\n{Fore.RED}Failed tests:{Style.RESET_ALL}")
#         for rule in rules_failed:
#             print(f"\n- {rule.rule_name}:")
#             print(rule.detail)

#     if not rules_failed and not rules_skipped:
#         print(f"{Fore.GREEN}All tests passed successfully!{Style.RESET_ALL}")

#     sys.exit(1 if rules_failed or rules_skipped else 0)


# if __name__ == "__main__":
#     main()



import os
import concurrent.futures
import subprocess
import shutil
import sys
from colorama import Fore, Style
from pydantic import BaseModel
from typing import List, Union

####################
# Classes #
####################

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
        return os.path.basename(self.rule_file).replace('.guard', '')

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
        return [shutil.which('cfn-guard-validate'), 'test', '--rules-file', self.rule_file, '--data-file', self.test_file]

    def run(self) -> RuleTestResult:
        """
        Method to run a cfn-guard test

        :return: A rule test result object
        :rtype: RuleTestResult
        """

        # skip if no test data
        if not os.path.isfile(self.test_file):
            return RuleTestResult(
                rule_name=self.rule_name,
                detail='Cannot find corresponding test file in `tests` directory'
            )

        # Run cfn-guard utility if we have a test file
        test_run = subprocess.run(self.test_cmd, capture_output=True)

        return RuleTestResult(
            rule_name=self.rule_name,
            status=True if test_run.returncode == 0 else False,
            detail=test_run.stdout
        )

################
# Main #
################

def main():
    # Inform user of test start
    print("Running CloudFormation Guard rule tests\n")

    # Capture rules directory
    rules_dir = f"{os.path.join(os.path.dirname(os.path.realpath(__file__)), 'rules')}"

    # Setup list to capture the tests we need to run
    guard_tests: List[RuleTest] = []

    # Walk the rules directory and look for files with a .guard extension
    for root, dirs, files in os.walk(rules_dir):
        for filename in files:
            if filename.endswith('.guard'):
                guard_tests.append(RuleTest(os.path.join(root, filename)))

    # Print length of found tests to run
    print(f"Found {len(guard_tests)} rules to test\n")

    # Setup lists to capture passed, failed, and skipped tests
    rules_passed: List[RuleTestResult] = []
    rules_failed: List[RuleTestResult] = []
    rules_skipped: List[RuleTestResult] = []

    # Setup concurrent execution for running the tests
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        test_results: List[RuleTestResult] = []
        for test in guard_tests:
            test_results.append(executor.submit(test.run))

        # Run through completed future results and send to proper tracking destination
        for f in concurrent.futures.as_completed(test_results):
            result: RuleTestResult = f.result()
            if result.status is None:
                rules_skipped.append(result)
            elif result.status is True:
                # Did it actually pass? sometimes cfn-guard tests returns 0 with bad tests
                if 'Error processing' in result.detail:
                    rules_failed.append(result)
                elif 'Parse error on ruleset file' in result.detail:
                    rules_failed.append(result)
                else:
                    rules_passed.append(result)
            elif result.status is False:
                rules_failed.append(result)

    # Send some feedback to the console including detailed reporting on pass, fail, and skips
    print("Finished running CloudFormation Guard rule tests\n")
    print(f"{Fore.GREEN} {len(rules_passed)}{Style.RESET_ALL} rules passed, "
          f"{Fore.RED}{len(rules_failed)}{Style.RESET_ALL} rules failed, "
          f"{Fore.YELLOW}{len(rules_skipped)}{Style.RESET_ALL} rules skipped\n")

    if len(rules_skipped) > 0:
        print("The following rules failed to execute tests:")
        for rule in rules_skipped:
            print(f"{Fore.YELLOW}Rule: {rule.rule_name:<28}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Reason: {rule.detail}{Style.RESET_ALL}\n")

    if len(rules_failed) > 0:
        print("The following rules failed tests:")
        for rule in rules_failed:
            print(f"{Fore.RED}Rule: {rule.rule_name:<10}{Style.RESET_ALL}")
            print(f"{Fore.RED}Reason: (see below test case details) {Style.RESET_ALL}\n")
            print(rule.detail)

    if len(rules_skipped) == 0 and len(rules_failed) == 0:
        print("No rules failed or skipped tests.")

    print("Finished!")

    if len(rules_failed) > 0 or len(rules_skipped) > 0:
        print("Exiting code 1")
        sys.exit(1)

if __name__ == '__main__':
    main()
