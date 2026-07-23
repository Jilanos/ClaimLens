from claimlens.cli import main
from claimlens.youtube import TranscriptResult, TranscriptSegment, YouTubeVideo


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
        "run-video",
        "transcribe",
        "analyze",
        "source-check",
        "brief",
        "verify-sources",
        "serve",
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
        ["run-daily"],
    ]

    for command in commands:
        assert main(command) == 0

    output = capsys.readouterr().out
    assert "planned for Milestone" in output


def test_run_video_rejects_non_video_url(capsys):
    exit_code = main(["run-video", "https://www.youtube.com/@example/videos"])

    assert exit_code == 1
    assert "exactly one YouTube video ID" in capsys.readouterr().out


def test_analyze_requires_openai_key(tmp_path, capsys):
    database = tmp_path / "claimlens.sqlite3"

    exit_code = main(["analyze", "video123", "--database", str(database)])

    assert exit_code == 1
    assert "OPENAI_API_KEY is required" in capsys.readouterr().out


def test_source_check_requires_analysis(tmp_path, capsys):
    database = tmp_path / "claimlens.sqlite3"

    exit_code = main(["source-check", "video123", "--database", str(database)])

    assert exit_code == 1
    assert "Cannot verify sources before analysis exists" in capsys.readouterr().out


def test_transcribe_channel_extracts_and_stores_transcript(monkeypatch, tmp_path, capsys):
    database = tmp_path / "claimlens.sqlite3"

    monkeypatch.setattr(
        "claimlens.cli.latest_channel_videos",
        lambda channel_url, *, limit: [
            YouTubeVideo(
                id="video123",
                title="Test Video",
                url="https://www.youtube.com/watch?v=video123",
                published_text="1 day ago",
            )
        ],
    )
    monkeypatch.setattr(
        "claimlens.cli.fetch_transcript",
        lambda video_id: TranscriptResult(
            video_id=video_id,
            source="youtube-auto",
            language="en",
            text="hello world",
            segments=[TranscriptSegment(start_seconds=0.0, end_seconds=1.0, text="hello world")],
        ),
    )

    exit_code = main(
        [
            "transcribe",
            "https://www.youtube.com/@example/videos",
            "--limit",
            "1",
            "--database",
            str(database),
        ]
    )

    output = capsys.readouterr().out
    assert exit_code == 0
    assert "Extracted subtitles: video123 | Test Video | 1 segments" in output
    assert f"Stored 1 transcript(s) in {database}" in output
