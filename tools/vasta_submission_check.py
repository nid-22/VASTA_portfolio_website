"""Notify OpenClaw when the VAST website receives new form submissions."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


MONITOR_URL = os.environ.get(
    "VASTA_SUBMISSION_MONITOR_URL",
    "https://vastarchitects.in/internal/submissions/",
)
TOKEN_FILE = Path(
    os.environ.get(
        "VASTA_SUBMISSION_TOKEN_FILE",
        Path.home() / ".openclaw" / "secrets" / "vasta-submission-monitor-token",
    )
)
STATE_FILE = Path(
    os.environ.get(
        "VASTA_SUBMISSION_STATE_FILE",
        Path.home() / ".openclaw" / "state" / "vasta-submission-monitor.json",
    )
)
MAX_RESPONSE_BYTES = 64 * 1024


def load_state() -> dict[str, int] | None:
    if not STATE_FILE.exists():
        return None
    payload = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {
        "contact": max(0, int(payload.get("contact", 0))),
        "career": max(0, int(payload.get("career", 0))),
    }


def save_state(state: dict[str, int]) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        dir=STATE_FILE.parent,
        prefix=f"{STATE_FILE.name}.",
        suffix=".tmp",
        text=True,
    )
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as temporary_file:
            json.dump(state, temporary_file, separators=(",", ":"))
            temporary_file.write("\n")
        os.replace(temporary_name, STATE_FILE)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def fetch_counts(token: str, state: dict[str, int]) -> dict[str, dict[str, int]]:
    query = urlencode({
        "after_contact": state["contact"],
        "after_career": state["career"],
    })
    request = Request(
        f"{MONITOR_URL}?{query}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "VASTA-OpenClaw-Submission-Monitor/1.0",
        },
    )
    with urlopen(request, timeout=15) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
        if len(body) > MAX_RESPONSE_BYTES:
            raise ValueError("Monitor response was unexpectedly large.")
    payload = json.loads(body.decode("utf-8"))
    result = {}
    for submission_type in ("contact", "career"):
        values = payload[submission_type]
        result[submission_type] = {
            "new_count": max(0, int(values["new_count"])),
            "latest_id": max(0, int(values["latest_id"])),
        }
    return result


def plural(count: int, singular: str, plural_form: str) -> str:
    return f"{count} {singular if count == 1 else plural_form}"


def main() -> int:
    try:
        token = TOKEN_FILE.read_text(encoding="utf-8").strip()
        if not token:
            raise ValueError("The submission monitor token file is empty.")

        previous_state = load_state()
        cursor = previous_state or {"contact": 0, "career": 0}
        counts = fetch_counts(token, cursor)
        next_state = {
            "contact": counts["contact"]["latest_id"],
            "career": counts["career"]["latest_id"],
        }
        save_state(next_state)

        # The first run establishes a baseline so old and test records do not alert.
        if previous_state is None:
            print("NO_REPLY")
            return 0

        new_contacts = counts["contact"]["new_count"]
        new_careers = counts["career"]["new_count"]
        if not new_contacts and not new_careers:
            print("NO_REPLY")
            return 0

        lines = ["VAST WEBSITE — NEW SUBMISSION"]
        if new_contacts:
            lines.append(plural(new_contacts, "new enquiry", "new enquiries"))
            lines.append("https://vastarchitects.in/admin/projects/contactsubmission/")
        if new_careers:
            lines.append(plural(new_careers, "new career application", "new career applications"))
            lines.append("https://vastarchitects.in/admin/projects/careersubmission/")
        print("\n".join(lines))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError, HTTPError, URLError) as error:
        print(f"VAST submission monitor failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
