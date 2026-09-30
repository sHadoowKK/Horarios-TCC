import json

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./school_schedule.db"

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
        # --------------------------------------------------------------
        # CONFIGURAÇÕES
        # --------------------------------------------------------------
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

        # Regras que não podem ser relaxadas pela interface.
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

        # O antigo padrão de 2 aulas seguidas do mesmo professor entrava
        # em conflito com grades reais que possuem blocos maiores.
        conn.execute(text(
            "UPDATE system_configs "
            "SET max_consec_teacher_mode = 'ignore' "
            "WHERE max_consec_teacher_mode = 'hard' "
            "AND max_consec_per_teacher = 2"
        ))

        # --------------------------------------------------------------
        # TURMAS E MATRIZES
        # --------------------------------------------------------------
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

        # Migra a lógica antiga "toda turma recebe todas as matérias do curso"
        # para uma lista explícita por turma, preservando carga e divisão.
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

        # O antigo tipo de turma "Tarde" passa a representar Integral.
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

        # --------------------------------------------------------------
        # DISPONIBILIDADE DE PROFESSORES
        # --------------------------------------------------------------
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
                    # A nova 6ª aula da manhã herda a disponibilidade
                    # da antiga última aula matutina.
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

        # --------------------------------------------------------------
        # GRADE SALVA: teacher_id agora pode ser nulo.
        # SQLite não altera NOT NULL diretamente, então a tabela antiga
        # precisa ser reconstruída uma vez.
        # --------------------------------------------------------------
        timetable_info = conn.execute(
            text("PRAGMA table_info(timetable)")
        ).fetchall()

        timetable_rebuilt = False

        if timetable_info:
            timetable_columns = {
                row[1]: row
                for row in timetable_info
            }

            teacher_column = timetable_columns.get("teacher_id")
            teacher_is_not_null = bool(
                teacher_column and teacher_column[3]
            )
            has_student_group = (
                "student_group" in timetable_columns
            )

            if teacher_is_not_null or not has_student_group:
                conn.execute(text(
                    "DROP TABLE IF EXISTS timetable_new"
                ))
                conn.execute(text(
                    """
                    CREATE TABLE timetable_new (
                        id INTEGER NOT NULL PRIMARY KEY,
                        classroom_id INTEGER NOT NULL,
                        subject_id INTEGER NOT NULL,
                        teacher_id INTEGER,
                        day INTEGER NOT NULL,
                        period INTEGER NOT NULL,
                        student_group VARCHAR NOT NULL DEFAULT 'Todos'
                    )
                    """
                ))

                student_group_expr = (
                    "student_group"
                    if has_student_group
                    else "'Todos'"
                )

                conn.execute(text(
                    f"""
                    INSERT INTO timetable_new (
                        id,
                        classroom_id,
                        subject_id,
                        teacher_id,
                        day,
                        period,
                        student_group
                    )
                    SELECT
                        id,
                        classroom_id,
                        subject_id,
                        teacher_id,
                        day,
                        period,
                        {student_group_expr}
                    FROM timetable
                    """
                ))

                conn.execute(text("DROP TABLE timetable"))
                conn.execute(text(
                    "ALTER TABLE timetable_new "
                    "RENAME TO timetable"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_timetable_classroom_id "
                    "ON timetable (classroom_id)"
                ))
                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS "
                    "ix_timetable_teacher_id "
                    "ON timetable (teacher_id)"
                ))

                timetable_rebuilt = True

        # Alterações estruturais tornam uma grade antiga ambígua.
        # Os cadastros permanecem preservados.
        if (
            subject_settings_added
            or old_afternoon_count
            or availability_changed
            or timetable_rebuilt
        ):
            conn.execute(text("DELETE FROM timetable"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
