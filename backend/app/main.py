import sys
from pathlib import Path

from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from . import models, schemas
from .database import engine, ensure_database_compatibility, get_db
from .optimizer import JOURNEY_PERIODS, generate_schedule

models.Base.metadata.create_all(bind=engine)
ensure_database_compatibility()


def _frontend_dist_directory() -> Path:
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
        return bundle_root / "frontend_dist"

    # backend/app/main.py -> backend/app -> backend -> raiz do repositório.
    return Path(__file__).resolve().parents[2] / "frontend" / "dist"


FRONTEND_DIST = _frontend_dist_directory()

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
    index_file = FRONTEND_DIST / "index.html"
    if index_file.is_file():
        return FileResponse(index_file)
    return {"message": "API do Anatinus"}


@app.get("/health", include_in_schema=False)
def health():
    return {"app": "Anatinus", "status": "ok"}


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


@app.put("/courses/{course_id}", response_model=schemas.Course)
def update_course(
    course_id: int,
    data: schemas.CourseCreate,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Course)
        .filter(models.Course.id == course_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Curso não encontrado")

    item.name = data.name
    db.commit()
    db.refresh(item)
    return item


@app.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Course)
        .filter(models.Course.id == course_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Curso não encontrado")

    classroom_count = (
        db.query(models.Classroom)
        .filter(models.Classroom.course_id == course_id)
        .count()
    )

    if classroom_count:
        raise HTTPException(
            400,
            "Este curso ainda possui turmas. "
            "Remova ou altere essas turmas antes de excluir o curso.",
        )

    # Retira a associação do curso nas disciplinas sem apagá-las.
    for subject in db.query(models.Subject).all():
        course_ids = list(subject.course_ids or [])
        if course_id in course_ids:
            subject.course_ids = [
                current_id
                for current_id in course_ids
                if current_id != course_id
            ]

    db.delete(item)
    db.commit()

    return {"detail": "Curso removido com sucesso"}


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

    values = data.model_dump()

    valid_subject_ids = {
        subject.id
        for subject in db.query(models.Subject).all()
        if values["course_id"] in (subject.course_ids or [])
    }

    values["subject_settings"] = [
        {
            **setting,
            "split": (
                bool(setting.get("split"))
                if values["has_groups"]
                else False
            ),
        }
        for setting in values.get("subject_settings", [])
        if setting.get("subject_id") in valid_subject_ids
    ]

    values["split_subject_ids"] = [
        subject_id
        for subject_id in values.get("split_subject_ids", [])
        if subject_id in valid_subject_ids
    ]

    selected_settings = {
        setting["subject_id"]: setting
        for setting in values["subject_settings"]
    }
    sequences = []
    for pair in values.get("preferred_subject_sequences", []) or []:
        if len(pair) != 2:
            continue
        first_id, second_id = pair
        if (
            first_id == second_id
            or first_id not in selected_settings
            or second_id not in selected_settings
        ):
            continue
        if bool(selected_settings[first_id].get("split")) != bool(
            selected_settings[second_id].get("split")
        ):
            continue
        normalized_pair = [int(first_id), int(second_id)]
        if normalized_pair not in sequences:
            sequences.append(normalized_pair)
    values["preferred_subject_sequences"] = sequences

    for key, value in values.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return item


@app.delete("/classrooms/{classroom_id}")
def delete_classroom(
    classroom_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Classroom)
        .filter(models.Classroom.id == classroom_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Turma não encontrada")

    db.query(models.TimetableItem).filter(
        models.TimetableItem.classroom_id == classroom_id
    ).delete(synchronize_session=False)

    db.delete(item)
    db.commit()

    return {"detail": "Turma removida com sucesso"}


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

    values = data.model_dump()

    for key, value in values.items():
        setattr(item, key, value)

    valid_course_ids = set(values.get("course_ids", []))

    for classroom in db.query(models.Classroom).all():
        if classroom.course_id in valid_course_ids:
            continue

        classroom.subject_settings = [
            setting
            for setting in (classroom.subject_settings or [])
            if setting.get("subject_id") != subject_id
        ]
        classroom.split_subject_ids = [
            current_id
            for current_id in (classroom.split_subject_ids or [])
            if current_id != subject_id
        ]

    db.commit()
    db.refresh(item)
    return item


@app.delete("/subjects/{subject_id}")
def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
):
    item = (
        db.query(models.Subject)
        .filter(models.Subject.id == subject_id)
        .first()
    )

    if not item:
        raise HTTPException(404, "Disciplina não encontrada")

    for classroom in db.query(models.Classroom).all():
        classroom.subject_settings = [
            setting
            for setting in (classroom.subject_settings or [])
            if setting.get("subject_id") != subject_id
        ]
        classroom.split_subject_ids = [
            current_id
            for current_id in (classroom.split_subject_ids or [])
            if current_id != subject_id
        ]

    for teacher in db.query(models.Teacher).all():
        teacher.allowed_subjects = [
            current_id
            for current_id in (teacher.allowed_subjects or [])
            if current_id != subject_id
        ]

    db.query(models.TimetableItem).filter(
        models.TimetableItem.subject_id == subject_id
    ).delete(synchronize_session=False)

    db.delete(item)
    db.commit()

    return {"detail": "Disciplina removida com sucesso"}


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

    # Preserva a última grade como referência histórica, mas as aulas
    # do professor removido passam a aparecer como "Sem professor".
    db.query(models.TimetableItem).filter(
        models.TimetableItem.teacher_id == teacher_id
    ).update(
        {models.TimetableItem.teacher_id: None},
        synchronize_session=False,
    )

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
def generate_timetable(
    db: Session = Depends(get_db),
    payload: schemas.TimetableGenerationRequest | None = Body(default=None),
):
    payload = payload or schemas.TimetableGenerationRequest()
    scope = payload.scope
    target_classroom_id = payload.classroom_id
    target_subject_id = payload.subject_id

    classroom_rows = db.query(models.Classroom).all()
    subject_rows = db.query(models.Subject).all()
    teacher_rows = db.query(models.Teacher).all()
    saved_rows = db.query(models.TimetableItem).all()

    if scope != "all":
        if not saved_rows:
            raise HTTPException(
                400,
                "Gere a grade da escola inteira antes de usar uma regeneração parcial.",
            )
        if target_classroom_id is None:
            raise HTTPException(400, "Selecione a turma que deseja regenerar.")

        target_classroom = next(
            (row for row in classroom_rows if row.id == target_classroom_id),
            None,
        )
        if target_classroom is None:
            raise HTTPException(404, "A turma selecionada não existe.")

        if scope == "subject":
            if target_subject_id is None:
                raise HTTPException(400, "Selecione a matéria que deseja regenerar.")
            if not any(
                int(setting.get("subject_id", -1)) == target_subject_id
                for setting in (target_classroom.subject_settings or [])
            ):
                raise HTTPException(
                    400,
                    "A matéria selecionada não está configurada nessa turma.",
                )
        elif scope != "classroom":
            raise HTTPException(400, "Escopo de regeneração inválido.")
    else:
        # Ignora IDs de escopo antigos se o usuário voltar para Escola inteira.
        target_classroom_id = None
        target_subject_id = None

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
            "preferred_subject_sequences": (
                classroom.preferred_subject_sequences or []
            ),
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

    # --------------------------------------------------------------
    # PRÉ-VALIDAÇÃO
    # --------------------------------------------------------------
    # Alguns cenários podem ser identificados como impossíveis sem
    # construir o modelo CP-SAT. Isso economiza tempo e produz mensagens
    # mais úteis para quem está montando a grade.
    subject_by_id = {
        subject["id"]: subject
        for subject in subjects
    }

    preflight_errors = []

    for classroom in classrooms:
        weekly_capacity = (
            len(
                JOURNEY_PERIODS.get(
                    classroom.get("shift", "Manhã"),
                    JOURNEY_PERIODS["Manhã"],
                )
            )
            * 5
        )

        settings = classroom.get(
            "subject_settings",
            [],
        ) or []

        has_groups = bool(classroom.get("has_groups"))
        workload_by_group = {"A": 0, "B": 0}
        high_workload_by_group = {"A": 0, "B": 0}

        for setting in settings:
            base = int(setting.get("workload", 0) or 0)
            split = has_groups and bool(setting.get("split"))
            raw_joint = setting.get("joint_workload")

            if split:
                joint = int(raw_joint or 0)
                raw_a = setting.get("workload_a")
                raw_b = setting.get("workload_b")
                workload_a = (
                    base if raw_a is None and joint == 0
                    else int(raw_a or 0)
                )
                workload_b = (
                    base if raw_b is None and joint == 0
                    else int(raw_b or 0)
                )
                effective_a = joint + workload_a
                effective_b = joint + workload_b
            else:
                joint = base if raw_joint is None else int(raw_joint)
                effective_a = joint
                effective_b = joint

            workload_by_group["A"] += effective_a
            workload_by_group["B"] += effective_b

            subject = subject_by_id.get(setting.get("subject_id"))
            if subject and subject.get("complexity") == "Alta":
                high_workload_by_group["A"] += effective_a
                high_workload_by_group["B"] += effective_b

        max_group = max(workload_by_group, key=workload_by_group.get)
        total_workload = workload_by_group[max_group]
        if total_workload > weekly_capacity:
            workload_detail = (
                f"A={workload_by_group['A']}, B={workload_by_group['B']}"
                if has_groups
                else str(total_workload)
            )
            preflight_errors.append(
                f"{classroom['name']}: {workload_detail} aulas semanais "
                f"configuradas; há apenas {weekly_capacity} períodos "
                f"disponíveis por grupo."
            )

        high_capacity = int(config.max_high_complexity_per_day) * 5
        max_high_group = max(high_workload_by_group, key=high_workload_by_group.get)
        high_workload = high_workload_by_group[max_high_group]
        if high_workload > high_capacity:
            high_detail = (
                f"A={high_workload_by_group['A']}, B={high_workload_by_group['B']}"
                if has_groups
                else str(high_workload)
            )
            preflight_errors.append(
                f"{classroom['name']}: aulas de alta complexidade {high_detail}, "
                f"mas o limite atual permite no máximo {high_capacity} por semana."
            )

    if preflight_errors:
        raise HTTPException(
            400,
            "A configuração possui impossibilidades antes "
            "da geração: "
            + " | ".join(preflight_errors),
        )

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

    saved_schedule = [
        {
            "classroom_id": row.classroom_id,
            "subject_id": row.subject_id,
            "teacher_id": row.teacher_id,
            "day": row.day,
            "period": row.period,
            "student_group": row.student_group,
        }
        for row in saved_rows
    ]

    fixed_schedule = saved_schedule if scope != "all" else None
    result = generate_schedule(
        classrooms,
        subjects,
        teachers,
        sys_config,
        fixed_schedule=fixed_schedule,
        mutable_classroom_id=target_classroom_id,
        mutable_subject_id=target_subject_id if scope == "subject" else None,
    )

    if result["status"] == "infeasible":
        raise HTTPException(400, result["message"])

    if result["status"] == "timeout":
        raise HTTPException(504, result["message"])

    if result["status"] == "error":
        raise HTTPException(500, result["message"])

    if scope == "all":
        result["generation_scope"] = "all"
        result["preserved_lessons"] = 0
        result["message"] = "Grade da escola inteira gerada."
    else:
        preserved = [
            row for row in saved_schedule
            if not (
                row["classroom_id"] == target_classroom_id
                and (
                    scope == "classroom"
                    or row["subject_id"] == target_subject_id
                )
            )
        ]
        result["generation_scope"] = scope
        result["preserved_lessons"] = len(preserved)
        result["message"] = (
            "Grade da turma regenerada; os demais horários foram preservados."
            if scope == "classroom"
            else "Grade da matéria regenerada; os demais horários foram preservados."
        )

    # A geração e o salvamento passam a fazer parte da mesma operação.
    # Assim a interface nunca precisa depender de uma segunda requisição
    # para persistir a grade recém-calculada.
    db.query(models.TimetableItem).delete()

    rows = [
        models.TimetableItem(**item)
        for item in result["schedule"]
    ]

    db.add_all(rows)
    db.commit()

    return result


# ----------------------------------------------------------------------
# FRONTEND DE PRODUÇÃO
# ----------------------------------------------------------------------
@app.get("/{frontend_path:path}", include_in_schema=False)
def serve_frontend(frontend_path: str):
    index_file = FRONTEND_DIST / "index.html"

    if not index_file.is_file():
        raise HTTPException(404, "Rota não encontrada")

    frontend_root = FRONTEND_DIST.resolve()
    requested_file = (frontend_root / frontend_path).resolve()

    # Não permite que um caminho solicitado leia arquivos fora da pasta pública.
    try:
        requested_file.relative_to(frontend_root)
    except ValueError:
        return FileResponse(index_file)

    if requested_file.is_file():
        return FileResponse(requested_file)

    # Fallback para rotas do React Router, como /professores e /turmas.
    return FileResponse(index_file)
