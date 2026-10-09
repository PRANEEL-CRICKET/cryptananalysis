import json
from datetime import datetime
from pathlib import Path


DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "progress.json"


def load_progress():
    """Read saved practice attempts, or return an empty list."""
    if not DATA_FILE.exists():
        return []

    try:
        data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        return []


def record_attempt(
    equation,
    solved,
    letter_count=0,
    difficulty="Unknown",
    *,
    challenge=False,
    reason="",
):
    """Save one practice result or timed challenge outcome."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    history = load_progress()
    history.append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "equation": equation,
            "solved": bool(solved),
            "letter_count": letter_count,
            "difficulty": difficulty,
            "source": "challenge" if challenge else "practice",
            "reason": reason,
        }
    )

    DATA_FILE.write_text(
        json.dumps(history, indent=2),
        encoding="utf-8",
    )


def suggested_difficulty():
    """Suggest a level based on the five most recent practice results."""
    recent = load_progress()[-5:]

    if len(recent) < 3:
        return "Easy"

    success_rate = sum(
        bool(attempt.get("solved", False))
        for attempt in recent
    ) / len(recent)

    if success_rate >= 0.8:
        return "Hard"
    if success_rate >= 0.5:
        return "Medium"
    return "Easy"