from typing import Any
from minydra.exceptions import MinyDictWrongAttributeException
from minydra.utils import split_line
import io
from contextlib import redirect_stdout
import shutil


class MinyDict(dict):
    """
    dot.notation access to dictionary attributes with additional custom
    methods
        .resolve() to map "foo.bar" keys into nested MinyDicts
        .pretty_print() to recursively print the MinyDict's items.
    """

    __getattr__ = dict.get
    __delattr__ = dict.__delitem__

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
            if "." not in k:
                continue
            else:
                sub_keys = k.split(".")
                d = self
                for sk in sub_keys[:-1]:
                    if not isinstance(d, (dict, MinyDict)) or sk not in d:
                        d[sk] = MinyDict()
                    if isinstance(d, dict):
                        d = MinyDict(d)
                    d = d[sk]
                d[sub_keys[-1]] = v
                del self[k]
        return self

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Set an attribute if it is not protected. Protected attributes
        are the set of native dict's attributes and MinyDict's custom
        methods

        Args:
            name (str): name of the attribute to set.
            value (Any): Value for the attribute.

        Raises:
            MinyDictWrongAttributeException: The attribute is protected
        """
        if name in set(dir(dict())) | {
            "resolve",
            "pretty_print",
            "_resolve_nests",
            "_resolve_dots",
        }:
            raise MinyDictWrongAttributeException(
                f"`{name}` is a  protected attribute of MinyDict"
            )
        super().__setitem__(name, value)

    def pretty_print(self, level=0):
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
            level (int, optional): Recursion level for indentation. Defaults to 0.
        """
        # capture output
        f = io.StringIO()
        with redirect_stdout(f):
            # indent according to nesting level in the dictionnary
            indent = level * 4 * " "

            # format to equal length before the keys' `:`
            ml = max([len(str(k)) for k in self] + [0]) + 1

            # print in alphabetical order
            for i in [
                i[0]
                for i in sorted(enumerate(map(str, self.keys())), key=lambda x: x[1])
            ]:
                k = list(self.keys())[i]
                v = self[k]
                if "MinyDict" in str(type(v)):
                    # recursive pretty_print call
                    print(f"{indent}{k}")
                    v.pretty_print(level + 1)
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

            # box bottom border
            new_lines += ["╰" + "─" * (max_len + 2) + "╯"]

            # print box
            print("\n".join(new_lines))
        return self
