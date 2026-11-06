"""Cria a base fictícia do Anatinus usada na apresentação.

Executar a partir da pasta backend:
    python seed_apresentacao.py

Recria exclusivamente backend/school_schedule_demo.db. A base normal
school_schedule.db não é lida, apagada nem modificada.

Todos os nomes, cursos, cargas e horários docentes desta base são inventados.
A grade é gerada e salva automaticamente pela API real do Anatinus.
"""

import os
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name("school_schedule_demo.db")
os.environ["ANATINUS_DATABASE_URL"] = f"sqlite:///{DATABASE_PATH.as_posix()}"

from fastapi import HTTPException  # noqa: E402
from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine, ensure_database_compatibility  # noqa: E402


# Integral com almoço entre os períodos 5 e 6.
ALLOWED_PERIODS = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]
WEEKDAYS = ["Seg", "Ter", "Qua", "Qui", "Sex"]
DAILY_TARGET = 6


def make_availability(days_off=()):
    unavailable_days = set(days_off)
    allowed = set(ALLOWED_PERIODS)
    return {
        str(day): [
            period in allowed and day not in unavailable_days
            for period in range(16)
        ]
        for day in range(5)
    }


def make_setting(subject, workload, *, split=False):
    setting = {
        "subject_id": subject.id,
        "workload": workload,
        "split": split,
    }
    if split:
        setting.update({
            "joint_workload": 0,
            "workload_a": workload,
            "workload_b": workload,
        })
    return setting


def main():
    print("Criando a base fictícia de apresentação...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ensure_database_compatibility()

    db = SessionLocal()
    try:
        ds_course = models.Course(name="Desenvolvimento de Sistemas")
        admin_course = models.Course(name="Administração")
        db.add_all([ds_course, admin_course])
        db.flush()

        # Componentes comuns aos dois cursos.
        general_specs = [
            ("Língua Portuguesa", 3, "Baixa", "Ensino Médio"),
            ("Matemática", 3, "Media", "Ensino Médio"),
            ("Inglês", 2, "Baixa", "Ensino Médio"),
            ("História", 2, "Baixa", "Ensino Médio"),
            ("Geografia", 2, "Baixa", "Ensino Médio"),
            ("Biologia", 2, "Media", "Ensino Médio"),
            ("Filosofia", 2, "Baixa", "Ensino Médio"),
            ("Sociologia", 2, "Baixa", "Ensino Médio"),
            ("Educação Física", 2, "Media", "Ensino Médio"),
        ]
        general = {}
        for name, workload, complexity, category in general_specs:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category=category,
                course_ids=[ds_course.id, admin_course.id],
            )
            db.add(subject)
            db.flush()
            general[name] = subject

        ds_specs = [
            ("Programação", 4, "Alta"),
            ("Banco de Dados", 4, "Alta"),
            ("Redes de Computadores", 2, "Media"),
        ]
        ds_subjects = {}
        for name, workload, complexity in ds_specs:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category="Técnica",
                course_ids=[ds_course.id],
            )
            db.add(subject)
            db.flush()
            ds_subjects[name] = subject

        admin_specs = [
            ("Gestão de Projetos", 4, "Media"),
            ("Contabilidade", 4, "Alta"),
            ("Marketing", 2, "Baixa"),
        ]
        admin_subjects = {}
        for name, workload, complexity in admin_specs:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category="Técnica",
                course_ids=[admin_course.id],
            )
            db.add(subject)
            db.flush()
            admin_subjects[name] = subject

        general_settings = [
            make_setting(general[name], workload)
            for name, workload, _, _ in general_specs
        ]
        ds_shared_settings = list(general_settings)
        admin_class_settings = list(general_settings)

        first_ds_settings = list(general_settings)
        for name, workload, _ in ds_specs:
            # Nesta turma, a parte técnica acontece separadamente nos grupos A/B.
            first_ds_settings.append(
                make_setting(ds_subjects[name], workload, split=True)
            )

        second_ds_settings = [
            *general_settings,
            *[
                make_setting(ds_subjects[name], workload)
                for name, workload, _ in ds_specs
            ],
        ]
        admin_class_settings.extend(
            make_setting(admin_subjects[name], workload)
            for name, workload, _ in admin_specs
        )

        preferred_sequence = [[
            general["Filosofia"].id,
            general["Sociologia"].id,
        ]]

        classrooms = [
            models.Classroom(
                name="1º DS Integral",
                shift="Integral",
                course_id=ds_course.id,
                has_groups=True,
                allowed_periods=ALLOWED_PERIODS,
                subject_settings=first_ds_settings,
                preferred_subject_sequences=preferred_sequence,
                split_subject_ids=[
                    ds_subjects[name].id for name, _, _ in ds_specs
                ],
            ),
            models.Classroom(
                name="2º DS Integral",
                shift="Integral",
                course_id=ds_course.id,
                has_groups=False,
                allowed_periods=ALLOWED_PERIODS,
                subject_settings=second_ds_settings,
                preferred_subject_sequences=preferred_sequence,
                split_subject_ids=[],
            ),
            models.Classroom(
                name="1º ADM Integral",
                shift="Integral",
                course_id=admin_course.id,
                has_groups=False,
                allowed_periods=ALLOWED_PERIODS,
                subject_settings=admin_class_settings,
                preferred_subject_sequences=preferred_sequence,
                split_subject_ids=[],
            ),
        ]
        db.add_all(classrooms)

        # Horários fictícios: alguns docentes têm um dia da semana bloqueado.
        # Todos os docentes têm habilitação explícita para suas disciplinas.
        teacher_specs = [
            ("Camila Nogueira", [general["Língua Portuguesa"]], [2], 94),
            ("Bruno Tavares", [general["Matemática"]], [4], 96),
            ("Aline Costa", [general["Inglês"]], [1], 88),
            ("Diego Martins", [general["História"]], [3], 86),
            ("Marina Alves", [general["Geografia"]], [2], 91),
            ("Rafaela Souza", [general["Biologia"]], [4], 84),
            ("João Pedro", [general["Filosofia"]], [0], 82),
            ("Larissa Mendes", [general["Sociologia"]], [3], 87),
            ("Pedro Henrique", [general["Educação Física"]], [1], 90),
            ("Gabriel Rocha", [ds_subjects["Programação"]], [2], 97),
            ("Luiza Ferreira", [ds_subjects["Banco de Dados"]], [4], 93),
            ("Caio Mendes", [ds_subjects["Redes de Computadores"]], [0], 85),
            ("Renata Lima", [admin_subjects["Gestão de Projetos"]], [2], 89),
            ("Felipe Santos", [admin_subjects["Contabilidade"]], [1], 92),
            ("Beatriz Melo", [admin_subjects["Marketing"]], [3], 83),
        ]

        for name, subjects, days_off, score in teacher_specs:
            db.add(models.Teacher(
                name=name,
                allowed_subjects=sorted(subject.id for subject in subjects),
                availability=make_availability(days_off),
                score=score,
            ))

        db.add(models.SystemConfig(
            max_classes_per_day=DAILY_TARGET,
            max_consecutive_classes=6,
            max_high_complexity_per_day=2,
            student_gaps_hard=True,
            teacher_gaps_hard=False,
            min_classes_students=2,
            min_classes_teachers=2,
            avoid_first_period=False,
            avoid_last_period=False,
            avoid_friday=False,
            max_consec_per_teacher=2,
            max_consec_teacher_mode="ignore",
        ))
        db.commit()

        # Gera pela mesma função usada pela interface e grava no SQLite.
        from app.main import generate_timetable

        try:
            result = generate_timetable(db=db)
        except HTTPException as exc:
            raise RuntimeError(
                f"Não foi possível gerar a grade de apresentação "
                f"(HTTP {exc.status_code}): {exc.detail}"
            ) from exc

        schedule = result.get("schedule", [])
        if result.get("status") != "success" or not schedule:
            raise RuntimeError(f"O gerador não produziu uma grade: {result!r}")

        unstaffed = sum(item.get("teacher_id") is None for item in schedule)
        if unstaffed:
            raise RuntimeError(
                f"A grade de apresentação ficou com {unstaffed} aula(s) sem professor."
            )

        expected_total = 100
        if len(schedule) != expected_total:
            raise RuntimeError(
                f"Esperadas {expected_total} aulas na grade, geradas {len(schedule)}."
            )

        saved_count = db.query(models.TimetableItem).count()
        if saved_count != len(schedule):
            raise RuntimeError(
                f"Persistência divergente: {len(schedule)} na API e "
                f"{saved_count} no banco."
            )

        classroom_by_id = {row.id: row for row in classrooms}
        for classroom in classrooms:
            for audience in (["A", "B"] if classroom.has_groups else ["Todos"]):
                daily_counts = []
                for day in range(5):
                    count = sum(
                        item["classroom_id"] == classroom.id
                        and item["day"] == day
                        and item.get("student_group", "Todos") in ("Todos", audience)
                        for item in schedule
                    )
                    daily_counts.append(count)

                if daily_counts != [DAILY_TARGET] * 5:
                    raise RuntimeError(
                        f"{classroom.name} / {audience}: distribuição diária "
                        f"inesperada {daily_counts}; esperado {DAILY_TARGET} por dia."
                    )

        teachers_by_id = {
            row.id: row for row in db.query(models.Teacher).all()
        }
        for item in schedule:
            teacher = teachers_by_id.get(item.get("teacher_id"))
            if teacher is None:
                raise RuntimeError("Aula salva sem professor válido.")
            if item["subject_id"] not in (teacher.allowed_subjects or []):
                raise RuntimeError(
                    f"{teacher.name} foi associado a uma matéria não habilitada."
                )
            available = (teacher.availability or {}).get(str(item["day"]), [])
            if item["period"] >= len(available) or not available[item["period"]]:
                raise RuntimeError(
                    f"{teacher.name} foi alocado fora da disponibilidade cadastrada."
                )

        print("BASE FICTÍCIA E GRADE DE APRESENTAÇÃO GERADAS.")
        print(f"Banco: {DATABASE_PATH}")
        print(f"Cursos: {db.query(models.Course).count()}")
        print(f"Turmas: {db.query(models.Classroom).count()}")
        print(f"Disciplinas: {db.query(models.Subject).count()}")
        print(f"Professores: {db.query(models.Teacher).count()}")
        print(f"Aulas salvas: {saved_count}")
        print(f"Sem professor: {unstaffed}")
        print(f"Estado do solver: {result.get('solution_status', 'unknown')}")
        print(f"Tempo do solver: {result.get('solve_time_seconds', 0):.2f}s")
        for classroom in classrooms:
            label = "A/B" if classroom.has_groups else "Todos"
            print(
                f"- {classroom.name} ({label}): "
                f"6 aulas por dia, de segunda a sexta."
            )
        print("Todos os dados cadastrais e horários docentes são fictícios.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
