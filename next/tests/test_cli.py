import subprocess


def test_telos_command_is_installed_and_reports_its_version() -> None:
    result = subprocess.run(["telos", "--version"], capture_output=True, text=True, check=True)
    assert result.stdout.startswith("telos ")
