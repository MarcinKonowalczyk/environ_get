def test_version() -> None:
    from environ_get.environ_get import __version__ as environ_get_version
    from environ_get.environ_get_parser import __version__ as environ_get_parser_version

    assert environ_get_version == environ_get_parser_version
