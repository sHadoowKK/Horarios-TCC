from typing import Any, Dict, List
import time

from ortools.sat.python import cp_model


JOURNEY_PERIODS = {
    "Manhã": [0, 1, 2, 3, 4, 5],
    "Integral": [0, 1, 2, 3, 4, 6, 7, 8, 9, 10],
    "Noite": [11, 12, 13, 14, 15],
    "Tarde": [6, 7, 8, 9, 10],
}

# Um intervalo oficial quebra uma sequência de aulas.
CONTINUOUS_SEGMENTS = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7],
    [8, 9, 10],
    [11, 12, 13],
    [14, 15],
]

JOURNEY_SEGMENTS = {
    "Manhã": [[0, 1, 2], [3, 4, 5]],
    "Integral": [[0, 1, 2], [3, 4], [6, 7], [8, 9, 10]],
    "Noite": [[11, 12, 13], [14, 15]],
    "Tarde": [[6, 7], [8, 9, 10]],
}



def _subjects_for_classroom(classroom, subjects):
    return [
        subject
        for subject in subjects
        if classroom["course_id"] in subject.get("course_ids", [])
    ]


def _targets_for(classroom, subject):
    """
    A divisão é configurada por turma e por disciplina.

    - sem grupos: a disciplina ocupa a turma inteira;
    - com grupos e disciplina marcada para separar: cria carga para A e B;
    - com grupos e disciplina conjunta: ocupa A + B ao mesmo tempo.
    """
    split_subject_ids = classroom.get("split_subject_ids", []) or []

    if (
        classroom.get("has_groups", False)
        and subject["id"] in split_subject_ids
    ):
        return ["A", "B"]

    return ["Todos"]


def _audiences_for(classroom):
    return ["A", "B"] if classroom.get("has_groups", False) else ["Todos"]


def generate_schedule(
    classrooms: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    sys_config: Dict[str, Any],
    num_days: int = 5,
    num_periods: int = 16,
):
    model = cp_model.CpModel()
    penalties = []

    classroom_subjects = {
        classroom["id"]: _subjects_for_classroom(classroom, subjects)
        for classroom in classrooms
    }

    # Cada unidade é uma carga semanal independente.
    # Uma disciplina conjunta usa target "Todos".
    # Uma disciplina configurada como separada usa targets "A" e "B".
    units = []
    for classroom in classrooms:
        for subject in classroom_subjects[classroom["id"]]:
            for target in _targets_for(classroom, subject):
                units.append((classroom, subject, target))

    # A[c,s,g,t] escolhe um professor para aquela carga semanal.
    assignment = {}

    # Y[c,s,g,t,d,p] = 1 quando a aula é alocada naquele horário.
    lesson = {}

    for classroom, subject, target in units:
        allowed_periods = set(
            JOURNEY_PERIODS.get(
                classroom.get("shift", "Manhã"),
                JOURNEY_PERIODS["Manhã"],
            )
        )

        for teacher in teachers:
            assignment_key = (
                classroom["id"],
                subject["id"],
                target,
                teacher["id"],
            )
            assignment[assignment_key] = model.NewBoolVar(
                f"A_c{classroom['id']}_s{subject['id']}_"
                f"g{target}_t{teacher['id']}"
            )

            can_teach = (
                subject["id"] in teacher.get("allowed_subjects", [])
            )
            if not can_teach:
                model.Add(assignment[assignment_key] == 0)

            for day in range(num_days):
                for period in range(num_periods):
                    key = (
                        classroom["id"],
                        subject["id"],
                        target,
                        teacher["id"],
                        day,
                        period,
                    )
                    lesson[key] = model.NewBoolVar(
                        f"Y_c{classroom['id']}_s{subject['id']}_"
                        f"g{target}_t{teacher['id']}_d{day}_p{period}"
                    )

                    model.Add(
                        lesson[key] <= assignment[assignment_key]
                    )

                    if period not in allowed_periods:
                        model.Add(lesson[key] == 0)

                    availability = teacher.get("availability", {})
                    day_availability = availability.get(str(day))
                    if day_availability is not None:
                        if (
                            period >= len(day_availability)
                            or not day_availability[period]
                        ):
                            model.Add(lesson[key] == 0)

    # 1. Cada carga semanal usa exatamente um professor.
    for classroom, subject, target in units:
        choices = [
            assignment[(
                classroom["id"],
                subject["id"],
                target,
                teacher["id"],
            )]
            for teacher in teachers
        ]
        if choices:
            model.AddExactlyOne(choices)

    # 2. Carga horária semanal exata.
    for classroom, subject, target in units:
        model.Add(
            sum(
                lesson[(
                    classroom["id"],
                    subject["id"],
                    target,
                    teacher["id"],
                    day,
                    period,
                )]
                for teacher in teachers
                for day in range(num_days)
                for period in range(num_periods)
            )
            == subject["workload"]
        )

    def unit_vars_for_audience(classroom, audience, day, period):
        vars_for_audience = []

        for subject in classroom_subjects[classroom["id"]]:
            targets = _targets_for(classroom, subject)

            if targets == ["A", "B"]:
                target = audience
                if target not in targets:
                    continue
            else:
                target = "Todos"

            for teacher in teachers:
                vars_for_audience.append(
                    lesson[(
                        classroom["id"],
                        subject["id"],
                        target,
                        teacher["id"],
                        day,
                        period,
                    )]
                )

        return vars_for_audience

    def teacher_vars(teacher_id, day, period):
        return [
            lesson[(
                classroom["id"],
                subject["id"],
                target,
                teacher_id,
                day,
                period,
            )]
            for classroom, subject, target in units
        ]

    # 3. Conflitos de turma/grupo.
    #
    # Uma aula conjunta ("Todos") aparece tanto na ocupação de A quanto de B.
    # Assim ela bloqueia os dois grupos. Aulas técnicas A e B podem ocorrer
    # simultaneamente, inclusive com matérias diferentes.
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in range(num_periods):
                    vars_for_audience = unit_vars_for_audience(
                        classroom,
                        audience,
                        day,
                        period,
                    )
                    if vars_for_audience:
                        model.AddAtMostOne(vars_for_audience)

    # 4. Um professor não pode dar duas aulas ao mesmo tempo.
    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                vars_for_teacher = teacher_vars(
                    teacher["id"],
                    day,
                    period,
                )
                if vars_for_teacher:
                    model.AddAtMostOne(vars_for_teacher)

    # Ocupação booleana de cada grupo/turma e de cada professor.
    student_occupancy = {}
    for classroom in classrooms:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )

        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in allowed_periods:
                    occupancy = model.NewBoolVar(
                        f"occ_c{classroom['id']}_g{audience}_"
                        f"d{day}_p{period}"
                    )
                    vars_for_audience = unit_vars_for_audience(
                        classroom,
                        audience,
                        day,
                        period,
                    )
                    if vars_for_audience:
                        model.AddMaxEquality(
                            occupancy,
                            vars_for_audience,
                        )
                    else:
                        model.Add(occupancy == 0)

                    student_occupancy[(
                        classroom["id"],
                        audience,
                        day,
                        period,
                    )] = occupancy

    teacher_occupancy = {}
    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                occupancy = model.NewBoolVar(
                    f"occ_t{teacher['id']}_d{day}_p{period}"
                )
                vars_for_teacher = teacher_vars(
                    teacher["id"],
                    day,
                    period,
                )
                if vars_for_teacher:
                    model.AddMaxEquality(
                        occupancy,
                        vars_for_teacher,
                    )
                else:
                    model.Add(occupancy == 0)

                teacher_occupancy[(
                    teacher["id"],
                    day,
                    period,
                )] = occupancy

    # 5. Interjornada simplificada:
    # quem trabalha à noite não recebe aula na manhã do dia seguinte.
    night_periods = JOURNEY_PERIODS["Noite"]
    morning_periods = JOURNEY_PERIODS["Manhã"]

    for teacher in teachers:
        for day in range(num_days - 1):
            worked_at_night = model.NewBoolVar(
                f"night_t{teacher['id']}_d{day}"
            )

            night_occ = [
                teacher_occupancy[(teacher["id"], day, period)]
                for period in night_periods
            ]

            model.AddMaxEquality(worked_at_night, night_occ)

            model.Add(
                sum(
                    teacher_occupancy[(
                        teacher["id"],
                        day + 1,
                        period,
                    )]
                    for period in morning_periods
                )
                == 0
            ).OnlyEnforceIf(worked_at_night)

    # 6. Máximo de aulas consecutivas do professor.
    max_consecutive = sys_config.get(
        "max_consecutive_classes",
        5,
    )

    for teacher in teachers:
        for day in range(num_days):
            for segment in CONTINUOUS_SEGMENTS:
                window_size = max_consecutive + 1
                if len(segment) < window_size:
                    continue

                for start in range(
                    len(segment) - window_size + 1
                ):
                    periods = segment[
                        start:start + window_size
                    ]
                    model.Add(
                        sum(
                            teacher_occupancy[(
                                teacher["id"],
                                day,
                                period,
                            )]
                            for period in periods
                        )
                        <= max_consecutive
                    )

    # 7. Máximo de aulas por dia do professor.
    max_classes = sys_config.get(
        "max_classes_per_day",
        9,
    )

    for teacher in teachers:
        for day in range(num_days):
            model.Add(
                sum(
                    teacher_occupancy[(
                        teacher["id"],
                        day,
                        period,
                    )]
                    for period in range(num_periods)
                )
                <= max_classes
            )

    # 8. Máximo diário de matérias de alta complexidade.
    # Em turma dividida, a regra é aplicada separadamente para A e B.
    max_high = sys_config.get(
        "max_high_complexity_per_day",
        2,
    )

    for classroom in classrooms:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )

        high_subjects = {
            subject["id"]
            for subject in classroom_subjects[classroom["id"]]
            if subject.get("complexity") == "Alta"
        }

        for audience in _audiences_for(classroom):
            for day in range(num_days):
                high_vars = []

                for subject in classroom_subjects[classroom["id"]]:
                    if subject["id"] not in high_subjects:
                        continue

                    targets = _targets_for(classroom, subject)
                    target = (
                        audience
                        if targets == ["A", "B"]
                        else "Todos"
                    )

                    for teacher in teachers:
                        for period in allowed_periods:
                            high_vars.append(
                                lesson[(
                                    classroom["id"],
                                    subject["id"],
                                    target,
                                    teacher["id"],
                                    day,
                                    period,
                                )]
                            )

                if high_vars:
                    model.Add(sum(high_vars) <= max_high)

    # 9. Máximo de 2 aulas consecutivas da mesma disciplina.
    for classroom, subject, target in units:
        segments = JOURNEY_SEGMENTS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_SEGMENTS["Manhã"],
        )

        for day in range(num_days):
            for segment in segments:
                if len(segment) < 3:
                    continue

                for start in range(len(segment) - 2):
                    periods = segment[start:start + 3]

                    model.Add(
                        sum(
                            lesson[(
                                classroom["id"],
                                subject["id"],
                                target,
                                teacher["id"],
                                day,
                                period,
                            )]
                            for teacher in teachers
                            for period in periods
                        )
                        <= 2
                    )

    # 9b. Máximo de aulas seguidas do mesmo professor para os mesmos alunos.
    max_same_teacher = sys_config.get(
        "max_consec_per_teacher",
        2,
    )
    same_teacher_mode = sys_config.get(
        "max_consec_teacher_mode",
        "hard",
    )

    if same_teacher_mode != "ignore":
        for classroom in classrooms:
            segments = JOURNEY_SEGMENTS.get(
                classroom.get("shift", "Manhã"),
                JOURNEY_SEGMENTS["Manhã"],
            )

            for audience in _audiences_for(classroom):
                for teacher in teachers:
                    for day in range(num_days):
                        window_size = max_same_teacher + 1

                        for segment in segments:
                            if len(segment) < window_size:
                                continue

                            for start in range(
                                len(segment) - window_size + 1
                            ):
                                periods = segment[
                                    start:start + window_size
                                ]
                                class_vars = []

                                for subject in classroom_subjects[
                                    classroom["id"]
                                ]:
                                    targets = _targets_for(
                                        classroom,
                                        subject,
                                    )
                                    target = (
                                        audience
                                        if targets == ["A", "B"]
                                        else "Todos"
                                    )

                                    for period in periods:
                                        class_vars.append(
                                            lesson[(
                                                classroom["id"],
                                                subject["id"],
                                                target,
                                                teacher["id"],
                                                day,
                                                period,
                                            )]
                                        )

                                class_sum = sum(class_vars)

                                if same_teacher_mode == "hard":
                                    model.Add(
                                        class_sum
                                        <= max_same_teacher
                                    )
                                elif same_teacher_mode == "soft":
                                    penalty = model.NewIntVar(
                                        0,
                                        window_size,
                                        f"pen_consec_t{teacher['id']}_"
                                        f"c{classroom['id']}_g{audience}_"
                                        f"d{day}_s{start}",
                                    )
                                    model.Add(
                                        penalty
                                        >= class_sum
                                        - max_same_teacher
                                    )
                                    penalties.append(
                                        penalty * 40
                                    )

    # 10. Janelas dos alunos.
    student_gaps_hard = sys_config.get(
        "student_gaps_hard",
        True,
    )

    for classroom in classrooms:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )

        for audience in _audiences_for(classroom):
            for day in range(num_days):
                day_occ = [
                    student_occupancy[(
                        classroom["id"],
                        audience,
                        day,
                        period,
                    )]
                    for period in allowed_periods
                ]

                for left in range(len(day_occ) - 2):
                    for middle in range(
                        left + 1,
                        len(day_occ) - 1,
                    ):
                        for right in range(
                            middle + 1,
                            len(day_occ),
                        ):
                            expression = (
                                day_occ[left]
                                + (1 - day_occ[middle])
                                + day_occ[right]
                            )

                            if student_gaps_hard:
                                model.Add(
                                    expression <= 2
                                )
                            else:
                                gap_penalty = model.NewBoolVar(
                                    f"gap_c{classroom['id']}_"
                                    f"g{audience}_d{day}_"
                                    f"{left}_{middle}_{right}"
                                )
                                model.Add(
                                    expression - 2
                                    <= gap_penalty
                                )
                                penalties.append(
                                    gap_penalty * 100
                                )

    # 11. Janelas dos professores.
    teacher_gaps_hard = sys_config.get(
        "teacher_gaps_hard",
        False,
    )

    for teacher in teachers:
        for day in range(num_days):
            for segment in CONTINUOUS_SEGMENTS:
                if len(segment) < 3:
                    continue

                for left_index in range(
                    len(segment) - 2
                ):
                    for middle_index in range(
                        left_index + 1,
                        len(segment) - 1,
                    ):
                        for right_index in range(
                            middle_index + 1,
                            len(segment),
                        ):
                            left = segment[left_index]
                            middle = segment[middle_index]
                            right = segment[right_index]

                            expression = (
                                teacher_occupancy[(
                                    teacher["id"],
                                    day,
                                    left,
                                )]
                                + (
                                    1
                                    - teacher_occupancy[(
                                        teacher["id"],
                                        day,
                                        middle,
                                    )]
                                )
                                + teacher_occupancy[(
                                    teacher["id"],
                                    day,
                                    right,
                                )]
                            )

                            if teacher_gaps_hard:
                                model.Add(
                                    expression <= 2
                                )
                            else:
                                gap_penalty = model.NewBoolVar(
                                    f"gap_t{teacher['id']}_"
                                    f"d{day}_{left}_{middle}_{right}"
                                )
                                model.Add(
                                    expression - 2
                                    <= gap_penalty
                                )
                                penalties.append(
                                    gap_penalty * 80
                                )

    # ------------------------------------------------------------------
    # FUNÇÃO OBJETIVO
    # ------------------------------------------------------------------
    objective_terms = []

    # Professores com maior pontuação são preferidos quando houver escolha.
    for classroom, subject, target in units:
        for teacher in teachers:
            score = teacher.get("score", 0)
            if score <= 0:
                continue

            for day in range(num_days):
                for period in range(num_periods):
                    objective_terms.append(
                        score
                        * lesson[(
                            classroom["id"],
                            subject["id"],
                            target,
                            teacher["id"],
                            day,
                            period,
                        )]
                    )

    min_classes_students = sys_config.get(
        "min_classes_students",
        2,
    )
    min_classes_teachers = sys_config.get(
        "min_classes_teachers",
        2,
    )
    avoid_first_period = sys_config.get(
        "avoid_first_period",
        False,
    )
    avoid_last_period = sys_config.get(
        "avoid_last_period",
        False,
    )
    avoid_friday = sys_config.get(
        "avoid_friday",
        False,
    )

    # Evitar que professor vá à escola para pouquíssimas aulas.
    for teacher in teachers:
        for day in range(num_days):
            day_occ = [
                teacher_occupancy[(
                    teacher["id"],
                    day,
                    period,
                )]
                for period in range(num_periods)
            ]

            active = model.NewBoolVar(
                f"active_t{teacher['id']}_d{day}"
            )
            model.Add(sum(day_occ) > 0).OnlyEnforceIf(active)
            model.Add(sum(day_occ) == 0).OnlyEnforceIf(
                active.Not()
            )

            penalty = model.NewIntVar(
                0,
                num_periods,
                f"pen_min_t{teacher['id']}_d{day}",
            )
            model.Add(
                penalty
                >= min_classes_teachers - sum(day_occ)
            ).OnlyEnforceIf(active)
            model.Add(penalty == 0).OnlyEnforceIf(
                active.Not()
            )
            penalties.append(penalty * 100)

    # Preferências dos alunos, avaliadas por grupo quando houver divisão.
    for classroom in classrooms:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )
        first_period = allowed_periods[0]
        last_period = allowed_periods[-1]

        for audience in _audiences_for(classroom):
            for day in range(num_days):
                day_occ = [
                    student_occupancy[(
                        classroom["id"],
                        audience,
                        day,
                        period,
                    )]
                    for period in allowed_periods
                ]

                if avoid_first_period:
                    penalties.append(
                        student_occupancy[(
                            classroom["id"],
                            audience,
                            day,
                            first_period,
                        )]
                        * 20
                    )

                if avoid_last_period:
                    penalties.append(
                        student_occupancy[(
                            classroom["id"],
                            audience,
                            day,
                            last_period,
                        )]
                        * 20
                    )

                if avoid_friday and day == 4:
                    penalties.extend(
                        occupancy * 30
                        for occupancy in day_occ
                    )

                active = model.NewBoolVar(
                    f"active_c{classroom['id']}_"
                    f"g{audience}_d{day}"
                )
                model.Add(
                    sum(day_occ) > 0
                ).OnlyEnforceIf(active)
                model.Add(
                    sum(day_occ) == 0
                ).OnlyEnforceIf(active.Not())

                penalty = model.NewIntVar(
                    0,
                    num_periods,
                    f"pen_min_c{classroom['id']}_"
                    f"g{audience}_d{day}",
                )
                model.Add(
                    penalty
                    >= min_classes_students - sum(day_occ)
                ).OnlyEnforceIf(active)
                model.Add(
                    penalty == 0
                ).OnlyEnforceIf(active.Not())
                penalties.append(penalty * 100)

    model.Maximize(
        sum(objective_terms) - sum(penalties)
    )

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0

    started = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - started

    if status in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        schedule = []

        for classroom, subject, target in units:
            for teacher in teachers:
                for day in range(num_days):
                    for period in range(num_periods):
                        if solver.Value(
                            lesson[(
                                classroom["id"],
                                subject["id"],
                                target,
                                teacher["id"],
                                day,
                                period,
                            )]
                        ) == 1:
                            schedule.append({
                                "classroom_id": classroom["id"],
                                "subject_id": subject["id"],
                                "teacher_id": teacher["id"],
                                "day": day,
                                "period": period,
                                "student_group": target,
                            })

        return {
            "status": "success",
            "solution_status": (
                "optimal"
                if status == cp_model.OPTIMAL
                else "feasible"
            ),
            "solve_time_seconds": round(elapsed, 3),
            "schedule": schedule,
        }

    return {
        "status": "infeasible",
        "message": (
            "Não foi possível gerar uma grade com as "
            "restrições informadas."
        ),
    }
