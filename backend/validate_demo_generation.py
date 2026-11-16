"""Valida as grades demonstrativas sem confundir testes por turma com a escola inteira.

Uso, a partir de backend, depois de seed_realista.py:
    python validate_demo_generation.py
    python validate_demo_generation.py --classroom "3º INFO"
    python validate_demo_generation.py --all-together

O modo padrão testa cada turma isoladamente. Isso confirma a viabilidade das
matrizes e regras individuais, mas NÃO comprova que todas as turmas possam ser
combinadas simultaneamente sem conflitos entre professores.
"""

import argparse
from collections import defaultdict
import os
from pathlib import Path

DEMO_DATABASE = Path(__file__).resolve().with_name("school_schedule_demo.db")
os.environ["ANATINUS_DATABASE_URL"] = f"sqlite:///{DEMO_DATABASE.as_posix()}"

from fastapi import HTTPException  # noqa: E402
from app import models  # noqa: E402
from app.database import SessionLocal  # noqa: E402
from app.optimizer import (  # noqa: E402
    PERIOD_END_MINUTES,
    PERIOD_START_MINUTES,
    generate_schedule,
    get_allowed_periods,
    get_allowed_periods_for_day,
)


def _validate_api_generation(db, classrooms) -> None:
    if len(classrooms) != 1:
        raise SystemExit(
            "--api exige uma base com exatamente uma turma; "
            "use seed_realista.py --informatica-only."
        )

    from app.main import generate_timetable

    classroom_row = classrooms[0]
    try:
        result = generate_timetable(db=db)
    except HTTPException as exc:
        raise SystemExit(
            f"Geração pela API falhou (HTTP {exc.status_code}): {exc.detail}"
        ) from exc

    schedule = result.get("schedule", [])
    if result.get("status") != "success" or not schedule:
        raise SystemExit(f"A API não produziu uma grade: {result!r}")

    classroom = {
        "name": classroom_row.name,
        "shift": classroom_row.shift,
        "allowed_periods": classroom_row.allowed_periods,
        "allowed_periods_by_day": classroom_row.allowed_periods_by_day,
        "has_groups": classroom_row.has_groups,
    }
    expected = _expected_lesson_count({
        "shift": classroom_row.shift,
        "has_groups": classroom_row.has_groups,
        "subject_settings": classroom_row.subject_settings or [],
    })
    if len(schedule) != expected:
        raise SystemExit(
            f"API: esperadas {expected} aulas, geradas {len(schedule)}."
        )

    _assert_no_student_gaps(classroom, schedule)
    saved_count = db.query(models.TimetableItem).count()
    if saved_count != len(schedule):
        raise SystemExit(
            f"Persistência divergente: API retornou {len(schedule)} aulas, "
            f"mas o banco salvou {saved_count}."
        )

    print("Geração pela API e persistência validadas.")
    print(f"Turma: {classroom_row.name}")
    print(f"Aulas: {len(schedule)}")
    print(f"Sem professor: {result.get('unstaffed_lessons', 0)}")
    print(f"Estado: {result.get('solution_status', 'unknown')}")
    print(f"Solver: {result.get('solve_time_seconds', 0):.2f}s")


def _expected_lesson_count(classroom: dict) -> int:
    total = 0
    has_internal_groups = (
        bool(classroom.get("has_groups"))
        and classroom.get("shift") != "Noite"
    )

    for setting in classroom.get("subject_settings") or []:
        base = int(setting.get("workload", 0) or 0)
        if has_internal_groups and setting.get("split"):
            joint = int(setting.get("joint_workload") or 0)
            raw_a = setting.get("workload_a")
            raw_b = setting.get("workload_b")
            load_a = (
                base if raw_a is None and joint == 0
                else int(raw_a or 0)
            )
            load_b = (
                base if raw_b is None and joint == 0
                else int(raw_b or 0)
            )
            total += joint + load_a + load_b
        else:
            joint = setting.get("joint_workload")
            total += base if joint is None else int(joint or 0)

    return total


def _assert_no_student_gaps(classroom: dict, schedule: list[dict]) -> None:
    audiences = (
        ["A", "B"]
        if classroom.get("has_groups") and classroom.get("shift") != "Noite"
        else ["Todos"]
    )

    for audience in audiences:
        for day in range(5):
            allowed_periods = get_allowed_periods_for_day(classroom, day)
            occupied = {
                item["period"]
                for item in schedule
                if item["day"] == day
                and item["student_group"] in ("Todos", audience)
            }
            outside_allowed = occupied - set(allowed_periods)
            if outside_allowed:
                raise RuntimeError(
                    f"Período não permitido em {classroom['name']} "
                    f"(grupo {audience}, dia {day + 1}): {sorted(outside_allowed)}."
                )
            positions = sorted(
                allowed_periods.index(period)
                for period in occupied
                if period in allowed_periods
            )
            if positions and positions != list(
                range(positions[0], positions[-1] + 1)
            ):
                raise RuntimeError(
                    f"Janela de aluno encontrada em {classroom['name']} "
                    f"(grupo {audience}, dia {day + 1})."
                )


def _validate_one_classroom(
    classroom_row,
    all_subject_rows,
    all_teacher_rows,
    config_row,
) -> dict:
    settings = classroom_row.subject_settings or []
    subject_ids = {
        int(setting["subject_id"])
        for setting in settings
        if setting.get("subject_id") is not None
    }
    subjects = [
        {
            "id": subject.id,
            "name": subject.name,
            "course_ids": subject.course_ids or [],
            "workload": subject.workload,
            "complexity": subject.complexity,
            "category": subject.category,
        }
        for subject in all_subject_rows
        if subject.id in subject_ids
    ]
    teachers = [
        {
            "id": teacher.id,
            "name": teacher.name,
            "allowed_subjects": [
                subject_id
                for subject_id in (teacher.allowed_subjects or [])
                if subject_id in subject_ids
            ],
            "availability": teacher.availability or {},
            "score": teacher.score,
        }
        for teacher in all_teacher_rows
        if subject_ids.intersection(teacher.allowed_subjects or [])
    ]
    classroom = {
        "id": classroom_row.id,
        "name": classroom_row.name,
        "course_id": classroom_row.course_id,
        "shift": classroom_row.shift,
        "allowed_periods": classroom_row.allowed_periods,
        "allowed_periods_by_day": classroom_row.allowed_periods_by_day,
        "has_groups": classroom_row.has_groups,
        "subject_settings": settings,
        "preferred_subject_sequences": (
            classroom_row.preferred_subject_sequences or []
        ),
    }
    sys_config = {
        "max_classes_per_day": min(config_row.max_classes_per_day, 9),
        "max_high_complexity_per_day": config_row.max_high_complexity_per_day,
        "teacher_gaps_hard": config_row.teacher_gaps_hard,
        "min_classes_students": config_row.min_classes_students,
        "min_classes_teachers": config_row.min_classes_teachers,
        "avoid_first_period": config_row.avoid_first_period,
        "avoid_last_period": config_row.avoid_last_period,
        "avoid_friday": config_row.avoid_friday,
        "max_consec_per_teacher": config_row.max_consec_per_teacher,
        "max_consec_teacher_mode": config_row.max_consec_teacher_mode,
    }

    # Reproduz a mesma busca da grade-base da geração conjunta:
    # somente docentes habilitados para as matérias desta turma participam,
    # mas a validação exige que todas as aulas sejam preservadas.
    result = generate_schedule(
        [classroom],
        subjects,
        teachers,
        sys_config,
        _feasibility_only=True,
    )
    if result.get("status") != "success":
        raise RuntimeError(
            f"{classroom_row.name}: {result.get('message', result.get('status'))}; "
            f"métricas={result}"
        )

    expected = _expected_lesson_count(classroom)
    actual = len(result.get("schedule", []))
    if actual != expected:
        raise RuntimeError(
            f"{classroom_row.name}: esperadas {expected} aulas, geradas {actual}."
        )

    _assert_no_student_gaps(classroom, result["schedule"])
    return {
        "name": classroom_row.name,
        "lessons": actual,
        "unstaffed_in_feasibility_search": result.get("unstaffed_lessons", 0),
        "solution_status": result.get("solution_status", "unknown"),
        "validation_mode": "feasibility_only",
        "variables": result.get("model_variables", 0),
        "constraints": result.get("model_constraints", 0),
        "solve_seconds": result.get("solve_time_seconds", 0),
    }


def _assert_global_teacher_constraints(schedule, teachers, config) -> None:
    teacher_by_id = {teacher.id: teacher for teacher in teachers}
    occupied_slots = {}
    by_teacher = {}

    for item in schedule:
        teacher_id = item.get("teacher_id")
        if teacher_id is None:
            continue

        slot_key = (teacher_id, item["day"], item["period"])
        if slot_key in occupied_slots:
            previous = occupied_slots[slot_key]
            raise RuntimeError(
                f"Professor {teacher_id} alocado simultaneamente às turmas "
                f"{previous['classroom_id']} e {item['classroom_id']} "
                f"(dia {item['day'] + 1}, período {item['period']})."
            )
        occupied_slots[slot_key] = item
        by_teacher.setdefault(teacher_id, {}).setdefault(item["day"], []).append(
            item["period"]
        )

        teacher = teacher_by_id.get(teacher_id)
        if teacher is None:
            raise RuntimeError(f"Professor inexistente na grade: {teacher_id}.")

        day_availability = (teacher.availability or {}).get(str(item["day"]))
        if (
            day_availability is not None
            and (
                item["period"] >= len(day_availability)
                or not day_availability[item["period"]]
            )
        ):
            raise RuntimeError(
                f"{teacher.name} foi alocado fora da disponibilidade "
                f"(dia {item['day'] + 1}, período {item['period']})."
            )

    for teacher_id, days in by_teacher.items():
        teacher = teacher_by_id[teacher_id]
        for day, periods in days.items():
            unique_periods = sorted(periods)
            if len(unique_periods) > min(int(config.max_classes_per_day), 9):
                raise RuntimeError(
                    f"{teacher.name} ultrapassou o máximo diário de aulas "
                    f"no dia {day + 1}."
                )

            if int(config.min_classes_teachers) >= 2:
                for turn_name, turn_periods in (
                    ("manhã", set(range(6))),
                    ("tarde", set(range(6, 11))),
                    ("noite", set(range(11, 16))),
                ):
                    turn_count = sum(period in turn_periods for period in unique_periods)
                    if turn_count == 1:
                        raise RuntimeError(
                            f"{teacher.name} ficou com somente uma aula no "
                            f"turno {turn_name}, dia {day + 1}."
                        )

            for index in range(len(unique_periods) - 6):
                window = unique_periods[index:index + 7]
                if all(
                    PERIOD_START_MINUTES[right] - PERIOD_END_MINUTES[left] < 60
                    for left, right in zip(window, window[1:])
                ):
                    raise RuntimeError(
                        f"{teacher.name} ultrapassou seis aulas consecutivas "
                        f"sem descanso de uma hora no dia {day + 1}."
                    )

        for day in range(4):
            previous_periods = days.get(day, [])
            next_periods = days.get(day + 1, [])
            for previous_period in previous_periods:
                for next_period in next_periods:
                    rest_minutes = (
                        1440
                        + PERIOD_START_MINUTES[next_period]
                        - PERIOD_END_MINUTES[previous_period]
                    )
                    if rest_minutes < 11 * 60:
                        raise RuntimeError(
                            f"{teacher.name} não teve 11 horas de descanso "
                            f"entre os dias {day + 1} e {day + 2}."
                        )


def _validate_all_together(db) -> None:
    from app.main import generate_timetable

    classrooms = db.query(models.Classroom).order_by(models.Classroom.id).all()
    teachers = db.query(models.Teacher).all()
    config = db.query(models.SystemConfig).first()
    if config is None:
        raise SystemExit("A base demo não possui configuração do sistema.")

    try:
        result = generate_timetable(db=db)
    except HTTPException as exc:
        raise SystemExit(
            f"Geração conjunta falhou (HTTP {exc.status_code}): {exc.detail}"
        ) from exc

    schedule = result.get("schedule", [])
    if result.get("status") != "success" or not schedule:
        raise SystemExit(f"Geração conjunta não produziu grade: {result!r}")

    expected_total = 0
    for classroom_row in classrooms:
        classroom = {
            "name": classroom_row.name,
            "shift": classroom_row.shift,
            "allowed_periods": classroom_row.allowed_periods,
            "allowed_periods_by_day": classroom_row.allowed_periods_by_day,
            "has_groups": classroom_row.has_groups,
            "subject_settings": classroom_row.subject_settings or [],
        }
        expected = _expected_lesson_count(classroom)
        actual = sum(
            item["classroom_id"] == classroom_row.id for item in schedule
        )
        expected_total += expected

        if actual != expected:
            actual_by_group = defaultdict(int)
            for item in schedule:
                if item["classroom_id"] == classroom_row.id:
                    actual_by_group[item.get("student_group", "Todos")] += 1
            expected_by_group = {"Todos": 0, "A": 0, "B": 0}
            for setting in classroom_row.subject_settings or []:
                base = int(setting.get("workload", 0) or 0)
                if classroom_row.has_groups and classroom_row.shift != "Noite" and setting.get("split"):
                    joint = int(setting.get("joint_workload", 0) or 0)
                    expected_by_group["Todos"] += joint
                    expected_by_group["A"] += int(setting.get("workload_a", 0) or 0)
                    expected_by_group["B"] += int(setting.get("workload_b", 0) or 0)
                else:
                    expected_by_group["Todos"] += (
                        base if setting.get("joint_workload") is None
                        else int(setting.get("joint_workload", 0) or 0)
                    )
            raise RuntimeError(
                f"{classroom_row.name}: esperadas {expected} aulas, geradas {actual}; "
                f"por grupo esperado={expected_by_group}, real={dict(actual_by_group)}; "
                f"has_groups={classroom_row.has_groups}; "
                f"split_settings={sum(bool(s.get('split')) for s in classroom_row.subject_settings or [])}; "
                f"solution_status={result.get('solution_status')}; "
                f"teacher_fallback={result.get('teacher_assignment_fallback')}; "
                f"used_feasibility_seed={result.get('used_feasibility_seed')}; "
                f"solve_time={result.get('solve_time_seconds')}s."
            )
        _assert_no_student_gaps(classroom, [
            item for item in schedule
            if item["classroom_id"] == classroom_row.id
        ])

    if len(schedule) != expected_total:
        raise RuntimeError(
            f"Esperadas {expected_total} aulas na escola, geradas {len(schedule)}."
        )

    _assert_global_teacher_constraints(schedule, teachers, config)

    unstaffed = sum(item.get("teacher_id") is None for item in schedule)
    if unstaffed == len(schedule):
        raise RuntimeError(
            "A grade foi montada, mas nenhuma aula recebeu professor. "
            "A distribuição docente global ainda não foi resolvida."
        )

    saved_count = db.query(models.TimetableItem).count()
    if saved_count != len(schedule):
        raise RuntimeError(
            f"Persistência divergente: API retornou {len(schedule)} aulas, "
            f"mas o banco salvou {saved_count}."
        )

    print("Grade conjunta da escola gerada e validada.")
    print(f"Turmas: {len(classrooms)}")
    print(f"Aulas: {len(schedule)}")
    print(f"Com professor: {len(schedule) - unstaffed}")
    print(f"Sem professor: {unstaffed}")
    print(f"Estado: {result.get('solution_status', 'unknown')}")
    print(
        f"Solver: {result.get('solve_time_seconds', 0):.2f}s; "
        f"{result.get('model_variables', 0)} variáveis / "
        f"{result.get('model_constraints', 0)} restrições."
    )

    if unstaffed:
        classroom_by_id = {row.id: row.name for row in classrooms}
        subject_by_id = {
            row.id: row.name
            for row in db.query(models.Subject).all()
        }
        eligible_by_subject = defaultdict(list)
        for teacher in teachers:
            for subject_id in teacher.allowed_subjects or []:
                eligible_by_subject[subject_id].append(teacher.name)

        missing_by_unit = defaultdict(int)
        for item in schedule:
            if item.get("teacher_id") is None:
                key = (
                    item["classroom_id"],
                    item["subject_id"],
                    item.get("student_group", "Todos"),
                )
                missing_by_unit[key] += 1

        print("Aulas sem professor por turma/matéria/grupo:")
        for (classroom_id, subject_id, group), count in sorted(
            missing_by_unit.items()
        ):
            candidate_names = eligible_by_subject.get(subject_id, [])
            candidates = ", ".join(candidate_names) if candidate_names else "nenhum cadastrado"
            print(
                f"- {classroom_by_id[classroom_id]} / "
                f"{subject_by_id.get(subject_id, f'matéria {subject_id}')} / "
                f"{group}: {count} aula(s); "
                f"docentes habilitados: {candidates}"
            )

    # Relatório de qualidade visual/lógica: distribuição semanal e blocos.
    subject_rows = db.query(models.Subject).all()
    subject_by_id = {row.id: row.name for row in subject_rows}
    teacher_name_by_id = {row.id: row.name for row in teachers}
    contiguous_pairs = {
        (0, 1), (1, 2), (3, 4), (4, 5),
        (6, 7), (8, 9), (9, 10),
        (11, 12), (12, 13), (14, 15),
    }
    weekday_names = ["Seg", "Ter", "Qua", "Qui", "Sex"]

    print("RELATÓRIO DE DISTRIBUIÇÃO SEMANAL")
    for classroom_row in classrooms:
        class_schedule = [
            item for item in schedule
            if item["classroom_id"] == classroom_row.id
        ]
        audiences = (
            ["A", "B"]
            if classroom_row.has_groups and classroom_row.shift != "Noite"
            else ["Todos"]
        )
        for audience in audiences:
            print(
                f"{classroom_row.name} — grupo {audience}"
                if audience != "Todos" else classroom_row.name
            )
            daily_counts = []
            for day, weekday in enumerate(weekday_names):
                day_items = [
                    item for item in class_schedule
                    if item["day"] == day
                    and item.get("student_group", "Todos") in ("Todos", audience)
                ]
                day_items.sort(key=lambda item: item["period"])
                daily_counts.append(len(day_items))
                cells = []
                for item in day_items:
                    subject_name = subject_by_id.get(
                        item["subject_id"], f"#{item['subject_id']}"
                    )
                    teacher_name = (
                        teacher_name_by_id.get(item["teacher_id"], "?")
                        if item.get("teacher_id") is not None
                        else "SEM DOC"
                    )
                    cells.append(
                        f"{item['period'] + 1}:{subject_name} [{teacher_name}]"
                    )
                print(
                    f"  {weekday}: {len(day_items)} aulas — "
                    + (" | ".join(cells) if cells else "sem aulas")
                )
            if daily_counts:
                spread = max(daily_counts) - min(daily_counts)
                print(
                    f"  Distribuição diária: {daily_counts}; "
                    f"diferença entre maior/menor dia: {spread}."
                )

            # Blocos por matéria: destaca cargas de 2+ aulas quebradas em
            # ocorrências isoladas ou espalhadas por muitos dias.
            units_for_audience = defaultdict(list)
            for item in class_schedule:
                target = item.get("student_group", "Todos")
                if target in ("Todos", audience):
                    units_for_audience[(
                        item["subject_id"],
                        target,
                    )].append(item)

            for (subject_id, target), items in sorted(
                units_for_audience.items(),
                key=lambda pair: subject_by_id.get(pair[0][0], "")
            ):
                per_day = defaultdict(list)
                for item in items:
                    per_day[item["day"]].append(item["period"])
                daily_blocks = []
                for day, periods in sorted(per_day.items()):
                    periods = sorted(periods)
                    blocks = []
                    current = [periods[0]]
                    for period in periods[1:]:
                        if (current[-1], period) in contiguous_pairs:
                            current.append(period)
                        else:
                            blocks.append(current)
                            current = [period]
                    blocks.append(current)
                    daily_blocks.append(
                        f"{weekday_names[day]}:" + "+".join(
                            str(len(block)) for block in blocks
                        )
                    )
                total = len(items)
                if total >= 2:
                    print(
                        f"  Matéria {subject_by_id.get(subject_id, subject_id)}"
                        f" ({target}, {total} aulas): "
                        + ", ".join(daily_blocks)
                    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Valida os cenários de demonstração do Anatinus."
    )
    parser.add_argument(
        "--classroom",
        help="Valida somente a turma com esse nome exato.",
    )
    parser.add_argument(
        "--api",
        action="store_true",
        help="Valida geração e persistência pela API; requer somente uma turma.",
    )
    parser.add_argument(
        "--all-together",
        action="store_true",
        help="Tenta gerar todas as turmas juntas, incluindo conflitos entre professores.",
    )
    args = parser.parse_args()

    if sum((bool(args.classroom), bool(args.all_together), bool(args.api))) > 1:
        parser.error("--classroom, --api e --all-together são modos exclusivos.")

    db = SessionLocal()
    try:
        if args.all_together:
            _validate_all_together(db)
            return

        classrooms = db.query(models.Classroom).order_by(models.Classroom.id).all()
        if args.api:
            _validate_api_generation(db, classrooms)
            return
        if args.classroom:
            classrooms = [
                classroom
                for classroom in classrooms
                if classroom.name == args.classroom
            ]
            if not classrooms:
                raise SystemExit(f"Turma não encontrada: {args.classroom}")

        subjects = db.query(models.Subject).all()
        teachers = db.query(models.Teacher).all()
        config = db.query(models.SystemConfig).first()
        if config is None:
            raise SystemExit("A base demo não possui configuração do sistema.")

        results = []
        for classroom in classrooms:
            results.append(
                _validate_one_classroom(classroom, subjects, teachers, config)
            )

        print("Validação individual das turmas concluída.")
        for result in results:
            print(
                f"- {result['name']}: {result['lessons']} aulas; "
                f"{result['unstaffed_in_feasibility_search']} sem professor na busca de viabilidade; "
                f"{result['solution_status']}; "
                f"{result['solve_seconds']:.2f}s; "
                f"{result['variables']} variáveis / "
                f"{result['constraints']} restrições."
            )
        print(
            "Nota: este teste verifica as matrizes individualmente; "
            "não valida conflitos docentes entre turmas diferentes."
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
