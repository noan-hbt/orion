import shutil
import subprocess
import sys


def test_orion_command_is_installed_and_reports_its_version() -> None:
    executable = shutil.which("orion")
    cmd = [executable, "--version"] if executable else [sys.executable, "-m", "orion", "--version"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    assert result.stdout.startswith("orion ")

