from typing import Any, Dict, List
import time

from ortools.sat.python import cp_model


# Índices dos períodos de aula. Intervalos e almoço não recebem índice.
JOURNEY_PERIODS = {
    "Manhã": [0, 1, 2, 3, 4, 5],
    "Integral": [0, 1, 2, 3, 4, 6, 7, 8, 9, 10],
    "Noite": [11, 12, 13, 14, 15],
    # Compatibilidade defensiva com bancos antigos.
    "Tarde": [6, 7, 8, 9, 10],
}

# Horários reais em minutos desde 00:00.
PERIOD_START_MINUTES = [
    430,   # 07:10
    480,   # 08:00
    530,   # 08:50
    600,   # 10:00
    650,   # 10:50
    700,   # 11:40
    780,   # 13:00
    830,   # 13:50
    890,   # 14:50
    940,   # 15:40
    990,   # 16:30
    1140,  # 19:00
    1190,  # 19:50
    1230,  # 20:30
    1290,  # 21:30
    1335,  # 22:15
]

PERIOD_END_MINUTES = [
    480,   # 08:00
    530,   # 08:50
    580,   # 09:40
    650,   # 10:50
    700,   # 11:40
    750,   # 12:30
    830,   # 13:50
    880,   # 14:40
    940,   # 15:40
    990,   # 16:30
    1040,  # 17:20
    1190,  # 19:50
    1230,  # 20:30
    1275,  # 21:15
    1335,  # 22:15
    1380,  # 23:00
]

# Usado apenas para a preferência de evitar janelas de professores.
# Intervalos oficiais curtos quebram a sequência visual de aulas.
CONTINUOUS_SEGMENTS = [
    [0, 1, 2],
    [3, 4, 5],
    [6, 7],
    [8, 9, 10],
    [11, 12, 13],
    [14, 15],
]


def _subject_entries_for_classroom(classroom, subjects):
    """
    Retorna somente as disciplinas realmente presentes naquela turma.

    A carga semanal e a divisão A/B pertencem à relação Turma + Disciplina.
    """
    subject_by_id = {
        subject["id"]: subject
        for subject in subjects
    }

    if "subject_settings" in classroom:
        entries = []

        for setting in classroom.get("subject_settings", []) or []:
            subject = subject_by_id.get(setting.get("subject_id"))
            if not subject:
                continue

            item = dict(subject)
            item["workload"] = int(
                setting.get("workload", subject["workload"])
            )
            item["_split"] = bool(setting.get("split", False))
            entries.append(item)

        return entries

    # Compatibilidade defensiva com dados antigos.
    split_subject_ids = set(
        classroom.get("split_subject_ids", []) or []
    )

    entries = []
    for subject in subjects:
        if classroom["course_id"] not in subject.get("course_ids", []):
            continue

        item = dict(subject)
        item["_split"] = (
            subject["id"] in split_subject_ids
        )
        entries.append(item)

    return entries


def _targets_for(classroom, subject):
    if (
        classroom.get("has_groups", False)
        and subject.get("_split", False)
    ):
        return ["A", "B"]

    return ["Todos"]


def _audiences_for(classroom):
    if classroom.get("has_groups", False):
        return ["A", "B"]

    return ["Todos"]


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
    rewards = []

    classroom_subjects = {
        classroom["id"]: _subject_entries_for_classroom(
            classroom,
            subjects,
        )
        for classroom in classrooms
    }

    # Cada unidade representa uma carga semanal independente.
    # Ex.: Matemática conjunta -> target "Todos".
    #      UDA separada -> target "A" e target "B".
    units = []

    for classroom in classrooms:
        for subject in classroom_subjects[classroom["id"]]:
            for target in _targets_for(classroom, subject):
                units.append((classroom, subject, target))

    # A[c,s,g,t] = professor escolhido para a carga semanal.
    assignment = {}

    # N[c,s,g] = aquela carga ainda está sem professor.
    no_teacher_assignment = {}

    # Y[c,s,g,t,d,p] = aula com professor.
    lesson = {}

    # U[c,s,g,d,p] = aula existe, mas ainda está sem professor.
    no_teacher_lesson = {}

    # ------------------------------------------------------------------
    # VARIÁVEIS
    # ------------------------------------------------------------------
    for classroom, subject, target in units:
        allowed_periods = set(
            JOURNEY_PERIODS.get(
                classroom.get("shift", "Manhã"),
                JOURNEY_PERIODS["Manhã"],
            )
        )

        none_key = (
            classroom["id"],
            subject["id"],
            target,
        )
        no_teacher_assignment[none_key] = model.NewBoolVar(
            f"N_c{classroom['id']}_s{subject['id']}_g{target}"
        )

        for day in range(num_days):
            for period in range(num_periods):
                key = (
                    classroom["id"],
                    subject["id"],
                    target,
                    day,
                    period,
                )
                no_teacher_lesson[key] = model.NewBoolVar(
                    f"U_c{classroom['id']}_s{subject['id']}_"
                    f"g{target}_d{day}_p{period}"
                )

                model.Add(
                    no_teacher_lesson[key]
                    <= no_teacher_assignment[none_key]
                )

                if period not in allowed_periods:
                    model.Add(no_teacher_lesson[key] == 0)

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
                subject["id"]
                in teacher.get("allowed_subjects", [])
            )

            if not can_teach:
                model.Add(
                    assignment[assignment_key] == 0
                )

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
                        f"g{target}_t{teacher['id']}_"
                        f"d{day}_p{period}"
                    )

                    model.Add(
                        lesson[key]
                        <= assignment[assignment_key]
                    )

                    if period not in allowed_periods:
                        model.Add(lesson[key] == 0)

                    availability = teacher.get(
                        "availability",
                        {},
                    )
                    day_availability = availability.get(
                        str(day)
                    )

                    if day_availability is not None:
                        if (
                            period >= len(day_availability)
                            or not day_availability[period]
                        ):
                            model.Add(lesson[key] == 0)

    # ------------------------------------------------------------------
    # ESCOLHA DO PROFESSOR E CARGA HORÁRIA
    # ------------------------------------------------------------------
    for classroom, subject, target in units:
        none_key = (
            classroom["id"],
            subject["id"],
            target,
        )

        choices = [
            assignment[(
                classroom["id"],
                subject["id"],
                target,
                teacher["id"],
            )]
            for teacher in teachers
        ]
        choices.append(no_teacher_assignment[none_key])

        model.AddExactlyOne(choices)

        workload_vars = []

        for day in range(num_days):
            for period in range(num_periods):
                workload_vars.append(
                    no_teacher_lesson[(
                        classroom["id"],
                        subject["id"],
                        target,
                        day,
                        period,
                    )]
                )

                for teacher in teachers:
                    workload_vars.append(
                        lesson[(
                            classroom["id"],
                            subject["id"],
                            target,
                            teacher["id"],
                            day,
                            period,
                        )]
                    )

        model.Add(
            sum(workload_vars)
            == subject["workload"]
        )

    def vars_for_unit_at(
        classroom,
        subject,
        target,
        day,
        period,
    ):
        values = [
            no_teacher_lesson[(
                classroom["id"],
                subject["id"],
                target,
                day,
                period,
            )]
        ]

        values.extend(
            lesson[(
                classroom["id"],
                subject["id"],
                target,
                teacher["id"],
                day,
                period,
            )]
            for teacher in teachers
        )

        return values

    def vars_for_audience(
        classroom,
        audience,
        day,
        period,
    ):
        values = []

        for subject in classroom_subjects[classroom["id"]]:
            targets = _targets_for(
                classroom,
                subject,
            )

            if targets == ["A", "B"]:
                target = audience
            else:
                target = "Todos"

            values.extend(
                vars_for_unit_at(
                    classroom,
                    subject,
                    target,
                    day,
                    period,
                )
            )

        return values

    def vars_for_teacher(
        teacher_id,
        day,
        period,
    ):
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

    # ------------------------------------------------------------------
    # CONFLITOS DE TURMA / GRUPO
    # ------------------------------------------------------------------
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in range(num_periods):
                    values = vars_for_audience(
                        classroom,
                        audience,
                        day,
                        period,
                    )

                    if values:
                        model.AddAtMostOne(values)

    # Um professor não pode estar em dois lugares ao mesmo tempo.
    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                values = vars_for_teacher(
                    teacher["id"],
                    day,
                    period,
                )

                if values:
                    model.AddAtMostOne(values)

    # ------------------------------------------------------------------
    # OCUPAÇÃO
    # ------------------------------------------------------------------
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

                    values = vars_for_audience(
                        classroom,
                        audience,
                        day,
                        period,
                    )

                    if values:
                        model.AddMaxEquality(
                            occupancy,
                            values,
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

                values = vars_for_teacher(
                    teacher["id"],
                    day,
                    period,
                )

                if values:
                    model.AddMaxEquality(
                        occupancy,
                        values,
                    )
                else:
                    model.Add(occupancy == 0)

                teacher_occupancy[(
                    teacher["id"],
                    day,
                    period,
                )] = occupancy

    # ------------------------------------------------------------------
    # REGRAS TRABALHISTAS FIXAS
    # ------------------------------------------------------------------

    # 1) Interjornada real de 11 horas.
    # Compara o término de cada aula de um dia com o início de cada aula
    # possível no dia seguinte.
    minimum_rest_minutes = 11 * 60

    for teacher in teachers:
        for day in range(num_days - 1):
            for current_period in range(num_periods):
                for next_period in range(num_periods):
                    rest_minutes = (
                        24 * 60
                        + PERIOD_START_MINUTES[next_period]
                        - PERIOD_END_MINUTES[current_period]
                    )

                    if rest_minutes < minimum_rest_minutes:
                        model.Add(
                            teacher_occupancy[(
                                teacher["id"],
                                day,
                                current_period,
                            )]
                            + teacher_occupancy[(
                                teacher["id"],
                                day + 1,
                                next_period,
                            )]
                            <= 1
                        )

    # 2) Após no máximo 6 aulas sem uma pausa de 1 hora,
    # precisa existir descanso antes de continuar.
    #
    # Em vez de enumerar todas as combinações possíveis de 7 aulas,
    # mantemos um contador de sequência para cada período. Se duas
    # aulas ocupadas tiverem menos de 60 minutos de descanso entre
    # elas, a segunda precisa ter contador maior que a primeira.
    # Como o contador máximo é 6, uma sétima aula sem pausa suficiente
    # torna a combinação inviável. A regra é equivalente à anterior,
    # mas gera muito menos restrições no modelo.
    short_rest_edges = []

    for current_period in range(num_periods):
        for next_period in range(
            current_period + 1,
            num_periods,
        ):
            rest_minutes = (
                PERIOD_START_MINUTES[next_period]
                - PERIOD_END_MINUTES[current_period]
            )

            if rest_minutes < 60:
                short_rest_edges.append(
                    (current_period, next_period)
                )

    for teacher in teachers:
        for day in range(num_days):
            streak = {}

            for period in range(num_periods):
                occupancy = teacher_occupancy[(
                    teacher["id"],
                    day,
                    period,
                )]

                streak[period] = model.NewIntVar(
                    0,
                    6,
                    f"streak_t{teacher['id']}_d{day}_p{period}",
                )

                # Sem aula, a sequência naquele período vale zero.
                # Com aula, começa em pelo menos uma.
                model.Add(
                    streak[period]
                    <= 6 * occupancy
                )
                model.Add(
                    streak[period]
                    >= occupancy
                )

            for (
                current_period,
                next_period,
            ) in short_rest_edges:
                current_occupancy = teacher_occupancy[(
                    teacher["id"],
                    day,
                    current_period,
                )]
                next_occupancy = teacher_occupancy[(
                    teacher["id"],
                    day,
                    next_period,
                )]

                model.Add(
                    streak[next_period]
                    >= streak[current_period] + 1
                ).OnlyEnforceIf([
                    current_occupancy,
                    next_occupancy,
                ])

    # 3) Máximo absoluto de 9 aulas por dia.
    configured_max = int(
        sys_config.get("max_classes_per_day", 9)
    )
    max_classes_per_day = min(
        max(configured_max, 1),
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
                <= max_classes_per_day
            )

    # ------------------------------------------------------------------
    # REGRAS PEDAGÓGICAS
    # ------------------------------------------------------------------

    # Limite diário de aulas de alta complexidade.
    max_high = int(
        sys_config.get(
            "max_high_complexity_per_day",
            2,
        )
    )

    for classroom in classrooms:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )

        for audience in _audiences_for(classroom):
            for day in range(num_days):
                high_values = []

                for subject in classroom_subjects[
                    classroom["id"]
                ]:
                    if subject.get("complexity") != "Alta":
                        continue

                    targets = _targets_for(
                        classroom,
                        subject,
                    )
                    target = (
                        audience
                        if targets == ["A", "B"]
                        else "Todos"
                    )

                    for period in allowed_periods:
                        high_values.extend(
                            vars_for_unit_at(
                                classroom,
                                subject,
                                target,
                                day,
                                period,
                            )
                        )

                if high_values:
                    model.Add(
                        sum(high_values) <= max_high
                    )

    # Preferência de distribuição das disciplinas.
    #
    # Diurno: o alvo é 2 aulas da mesma matéria no mesmo dia.
    # - 2 aulas: ideal;
    # - 1 aula: permitido, mas menos desejável;
    # - 3 ou mais: permitido somente quando necessário e mais penalizado.
    #
    # Noite: blocos de 3, 4 ou 5 fazem parte de grades reais, então apenas
    # aulas isoladas recebem penalidade.
    for classroom, subject, target in units:
        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )
        is_night = classroom.get("shift") == "Noite"

        for day in range(num_days):
            day_count = model.NewIntVar(
                0,
                len(allowed_periods),
                f"subject_day_count_c{classroom['id']}_"
                f"s{subject['id']}_g{target}_d{day}",
            )

            model.Add(
                day_count
                == sum(
                    sum(
                        vars_for_unit_at(
                            classroom,
                            subject,
                            target,
                            day,
                            period,
                        )
                    )
                    for period in allowed_periods
                )
            )

            if is_night:
                # 0 = sem aula, 1 = indesejado, 2+ = normal.
                day_costs = [
                    0,
                    120,
                ] + [
                    0
                    for _ in range(
                        max(
                            len(allowed_periods) - 1,
                            0,
                        )
                    )
                ]
            else:
                # 2 é o alvo. Uma aula única é tolerável.
                # Três ou mais são mais indesejáveis do que deixar aulas
                # isoladas, mas continuam possíveis se as outras regras
                # exigirem.
                day_costs = [0, 120, 0]

                for count in range(
                    3,
                    len(allowed_periods) + 1,
                ):
                    day_costs.append(
                        (count - 2) * 500
                    )

            day_penalty = model.NewIntVar(
                0,
                max(day_costs),
                f"subject_distribution_penalty_"
                f"c{classroom['id']}_s{subject['id']}_"
                f"g{target}_d{day}",
            )

            model.AddElement(
                day_count,
                day_costs,
                day_penalty,
            )
            penalties.append(day_penalty)

    # Regra opcional legada de mesmo professor seguido.
    # Por padrão fica ignorada porque horários reais podem ter blocos longos.
    max_same_teacher = int(
        sys_config.get(
            "max_consec_per_teacher",
            2,
        )
    )
    same_teacher_mode = sys_config.get(
        "max_consec_teacher_mode",
        "ignore",
    )

    if same_teacher_mode != "ignore":
        for classroom in classrooms:
            allowed_periods = JOURNEY_PERIODS.get(
                classroom.get("shift", "Manhã"),
                JOURNEY_PERIODS["Manhã"],
            )

            for audience in _audiences_for(classroom):
                for teacher in teachers:
                    for day in range(num_days):
                        window_size = max_same_teacher + 1

                        if len(allowed_periods) < window_size:
                            continue

                        for start in range(
                            len(allowed_periods)
                            - window_size
                            + 1
                        ):
                            periods = allowed_periods[
                                start:start + window_size
                            ]

                            class_values = []

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
                                    class_values.append(
                                        lesson[(
                                            classroom["id"],
                                            subject["id"],
                                            target,
                                            teacher["id"],
                                            day,
                                            period,
                                        )]
                                    )

                            class_sum = sum(class_values)

                            if same_teacher_mode == "hard":
                                model.Add(
                                    class_sum
                                    <= max_same_teacher
                                )
                            elif same_teacher_mode == "soft":
                                penalty = model.NewIntVar(
                                    0,
                                    window_size,
                                    f"pen_same_t{teacher['id']}_"
                                    f"c{classroom['id']}_"
                                    f"g{audience}_d{day}_s{start}",
                                )
                                model.Add(
                                    penalty
                                    >= class_sum
                                    - max_same_teacher
                                )
                                penalties.append(
                                    penalty * 40
                                )

    # 4) Janelas para alunos são proibidas.
    # Intervalos e almoço oficiais não aparecem em allowed_periods,
    # portanto não contam como janela.
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
                            model.Add(
                                day_occ[left]
                                + (1 - day_occ[middle])
                                + day_occ[right]
                                <= 2
                            )

    # Janelas de professores continuam configuráveis.
    teacher_gaps_hard = bool(
        sys_config.get(
            "teacher_gaps_hard",
            False,
        )
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
                                    f"gap_t{teacher['id']}_d{day}_"
                                    f"{left}_{middle}_{right}"
                                )
                                model.Add(
                                    expression - 2
                                    <= gap_penalty
                                )
                                penalties.append(
                                    gap_penalty * 80
                                )

    # Casar divisões de turma quando for possível:
    # ocupar A e B no mesmo horário é uma preferência, não obrigação.
    for classroom in classrooms:
        if not classroom.get("has_groups", False):
            continue

        allowed_periods = JOURNEY_PERIODS.get(
            classroom.get("shift", "Manhã"),
            JOURNEY_PERIODS["Manhã"],
        )

        for day in range(num_days):
            for period in allowed_periods:
                group_a = student_occupancy[(
                    classroom["id"],
                    "A",
                    day,
                    period,
                )]
                group_b = student_occupancy[(
                    classroom["id"],
                    "B",
                    day,
                    period,
                )]

                mismatch = model.NewBoolVar(
                    f"split_mismatch_c{classroom['id']}_"
                    f"d{day}_p{period}"
                )
                model.AddAbsEquality(
                    mismatch,
                    group_a - group_b,
                )
                penalties.append(
                    mismatch * 25
                )

    # ------------------------------------------------------------------
    # PREFERÊNCIAS / OBJETIVO
    # ------------------------------------------------------------------

    # Falta de professor é permitida, mas é sempre a última opção.
    for classroom, subject, target in units:
        for day in range(num_days):
            for period in range(num_periods):
                penalties.append(
                    no_teacher_lesson[(
                        classroom["id"],
                        subject["id"],
                        target,
                        day,
                        period,
                    )]
                    * 10000
                )

    # Pontuação docente: quanto maior, maior a prioridade quando há escolha.
    for classroom, subject, target in units:
        for teacher in teachers:
            score = int(
                teacher.get("score", 0) or 0
            )

            if score <= 0:
                continue

            for day in range(num_days):
                for period in range(num_periods):
                    rewards.append(
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

    min_classes_students = int(
        sys_config.get(
            "min_classes_students",
            2,
        )
    )
    min_classes_teachers = int(
        sys_config.get(
            "min_classes_teachers",
            2,
        )
    )
    avoid_first_period = bool(
        sys_config.get(
            "avoid_first_period",
            False,
        )
    )
    avoid_last_period = bool(
        sys_config.get(
            "avoid_last_period",
            False,
        )
    )
    avoid_friday = bool(
        sys_config.get(
            "avoid_friday",
            False,
        )
    )

    # Evita que professor vá à escola para pouquíssimas aulas.
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

            model.Add(
                sum(day_occ) > 0
            ).OnlyEnforceIf(active)

            model.Add(
                sum(day_occ) == 0
            ).OnlyEnforceIf(active.Not())

            minimum_penalty = model.NewIntVar(
                0,
                num_periods,
                f"pen_min_t{teacher['id']}_d{day}",
            )

            model.Add(
                minimum_penalty
                >= min_classes_teachers
                - sum(day_occ)
            ).OnlyEnforceIf(active)

            model.Add(
                minimum_penalty == 0
            ).OnlyEnforceIf(active.Not())

            penalties.append(
                minimum_penalty * 100
            )

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

                minimum_penalty = model.NewIntVar(
                    0,
                    num_periods,
                    f"pen_min_c{classroom['id']}_"
                    f"g{audience}_d{day}",
                )

                model.Add(
                    minimum_penalty
                    >= min_classes_students
                    - sum(day_occ)
                ).OnlyEnforceIf(active)

                model.Add(
                    minimum_penalty == 0
                ).OnlyEnforceIf(active.Not())

                penalties.append(
                    minimum_penalty * 100
                )

    model.Maximize(
        sum(rewards) - sum(penalties)
    )

    # ------------------------------------------------------------------
    # RESOLUÇÃO
    # ------------------------------------------------------------------
    model_proto = model.Proto()
    model_variables = len(model_proto.variables)
    model_constraints = len(model_proto.constraints)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0

    started = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - started

    if status == cp_model.INFEASIBLE:
        return {
            "status": "infeasible",
            "message": (
                "Não existe uma grade que cumpra todas as "
                "restrições atuais. Revise cargas horárias, "
                "jornadas e disponibilidade."
            ),
        }

    if status == cp_model.MODEL_INVALID:
        return {
            "status": "error",
            "message": (
                "O modelo de geração ficou inválido. "
                "Isso indica um erro interno do Anatinus."
            ),
        }

    if status == cp_model.UNKNOWN:
        return {
            "status": "timeout",
            "message": (
                "O Anatinus não conseguiu concluir a busca "
                "dentro do tempo de cálculo. Tente gerar novamente "
                "ou revise restrições muito concentradas."
            ),
            "solve_time_seconds": round(elapsed, 3),
            "model_variables": model_variables,
            "model_constraints": model_constraints,
        }

    if status not in (
        cp_model.OPTIMAL,
        cp_model.FEASIBLE,
    ):
        return {
            "status": "error",
            "message": (
                "Ocorreu um problema inesperado durante "
                "a geração da grade."
            ),
        }

    schedule = []

    for classroom, subject, target in units:
        for day in range(num_days):
            for period in range(num_periods):
                no_teacher_key = (
                    classroom["id"],
                    subject["id"],
                    target,
                    day,
                    period,
                )

                if solver.Value(
                    no_teacher_lesson[no_teacher_key]
                ) == 1:
                    schedule.append({
                        "classroom_id": classroom["id"],
                        "subject_id": subject["id"],
                        "teacher_id": None,
                        "day": day,
                        "period": period,
                        "student_group": target,
                    })

                for teacher in teachers:
                    lesson_key = (
                        classroom["id"],
                        subject["id"],
                        target,
                        teacher["id"],
                        day,
                        period,
                    )

                    if solver.Value(
                        lesson[lesson_key]
                    ) == 1:
                        schedule.append({
                            "classroom_id": classroom["id"],
                            "subject_id": subject["id"],
                            "teacher_id": teacher["id"],
                            "day": day,
                            "period": period,
                            "student_group": target,
                        })

    schedule.sort(
        key=lambda item: (
            item["day"],
            item["period"],
            item["classroom_id"],
            item["student_group"],
            item["subject_id"],
        )
    )

    unstaffed_by_unit = {}

    for item in schedule:
        if item["teacher_id"] is not None:
            continue

        key = (
            item["classroom_id"],
            item["subject_id"],
            item["student_group"],
        )
        unstaffed_by_unit[key] = (
            unstaffed_by_unit.get(key, 0) + 1
        )

    unstaffed_assignments = [
        {
            "classroom_id": classroom_id,
            "subject_id": subject_id,
            "student_group": student_group,
            "lessons": lessons,
        }
        for (
            classroom_id,
            subject_id,
            student_group,
        ), lessons in sorted(
            unstaffed_by_unit.items()
        )
    ]

    return {
        "status": "success",
        "solution_status": (
            "optimal"
            if status == cp_model.OPTIMAL
            else "feasible"
        ),
        "solve_time_seconds": round(
            elapsed,
            3,
        ),
        "objective_value": round(
            solver.ObjectiveValue(),
            3,
        ),
        "best_objective_bound": round(
            solver.BestObjectiveBound(),
            3,
        ),
        "model_variables": model_variables,
        "model_constraints": model_constraints,
        "schedule": schedule,
        "unstaffed_lessons": sum(
            item["teacher_id"] is None
            for item in schedule
        ),
        "unstaffed_assignments":
            unstaffed_assignments,
    }
