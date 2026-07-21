from claimlens.cli import main


def test_cli_help_lists_mvp_commands(capsys):
    try:
        main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0

    output = capsys.readouterr().out

    for command in [
        "init-db",
        "ingest",
        "candidates",
        "transcribe",
        "analyze",
        "source-check",
        "brief",
        "run-daily",
    ]:
        assert command in output


def test_init_db_command_creates_database(tmp_path, capsys):
    database = tmp_path / "claimlens.sqlite3"

    exit_code = main(["init-db", "--database", str(database)])

    assert exit_code == 0
    assert database.exists()
    assert str(database) in capsys.readouterr().out


def test_placeholder_commands_exit_successfully(capsys):
    commands = [
        ["ingest"],
        ["candidates"],
        ["transcribe", "video123"],
        ["analyze", "video123"],
        ["source-check", "video123"],
        ["brief", "video123"],
        ["run-daily"],
    ]

    for command in commands:
        assert main(command) == 0

    output = capsys.readouterr().out
    assert "planned for Milestone" in output
    assert "video123" in output
