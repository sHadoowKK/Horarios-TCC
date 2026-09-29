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


def ensure_database_compatibility():
    """Atualiza automaticamente bancos locais antigos para a estrutura atual."""
    with engine.begin() as conn:
        # Preferências separadas de primeira e última aula.
        config_columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(system_configs)"))
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

        # O antigo tipo de turma "Tarde" passa a representar a jornada Integral.
        old_afternoon_count = conn.execute(
            text("SELECT COUNT(*) FROM classrooms WHERE shift = 'Tarde'")
        ).scalar() or 0

        if old_afternoon_count:
            conn.execute(text(
                "UPDATE classrooms SET shift = 'Integral' "
                "WHERE shift = 'Tarde'"
            ))

        # Disponibilidade antiga tinha 15 períodos:
        # 5 manhã + 5 tarde + 5 noite.
        # Agora existem 16 porque a turma somente matutina possui 11:40-12:30.
        availability_changed = False
        teacher_rows = conn.execute(
            text("SELECT id, availability FROM teachers")
        ).fetchall()

        for teacher_id, raw_availability in teacher_rows:
            if not raw_availability:
                continue

            try:
                availability = (
                    json.loads(raw_availability)
                    if isinstance(raw_availability, str)
                    else raw_availability
                )
            except (TypeError, json.JSONDecodeError):
                continue

            teacher_changed = False

            for day, values in availability.items():
                if isinstance(values, list) and len(values) == 15:
                    # A nova 6ª aula da manhã herda a disponibilidade da
                    # antiga última aula matutina, evitando inventar um valor.
                    availability[day] = (
                        values[:5] + [values[4]] + values[5:]
                    )
                    teacher_changed = True

            if teacher_changed:
                conn.execute(
                    text(
                        "UPDATE teachers SET availability = :availability "
                        "WHERE id = :teacher_id"
                    ),
                    {
                        "availability": json.dumps(
                            availability, ensure_ascii=False
                        ),
                        "teacher_id": teacher_id,
                    },
                )
                availability_changed = True

        # Grades antigas usam índices de período diferentes.
        # É mais seguro apagá-las e gerar uma nova do que reinterpretá-las errado.
        if old_afternoon_count or availability_changed:
            conn.execute(text("DELETE FROM timetable"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
