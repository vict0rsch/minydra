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
    d = MinyDict({"a.b.c": 2, "a.b.d": 3})
    d.resolve()
    assert d == MinyDict({"a": {"b": {"c": 2, "d": 3}}})


def test_pretty_print():
    d = MinyDict({"a": 1, "b": 2, 4: "x", "r": {"t": 5}})
    d.pretty_print()
