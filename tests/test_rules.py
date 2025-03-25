import subprocess
import os

def run_cfn_guard(template, ruleset):
    result = subprocess.run(
        ["cfn-guard", "validate", "-r", ruleset, "-d", template],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    return result.returncode, result.stdout.decode(), result.stderr.decode()

def test_valid_template():
    code, out, err = run_cfn_guard("templates/valid_template.yaml", "rules/s3.guard")
    assert code == 0, f"Expected pass but failed. Output: {out}\nError: {err}"

def test_invalid_template():
    code, out, err = run_cfn_guard("templates/invalid_template.yaml", "rules/s3.guard")
    assert code != 0, "Expected failure but passed"
    assert "BucketEncryption" in out or err, "Expected encryption failure message"
