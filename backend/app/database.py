import json
import os
import shutil
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker


def _database_url() -> str:
    """Mantém o banco no diretório de trabalho em desenvolvimento e usa AppData no EXE."""
    explicit_url = os.environ.get("ANATINUS_DATABASE_URL")
    if explicit_url:
        return explicit_url

    data_directory = os.environ.get("ANATINUS_DATA_DIR")
    if data_directory:
        database_directory = Path(data_directory).expanduser()
        database_directory.mkdir(parents=True, exist_ok=True)
        database_path = database_directory / "school_schedule.db"
        return f"sqlite:///{database_path.as_posix()}"

    if getattr(sys, "frozen", False):
        local_app_data = os.environ.get("LOCALAPPDATA")
        base_directory = (
            Path(local_app_data)
            if local_app_data
            else Path.home() / "AppData" / "Local"
        )
        database_directory = base_directory / "Anatinus"
        database_directory.mkdir(parents=True, exist_ok=True)
        database_path = database_directory / "school_schedule.db"

        if not database_path.exists():
            bundle_root = Path(
                getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent)
            )
            demo_database = bundle_root / "demo_seed" / "school_schedule_demo.db"
            if demo_database.is_file():
                shutil.copy2(demo_database, database_path)

        return f"sqlite:///{database_path.as_posix()}"

    return "sqlite:///./school_schedule.db"


DATABASE_URL = _database_url()

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def _load_json(raw, fallback):
    if raw is None:
        return fallback

    if isinstance(raw, (list, dict)):
        return raw

    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return fallback


def ensure_database_compatibility():
    """Atualiza automaticamente bancos locais antigos para a estrutura atual."""
    with engine.begin() as conn:
        # CONFIGURAÇÕES
        config_columns = {
            row[1]
            for row in conn.execute(
                text("PRAGMA table_info(system_configs)")
            )
        }

        if "avoid_first_period" not in config_columns:
            conn.execute(text(
                "ALTER TABLE system_configs "
                "ADD COLUMN avoid_first_period BOOLEAN DEFAULT 0"
            ))
            if "avoid_edges" in config_columns:
                conn.execute(text(
                    "UPDATE system_configs "
                    "SET avoid_first_period = avoid_edges"
                ))

        if "avoid_last_period" not in config_columns:
            conn.execute(text(
                "ALTER TABLE system_configs "
                "ADD COLUMN avoid_last_period BOOLEAN DEFAULT 0"
            ))
            if "avoid_edges" in config_columns:
                conn.execute(text(
                    "UPDATE system_configs "
                    "SET avoid_last_period = avoid_edges"
                ))

        conn.execute(text(
            "UPDATE system_configs "
            "SET max_classes_per_day = 9 "
            "WHERE max_classes_per_day > 9"
        ))
        conn.execute(text(
            "UPDATE system_configs "
            "SET max_consecutive_classes = 6"
        ))
        conn.execute(text(
            "UPDATE system_configs "
            "SET student_gaps_hard = 1"
        ))

        conn.execute(text(
            "UPDATE system_configs "
            "SET max_consec_teacher_mode = 'ignore' "
            "WHERE max_consec_teacher_mode = 'hard' "
            "AND max_consec_per_teacher = 2"
        ))

        # TURMAS E MATRIZES
        classroom_columns = {
            row[1]
            for row in conn.execute(
                text("PRAGMA table_info(classrooms)")
            )
        }

        if "has_groups" not in classroom_columns:
            conn.execute(text(
                "ALTER TABLE classrooms "
                "ADD COLUMN has_groups BOOLEAN DEFAULT 0"
            ))

        if "split_subject_ids" not in classroom_columns:
            conn.execute(text(
                "ALTER TABLE classrooms "
                "ADD COLUMN split_subject_ids JSON DEFAULT '[]'"
            ))

        subject_settings_added = False
        if "subject_settings" not in classroom_columns:
            conn.execute(text(
                "ALTER TABLE classrooms "
                "ADD COLUMN subject_settings JSON DEFAULT '[]'"
            ))
            subject_settings_added = True

        if "preferred_subject_sequences" not in classroom_columns:
            conn.execute(text(
                "ALTER TABLE classrooms "
                "ADD COLUMN preferred_subject_sequences JSON DEFAULT '[]'"
            ))

        if subject_settings_added:
            subject_rows = conn.execute(text(
                "SELECT id, workload, course_ids FROM subjects"
            )).fetchall()

            parsed_subjects = []
            for subject_id, workload, raw_course_ids in subject_rows:
                course_ids = _load_json(raw_course_ids, [])
                parsed_subjects.append(
                    (subject_id, workload, course_ids)
                )

            classroom_rows = conn.execute(text(
                "SELECT id, course_id, has_groups, split_subject_ids "
                "FROM classrooms"
            )).fetchall()

            for (
                classroom_id,
                course_id,
                has_groups,
                raw_split_subject_ids,
            ) in classroom_rows:
                split_subject_ids = set(
                    _load_json(raw_split_subject_ids, [])
                )

                settings = []
                for subject_id, workload, course_ids in parsed_subjects:
                    if course_id not in course_ids:
                        continue

                    settings.append({
                        "subject_id": subject_id,
                        "workload": workload,
                        "split": bool(
                            has_groups
                            and subject_id in split_subject_ids
                        ),
                    })

                conn.execute(
                    text(
                        "UPDATE classrooms "
                        "SET subject_settings = :settings "
                        "WHERE id = :classroom_id"
                    ),
                    {
                        "settings": json.dumps(
                            settings,
                            ensure_ascii=False,
                        ),
                        "classroom_id": classroom_id,
                    },
                )

        old_afternoon_count = conn.execute(
            text(
                "SELECT COUNT(*) FROM classrooms "
                "WHERE shift = 'Tarde'"
            )
        ).scalar() or 0

        if old_afternoon_count:
            conn.execute(text(
                "UPDATE classrooms SET shift = 'Integral' "
                "WHERE shift = 'Tarde'"
            ))

        # DISPONIBILIDADE DE PROFESSORES
        availability_changed = False
        teacher_rows = conn.execute(
            text("SELECT id, availability FROM teachers")
        ).fetchall()

        for teacher_id, raw_availability in teacher_rows:
            availability = _load_json(raw_availability, None)
            if not isinstance(availability, dict):
                continue

            teacher_changed = False

            for day, values in availability.items():
                if isinstance(values, list) and len(values) == 15:
                    availability[day] = (
                        values[:5] + [values[4]] + values[5:]
                    )
                    teacher_changed = True

            if teacher_changed:
                conn.execute(
                    text(
                        "UPDATE teachers "
                        "SET availability = :availability "
                        "WHERE id = :teacher_id"
                    ),
                    {
                        "availability": json.dumps(
                            availability,
                            ensure_ascii=False,
                        ),
                        "teacher_id": teacher_id,
                    },
                )
                availability_changed = True

        # GRADE SALVA: garante a presença da coluna is_manual
        timetable_info = conn.execute(
            text("PRAGMA table_info(timetable)")
        ).fetchall()

        if timetable_info:
            timetable_columns = {row[1] for row in timetable_info}
            if "is_manual" not in timetable_columns:
                conn.execute(text(
                    "ALTER TABLE timetable "
                    "ADD COLUMN is_manual BOOLEAN DEFAULT 0"
                ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()