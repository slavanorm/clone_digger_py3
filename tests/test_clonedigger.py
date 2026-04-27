import re
from pathlib import Path
from clonedigger.main import main


def test_finds_clones():
    output = Path("output.html")
    main(fps=[Path("tests/test_me.py")], output=output)
    assert output.exists()


def test_diff_chunks_formatted(tmp_path):
    """#3: code in output.html should be indented with newlines inside <PRE> tags."""
    output = tmp_path / "output.html"
    main(fps=[Path("tests/test_me.py")], output=output)
    html = output.read_text()
    blocks = re.findall(r"<PRE>(.*?)</PRE>", html, re.DOTALL)
    assert len(blocks) > 0
    for block in blocks:
        assert "\n" in block or len(block.splitlines()) == 1
        assert "\\n" not in block


def test_multiline_strings_preserved(tmp_path):
    """#6: multiline docstrings should not lose lines in report."""
    output = tmp_path / "output.html"
    main(fps=[Path("tests/test_issue6.py")], output=output)
    html = output.read_text()
    assert "param (str): param" in html
