"""A missing --data-list file must be a clean CLI error, not a traceback."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_missing_data_list_exits_2_with_clean_message():
    proc = subprocess.run(
        [sys.executable, "slate.py", "-d", "definitely-missing-list.txt"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "Cannot open / find 'definitely-missing-list.txt'" in proc.stderr
    assert "Traceback" not in proc.stderr
