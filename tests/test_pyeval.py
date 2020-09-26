import io

from pyeval.user_shell import UserShell


def test_execute_code():
    buf = io.StringIO()
    user_shell = UserShell(print_file=buf)
    user_shell.execute_code("a = 1; a + 1; b = 2; a + b")
    result = buf.getvalue()
    assert result == "2\n3\n"
