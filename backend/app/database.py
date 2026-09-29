from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = "sqlite:///./school_schedule.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def ensure_config_columns():
    """Mantém bancos SQLite locais antigos compatíveis com novas preferências."""
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(system_configs)"))
        }

        if "avoid_first_period" not in columns:
            conn.execute(text(
                "ALTER TABLE system_configs "
                "ADD COLUMN avoid_first_period BOOLEAN DEFAULT 0"
            ))
            if "avoid_edges" in columns:
                conn.execute(text(
                    "UPDATE system_configs "
                    "SET avoid_first_period = avoid_edges"
                ))

        if "avoid_last_period" not in columns:
            conn.execute(text(
                "ALTER TABLE system_configs "
                "ADD COLUMN avoid_last_period BOOLEAN DEFAULT 0"
            ))
            if "avoid_edges" in columns:
                conn.execute(text(
                    "UPDATE system_configs "
                    "SET avoid_last_period = avoid_edges"
                ))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
