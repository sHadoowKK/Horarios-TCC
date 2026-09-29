from ortools.sat.python import cp_model
from typing import Any, Dict, List
import time


# Índices dos períodos de aula ao longo do dia.
# Intervalos e almoço NÃO recebem índice porque nunca podem receber aula.
JOURNEY_PERIODS = {
    "Manhã": [0, 1, 2, 3, 4, 5],
    "Integral": [0, 1, 2, 3, 4, 6, 7, 8, 9, 10],
    "Noite": [11, 12, 13, 14, 15],
    # Compatibilidade defensiva com bancos antigos.
    "Tarde": [6, 7, 8, 9, 10],
}

# Blocos realmente consecutivos. Um intervalo oficial quebra a sequência.
CONTINUOUS_SEGMENTS = [
    [0, 1, 2],       # manhã antes do intervalo
    [3, 4, 5],       # manhã depois do intervalo
    [6, 7],          # tarde antes do intervalo
    [8, 9, 10],      # tarde depois do intervalo
    [11, 12, 13],    # noite antes do intervalo
    [14, 15],        # noite depois do intervalo
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


def _teacher_lesson_vars(Y, teacher_id, classrooms, subjects, day, period):
    return [
        Y[(classroom["id"], subject["id"], teacher_id, day, period)]
        for classroom in classrooms
        for subject in _subjects_for_classroom(classroom, subjects)
    ]


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

    # Y[c,s,t,d,p] = 1 se a turma c tem a disciplina s com o professor t
    # no dia d e período p.
    Y = {}

    # A[c,s,t] = 1 se o professor t é o professor escolhido para aquela
    # disciplina naquela turma.
    A = {}

    # ------------------------------------------------------------------
    # VARIÁVEIS E RESTRIÇÕES BÁSICAS
    # ------------------------------------------------------------------
    for classroom in classrooms:
        journey = classroom.get("shift", "Manhã")
        allowed_periods = set(JOURNEY_PERIODS.get(journey, JOURNEY_PERIODS["Manhã"]))
        classroom_subjects = _subjects_for_classroom(classroom, subjects)

        for subject in classroom_subjects:
            for teacher in teachers:
                can_teach = subject["id"] in teacher.get("allowed_subjects", [])

                assignment_key = (classroom["id"], subject["id"], teacher["id"])
                A[assignment_key] = model.NewBoolVar(
                    f"A_c{classroom['id']}_s{subject['id']}_t{teacher['id']}"
                )

                if not can_teach:
                    model.Add(A[assignment_key] == 0)

                for day in range(num_days):
                    for period in range(num_periods):
                        key = (
                            classroom["id"],
                            subject["id"],
                            teacher["id"],
                            day,
                            period,
                        )
                        Y[key] = model.NewBoolVar(
                            f"Y_c{classroom['id']}_s{subject['id']}_"
                            f"t{teacher['id']}_d{day}_p{period}"
                        )

                        model.Add(Y[key] <= A[assignment_key])

                        # A turma só pode receber aulas nos períodos de sua jornada.
                        if period not in allowed_periods:
                            model.Add(Y[key] == 0)

                        # Disponibilidade do professor.
                        availability = teacher.get("availability", {})
                        day_availability = availability.get(str(day))
                        if day_availability is not None:
                            if period >= len(day_availability) or not day_availability[period]:
                                model.Add(Y[key] == 0)

    # 1. Exatamente um professor por disciplina/turma.
    for classroom in classrooms:
        for subject in _subjects_for_classroom(classroom, subjects):
            if subject["workload"] > 0:
                model.AddExactlyOne([
                    A[(classroom["id"], subject["id"], teacher["id"])]
                    for teacher in teachers
                ])

    # 2. Carga horária semanal exata.
    for classroom in classrooms:
        for subject in _subjects_for_classroom(classroom, subjects):
            model.Add(
                sum(
                    Y[(classroom["id"], subject["id"], teacher["id"], day, period)]
                    for teacher in teachers
                    for day in range(num_days)
                    for period in range(num_periods)
                )
                == subject["workload"]
            )

    # 3. Uma turma não pode ter duas aulas ao mesmo tempo.
    for classroom in classrooms:
        classroom_subjects = _subjects_for_classroom(classroom, subjects)
        for day in range(num_days):
            for period in range(num_periods):
                model.AddAtMostOne([
                    Y[(classroom["id"], subject["id"], teacher["id"], day, period)]
                    for subject in classroom_subjects
                    for teacher in teachers
                ])

    # 4. Um professor não pode estar em duas turmas ao mesmo tempo.
    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                model.AddAtMostOne(
                    _teacher_lesson_vars(
                        Y, teacher["id"], classrooms, subjects, day, period
                    )
                )

    # ------------------------------------------------------------------
    # REGRAS TRABALHISTAS E PEDAGÓGICAS
    # ------------------------------------------------------------------

    # 5. Interjornada simplificada:
    # se o professor trabalha à noite, não recebe aula pela manhã no dia seguinte.
    night_periods = JOURNEY_PERIODS["Noite"]
    morning_periods = JOURNEY_PERIODS["Manhã"]

    for teacher in teachers:
        for day in range(num_days - 1):
            night_vars = [
                var
                for period in night_periods
                for var in _teacher_lesson_vars(
                    Y, teacher["id"], classrooms, subjects, day, period
                )
            ]
            next_morning_vars = [
                var
                for period in morning_periods
                for var in _teacher_lesson_vars(
                    Y, teacher["id"], classrooms, subjects, day + 1, period
                )
            ]

            if night_vars and next_morning_vars:
                taught_at_night = model.NewBoolVar(
                    f"night_t{teacher['id']}_d{day}"
                )
                model.Add(sum(night_vars) > 0).OnlyEnforceIf(taught_at_night)
                model.Add(sum(night_vars) == 0).OnlyEnforceIf(taught_at_night.Not())
                model.Add(sum(next_morning_vars) == 0).OnlyEnforceIf(taught_at_night)

    # 6. Máximo de aulas consecutivas do professor.
    # Intervalos oficiais quebram a sequência.
    max_consecutive = sys_config.get("max_consecutive_classes", 5)
    for teacher in teachers:
        for day in range(num_days):
            for segment in CONTINUOUS_SEGMENTS:
                window_size = max_consecutive + 1
                if len(segment) < window_size:
                    continue
                for start in range(len(segment) - window_size + 1):
                    window_periods = segment[start:start + window_size]
                    window_vars = [
                        var
                        for period in window_periods
                        for var in _teacher_lesson_vars(
                            Y, teacher["id"], classrooms, subjects, day, period
                        )
                    ]
                    if window_vars:
                        model.Add(sum(window_vars) <= max_consecutive)

    # 7. Máximo de aulas por dia do professor.
    max_classes = sys_config.get("max_classes_per_day", 9)
    for teacher in teachers:
        for day in range(num_days):
            day_vars = [
                var
                for period in range(num_periods)
                for var in _teacher_lesson_vars(
                    Y, teacher["id"], classrooms, subjects, day, period
                )
            ]
            if day_vars:
                model.Add(sum(day_vars) <= max_classes)

    # 8. Máximo de aulas de alta complexidade por dia para cada turma.
    max_high = sys_config.get("max_high_complexity_per_day", 2)
    for classroom in classrooms:
        high_subjects = [
            subject
            for subject in _subjects_for_classroom(classroom, subjects)
            if subject.get("complexity") == "Alta"
        ]
        for day in range(num_days):
            high_vars = [
                Y[(classroom["id"], subject["id"], teacher["id"], day, period)]
                for subject in high_subjects
                for teacher in teachers
                for period in range(num_periods)
            ]
            if high_vars:
                model.Add(sum(high_vars) <= max_high)

    # 9. Máximo de 2 aulas consecutivas da mesma disciplina.
    # Um intervalo oficial quebra a sequência.
    for classroom in classrooms:
        journey = classroom.get("shift", "Manhã")
        segments = JOURNEY_SEGMENTS.get(journey, JOURNEY_SEGMENTS["Manhã"])

        for subject in _subjects_for_classroom(classroom, subjects):
            for day in range(num_days):
                for segment in segments:
                    if len(segment) < 3:
                        continue
                    for start in range(len(segment) - 2):
                        periods = segment[start:start + 3]
                        model.Add(
                            sum(
                                Y[(
                                    classroom["id"],
                                    subject["id"],
                                    teacher["id"],
                                    day,
                                    period,
                                )]
                                for teacher in teachers
                                for period in periods
                            )
                            <= 2
                        )

    # 9b. Máximo de aulas seguidas do mesmo professor na mesma turma.
    max_same_teacher = sys_config.get("max_consec_per_teacher", 2)
    same_teacher_mode = sys_config.get("max_consec_teacher_mode", "hard")

    if same_teacher_mode != "ignore":
        for classroom in classrooms:
            journey = classroom.get("shift", "Manhã")
            segments = JOURNEY_SEGMENTS.get(journey, JOURNEY_SEGMENTS["Manhã"])
            classroom_subjects = _subjects_for_classroom(classroom, subjects)

            for teacher in teachers:
                for day in range(num_days):
                    window_size = max_same_teacher + 1
                    for segment in segments:
                        if len(segment) < window_size:
                            continue
                        for start in range(len(segment) - window_size + 1):
                            periods = segment[start:start + window_size]
                            class_sum = sum(
                                Y[(
                                    classroom["id"],
                                    subject["id"],
                                    teacher["id"],
                                    day,
                                    period,
                                )]
                                for subject in classroom_subjects
                                for period in periods
                            )

                            if same_teacher_mode == "hard":
                                model.Add(class_sum <= max_same_teacher)
                            elif same_teacher_mode == "soft":
                                penalty = model.NewIntVar(
                                    0,
                                    window_size,
                                    f"pen_consec_t{teacher['id']}_"
                                    f"c{classroom['id']}_d{day}_s{start}",
                                )
                                model.Add(
                                    penalty >= class_sum - max_same_teacher
                                )
                                penalties.append(penalty * 40)

    # 10. Janelas dos alunos.
    # A lista da jornada já ignora intervalos e almoço, então eles nunca
    # são tratados como "buracos" na grade.
    student_gaps_hard = sys_config.get("student_gaps_hard", True)

    for classroom in classrooms:
        journey = classroom.get("shift", "Manhã")
        allowed_periods = JOURNEY_PERIODS.get(
            journey, JOURNEY_PERIODS["Manhã"]
        )
        classroom_subjects = _subjects_for_classroom(classroom, subjects)

        for day in range(num_days):
            has_class = []
            for period in allowed_periods:
                period_var = model.NewBoolVar(
                    f"c_has_class_c{classroom['id']}_d{day}_p{period}"
                )
                model.AddMaxEquality(
                    period_var,
                    [
                        Y[(
                            classroom["id"],
                            subject["id"],
                            teacher["id"],
                            day,
                            period,
                        )]
                        for subject in classroom_subjects
                        for teacher in teachers
                    ],
                )
                has_class.append(period_var)

            # Proíbe/penaliza qualquer buraco entre duas aulas do mesmo dia.
            for left in range(len(has_class) - 2):
                for middle in range(left + 1, len(has_class) - 1):
                    for right in range(middle + 1, len(has_class)):
                        expression = (
                            has_class[left]
                            + (1 - has_class[middle])
                            + has_class[right]
                        )
                        if student_gaps_hard:
                            model.Add(expression <= 2)
                        else:
                            gap_penalty = model.NewBoolVar(
                                f"gap_c{classroom['id']}_d{day}_"
                                f"{left}_{middle}_{right}"
                            )
                            model.Add(expression - 2 <= gap_penalty)
                            penalties.append(gap_penalty * 100)

    # 11. Janelas dos professores.
    # Só contam dentro de blocos sem intervalo oficial.
    teacher_gaps_hard = sys_config.get("teacher_gaps_hard", False)

    for teacher in teachers:
        for day in range(num_days):
            has_class = []
            for period in range(num_periods):
                period_var = model.NewBoolVar(
                    f"t_has_class_t{teacher['id']}_d{day}_p{period}"
                )
                model.AddMaxEquality(
                    period_var,
                    _teacher_lesson_vars(
                        Y, teacher["id"], classrooms, subjects, day, period
                    ),
                )
                has_class.append(period_var)

            for segment in CONTINUOUS_SEGMENTS:
                if len(segment) < 3:
                    continue
                for left_index in range(len(segment) - 2):
                    for middle_index in range(left_index + 1, len(segment) - 1):
                        for right_index in range(middle_index + 1, len(segment)):
                            left = segment[left_index]
                            middle = segment[middle_index]
                            right = segment[right_index]
                            expression = (
                                has_class[left]
                                + (1 - has_class[middle])
                                + has_class[right]
                            )

                            if teacher_gaps_hard:
                                model.Add(expression <= 2)
                            else:
                                gap_penalty = model.NewBoolVar(
                                    f"gap_t{teacher['id']}_d{day}_"
                                    f"{left}_{middle}_{right}"
                                )
                                model.Add(expression - 2 <= gap_penalty)
                                penalties.append(gap_penalty * 80)

    # ------------------------------------------------------------------
    # FUNÇÃO OBJETIVO
    # ------------------------------------------------------------------
    objective_terms = []

    # Pontuação dos professores: quanto maior, mais o solver prefere esse
    # professor quando mais de um pode dar a mesma disciplina.
    for classroom in classrooms:
        for subject in _subjects_for_classroom(classroom, subjects):
            for teacher in teachers:
                score = teacher.get("score", 0)
                if score <= 0:
                    continue
                for day in range(num_days):
                    for period in range(num_periods):
                        objective_terms.append(
                            score
                            * Y[(
                                classroom["id"],
                                subject["id"],
                                teacher["id"],
                                day,
                                period,
                            )]
                        )

    min_classes_students = sys_config.get("min_classes_students", 2)
    min_classes_teachers = sys_config.get("min_classes_teachers", 2)
    avoid_first_period = sys_config.get("avoid_first_period", False)
    avoid_last_period = sys_config.get("avoid_last_period", False)
    avoid_friday = sys_config.get("avoid_friday", False)

    # Preferência: evitar que o professor vá à escola para pouquíssimas aulas.
    for teacher in teachers:
        for day in range(num_days):
            day_vars = [
                var
                for period in range(num_periods)
                for var in _teacher_lesson_vars(
                    Y, teacher["id"], classrooms, subjects, day, period
                )
            ]

            if day_vars:
                active = model.NewBoolVar(
                    f"active_t{teacher['id']}_d{day}"
                )
                model.Add(sum(day_vars) > 0).OnlyEnforceIf(active)
                model.Add(sum(day_vars) == 0).OnlyEnforceIf(active.Not())

                penalty = model.NewIntVar(
                    0, num_periods, f"pen_min_t{teacher['id']}_d{day}"
                )
                model.Add(
                    penalty >= min_classes_teachers - sum(day_vars)
                ).OnlyEnforceIf(active)
                model.Add(penalty == 0).OnlyEnforceIf(active.Not())
                penalties.append(penalty * 100)

    # Preferências da turma.
    for classroom in classrooms:
        journey = classroom.get("shift", "Manhã")
        allowed_periods = JOURNEY_PERIODS.get(
            journey, JOURNEY_PERIODS["Manhã"]
        )
        classroom_subjects = _subjects_for_classroom(classroom, subjects)

        first_period = allowed_periods[0]
        last_period = allowed_periods[-1]

        for day in range(num_days):
            day_vars = []

            for period in allowed_periods:
                for subject in classroom_subjects:
                    for teacher in teachers:
                        lesson = Y[(
                            classroom["id"],
                            subject["id"],
                            teacher["id"],
                            day,
                            period,
                        )]
                        day_vars.append(lesson)

                        if avoid_first_period and period == first_period:
                            penalties.append(lesson * 20)

                        if avoid_last_period and period == last_period:
                            penalties.append(lesson * 20)

                        if avoid_friday and day == 4:
                            penalties.append(lesson * 30)

            if day_vars:
                active = model.NewBoolVar(
                    f"active_c{classroom['id']}_d{day}"
                )
                model.Add(sum(day_vars) > 0).OnlyEnforceIf(active)
                model.Add(sum(day_vars) == 0).OnlyEnforceIf(active.Not())

                penalty = model.NewIntVar(
                    0, num_periods, f"pen_min_c{classroom['id']}_d{day}"
                )
                model.Add(
                    penalty >= min_classes_students - sum(day_vars)
                ).OnlyEnforceIf(active)
                model.Add(penalty == 0).OnlyEnforceIf(active.Not())
                penalties.append(penalty * 100)

    model.Maximize(sum(objective_terms) - sum(penalties))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0

    started = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - started

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        schedule = []

        for classroom in classrooms:
            for subject in _subjects_for_classroom(classroom, subjects):
                for teacher in teachers:
                    for day in range(num_days):
                        for period in range(num_periods):
                            if solver.Value(
                                Y[(
                                    classroom["id"],
                                    subject["id"],
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
                                })

        return {
            "status": "success",
            "solution_status": (
                "optimal" if status == cp_model.OPTIMAL else "feasible"
            ),
            "solve_time_seconds": round(elapsed, 3),
            "schedule": schedule,
        }

    return {
        "status": "infeasible",
        "message": (
            "Não foi possível gerar uma grade com as restrições informadas."
        ),
    }
