"""
Single-file module with a utility function to parse the source code and generate a reStructuredText
document with the environment variables defined using the ``environ_get`` function.

This is an optional extension to ``environ_get``.

Hosted at https://github.com/MarcinKonowalczyk/environ_get

Written by Marcin Konowalczyk.
"""

import ast
import textwrap
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from typing_extensions import TypeGuard
else:
    TypeGuard = type

# NOTE: This mirrors the version in environ_get.py. Remember to update both. There is a test which checks this.
__version__ = "1.0.2"

__all__ = ["generate_environ_doc"]


_warning = lambda msg: print(f"WARNING: {msg}")


@dataclass(frozen=True)
class EnvironGetCall:
    key: str
    description: Optional["Description"] = None
    other: tuple[str, ...] = ()
    default: Union[str, None] = None
    type: Union[str, None] = None

    def get_type(self) -> str:
        if self.description and self.description.type:
            return self.description.type
        elif self.type:
            if self.type in ("int", "float", "str", "bool"):
                return self.type
            elif self.type == "bool_parser":
                return "bool"
            else:
                _warning(f"Unknown type: {self.type}")
                return self.type
        else:
            return "str"

    def get_default(self) -> Union[str, None]:
        if self.description and self.description.default:
            return self.description.default
        elif self.default:
            return self.default
        else:
            return None

    def is_required(self) -> bool:
        return self.get_default() is None

    @property
    def section(self) -> Union[str, None]:
        if self.is_required():
            # Override the section for required variables
            return "REQUIRED"
        if self.description and self.description.section:
            return self.description.section
        return None


def is_environ_get(node: Union[ast.AST, None]) -> TypeGuard[ast.Call]:
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "environ_get"


def get_args_kwargs(node: ast.Call) -> tuple[tuple[str, ...], dict[str, str]]:
    args = tuple(ast.unparse(arg).strip("'") for arg in node.args)
    kwargs = {kw.arg: ast.unparse(kw.value).strip("'") for kw in node.keywords if kw.arg}
    return args, kwargs


@dataclass(frozen=True)
class Description:
    description: str
    default: Union[str, None] = None
    type: Union[str, None] = None
    section: Union[str, None] = None

    @classmethod
    def from_desc(cls, desc: str) -> "Description":
        _default, _type, _section = None, None, None
        new_desc = []
        for line in map(str.strip, desc.splitlines()):
            if line.startswith(".. default::"):
                _default = line.split("::")[1].strip()
            elif line.startswith(".. type::"):
                _type = line.split("::")[1].strip()
            elif line.startswith(".. section::"):
                _section = line.split("::")[1].strip()
            else:
                new_desc.append(line)
        return Description(
            description="\n".join(new_desc),
            default=_default,
            type=_type,
            section=_section,
        )


def _process_node(
    node: ast.Call,
    *,
    environ_get_calls: dict[str, EnvironGetCall],
    seen_linenumbers: set[int],
) -> None:
    args, kwargs = get_args_kwargs(node)
    key = args[0]
    if key in environ_get_calls:
        raise ValueError(f"Duplicate call to environ_get for {key} in line {node.lineno}")

    # Pick out the other argument and convert it to a tuple
    _other = kwargs.get("other")
    other: tuple[str, ...] = ()
    if _other:
        if _other[0] in ("(", "["):
            # other is a list or tuple
            try:
                other = eval(_other)
            except SyntaxError:
                _warning(f"Invalid other argument: {_other}")
        else:
            # Other is a single value
            other = (_other,)
    assert isinstance(other, tuple)

    # Check for duplicates in the other argument too.
    if other:
        for other_key in other:
            if other_key in environ_get_calls:
                raise ValueError(f"Duplicate call to environ_get for {key} in line {node.lineno}")

    environ_get_calls[key] = EnvironGetCall(
        key=key,
        other=other,
        default=kwargs.get("default"),
        type=kwargs.get("type"),
    )
    seen_linenumbers.add(node.lineno)


def find_environ_get_calls(content: str) -> dict[str, EnvironGetCall]:
    """Find all calls to environ_get in the source code and return a dictionary of EnvironGetCall objects."""

    environ_get_calls: dict[str, EnvironGetCall] = {}
    seen_linenumbers: set[int] = set()
    prev_node = None

    _process_node2 = lambda node: _process_node(
        node,
        environ_get_calls=environ_get_calls,
        seen_linenumbers=seen_linenumbers,
    )

    for node in ast.walk(ast.parse(content)):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if is_environ_get(value) and node.lineno not in seen_linenumbers:
                _process_node2(value)

        if is_environ_get(node) and node.lineno not in seen_linenumbers:
            _process_node2(node)

        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and prev_node
            and (isinstance(prev_node, (ast.Assign, ast.AnnAssign)))
        ):
            # Look for docstrings like just after the assignment
            value = prev_node.value
            if is_environ_get(value):
                args, _kwargs = get_args_kwargs(value)
                key = args[0]
                desc = textwrap.dedent(node.value.value).strip()
                environ_get_calls[key] = replace(environ_get_calls[key], description=Description.from_desc(desc))
                seen_linenumbers.add(node.lineno)

        prev_node = node

    return environ_get_calls


def render_doc_lines(
    calls_by_section: dict[Union[str, None], dict[str, EnvironGetCall]],
    *,
    refs: bool = True,
) -> list[str]:
    _lines = []

    def _add(s: Union[str, list[str]]) -> None:
        _lines.extend([s, ""] if isinstance(s, str) else [*s, ""])

    _add(["Environment Variables", "====================="])

    note = "_This document is automatically generated from the ``environ_get`` calls in the source code._"

    _add(textwrap.dedent(note).strip())

    sections = list(calls_by_section.keys())

    for section in sections:
        if section:
            _add([section, "-" * len(section)])
        else:
            _add(["Miscellaneous", "-------------"])

        calls = calls_by_section[section]

        for name, call in calls.items():
            if refs:
                # Add a reference to the variable. This is useful when using the
                # rendered documentation as part of a larger doc. It can then be
                # referenced using ``:ref:`VAR_NAME````
                _add(f".. _{name}:")

            if not call.other:
                _add(f"``{name}``")
            else:
                other_args = [f"``{arg}``" for arg in call.other]
                _add(f"``{name}`` (aliases: {', '.join(other_args)})")

            if call.description:
                desc_lines = [ln for ln in call.description.description.splitlines() if ln]
                _add(desc_lines)
            else:
                _warning(f"Missing description for {name}")

            default = call.get_default()
            if default:
                _add(f"**default**: {default} `({call.get_type()})`")
            else:
                # We're already in the REQUIRED section, so no need to add it again
                # _add(f"**REQUIRED** _({call.get_type()})_")
                pass

    return _lines


def sort_by_section(calls: dict[str, EnvironGetCall]) -> dict[Union[str, None], dict[str, EnvironGetCall]]:
    # Sort by section
    calls_by_section: dict[Union[str, None], dict[str, EnvironGetCall]] = {}
    for name, call in calls.items():
        if call.section not in calls_by_section:
            calls_by_section[call.section] = {}
        calls_by_section[call.section][name] = call

    # Within each section, sort by name
    for key in calls_by_section:
        section = calls_by_section[key]
        calls_by_section[key] = dict(sorted(section.items()))

    # Sort the sections such that REQUIRED is first
    sections = list(calls_by_section.keys())
    sections = sorted(sections, key=lambda x: x or "")
    if "REQUIRED" in sections:
        sections.remove("REQUIRED")
        sections.insert(0, "REQUIRED")

    # Sort the None section last
    if None in sections:
        sections.remove(None)
        sections.append(None)

    calls_by_section = {section: calls_by_section[section] for section in sections}

    return calls_by_section


def generate_environ_doc(
    content: str,
    *,
    refs: bool = True,
) -> str:
    """Render a reStructuredText document outlining the environment variables defined in the source code.
    `refs` is a flag that determines whether references to the variables are included in the generated documentation.
    """

    environ_get_calls = find_environ_get_calls(content)
    calls_by_section = sort_by_section(environ_get_calls)
    lines = render_doc_lines(calls_by_section, refs=refs)
    return "\n".join(lines)


__license__ = """
Copyright 2007-2024 Pallets
Copyright 2024 Marcin Konowalczyk

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:

1.  Redistributions of source code must retain the above copyright
    notice, this list of conditions and the following disclaimer.

2.  Redistributions in binary form must reproduce the above copyright
    notice, this list of conditions and the following disclaimer in the
    documentation and/or other materials provided with the distribution.

3.  Neither the name of the copyright holder nor the names of its
    contributors may be used to endorse or promote products derived from
    this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED
TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""


if __name__ == "__main__":
    # TODO: Write a nicer main to alow cli use and more these these to tests

    if False:
        TEST_ENV_VAR_ = environ_get("TEST_ENV_VAR_")  # type: ignore[name-defined] # noqa: F821
        """This is a test environment variable. This variable does not
        have a default value, so it is required. It will appear on top of the
        list of environment variables.
        """

        TEST_ENV_VAR_2 = environ_get("TEST_ENV_VAR_2", default=11, type=int)  # type: ignore[name-defined] # noqa: F821
        """This is another test environment variable. This one is an integer. The
        default value and type are automatically inferred from the call to
        ``environ_get``. This variable is in a section.

        .. section:: My Little Section
        """

        TEST_ENV_VAR_3 = environ_get("TEST_ENV_VAR_3", default=False, type=bool_parser)  # type: ignore[name-defined] # noqa: F821
        """This is a boolean test environment variable. It has a default value of
        ``False`` and is parsed using the ``bool_parser`` which is automatically
        understood by the documentation generator. It does not have a section so
        it will appear in the Miscellaneous section.
        """

        TEST_ENV_VAR_4 = environ_get("TEST_ENV_VAR_4", other="OLD_NAME_FOR_TEST_ENV_VAR_4")  # type: ignore[name-defined] # noqa: F821
        """This is a test environment variable with an alias. Its alias will be
        displayed in the parentheses next to the variable name.
        """

        TEST_ENV_VAR_5 = environ_get("TEST_ENV_VAR_5", default="hello", type=str)  # type: ignore[name-defined] # noqa: F821
        # This env var does not have a description. It will generate a warning.

        TEST_ENV_VAR_6 = environ_get("TEST_ENV_VAR_6", default=3.14, type=complex)  # type: ignore[name-defined] # noqa: F821
        """This variable has an unknown type. It will generate a warning.
        You should specify the type in the description using the ``.. type::``
        directive.
        """

    from pathlib import Path

    this_file = Path(__file__).resolve()

    out_rst = generate_environ_doc(
        this_file.read_text(),
        refs=True,
    )

    print(out_rst)
