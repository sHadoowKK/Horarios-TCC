"""Smoke test of full demonstration timetable generation.

Run from backend after seed_realista.py:
    python validate_demo_generation.py
"""

import os
from pathlib import Path

DEMO_DATABASE = Path(__file__).resolve().with_name("school_schedule_demo.db")
os.environ["ANATINUS_DATABASE_URL"] = f"sqlite:///{DEMO_DATABASE.as_posix()}"

from fastapi import HTTPException  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.main import generate_timetable  # noqa: E402


def main() -> None:
    db = SessionLocal()
    try:
        try:
            result = generate_timetable(db=db)
        except HTTPException as exc:
            raise SystemExit(
                f"Geração demo falhou (HTTP {exc.status_code}): {exc.detail}"
            ) from exc

        schedule = result.get("schedule", [])
        if result.get("status") != "success" or not schedule:
            raise SystemExit(
                f"Geração demo não produziu uma grade: {result!r}"
            )

        print("Grade demo gerada com sucesso.")
        print(f"Aulas alocadas: {len(schedule)}")
        print(f"Aulas sem professor: {result.get('unstaffed_lessons', 0)}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
