from pathlib import Path
from clonedigger.main import main


def test_finds_clones():
    output = Path("output.html")
    main(fps=[Path("tests/test_me.py")], output=output)
    assert output.exists()
