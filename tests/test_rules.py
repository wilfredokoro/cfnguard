import subprocess
import pytest

TEMPLATE_PATH = "templates/template.yaml"
RULES_PATH = "rules/s3.guard"

def run_cfn_guard(template_path, rules_path):
    """Run cfn-guard validate and return (code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["cfn-guard", "validate", "-r", rules_path, "-d", template_path],
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr
    except FileNotFoundError:
        pytest.fail("cfn-guard binary not found. Is it installed and in PATH?")
    except Exception as e:
        pytest.fail(f"Error running cfn-guard: {e}")

def test_template_compliance():
    """Test that the template passes cfn-guard rules."""
    code, out, err = run_cfn_guard(TEMPLATE_PATH, RULES_PATH)
    print("CFN Guard Output:\n", out or err)
    assert code == 0, f"Template failed validation. Exit code: {code}\n{out or err}"
