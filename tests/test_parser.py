import io
import subprocess
from contextlib import redirect_stdout

from minydra.dict import MinyDict

# from minydra.exceptions import MinydraWrongArgumentException

COMMAND = [
    "python",
    "-c",
    "from minydra import Parser; parser = Parser(); parser.args.resolve().pretty_print()",
]


def run(args):
    assert isinstance(args, list)
    return subprocess.run(COMMAND + args, capture_output=True).stdout.decode()


def fail(args):
    assert isinstance(args, list)
    return subprocess.run(COMMAND + args, capture_output=True).stderr.decode()


def capture(minydict):
    f = io.StringIO()
    with redirect_stdout(f):
        minydict.resolve().pretty_print()
    return f.getvalue()


def test_empty():
    assert run([]) == capture(MinyDict({}))


def test_basic():
    assert run(["a=1", "b=1e-3", "c", "-d"]) == capture(
        MinyDict({"a": 1, "b": 0.001, "c": True, "d": False})
    )


def test_env(monkeypatch):
    monkeypatch.setenv("USER", "TestingUser")
    assert run(["a=$USER"]) == capture(MinyDict({"a": "TestingUser"}))


def test_dict():
    assert run(["a={}".format('{"b": 3}')]) == capture(MinyDict({"a": {"b": 3}}))


def test_list():
    assert run(["a=[2, 4, 'x']"]) == capture(MinyDict({"a": [2, 4, "x"]}))


def test_dotted():
    assert run(["a.b.x=2"]) == capture(MinyDict({"a": {"b": {"x": 2}}}))


def test_fail_equal():
    assert "MinydraWrongArgumentException" in fail(["a="])
    assert "MinydraWrongArgumentException" in fail(["="])
    assert "MinydraWrongArgumentException" in fail(["a = b"])
    assert "MinydraWrongArgumentException" in fail(["a= b"])


def test_fail_dot():
    assert "MinydraWrongArgumentException" in fail([".a=3"])
