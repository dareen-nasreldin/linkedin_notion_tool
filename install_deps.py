"""Run this once to set up dependencies: python install_deps.py"""
import subprocess
import sys

pip = [sys.executable, "-m", "pip", "install"]

subprocess.run(pip + ["numpy>=2.0"], check=True)
subprocess.run(pip + ["python-jobspy", "--no-deps"], check=True)
subprocess.run(pip + ["-r", "requirements.txt"], check=True)
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)

print("\n✅ All dependencies installed.")
