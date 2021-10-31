# Largely inspired by https://github.com/mewwts/addict/blob/master/addict/addict.py

import copy
import io
import json
import pickle as pkl
import shutil
from contextlib import redirect_stdout
from typing import Any

from minydra.utils import resolve_path, split_line

try:
    import yaml
except ImportError:
    yaml = None


class MinyDict(dict):
    """
    dot.notation access to dictionary attributes with additional custom
    methods
        .resolve() to map "foo.bar" keys into nested MinyDicts
        .pretty_print() to recursively print the MinyDict's items.
    """

    __getattr__ = dict.get
    __getitem__ = dict.get
    __delattr__ = dict.__delitem__
    _frozen = False

    def __init__(self, *args, **kwargs):
        object.__setattr__(self, "_frozen", False)
        for arg in args:
            if not arg:
                continue
            elif isinstance(arg, dict):
                for key, val in arg.items():
                    self[key] = self._hook(val)
            elif isinstance(arg, tuple) and (not isinstance(arg[0], tuple)):
                self[arg[0]] = self._hook(arg[1])
            else:
                for key, val in iter(arg):
                    self[key] = self._hook(val)

        for key, val in kwargs.items():
            self[key] = self._hook(val)

    @classmethod
    def _hook(cls, item):
        if isinstance(item, MinyDict):
            return item
        if isinstance(item, dict):
            return cls(item)
        elif isinstance(item, (list, tuple)):
            return type(item)(cls._hook(elem) for elem in item)
        return item

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set an attribute if it is not protected. Protected attributes
        are the set of native dict's attributes and MinyDict's custom
        methods

        Args:
            name (str): name of the attribute to set.
            value (Any): Value for the attribute.

        Raises:
            AttributeError: The attribute is protected
        """
        if hasattr(self.__class__, name):
            raise AttributeError(f"`{name}` is a  protected attribute of MinyDict.")
        self.__setitem__(name, value)

    def __setitem__(self, name, value):
        isFrozen = hasattr(self, "_frozen") and object.__getattribute__(self, "_frozen")
        if isFrozen:
            raise AttributeError(
                "This MinyDict is frozen: no attribute can be changed."
                + " Use .unfreeze() to change this."
            )
        if isinstance(value, dict):
            value = MinyDict(value)
            value._resolve_nests()

        super().__setitem__(name, value)

    def __dir__(self):
        attrs = set(dir(self.__class__)) | set(self.keys())
        return sorted([a for a in attrs if isinstance(a, str)])

    def update(self, *args, strict=False, **kwargs):
        other = {}
        if args:
            if len(args) > 1:
                raise TypeError("Can only update from 1 other dict")
            other.update(args[0])
        other.update(kwargs)
        for k, v in other.items():
            if strict and k not in self:
                raise KeyError(
                    "Cannot create a non-existing key in strict mode "
                    + f'({{"{k}":{v}}}).'
                )
            if (
                (k not in self)
                or (not isinstance(self[k], dict))
                or (not isinstance(v, dict))
            ):
                self[k] = v
            else:
                self[k].update(v, strict=strict)
        return self

    def copy(self):
        return copy.copy(self)

    def deepcopy(self):
        return copy.deepcopy(self)

    def __deepcopy__(self, memo):
        other = self.__class__()
        memo[id(self)] = other
        for key, value in self.items():
            other[copy.deepcopy(key, memo)] = copy.deepcopy(value, memo)
        return other

    def __getnewargs__(self):
        return tuple(self.items())

    def __getstate__(self):
        return self

    def __setstate__(self, state):
        self.update(state)

    def freeze(self, shouldFreeze=True):
        object.__setattr__(self, "_frozen", shouldFreeze)
        for val in self.values():
            if isinstance(val, MinyDict):
                val.freeze(shouldFreeze)

    def to_pickle(self, file_path, return_path=True, allow_overwrite=True, verbose=0):
        """
        Dumps the MinyDict to a pickle file.

        Args:
            file_path (str or pathlib.Path): path (and name) of the file to save to
            return_path (bool, optional): Whether to return the resulting file's path
                (as str). Defaults to True.
            allow_overwrite (bool, optional): Whether to allow overwrites, or raise a
                FileError if the file already exits. Defaults to True.
            verbose (int, optional): >0 => print the path. Defaults to 0.

        Returns:
            Optional[str]: Path to the dumped file
        """
        p = resolve_path(file_path)

        if not allow_overwrite and p.exists():
            raise FileExistsError(
                f"Error dumping the MinyDict: file {p} already exists."
            )

        with p.open("wb") as f:
            pkl.dump(self, f)

        if verbose > 0:
            print("Pickled to:", str(p))

        if return_path:
            return str(p)

    @classmethod
    def from_pickle(self, file_path):
        """
        Reads a MinyDict from a pickle file.

        Args:
            file_path (str): Path to the file to load from.
        """
        p = resolve_path(file_path)
        with p.open("rb") as f:
            return pkl.load(f)

    def to_json(self, file_path, return_path=True, allow_overwrite=True, verbose=0):
        """
        Dumps the MinyDict to a json file.

        Args:
            file_path (str or pathlib.Path): path (and name) of the file to save to
            return_path (bool, optional): Whether to return the resulting file's path
                (as str). Defaults to True.
            allow_overwrite (bool, optional): Whether to allow overwrites, or raise a
                FileError if the file already exits. Defaults to True.
            verbose (int, optional): >0 => print the path. Defaults to 0.

        Returns:
            Optional[str]: Path to the dumped file
        """
        p = resolve_path(file_path)
        if not allow_overwrite and p.exists():
            raise FileExistsError(
                f"Error dumping the MinyDict: file {p} already exists."
            )

        with p.open("w") as f:
            json.dump(self.to_dict(), f)

        if verbose > 0:
            print("Json dumped to:", str(p))

        if return_path:
            return str(p)

    @classmethod
    def from_json(self, file_path):
        """
        Reads a MinyDict from a json file.

        Args:
            file_path (str): Path to the file to load from.
        """
        p = resolve_path(file_path)
        with p.open("r") as f:
            return MinyDict(json.load(f))

    def to_yaml(self, file_path, return_path=True, allow_overwrite=True, verbose=0):
        """
        Dumps the MinyDict to a YAML file. Requires the PyYAML package:
            $ pip install --upgrade minydra[yaml]
        Or
            $ pip install PyYAML

        Args:
            file_path (str or pathlib.Path): path (and name) of the file to save to
            return_path (bool, optional): Whether to return the resulting file's path
                (as str). Defaults to True.
            allow_overwrite (bool, optional): Whether to allow overwrites, or raise a
                FileError if the file already exits. Defaults to True.
            verbose (int, optional): >0 => print the path. Defaults to 0.

        Returns:
            Optional[str]: Path to the dumped file
        """
        if yaml is None:
            raise ModuleNotFoundError(
                "Cannot import module 'yaml'.\n"
                + "Install minydra with YAML: $ pip install minydra[yaml]\n"
                + "Or install it directly: $ pip install PyYAML"
            )
        p = resolve_path(file_path)

        if not allow_overwrite and p.exists():
            raise FileExistsError(
                f"Error dumping the MinyDict: file {p} already exists."
            )

        with p.open("w") as f:
            yaml.safe_dump(self.to_dict(), f)

        if verbose > 0:
            print("YAML dumped to:", str(p))

        if return_path:
            return str(p)

    @classmethod
    def from_yaml(self, file_path):
        """
        Reads a MinyDict from a json file.

        Args:
            file_path (str): Path to the file to load from.
        """
        if yaml is None:
            raise ModuleNotFoundError(
                "Cannot import module 'yaml'.\n"
                + "Install minydra with YAML: $ pip install minydra[yaml]\n"
                + "Or install it directly: $ pip install PyYAML"
            )
        p = resolve_path(file_path)
        with p.open("r") as f:
            return MinyDict(yaml.safe_load(f))

    def to_dict(self):
        base = {}
        for key, value in self.items():
            if isinstance(value, type(self)):
                base[key] = value.to_dict()
            elif isinstance(value, (list, tuple)):
                base[key] = type(value)(
                    item.to_dict() if isinstance(item, type(self)) else item
                    for item in value
                )
            else:
                base[key] = value
        return base

    def unfreeze(self):
        self.freeze(False)

    def resolve(self):
        """
        Chains the calls to resolve dotted keys and convert nested dicts to MinyDicts.
        Changes are done in-place but still returns self to chain calls

        Returns:
            MinyDict: Resolved version of self
        """
        return self._resolve_nests()._resolve_dots()

    def _resolve_nests(self):
        for k in list(self.keys()):
            v = self[k]
            if isinstance(v, dict):
                v = MinyDict(v)
                v._resolve_nests()
                self[k] = v
        return self

    def _resolve_dots(self):
        """
        Resolves "foo.bar" keys into nested MinyDicts:

        MinyDict({"a": 1, "b.c.d" : 2}).resolve()
        >>> MinyDict({
            "a": 1,
            "b": {
                "c": {
                    "d": 2
                }
            }
        })

        Changes are in-place *and* it returns itself to chain calls

        Returns:
            [type]: [description]
        """
        for k in list(self.keys()):
            v = self[k]
            if isinstance(v, MinyDict):
                self[k] = self[k]._resolve_dots()
            if not isinstance(k, str) or "." not in k:
                continue
            else:
                # Key has has dots:
                # iterate over subkeys
                # assign value to final sub-key
                sub_keys = k.split(".")
                d = self
                for sk in sub_keys[:-1]:
                    if sk not in d:  # sub key does not exist in original obj
                        # create new sub dict
                        d[sk] = MinyDict()
                    if isinstance(d[sk], MinyDict):
                        # next sub dict is a MinyDict:
                        # resolve its dots
                        d[sk] = d[sk]._resolve_dots()
                    d = d[sk]
                d[sub_keys[-1]] = v
                del self[k]
        return self

    def pretty_print(self, indents=2, sort_keys=True):
        """
        Recursively pretty print MinyDict's items.
        Returns itself to chain method calls

        $ python parser.py foo=bar yes.no.maybe=idontknow

        ╭───────────────────────────────╮
        │ foo : bar                     │
        │ yes                           │
        │     no                        │
        │         maybe : idontknow     │
        ╰───────────────────────────────╯

        Args:
            indents (int, optional): Number of space to indent nested dicts.
                Defaults to 2.
            sort_keys (bool, optional): Whether or not to sort dict keys before
                printing. Defaults to True.

        Returns:
            MinyDict: self
        """
        self._pretty_print_rec(indents, sort_keys, 0)
        return self

    def _pretty_print_rec(self, indents, sort_keys, level):
        """
        Recursively pretty print MinyDict's items.
        Returns itself to chain method calls

        Args:
            indents (int): Number of space to indent nested dicts Defaults to 2.
            sort_keys (bool): Whether or not to sort dict keys before printing.
            level (int): Recursion level for indentation.

        Returns:
            MinyDict: self
        """
        # capture output
        f = io.StringIO()
        with redirect_stdout(f):
            # indent according to nesting level in the dictionnary
            indent = ""
            for _ in range(level - 1):
                indent += "│" + " " * (indents - 1)
            if level > 0:
                indent += "│"
            # indent = level * indents * " "
            # indent = indent[:-1] + "╰"

            # format to equal length before the keys' `:`
            ml = max([len(str(k)) for k in self] + [0]) + 1

            # print in alphabetical order if sort_keys is True
            keys = map(str, self.keys())
            if sort_keys:
                keys = sorted(keys)

            for k in keys:
                v = self[k]
                if "MinyDict" in str(type(v)):
                    # recursive pretty_print_rec call
                    print(f"{indent}{k}")
                    v._pretty_print_rec(
                        indents=indents,
                        sort_keys=sort_keys,
                        level=level + 1,
                    )
                else:
                    # print value
                    print(f"{indent}{k:{ml}}: {v}")
        if level > 0:
            # lower recursive call: print to forward up to the
            # first (highest) call which will print the box
            print(f.getvalue())
        else:
            # highest call level: print captured output inside a box
            # matching the terminal's width

            # list of captured print outputs
            lines = f.getvalue().split("\n")
            # filter our trailing line
            if not lines[-1]:
                lines = lines[:-1]

            # maximum line length which would be printed (`| {line} |`)
            max_len = max(len(line) for line in lines + [""]) + 4

            # get terminal window width
            term_width = shutil.get_terminal_size((80, 20))[0] - 4

            # longest line is longer than terminal window width
            if max_len > term_width:
                max_len = term_width

            # box top border
            new_lines = ["╭" + "─" * (max_len + 2) + "╮"]

            # add lines
            for line in lines:
                # maximum authorized length is max_len if line is short
                # enough, otherwise it's max_len - indentation
                # where the indentation is computed to match the key's `:`
                line_max = (
                    max_len - (line.find(":") + 2)
                    if ":" in line and len(line) > max_len
                    else max_len
                )
                # add sublines
                for s, subline in enumerate(split_line(line, line_max)):
                    # the line was split: indent to match the key's `:`
                    if s > 0:
                        subline = " " * (line.find(":") + 2) + subline
                    new_lines.append(f"│ {subline:{max_len}} │")

                if line_max < 1:
                    # the previous for loop did not occur (no addition to new_lines)
                    new_lines.append(f"│ {line} │")

            # box bottom border
            new_lines += ["╰" + "─" * (max_len + 2) + "╯"]

            # print box
            print("\n".join(new_lines))
