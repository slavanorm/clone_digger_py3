from pathlib import Path
from unittest.mock import patch
from clonedigger.main import main


def test_finds_clones():
    with patch("sys.argv", ["clonedigger", "tests/test_me.py"]):
        main()
    assert Path("output.html").exists()
