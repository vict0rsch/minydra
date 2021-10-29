from pathlib import Path

import pytest

from minydra.dict import MinyDict


def test_init():
    _ = MinyDict()


def test_from_dict():
    _ = MinyDict({1: 2, 3: 4})


def test_in():
    d = MinyDict({"a": 1, "b": 2, 4: "x"})
    assert "a" in d
    assert "b" in d
    assert "x" not in d
    assert d.z is None
    assert 4 in d
    assert d.a == 1
    assert d.b == 2
    assert d[4] == "x"


def test_attr():
    d = MinyDict({"a": 1, "b": 2, 4: "x"})
    d.x = 3
    assert d.x == 3
    d.y = MinyDict({"w": 4})
    assert d.y.w == 4


def test_resolve():
    d = MinyDict({"a.b.c": 2})
    d.resolve()
    assert d == MinyDict({"a": {"b": {"c": 2}}})

    d = MinyDict({"a.b.c": 2, "a.b.d": 3})
    d.resolve()
    assert d == MinyDict({"a": {"b": {"c": 2, "d": 3}}})

    d = MinyDict({"a.b.c": 2, "a.b.d": {"r.v": 4}, "x": {"o.p": 3}})
    d.resolve()
    assert d == MinyDict(
        {"x": {"o": {"p": 3}}, "a": {"b": {"c": 2, "d": {"r": {"v": 4}}}}}
    )


def test_pretty_print():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    d.pretty_print()


def test_dir():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    assert "a" in dir(d)
    assert "b" in dir(d)
    assert "r" in dir(d)
    assert 4 in d.keys()


def test_protected():
    d = MinyDict()
    with pytest.raises(AttributeError):
        d.update = 4
    d["update"] = 4


def test_freeze():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    d.freeze()
    with pytest.raises(AttributeError):
        d.r.t = 4
    d.unfreeze()
    d.r.t = 4


def test_dump_pickle():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    p = Path(d.to_pickle("d.pkl"))
    assert MinyDict.from_pickle(p) == d
    p.unlink()


def test_dump_json():
    d = MinyDict({"a": 1, "b": 2, "u": "x", "r": {"t": 5}})
    p = Path(d.to_json("d.json"))
    assert MinyDict.from_json(p) == d
    p.unlink()


def test_dump_no_overwrite():
    d = MinyDict({"a": 1, "b": 2, "u": "x", "r": {"t": 5}})
    p = Path(d.to_json("d.json"))
    with pytest.raises(FileExistsError):
        d.to_json(p, allow_overwrite=False)
    p.unlink()

    p = Path(d.to_pickle("d.pickle"))
    with pytest.raises(FileExistsError):
        d.to_pickle(p, allow_overwrite=False)
    assert MinyDict.from_pickle(p) == d
    p.unlink()
