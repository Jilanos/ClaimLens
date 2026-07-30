from threading import Thread
from urllib.request import urlopen

from claimlens import db
from claimlens.api_keys import rotate_stored_api_keys, save_supadata_api_key, save_user_api_key
from claimlens.config import load_config
from claimlens.secrets import SecretKeyring, decrypt_secret
from claimlens.web import build_web_server, resolve_request_ip


def test_forwarded_ip_is_ignored_without_a_trusted_proxy():
    assert resolve_request_ip("10.0.0.9", "203.0.113.4", ()) == "10.0.0.9"
    assert resolve_request_ip("10.0.0.9", "203.0.113.4", ("10.0.0.9",)) == "203.0.113.4"


def test_http_server_health_and_guest_cookie(tmp_path):
    config = load_config(
        env={
            "CLAIMLENS_DB": str(tmp_path / "claimlens.sqlite3"),
            "CLAIMLENS_OUTPUTS": str(tmp_path / "outputs"),
        }
    )
    server = build_web_server(config, host="127.0.0.1", port=0)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{server.server_port}/health") as response:
            assert response.read() == b"ok\n"
        with urlopen(f"http://127.0.0.1:{server.server_port}/") as response:
            assert "claimlens_guest=" in response.headers["Set-Cookie"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_job_capacity_is_atomic_and_does_not_create_an_extra_job(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    run_id = db.create_pipeline_run(
        database, video_id="abc123XYZ_", source_url="https://example.test"
    )
    assert db.create_job(database, run_id=run_id, action="captions", max_queued_jobs=1)
    try:
        db.create_job(database, run_id=run_id, action="analysis", max_queued_jobs=1)
    except db.JobQueueFullError:
        pass
    else:
        raise AssertionError("Expected queue saturation")
    assert db.job_metrics(database)["queued"] == 1


def test_rotation_migrates_saved_keys_to_the_active_key_id(tmp_path):
    database = tmp_path / "claimlens.sqlite3"
    db.init_db(database)
    user_id = db.create_user(database, email="user@example.test", password_hash="hash")
    save_user_api_key(
        database, user_id=user_id, provider="openai", value="sk-test", deployment_secret="old"
    )
    save_supadata_api_key(
        database,
        user_id=user_id,
        label="main",
        value="supa-test",
        priority=1,
        deployment_secret="old",
    )
    keyring = SecretKeyring("new-2026", "new", {"primary": "old"})
    assert rotate_stored_api_keys(database, keyring=keyring) == 2
    user_key = db.get_user_api_key(database, user_id=user_id, provider="openai")
    assert user_key["encrypted_value"].startswith("v3:new-2026:")
    assert decrypt_secret(user_key["encrypted_value"], keyring) == "sk-test"
