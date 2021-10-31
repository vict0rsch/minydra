from pathlib import Path

import pytest

from minydra.dict import MinyDict


def test_init():
    _ = MinyDict()


def test_from_dict():
    d = MinyDict({1: 2, "a": 4, "b": {"c": 5}})
    assert d[1] == 2
    assert d["a"] == 4
    assert d["b"]["c"] == 5
    assert d.a == 4
    assert d.b.c == 5


def test_from_tuples():
    args = [("a", 1), ("b", 2), ("c", {"d": 3})]
    d = MinyDict(*args)
    assert d.a == 1
    assert d.b == 2
    assert d.c.d == 3

    d = MinyDict(args)
    assert d.a == 1
    assert d.b == 2
    assert d.c.d == 3


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
    d.z = {"m": 0}
    assert d.z.m == 0


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
    d = MinyDict({"a": 1, "r": {"t": 5, "key": ("superlongvalue" * 10)}})
    d.pretty_print()
    d = MinyDict(
        {"a": 1, "r": {"t": 5, ("superlongkey" * 10): 2}}
    )  # to be dealt with, not well handled
    d.pretty_print()


def test_dir():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    assert "a" in dir(d)
    assert "b" in dir(d)
    assert "r" in dir(d)
    assert 4 in d.keys()
    assert "t" in d.r


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
    p = Path(d.to_pickle("d.pkl", verbose=1))
    assert MinyDict.from_pickle(p) == d
    p.unlink()


def test_dump_json():
    d = MinyDict({"a": 1, "b": 2, "u": "x", "r": {"t": 5}})
    p = Path(d.to_json("d.json", verbose=1))
    assert MinyDict.from_json(p) == d
    p.unlink()


def test_dump_yaml():
    d = MinyDict({"a": 1, "b": 2, "u": "x", "r": {"t": 5}})
    p = Path(d.to_yaml("d.yaml", verbose=1))
    assert MinyDict.from_yaml(p) == d
    p.unlink()


def test_dump_no_overwrite():
    d = MinyDict({"a": 1, "b": 2, "u": "x", "r": {"t": 5}})
    p = Path(d.to_json("d.json"))
    with pytest.raises(FileExistsError):
        d.to_json(p, allow_overwrite=False)
    p.unlink()

    p = Path(d.to_pickle("d.pkl"))
    with pytest.raises(FileExistsError):
        d.to_pickle(p, allow_overwrite=False)
    assert MinyDict.from_pickle(p) == d
    p.unlink()

    p = Path(d.to_yaml("d.yaml"))
    with pytest.raises(FileExistsError):
        d.to_yaml(p, allow_overwrite=False)
    assert MinyDict.from_yaml(p) == d
    p.unlink()


def test_to_dict():
    d = MinyDict({"a": 1, "b": [{"c": 2}, {"d": {"e": 3}}]})
    assert d.b[0].c == 2
    assert d.to_dict() == {"a": 1, "b": [{"c": 2}, {"d": {"e": 3}}]}


def test_update():
    d1 = MinyDict({"a": 1, "b": 2, "r": {"t": 5}})
    d2 = d1.copy()
    u1 = MinyDict({"a": 3, "r": {"t": 4, "z": 7}})
    u2 = MinyDict({"a": 3, "r": {"t": 4}})
    t1 = MinyDict({"a": 3, "b": 2, "r": {"t": 4, "z": 7}})
    t2 = MinyDict({"a": 3, "b": 2, "r": {"t": 4}})

    assert d1.update(u1) == t1
    with pytest.raises(KeyError):
        d2.update(u1, strict=True)

    assert d2.update(u2, strict=False) == t2

    with pytest.raises(TypeError):
        d1.update({1: 2}, {3: 4})


def test_copy():
    d1 = MinyDict({"a": 1, "b": 2, "r": {"t": 5}})
    d2 = d1.copy()
    d3 = d1.deepcopy()

    assert d1 == d2
    assert d1 == d3

    d2.a = 2
    assert d1.a == 1
    d3.b = 4
    assert d1.b == 2
