import sys
from unittest.mock import patch

import pytest

from minydra import Parser
from minydra.exceptions import MinydraWrongArgumentException


def test_init():
    with patch.object(sys, "argv", []):
        _ = Parser()
        _ = Parser(verbose=1)
        _ = Parser(allow_overwrites=True)
        _ = Parser(allow_overwrites=False)
        _ = Parser(warn_overwrites=True)
        _ = Parser(warn_overwrites=False)
        _ = Parser(parse_env=False)
        _ = Parser(parse_env=True)
        _ = Parser(warn_env=False)
        _ = Parser(warn_env=True)


def test_check_args():
    Parser.check_args(["p=2", "x=4", "a", "-t", "r.s=0"])
    with pytest.raises(MinydraWrongArgumentException):
        Parser.check_args([" ="])
    with pytest.raises(MinydraWrongArgumentException):
        Parser.check_args(["= "])
    with pytest.raises(MinydraWrongArgumentException):
        Parser.check_args(["p="])
    with pytest.raises(MinydraWrongArgumentException):
        Parser.check_args(["-p=2"])
    with pytest.raises(MinydraWrongArgumentException):
        Parser.check_args([".p=2"])


def test_simple_map_argv(capfd):
    args = ["a=2"]
    assert Parser.map_argv(args, True, False) == {"a": "2"}


def test_map_argv_overwrite_warn(capfd):
    args = ["a=2", "a=3"]
    assert Parser.map_argv(args, True, True) == {"a": "3"}
    out, err = capfd.readouterr()
    assert "Repeated argument a" in out


def test_map_argv_overwrite_no_warn(capfd):
    args = ["a=2", "a=3"]
    assert Parser.map_argv(args, True, False) == {"a": "3"}
    out, err = capfd.readouterr()
    assert not out


def test_map_argv_no_overwrite(capfd):
    args = ["a=2", "a=3"]
    with pytest.raises(MinydraWrongArgumentException):
        Parser.map_argv(args, False, False)


def test_map_argv_positive_flag():
    args = ["a", "b"]
    assert Parser.map_argv(args, False, False) == {"a": True, "b": True}


def test_map_argv_negative_flag():
    args = ["-a", "-b"]
    assert Parser.map_argv(args, False, False) == {"a": False, "b": False}


def test_map_argv_mixed_flags():
    args = ["a", "-b"]
    assert Parser.map_argv(args, False, False) == {"a": True, "b": False}


def test_set_env(monkeypatch, capfd):
    monkeypatch.setenv("USER", "TestingUser")
    monkeypatch.setenv("HOME", "TestingHome")
    monkeypatch.setenv("OTHER_VAR", "OTHER")
    monkeypatch.setenv("other_var", "other")
    assert Parser.set_env(3) == 3
    assert Parser.set_env("$HOME") == "TestingHome"
    assert Parser.set_env("$OTHER_VAR") == "OTHER"
    assert Parser.set_env("$other_var") == "other"
    assert Parser.set_env("$HOME/$USER") == "TestingHome/TestingUser"
    assert Parser.set_env("$HOME/$USER/project") == "TestingHome/TestingUser/project"
    assert Parser.set_env("$MINY_VAR_DOES_NOT_EXIST") == "$MINY_VAR_DOES_NOT_EXIST"
    out, err = capfd.readouterr()
    assert "Detected variable $MINY_VAR_DOES_NOT_EXIST" in out


def test_parse_arg_types_int():
    assert Parser.parse_arg_types({"a": "3"}) == {"a": 3}


def test_parse_arg_types_float():
    assert Parser.parse_arg_types({"a": "3.1"}) == {"a": 3.1}
    assert Parser.parse_arg_types({"a": "1e-4"}) == {"a": 0.0001}


def test_parse_arg_types_bool():
    assert Parser.parse_arg_types({"a": "true"}) == {"a": True}
    assert Parser.parse_arg_types({"a": "True"}) == {"a": True}
    assert Parser.parse_arg_types({"a": "false"}) == {"a": False}
    assert Parser.parse_arg_types({"a": "False"}) == {"a": False}


def test_parse_arg_types_list():
    assert Parser.parse_arg_types({"a": "[]"}) == {"a": []}
    assert Parser.parse_arg_types({"a": "[1, 2]"}) == {"a": [1, 2]}
    assert Parser.parse_arg_types({"a": "[1, 2, 'b']"}) == {"a": [1, 2, "b"]}
    assert Parser.parse_arg_types({"a": "[1, 2, 'b']", "c": 4}) == {
        "a": [1, 2, "b"],
        "c": 4,
    }
    assert Parser.parse_arg_types({"a": "[1, [2, 3]]"}) == {"a": [1, [2, 3]]}
    assert Parser.parse_arg_types({"a": "[1, [2, 1e-3]]"}) == {"a": [1, [2, 0.001]]}
    assert Parser.parse_arg_types({"a": "['false']"}) == {"a": [False]}
    assert Parser.parse_arg_types({"a": "[False]"}) == {"a": [False]}


def test_parse_arg_types_dict(monkeypatch):
    assert Parser.parse_arg_types({"a": "{}"}) == {"a": {}}
    assert Parser.parse_arg_types({"a": "{1: 2}"}) == {"a": {1: 2}}
    assert Parser.parse_arg_types({"a": "{1: 2e-3}"}) == {"a": {1: 0.002}}
    assert Parser.parse_arg_types({"a": "{1: False}"}) == {"a": {1: False}}
    assert Parser.parse_arg_types({"a": "{1: [1, 3]}"}) == {"a": {1: [1, 3]}}

    monkeypatch.setenv("USER", "TestingUser")
    assert Parser.parse_arg_types({"a": "{1: '$USER'}"}) == {"a": {1: "TestingUser"}}
