"""Prepara a base completa da planilha e uma grade inicial para a demo.

Recria somente school_schedule_demo.db. A base normal não é modificada.
"""

from collections import Counter

import seed_realista

from app.models import Classroom, Subject, Teacher, SystemConfig, TimetableItem
from app.optimizer import generate_schedule


def _classroom_payload(row):
    return {
        "id": row.id,
        "name": row.name,
        "course_id": row.course_id,
        "shift": row.shift,
        "allowed_periods": row.allowed_periods,
        "allowed_periods_by_day": row.allowed_periods_by_day,
        "has_groups": row.has_groups,
        "subject_settings": row.subject_settings or [],
        "preferred_subject_sequences": row.preferred_subject_sequences or [],
    }


def _solver_config(row):
    return {
        "max_classes_per_day": row.max_classes_per_day,
        "max_high_complexity_per_day": row.max_high_complexity_per_day,
        "teacher_gaps_hard": row.teacher_gaps_hard,
        "min_classes_students": row.min_classes_students,
        "min_classes_teachers": row.min_classes_teachers,
        "avoid_first_period": row.avoid_first_period,
        "avoid_last_period": row.avoid_last_period,
        "avoid_friday": row.avoid_friday,
        "max_consec_per_teacher": row.max_consec_per_teacher,
        "max_consec_teacher_mode": row.max_consec_teacher_mode,
    }


def main():
    seed_realista.main("all")

    db = seed_realista.SessionLocal()
    try:
        classroom_row = next(
            classroom
            for classroom in db.query(Classroom).all()
            if seed_realista.norm(classroom.name) == "3OINFORMATICA"
        )
        classroom = _classroom_payload(classroom_row)
        subjects = [
            {
                "id": row.id,
                "name": row.name,
                "course_ids": row.course_ids or [],
                "workload": row.workload,
                "complexity": row.complexity,
                "category": row.category,
            }
            for row in db.query(Subject).all()
        ]
        teachers = [
            {
                "id": row.id,
                "name": row.name,
                "allowed_subjects": row.allowed_subjects or [],
                "availability": row.availability or {},
                "score": row.score or 0,
            }
            for row in db.query(Teacher).all()
        ]
        config = db.query(SystemConfig).first()
        if config is None:
            raise RuntimeError("A base da planilha não possui configuração do sistema.")

        expected_groups = {"Todos": 22, "A": 14, "B": 14}
        schedule = None
        for attempt in range(1, 4):
            result = generate_schedule(
                [classroom], subjects, teachers, _solver_config(config)
            )
            candidate = result.get("schedule", []) or []
            group_counts = Counter(
                item.get("student_group", "Todos") for item in candidate
            )
            unstaffed = sum(item.get("teacher_id") is None for item in candidate)
            if (
                result.get("status") == "success"
                and group_counts == expected_groups
                and unstaffed == 0
                and not result.get("teacher_assignment_fallback")
            ):
                schedule = candidate
                print(
                    f"Grade demonstrativa: {classroom_row.name}; "
                    f"{len(schedule)} aulas, 0 sem professor; "
                    f"tentativa {attempt}; "
                    f"solver {result.get('solve_time_seconds', 0):.2f}s."
                )
                break

        if schedule is None:
            raise RuntimeError(
                "Não foi possível gerar uma grade completa e com professores "
                "para o 3º Informática em três tentativas."
            )

        db.query(TimetableItem).delete()
        db.add_all(TimetableItem(**item) for item in schedule)
        db.commit()

        lesson_units = sum(
            int(setting.get("joint_workload", setting.get("workload", 0)) or 0)
            + int(setting.get("workload_a", 0) or 0)
            + int(setting.get("workload_b", 0) or 0)
            if (
                classroom_row.has_groups
                and classroom_row.shift != "Noite"
                and setting.get("split")
            )
            else int(setting.get("workload", 0) or 0)
            for classroom_row in db.query(Classroom).all()
            for setting in classroom_row.subject_settings or []
        )
        if lesson_units != 695:
            raise RuntimeError(
                f"A matriz semanal foi alterada: esperadas 695 aulas, encontradas {lesson_units}."
            )
        print(
            "Base de apresentação pronta: "
            f"{db.query(Classroom).count()} turmas, "
            f"{db.query(Subject).count()} disciplinas, "
            f"{db.query(Teacher).count()} docentes e "
            f"{lesson_units} aulas semanais configuradas."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
