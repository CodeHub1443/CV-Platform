import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest",
     "tests/configuration/api/",
     "-v", "--tb=short"],
    cwd="E:/dev/CV-Platform/CV-Platform",
    capture_output=True,
    text=True
)
print(result.stdout)
print(result.stderr)
sys.exit(result.returncode)
