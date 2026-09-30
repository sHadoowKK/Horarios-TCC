from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, ensure_database_compatibility, get_db
from .optimizer import generate_schedule

models.Base.metadata.create_all(bind=engine)
ensure_database_compatibility()

app = FastAPI(title="Anatinus API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_or_create_config(db: Session) -> models.SystemConfig:
    config = db.query(models.SystemConfig).first()

    if config is None:
        config = models.SystemConfig()
        db.add(config)
        db.commit()
        db.refresh(config)

    # Regras fixas do sistema.
    changed = False

    if config.max_classes_per_day > 9:
        config.max_classes_per_day = 9
        changed = True

    if config.max_consecutive_classes != 6:
        config.max_consecutive_classes = 6
        changed = True

    if not config.student_gaps_hard:
        config.student_gaps_hard = True
        changed = True

    if changed:
        db.commit()
        db.refresh(config)

    return config


@app.get("/")
def root():
    return {"message": "API do Anatinus"}


# ----------------------------------------------------------------------
# CURSOS
# ----------------------------------------------------------------------
@app.post("/courses/", response_model=schemas.Course)
def create_course(
    course: schemas.CourseCreate,
    db: Session = Depends(get_db),
):
    item = models.Course(**course.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/courses/", response_model=list[schemas.Course])
def read_courses(db: Session = Depends(get_db)):
    return db.query(models.Course).all()


# ----------------------------------------------------------------------
# TURMAS
# ----------------------------------------------------------------------
@app.post("/classrooms/", response_model=schemas.Classroom)
def create_classroom(
    data: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
):
    item = models.Classroom(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/classrooms/", response_model=list[schemas.Classroom])
def read_classrooms(db: Session = Depends(get_db)):
    return db.query(models.Classroom).all()


@app.put("/classrooms/{classroom_id}", response_model=schemas.Classroom)
def update_classroom(
    classroom_id: int,
    data: schemas.ClassroomCreate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Classroom)
        .filter(models.Classroom.id == classroom_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Turma não encontrada")

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


# ----------------------------------------------------------------------
# DISCIPLINAS
# ----------------------------------------------------------------------
@app.post("/subjects/", response_model=schemas.Subject)
def create_subject(
    data: schemas.SubjectCreate,
    db: Session = Depends(get_db),
):
    item = models.Subject(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/subjects/", response_model=list[schemas.Subject])
def read_subjects(db: Session = Depends(get_db)):
    return db.query(models.Subject).all()


@app.put("/subjects/{subject_id}", response_model=schemas.Subject)
def update_subject(
    subject_id: int,
    data: schemas.SubjectCreate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Subject)
        .filter(models.Subject.id == subject_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Disciplina não encontrada")

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


# ----------------------------------------------------------------------
# PROFESSORES
# ----------------------------------------------------------------------
@app.post("/teachers/", response_model=schemas.Teacher)
def create_teacher(
    data: schemas.TeacherCreate,
    db: Session = Depends(get_db),
):
    item = models.Teacher(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@app.get("/teachers/", response_model=list[schemas.Teacher])
def read_teachers(db: Session = Depends(get_db)):
    return db.query(models.Teacher).all()


@app.put("/teachers/{teacher_id}", response_model=schemas.Teacher)
def update_teacher(
    teacher_id: int,
    data: schemas.TeacherCreate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Teacher)
        .filter(models.Teacher.id == teacher_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Professor não encontrado")

    for key, value in data.model_dump().items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@app.delete("/teachers/{teacher_id}")
def delete_teacher(
    teacher_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Teacher)
        .filter(models.Teacher.id == teacher_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Professor não encontrado")

    db.delete(item)
    db.commit()

    return {"detail": "Professor removido com sucesso"}


# ----------------------------------------------------------------------
# PERÍODOS
# ----------------------------------------------------------------------
@app.get("/periods/", response_model=list[schemas.Period])
def read_periods(db: Session = Depends(get_db)):
    return db.query(models.Period).all()


@app.post("/periods/", response_model=schemas.Period)
def create_period(
    data: schemas.PeriodCreate,
    db: Session = Depends(get_db),
):
    item = models.Period(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


# ----------------------------------------------------------------------
# CONFIGURAÇÕES
# ----------------------------------------------------------------------
@app.get("/config/", response_model=schemas.SystemConfig)
def read_config(db: Session = Depends(get_db)):
    return get_or_create_config(db)


@app.put("/config/", response_model=schemas.SystemConfig)
def update_config(
    data: schemas.SystemConfigUpdate,
    db: Session = Depends(get_db),
):
    config = get_or_create_config(db)
    values = data.model_dump()

    # Regras obrigatórias: podem ser endurecidas, mas não relaxadas.
    values["max_classes_per_day"] = min(
        values["max_classes_per_day"],
        9,
    )
    values["max_consecutive_classes"] = 6
    values["student_gaps_hard"] = True

    for key, value in values.items():
        setattr(config, key, value)

    db.commit()
    db.refresh(config)
    return config


# ----------------------------------------------------------------------
# GRADE SALVA
# ----------------------------------------------------------------------
@app.get("/timetable/", response_model=list[schemas.TimetableItem])
def read_timetable(db: Session = Depends(get_db)):
    return db.query(models.TimetableItem).all()


@app.post("/timetable/", response_model=list[schemas.TimetableItem])
def save_timetable(
    items: list[schemas.TimetableItemCreate],
    db: Session = Depends(get_db),
):
    db.query(models.TimetableItem).delete()

    rows = [
        models.TimetableItem(**item.model_dump())
        for item in items
    ]

    db.add_all(rows)
    db.commit()

    for row in rows:
        db.refresh(row)

    return rows


# ----------------------------------------------------------------------
# GERAÇÃO
# ----------------------------------------------------------------------
@app.post("/generate/")
def generate_timetable(db: Session = Depends(get_db)):
    classroom_rows = db.query(models.Classroom).all()
    subject_rows = db.query(models.Subject).all()
    teacher_rows = db.query(models.Teacher).all()

    if not classroom_rows:
        raise HTTPException(
            400,
            "Cadastre pelo menos uma turma antes de gerar a grade.",
        )

    if not subject_rows:
        raise HTTPException(
            400,
            "Cadastre pelo menos uma disciplina antes de gerar a grade.",
        )

    missing_matrix = [
        classroom.name
        for classroom in classroom_rows
        if not (classroom.subject_settings or [])
    ]

    if missing_matrix:
        names = ", ".join(missing_matrix)
        raise HTTPException(
            400,
            "Escolha as matérias presentes nas seguintes turmas "
            f"antes de gerar: {names}.",
        )

    classrooms = [
        {
            "id": classroom.id,
            "name": classroom.name,
            "course_id": classroom.course_id,
            "shift": classroom.shift,
            "has_groups": classroom.has_groups,
            "subject_settings": classroom.subject_settings or [],
        }
        for classroom in classroom_rows
    ]

    subjects = [
        {
            "id": subject.id,
            "name": subject.name,
            "course_ids": subject.course_ids or [],
            "workload": subject.workload,
            "complexity": subject.complexity,
            "category": subject.category,
        }
        for subject in subject_rows
    ]

    teachers = [
        {
            "id": teacher.id,
            "name": teacher.name,
            "allowed_subjects": teacher.allowed_subjects or [],
            "availability": teacher.availability or {},
            "score": teacher.score,
        }
        for teacher in teacher_rows
    ]

    config = get_or_create_config(db)

    sys_config = {
        "max_classes_per_day": min(
            config.max_classes_per_day,
            9,
        ),
        "max_high_complexity_per_day":
            config.max_high_complexity_per_day,
        "teacher_gaps_hard": config.teacher_gaps_hard,
        "min_classes_students": config.min_classes_students,
        "min_classes_teachers": config.min_classes_teachers,
        "avoid_first_period": config.avoid_first_period,
        "avoid_last_period": config.avoid_last_period,
        "avoid_friday": config.avoid_friday,
        "max_consec_per_teacher":
            config.max_consec_per_teacher,
        "max_consec_teacher_mode":
            config.max_consec_teacher_mode,
    }

    result = generate_schedule(
        classrooms,
        subjects,
        teachers,
        sys_config,
    )

    if result["status"] == "infeasible":
        raise HTTPException(400, result["message"])

    return result
