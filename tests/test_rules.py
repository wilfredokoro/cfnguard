import subprocess
import pytest
import os

# Define test cases: (template_path, rule_path, should_pass)
test_cases = [
    ("templates/valid_s3.yaml", "rules/s3.guard", True),
    ("templates/invalid_s3.yaml", "rules/s3.guard", False),
    ("templates/valid_iam.yaml", "rules/iam.guard", True),
    # Add more here...
]

@pytest.mark.parametrize("template, rule, expected_success", test_cases)
def test_template_guard_compliance(template, rule, expected_success):
    assert os.path.exists(template), f"Template file not found: {template}"
    assert os.path.exists(rule), f"Guard rule file not found: {rule}"

    try:
        result = subprocess.run(
            ["cfn-guard", "validate", "-r", rule, "-d", template],
            capture_output=True,
            text=True
        )
    except FileNotFoundError:
        pytest.fail("❌ 'cfn-guard' not found. Make sure it's installed and in PATH.")

    if expected_success:
        assert result.returncode == 0, f"❌ FAILED: {template} should PASS against {rule}"
    else:
        assert result.returncode != 0, f"❌ FAILED: {template} should FAIL against {rule}"
