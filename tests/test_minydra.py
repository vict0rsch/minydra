import json
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

import minydra
from minydra.dict import MinyDict


def test_resolved_args():
    with patch.object(sys, "argv", ["", "foo=bar", "-verbose"]):
        args = minydra.resolved_args()
        assert not args.verbose
        assert args.foo == "bar"


def test_parse_args_decorator():
    with patch.object(sys, "argv", ["", "foo=bar", "-verbose"]):

        @minydra.parse_args()
        def main(args):
            args.resolve()
            assert args.verbose is False
            assert args.foo == "bar"

        main()


def test_defaults():

    examples = Path(__file__).resolve().parent.parent / "examples"
    d1 = examples / "demo.json"
    d2 = examples / "demo2.json"
    y1 = examples / "demo.yaml"

    p = MinyDict({"a": "2", "c": 3, "d": {"e": {"f": 4, "g": 5}}})
    pkl = p.to_pickle(Path(__file__).resolve().parent / "test.pkl")

    with patch.object(sys, "argv", [""]):
        args = minydra.resolved_args(defaults=p)
        assert args == p

    with patch.object(sys, "argv", ["", "d.e.f=2"]):
        args = minydra.resolved_args(defaults=p)
        assert args.d.e.f == 2

    with patch.object(sys, "argv", ["", f"@defaults={str(d1)}"]):
        args = minydra.resolved_args()
        del args["@defaults"]
        assert args.to_dict() == json.loads(d1.read_text())

    with patch.object(sys, "argv", ["", f"@defaults={str(y1)}"]):
        args = minydra.resolved_args()
        del args["@defaults"]
        assert args.to_dict() == MinyDict.from_yaml(y1)

    with patch.object(sys, "argv", ["", f"@defaults={str(pkl)}"]):
        args = minydra.resolved_args()
        del args["@defaults"]
        assert args.to_dict() == MinyDict.from_pickle(pkl)
        Path(pkl).unlink()

    with pytest.raises(ValueError):
        with patch.object(
            sys, "argv", ["", f"@defaults={str(d1).replace('.json', '.py')}"]
        ):
            args = minydra.resolved_args()

    with pytest.raises(KeyError):
        with patch.object(sys, "argv", ["", f"@defaults={str(d1)}", "new_key=3"]):
            args = minydra.resolved_args()
            del args["@defaults"]
            assert args.to_dict() == json.loads(d1.read_text())

    with patch.object(
        sys, "argv", ["", f"@defaults={str(d1)}", "@strict=false", "new_key=3"]
    ):
        args = minydra.resolved_args(keep_special_kwargs=False)
        target = json.loads(d1.read_text())
        target["new_key"] = 3
        assert args.to_dict() == target

    with patch.object(
        sys, "argv", ["", f"@defaults={str(d1)}", "@strict=false", "new_key=3"]
    ):
        args = minydra.resolved_args()
        del args["@defaults"]
        del args["@strict"]
        target = json.loads(d1.read_text())
        target["new_key"] = 3
        assert args.to_dict() == target

    double_defaults = f"['{str(d1)}', '{str(d2)}']"
    with patch.object(sys, "argv", ["", f"@defaults={double_defaults}", "new_key=3"]):
        args = minydra.resolved_args()
        d1d = MinyDict.from_json(d1)
        d2d = MinyDict.from_json(d2)
        d1d = d1d.update(d2d)
        del args["@defaults"]
        assert args == d1d
