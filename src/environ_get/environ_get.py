"""
Single-file module with a utility function to get the value of the key from the environment
with optional type conversion and default value.

Hosted at https://github.com/MarcinKonowalczyk/environ_get

Written by Marcin Konowalczyk.
"""

import os
from collections.abc import Callable
from typing import TypeVar, Union, overload

__version__ = "0.2.0"

__all__ = ["environ_get", "set_environ_get_strict", "bool_parser"]

_D = TypeVar("_D")
_T = TypeVar("_T")

_missing = object()

__ENVIRON_GET_STRICT = False
"""If True, raise an exception if the key is not found in the environment."""


def set_environ_get_strict(strict: bool) -> None:
    global __ENVIRON_GET_STRICT  # noqa: PLW0603
    __ENVIRON_GET_STRICT = strict


@overload
def environ_get(*keys: str, default: None = ..., type: None = ...) -> str: ...


@overload
def environ_get(*keys: str, default: _D, type: None = ...) -> Union[_D, str]: ...


@overload
def environ_get(*keys: str, default: _D, type: Callable[[str], _T]) -> Union[_D, _T]: ...


@overload
def environ_get(*keys: str, type: Callable[[str], _T]) -> _T: ...


def environ_get(
    *keys: str,
    default: _D = _missing,  # type: ignore
    type: Union[Callable[[str], _T], None] = None,
    strict: Union[bool, None] = None,
) -> Union[str, _D, _T]:
    """Get the value of the first key found in the environment. If no key is found, return the default value,
    or raise an exception if no default is provided. Optionally, convert the value to the desired type.
    If the conversion fails, raise an exception or return the default value (if provided).
    """
    strict = __ENVIRON_GET_STRICT if strict is None else strict
    environ = os.environ
    value: Union[str, None] = None
    for key in keys:
        # NOTE: environ.get() returns str | None
        value = environ.get(key)
        if value is not None:
            break

    # Found a key! Return it possibly converted to the desired type
    if value is not None:
        if type is not None:
            try:
                return type(value)
            except ValueError:
                # If the conversion fails, raise an exception or return the default value
                if strict:
                    raise
                if default is _missing:
                    # We don't have a default value. Nothing else to do.
                    raise
                return default
        return value

    # We got here because none of the keys were found
    if default is _missing:
        if len(keys) == 1:
            message = f"The key {keys[0]} was not found in the environment."
        else:
            message = f"None of the keys {list(keys)} were found in the environment."
        raise ValueError(message)

    return default


TRUE_VALUES = {"T", "Y", "1", "True", "true", "TRUE", "Yes", "yes", "YES", True, 1}
FALSE_VALUES = {"F", "N", "0", "False", "false", "FALSE", "No", "no", "NO", "", False, 0}


def bool_parser(
    value: object,
    true_values: set[object] = TRUE_VALUES,
    false_values: set[object] = FALSE_VALUES,
) -> bool:
    """Universal bool parser"""
    if value in true_values:
        return True
    elif value in false_values:
        return False
    else:
        raise ValueError(f"Cannot parse '{value!r}' of type {type(value)} to a bool.")


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
