import os
from collections.abc import Iterator

import pytest

from environ_get import bool_parser, environ_get, set_environ_get_strict


@pytest.fixture(autouse=True)
def _prepare_environ() -> Iterator[None]:
    keys = {
        "NONEXISTENT_KEY": None,
        "INT_KEY": 42,
        "FLOAT_KEY": 3.14,
        "BOOL_KEY": True,
        "STR_KEY": "hello",
    }

    old_values = {key: os.environ.get(key) for key in keys}

    # Set the environment
    for key, value in keys.items():
        if value is not None:
            os.environ[key] = str(value)
        elif key in os.environ:
            del os.environ[key]

    yield

    # Restore the environment
    for key, value in old_values.items():
        if value is not None:
            os.environ[key] = value
        elif key in os.environ:
            del os.environ[key]


def test_environ_get() -> None:
    assert environ_get("INT_KEY") == "42"
    assert environ_get("FLOAT_KEY") == "3.14"
    assert environ_get("BOOL_KEY") == "True"
    assert environ_get("STR_KEY") == "hello"
    assert environ_get("NONEXISTENT_KEY", default=None) is None


def test_bool_parser() -> None:
    assert environ_get("BOOL_KEY", type=bool_parser) is True

    os.environ["BOOL_KEY"] = "false"
    assert environ_get("BOOL_KEY", type=bool_parser) is False

    os.environ["BOOL_KEY"] = "0"
    assert environ_get("BOOL_KEY", type=bool_parser) is False

    os.environ["BOOL_KEY"] = "1"
    assert environ_get("BOOL_KEY", type=bool_parser) is True

    os.environ["BOOL_KEY"] = "true"
    assert environ_get("BOOL_KEY", type=bool_parser) is True

    # Also test the parser directly
    assert bool_parser(True) is True
    assert bool_parser(False) is False
    assert bool_parser(1) is True
    assert bool_parser(0) is False


def test_environ_get_with_other() -> None:
    # Fallback to INT_KEY
    assert environ_get("NONEXISTENT_KEY", other="INT_KEY") == "42"

    # Match STR_KEY before FLOAT_KEY
    assert environ_get("NONEXISTENT_KEY", other=["STR_KEY", "FLOAT_KEY"]) == "hello"


def test_environ_get_strict() -> None:
    os.environ["INT_KEY"] = "not an int"

    # Non-strict mode returns the default value
    assert environ_get("INT_KEY", default=77, type=int, strict=False) == 77

    # Strict mode raises a ValueError
    with pytest.raises(ValueError):
        environ_get("INT_KEY", default=77, type=int, strict=True)

    # The default should be the non-strict mode
    assert environ_get("INT_KEY", default=77, type=int) == 77

    # But there is a way to set the strict mode globally
    set_environ_get_strict(True)

    with pytest.raises(ValueError):
        environ_get("INT_KEY", default=77, type=int)

    set_environ_get_strict(False)  # reset
