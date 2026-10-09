import json

from cryptarithm import progress


def test_record_challenge_attempt_saves_category_and_reason(tmp_path, monkeypatch):
    data_file = tmp_path / "progress.json"
    monkeypatch.setattr(progress, "DATA_FILE", data_file)

    progress.record_attempt(
        "SEND + MORE = MONEY",
        False,
        letter_count=8,
        difficulty="Easy",
        challenge=True,
        reason="Time expired.",
    )

    attempt = json.loads(data_file.read_text(encoding="utf-8"))[0]
    assert attempt["solved"] is False
    assert attempt["source"] == "challenge"
    assert attempt["reason"] == "Time expired."
