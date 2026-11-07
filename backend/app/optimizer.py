from itertools import combinations
from typing import Any, Dict, List
import time

from ortools.sat.python import cp_model


JOURNEY_PERIODS = {
    "Manhã": [0, 1, 2, 3, 4, 5],
    "Integral": [0, 1, 2, 3, 4, 6, 7, 8, 9, 10],
    "Noite": [11, 12, 13, 14, 15],
    "Tarde": [6, 7, 8, 9, 10],
}

TURNS_DEFINITIONS = {
    "Manhã": [0, 1, 2, 3, 4, 5],
    "Tarde": [6, 7, 8, 9, 10],
    "Noite": [11, 12, 13, 14, 15],
}

PERIOD_START_MINUTES = [
    430,  # 0: Manhã 1ª (07:10)
    480,  # 1: Manhã 2ª (08:00)
    530,  # 2: Manhã 3ª (08:50)
    600,  # 3: Manhã 4ª (10:00)
    650,  # 4: Manhã 5ª (10:50)
    700,  # 5: Manhã 6ª (11:40)
    780,  # 6: Tarde 1ª (13:00)
    830,  # 7: Tarde 2ª (13:50)
    890,  # 8: Tarde 3ª (14:50)
    940,  # 9: Tarde 4ª (15:40)
    990,  # 10: Tarde 5ª (16:30)
    1140, # 11: Noturno Mod 1ª (19:00)
    1185, # 12: Noturno Mod 2ª (19:45)
    1230, # 13: Noturno Mod 3ª (20:30)
    1290, # 14: Noturno Mod 4ª (21:30)
    1335  # 15: Noturno Mod 5ª (22:15)
]

PERIOD_END_MINUTES = [
    480,  # 0: 08:00
    530,  # 1: 08:50
    580,  # 2: 09:40
    650,  # 3: 10:50
    700,  # 4: 11:40
    750,  # 5: 12:30
    830,  # 6: 13:50
    880,  # 7: 14:40
    940,  # 8: 15:40
    990,  # 9: 16:30
    1040, # 10: 17:20
    1185, # 11: 19:45
    1230, # 12: 20:30
    1275, # 13: 21:15
    1335, # 14: 22:15
    1380  # 15: 23:00
]


def get_allowed_periods(classroom):
    """Retorna os períodos configurados, com fallback para o turno legado.

    O período 5 (11:40–12:30) só pode ser usado por jornadas diurnas
    que o habilitem explicitamente; a jornada padrão permanece 5+5.
    """
    shift = classroom.get("shift", "Manhã")
    fallback = list(JOURNEY_PERIODS.get(shift, JOURNEY_PERIODS["Manhã"]))
    configured = classroom.get("allowed_periods")

    if configured is None:
        return fallback

    if shift == "Integral":
        valid_periods = set(range(11))
    else:
        valid_periods = set(fallback)

    normalized = set()
    if not isinstance(configured, (list, tuple, set)):
        return fallback

    for raw_period in configured:
        try:
            period = int(raw_period)
        except (TypeError, ValueError):
            continue
        if period in valid_periods and 0 <= period < len(PERIOD_START_MINUTES):
            normalized.add(period)

    return sorted(normalized)


def get_allowed_periods_for_day(classroom, day):
    """Retorna os períodos permitidos no dia, respeitando overrides explícitos."""
    configured_by_day = classroom.get("allowed_periods_by_day")
    if not isinstance(configured_by_day, dict) or not configured_by_day:
        return get_allowed_periods(classroom)

    raw_periods = configured_by_day.get(str(day), configured_by_day.get(day, []))
    if not isinstance(raw_periods, (list, tuple, set)):
        return []

    valid_periods = set(get_allowed_periods(classroom))
    normalized = set()
    for raw_period in raw_periods:
        try:
            period = int(raw_period)
        except (TypeError, ValueError):
            continue
        if period in valid_periods:
            normalized.add(period)
    return sorted(normalized)


def _get_allowed_periods(classroom):
    """Alias compatível com testes/código que usam o nome interno antigo."""
    return get_allowed_periods(classroom)


def _get_allowed_periods_for_day(classroom, day):
    return get_allowed_periods_for_day(classroom, day)


def _subject_entries_for_classroom(classroom, subjects):
    subject_by_id = {subject["id"]: subject for subject in subjects}

    if "subject_settings" in classroom:
        entries = []
        for setting in classroom.get("subject_settings", []) or []:
            subject = subject_by_id.get(setting.get("subject_id"))
            if not subject:
                continue

            item = dict(subject)
            base_workload = int(setting.get("workload", subject["workload"]))
            split = bool(setting.get("split", False))
            raw_joint_workload = setting.get("joint_workload")

            if split and classroom.get("shift") != "Noite":
                joint_workload = int(raw_joint_workload or 0)
                raw_a = setting.get("workload_a")
                raw_b = setting.get("workload_b")
                workload_a = base_workload if raw_a is None and joint_workload == 0 else int(raw_a or 0)
                workload_b = base_workload if raw_b is None and joint_workload == 0 else int(raw_b or 0)
            else:
                joint_workload = base_workload if raw_joint_workload is None else int(raw_joint_workload)
                workload_a = 0
                workload_b = 0
                split = False

            item["workload"] = base_workload
            item["_joint_workload"] = joint_workload
            item["_workload_by_target"] = {
                "Todos": joint_workload,
                "A": workload_a,
                "B": workload_b,
            }
            item["_split"] = split

            default_triple_preference = 3 in (joint_workload, workload_a, workload_b)
            configured_triple_preference = setting.get("prefer_triple_block")
            item["_prefer_triple_block"] = (
                default_triple_preference
                if configured_triple_preference is None
                else bool(configured_triple_preference)
            )
            entries.append(item)

        return entries

    split_subject_ids = set(classroom.get("split_subject_ids", []) or [])
    entries = []
    for subject in subjects:
        if classroom["course_id"] not in subject.get("course_ids", []):
            continue
        item = dict(subject)
        item["_split"] = subject["id"] in split_subject_ids and classroom.get("shift") != "Noite"
        entries.append(item)

    return entries


def _targets_for(classroom, subject):
    if classroom.get("shift") == "Noite" or not classroom.get("has_groups", False) or not subject.get("_split", False):
        return ["Todos"]

    workloads = subject.get("_workload_by_target", {})
    targets = []
    if int(subject.get("_joint_workload", 0) or 0) > 0:
        targets.append("Todos")
    if int(workloads.get("A", 0) or 0) > 0:
        targets.append("A")
    if int(workloads.get("B", 0) or 0) > 0:
        targets.append("B")

    return targets or ["Todos"]


def _audiences_for(classroom):
    if classroom.get("shift") == "Noite" or not classroom.get("has_groups", False):
        return ["Todos"]
    return ["A", "B"]


def generate_schedule(
    classrooms: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    sys_config: Dict[str, Any],
    num_days: int = 5,
    num_periods: int = 16,
    fixed_schedule: List[Dict[str, Any]] | None = None,
    mutable_classroom_id: int | None = None,
    mutable_classroom_ids: List[int] | None = None,
    mutable_subject_id: int | None = None,
    _feasibility_only: bool = False,
):
    model = cp_model.CpModel()
    penalties = []
    rewards = []

    # Configurações globais
    avoid_first_period = bool(sys_config.get("avoid_first_period", False))
    avoid_last_period = bool(sys_config.get("avoid_last_period", False))
    avoid_friday = bool(sys_config.get("avoid_friday", False))
    min_classes_students = int(sys_config.get("min_classes_students", 2))
    min_classes_teachers = int(sys_config.get("min_classes_teachers", 2))
    max_high = int(sys_config.get("max_high_complexity_per_day", 2))
    configured_max = int(sys_config.get("max_classes_per_day", 9))
    max_classes_per_day = min(max(configured_max, 1), 9)

    classroom_subjects = {
        classroom["id"]: _subject_entries_for_classroom(classroom, subjects)
        for classroom in classrooms
    }

    units = []
    for classroom in classrooms:
        for subject in classroom_subjects[classroom["id"]]:
            for target in _targets_for(classroom, subject):
                units.append((classroom, subject, target))

    eligible_teachers = {}
    for classroom, subject, target in units:
        unit_key = (classroom["id"], subject["id"], target)
        eligible_teachers[unit_key] = [
            teacher for teacher in teachers if subject["id"] in teacher.get("allowed_subjects", [])
        ]

    assignment = {}
    no_teacher_assignment = {}
    lesson = {}
    no_teacher_lesson = {}

    # Em uma primeira geração, não criamos variáveis para slots impossíveis.
    # Regenerações com aulas fixadas preservam a grade antiga e mantêm o caminho
    # de compatibilidade completo para não descartar manualizações existentes.
    candidate_periods = (
        list(range(num_periods)) if fixed_schedule else None
    )

    for classroom, subject, target in units:
        allowed_periods_by_day = {
            day: set(_get_allowed_periods_for_day(classroom, day))
            for day in range(num_days)
        }
        unit_periods = (
            candidate_periods
            if candidate_periods is not None
            else sorted(set().union(*allowed_periods_by_day.values()))
        )
        none_key = (classroom["id"], subject["id"], target)
        no_teacher_assignment[none_key] = model.NewBoolVar(f"N_c{classroom['id']}_s{subject['id']}_g{target}")

        for day in range(num_days):
            allowed_today = allowed_periods_by_day[day]
            for period in unit_periods:
                key = (classroom["id"], subject["id"], target, day, period)
                no_teacher_lesson[key] = model.NewBoolVar(f"U_c{classroom['id']}_s{subject['id']}_g{target}_d{day}_p{period}")
                model.Add(no_teacher_lesson[key] <= no_teacher_assignment[none_key])

                if period not in allowed_today:
                    model.Add(no_teacher_lesson[key] == 0)

        unit_key = (classroom["id"], subject["id"], target)
        for teacher in eligible_teachers[unit_key]:
            assignment_key = (classroom["id"], subject["id"], target, teacher["id"])
            assignment[assignment_key] = model.NewBoolVar(f"A_c{classroom['id']}_s{subject['id']}_g{target}_t{teacher['id']}")
            availability = teacher.get("availability", {})

            for day in range(num_days):
                day_availability = availability.get(str(day))
                allowed_today = allowed_periods_by_day[day]
                for period in unit_periods:
                    # Na geração inicial, slots fora da disponibilidade docente
                    # são omitidos, não criados como variáveis travadas em zero.
                    if candidate_periods is None and day_availability is not None:
                        if period >= len(day_availability) or not day_availability[period]:
                            continue

                    key = (classroom["id"], subject["id"], target, teacher["id"], day, period)
                    lesson[key] = model.NewBoolVar(f"Y_c{classroom['id']}_s{subject['id']}_g{target}_t{teacher['id']}_d{day}_p{period}")
                    model.Add(lesson[key] <= assignment[assignment_key])

                    if period not in allowed_today:
                        model.Add(lesson[key] == 0)

                    if candidate_periods is not None and day_availability is not None:
                        if period >= len(day_availability) or not day_availability[period]:
                            model.Add(lesson[key] == 0)

    # PROCESSAMENTO DE FIXED_SCHEDULE (AULAS FIXADAS/MANUAIS)
    if fixed_schedule:
        for fx in fixed_schedule:
            fx_c = fx.get("classroom_id")
            fx_s = fx.get("subject_id")
            fx_t = fx.get("teacher_id")
            fx_d = fx.get("day")
            fx_p = fx.get("period")
            fx_g = fx.get("student_group", "Todos")

            # Em uma regeneração parcial, libera somente as aulas do escopo
            # solicitado. Todo o restante continua fixado no dia/período/professor.
            has_mutable_scope = (
                mutable_classroom_id is not None
                or mutable_classroom_ids is not None
                or mutable_subject_id is not None
            )
            is_mutable_classroom = (
                (mutable_classroom_id is None or fx_c == mutable_classroom_id)
                and (
                    mutable_classroom_ids is None
                    or fx_c in mutable_classroom_ids
                )
            )
            is_mutable = (
                has_mutable_scope
                and is_mutable_classroom
                and (
                    mutable_subject_id is None
                    or fx_s == mutable_subject_id
                )
            )
            if is_mutable:
                continue

            # Força a aula a ocorrer exatamente neste slot com este professor
            unit_key = (fx_c, fx_s, fx_g)
            if fx_t is not None:
                t_assign_key = (fx_c, fx_s, fx_g, fx_t)
                if t_assign_key in assignment:
                    model.Add(assignment[t_assign_key] == 1)
                t_lesson_key = (fx_c, fx_s, fx_g, fx_t, fx_d, fx_p)
                if t_lesson_key in lesson:
                    model.Add(lesson[t_lesson_key] == 1)
            else:
                none_key = (fx_c, fx_s, fx_g)
                if none_key in no_teacher_assignment:
                    model.Add(no_teacher_assignment[none_key] == 1)
                no_t_lesson_key = (fx_c, fx_s, fx_g, fx_d, fx_p)
                if no_t_lesson_key in no_teacher_lesson:
                    model.Add(no_teacher_lesson[no_t_lesson_key] == 1)

    def vars_for_unit_at(classroom, subject, target, day, period):
        key = (classroom["id"], subject["id"], target, day, period)
        if key not in no_teacher_lesson:
            return []
        values = [no_teacher_lesson[key]]
        unit_key = (classroom["id"], subject["id"], target)
        for teacher in eligible_teachers.get(unit_key, []):
            t_key = (classroom["id"], subject["id"], target, teacher["id"], day, period)
            if t_key in lesson:
                values.append(lesson[t_key])
        return values

    def vars_for_audience(classroom, audience, day, period):
        values = []
        for subject in classroom_subjects[classroom["id"]]:
            targets = _targets_for(classroom, subject)
            for target in targets:
                if target != "Todos" and target != audience:
                    continue
                values.extend(vars_for_unit_at(classroom, subject, target, day, period))
        return values

    def vars_for_teacher(teacher_id, day, period):
        values = []
        for classroom, subject, target in units:
            key = (classroom["id"], subject["id"], target, teacher_id, day, period)
            if key in lesson:
                values.append(lesson[key])
        return values

    # Carga Horária Semanal
    for classroom, subject, target in units:
        none_key = (classroom["id"], subject["id"], target)
        unit_key = (classroom["id"], subject["id"], target)

        choices = [assignment[(classroom["id"], subject["id"], target, teacher["id"])] for teacher in eligible_teachers[unit_key]]
        choices.append(no_teacher_assignment[none_key])
        model.AddExactlyOne(choices)

        workload_vars = []
        for day in range(num_days):
            for period in range(num_periods):
                workload_vars.extend(vars_for_unit_at(classroom, subject, target, day, period))

        weekly_target = subject.get("_workload_by_target", {}).get(target, subject["workload"])
        model.Add(sum(workload_vars) == weekly_target)

    # Conflitos de Turma e Professor
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in range(num_periods):
                    values = vars_for_audience(classroom, audience, day, period)
                    if values:
                        model.AddAtMostOne(values)

    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                values = vars_for_teacher(teacher["id"], day, period)
                if values:
                    model.AddAtMostOne(values)

    # Ocupação de Estudantes e Professores
    student_occupancy = {}
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in _get_allowed_periods_for_day(classroom, day):
                    occupancy = model.NewBoolVar(f"occ_c{classroom['id']}_g{audience}_d{day}_p{period}")
                    values = vars_for_audience(classroom, audience, day, period)
                    if values:
                        model.AddMaxEquality(occupancy, values)
                    else:
                        model.Add(occupancy == 0)
                    student_occupancy[(classroom["id"], audience, day, period)] = occupancy

    teacher_occupancy = {}
    for teacher in teachers:
        for day in range(num_days):
            for period in range(num_periods):
                occupancy = model.NewBoolVar(f"occ_t{teacher['id']}_d{day}_p{period}")
                values = vars_for_teacher(teacher["id"], day, period)
                if values:
                    model.AddMaxEquality(occupancy, values)
                else:
                    model.Add(occupancy == 0)
                teacher_occupancy[(teacher["id"], day, period)] = occupancy

    # DISTRIBUIÇÃO DIÁRIA DAS AULAS DOS ALUNOS
    # Evita concentrar a carga semanal em poucos dias. É uma preferência:
    # a grade continua livre para se afastar da média quando outras regras
    # obrigatórias ou a disponibilidade docente exigirem.
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            weekly_load = sum(
                int(subject.get("_workload_by_target", {}).get(
                    target, subject["workload"]
                ) or 0)
                for unit_classroom, subject, target in units
                if unit_classroom["id"] == classroom["id"]
                and target in ("Todos", audience)
            )
            target_daily_load = weekly_load // num_days
            for day in range(num_days):
                allowed_today = _get_allowed_periods_for_day(classroom, day)
                daily_load = sum(
                    student_occupancy[(classroom["id"], audience, day, period)]
                    for period in allowed_today
                    if (classroom["id"], audience, day, period) in student_occupancy
                )
                deviation = model.NewIntVar(
                    0,
                    len(allowed_today),
                    f"daily_balance_c{classroom['id']}_g{audience}_d{day}",
                )
                model.AddAbsEquality(deviation, daily_load - target_daily_load)
                penalties.append(deviation * 5000)

    # Preferência para sincronizar divisões A/B com matérias diferentes.
    # Em cada período, a turma só pode ter uma ocupação por grupo. Portanto,
    # não é necessário criar uma variável para cada par matéria A x matéria B:
    # basta detectar ocupação simultânea e excluir o caso em que é a mesma matéria.
    for classroom in classrooms:
        if (
            not classroom.get("has_groups", False)
            or classroom.get("shift") == "Noite"
        ):
            continue

        subjects = classroom_subjects[classroom["id"]]

        for day in range(num_days):
            for period in _get_allowed_periods_for_day(classroom, day):
                all_a_vars = []
                all_b_vars = []
                same_subject_parallel_vars = []

                for subject in subjects:
                    targets = _targets_for(classroom, subject)
                    vars_a = (
                        vars_for_unit_at(classroom, subject, "A", day, period)
                        if "A" in targets else []
                    )
                    vars_b = (
                        vars_for_unit_at(classroom, subject, "B", day, period)
                        if "B" in targets else []
                    )

                    all_a_vars.extend(vars_a)
                    all_b_vars.extend(vars_b)

                    if vars_a and vars_b:
                        same_parallel = model.NewBoolVar(
                            f"same_parallel_c{classroom['id']}_"
                            f"s{subject['id']}_d{day}_p{period}"
                        )
                        occupied_a_for_subject = sum(vars_a)
                        occupied_b_for_subject = sum(vars_b)
                        model.Add(same_parallel <= occupied_a_for_subject)
                        model.Add(same_parallel <= occupied_b_for_subject)
                        model.Add(
                            same_parallel
                            >= occupied_a_for_subject + occupied_b_for_subject - 1
                        )
                        same_subject_parallel_vars.append(same_parallel)

                if not all_a_vars or not all_b_vars:
                    continue

                occupied_a = model.NewBoolVar(
                    f"occupied_a_c{classroom['id']}_d{day}_p{period}"
                )
                occupied_b = model.NewBoolVar(
                    f"occupied_b_c{classroom['id']}_d{day}_p{period}"
                )
                model.AddMaxEquality(occupied_a, all_a_vars)
                model.AddMaxEquality(occupied_b, all_b_vars)

                same_subject_parallel = model.NewBoolVar(
                    f"same_subject_parallel_c{classroom['id']}_d{day}_p{period}"
                )
                if same_subject_parallel_vars:
                    model.AddMaxEquality(
                        same_subject_parallel,
                        same_subject_parallel_vars,
                    )
                else:
                    model.Add(same_subject_parallel == 0)

                parallel_distinct_subjects = model.NewBoolVar(
                    f"parallel_distinct_c{classroom['id']}_d{day}_p{period}"
                )
                model.Add(parallel_distinct_subjects <= occupied_a)
                model.Add(parallel_distinct_subjects <= occupied_b)
                model.Add(
                    parallel_distinct_subjects + same_subject_parallel <= 1
                )
                model.Add(
                    parallel_distinct_subjects
                    >= occupied_a + occupied_b - same_subject_parallel - 1
                )
                rewards.append(parallel_distinct_subjects * 1200)

    # Descanso mínimo de 11 horas entre jornadas em dias consecutivos.
    # Se o descanso real entre duas aulas possíveis for menor que 660 min,
    # o professor não pode ocupar ambos os períodos.
    for teacher in teachers:
        teacher_id = teacher["id"]
        for day in range(num_days - 1):
            for previous_period in range(min(num_periods, len(PERIOD_END_MINUTES))):
                previous_key = (teacher_id, day, previous_period)
                if previous_key not in teacher_occupancy:
                    continue
                for next_period in range(min(num_periods, len(PERIOD_START_MINUTES))):
                    next_key = (teacher_id, day + 1, next_period)
                    if next_key not in teacher_occupancy:
                        continue
                    rest_minutes = (
                        1440
                        + PERIOD_START_MINUTES[next_period]
                        - PERIOD_END_MINUTES[previous_period]
                    )
                    if rest_minutes < 11 * 60:
                        model.Add(
                            teacher_occupancy[previous_key]
                            + teacher_occupancy[next_key]
                            <= 1
                        )

    # Equilíbrio diário entre Grupo A e Grupo B
    for classroom in classrooms:
        if classroom.get("has_groups", False) and classroom.get("shift") != "Noite":
            for day in range(num_days):
                allowed_today = _get_allowed_periods_for_day(classroom, day)
                sum_a = sum(student_occupancy[(classroom["id"], "A", day, p)] for p in allowed_today if (classroom["id"], "A", day, p) in student_occupancy)
                sum_b = sum(student_occupancy[(classroom["id"], "B", day, p)] for p in allowed_today if (classroom["id"], "B", day, p) in student_occupancy)
                model.Add(sum_a - sum_b <= 2)
                model.Add(sum_b - sum_a <= 2)

    # MÍNIMO DE 2 AULAS POR TURNO
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                allowed_today = set(_get_allowed_periods_for_day(classroom, day))
                for turn_name, turn_periods in TURNS_DEFINITIONS.items():
                    valid_turn_periods = [p for p in turn_periods if p in allowed_today]
                    if valid_turn_periods and min_classes_students >= 2:
                        turn_sum = sum(student_occupancy[(classroom["id"], audience, day, p)] for p in valid_turn_periods if (classroom["id"], audience, day, p) in student_occupancy)
                        model.Add(turn_sum != 1)

    for teacher in teachers:
        for day in range(num_days):
            for turn_name, turn_periods in TURNS_DEFINITIONS.items():
                if min_classes_teachers >= 2:
                    turn_sum = sum(teacher_occupancy[(teacher["id"], day, p)] for p in turn_periods if (teacher["id"], day, p) in teacher_occupancy)
                    model.Add(turn_sum != 1)

    # Máximo de seis aulas consecutivas sem uma pausa de pelo menos 60 min.
    # Proíbe qualquer conjunto de sete aulas ocupadas em que cada aula seguinte
    # comece a menos de 60 min do término da anterior.
    valid_streak_periods = [
        period for period in range(min(num_periods, len(PERIOD_START_MINUTES), len(PERIOD_END_MINUTES)))
    ]
    streak_windows = [
        window
        for window in combinations(valid_streak_periods, 7)
        if all(
            PERIOD_START_MINUTES[right] - PERIOD_END_MINUTES[left] < 60
            for left, right in zip(window, window[1:])
        )
    ]
    for teacher in teachers:
        teacher_id = teacher["id"]
        for day in range(num_days):
            for window in streak_windows:
                model.Add(
                    sum(
                        teacher_occupancy[(teacher_id, day, period)]
                        for period in window
                    ) <= 6
                )

    # COMPRESSÃO DE DIAS DOS PROFESSORES
    for teacher in teachers:
        for day in range(num_days):
            day_occ = [teacher_occupancy[(teacher["id"], day, period)] for period in range(num_periods)]
            is_active = model.NewBoolVar(f"act_t{teacher['id']}_d{day}")
            model.Add(sum(day_occ) > 0).OnlyEnforceIf(is_active)
            model.Add(sum(day_occ) == 0).OnlyEnforceIf(is_active.Not())
            penalties.append(is_active * 600)

    # AGRUPAMENTO DE AULAS (PARES E TRIPLOS)
    # Só recompensa blocos sem intervalo entre uma aula e a próxima.
    # Há pausas entre 2ª/3ª aula da manhã, 2ª/3ª da tarde e 3ª/4ª da noite.
    contiguous_period_pairs = [
        (0, 1), (1, 2), (3, 4), (4, 5),
        (6, 7), (8, 9), (9, 10),
        (11, 12), (12, 13), (14, 15)
    ]

    contiguous_period_triples = [
        (0, 1, 2), (3, 4, 5),
        (8, 9, 10), (11, 12, 13)
    ]

    for classroom, subject, target in units:
        weekly_workload = int(subject.get("_workload_by_target", {}).get(target, subject["workload"]))

        days_active = []

        for day in range(num_days):
            allowed_today = _get_allowed_periods_for_day(classroom, day)
            allowed_set = set(allowed_today)
            slot_vars = {}
            for period in allowed_today:
                sv = model.NewBoolVar(f"slot_c{classroom['id']}_s{subject['id']}_g{target}_d{day}_p{period}")
                unit_vars = vars_for_unit_at(classroom, subject, target, day, period)
                if unit_vars:
                    model.Add(sv == sum(unit_vars))
                else:
                    model.Add(sv == 0)
                slot_vars[period] = sv

            pair_vars = []
            for p1, p2 in contiguous_period_pairs:
                if p1 in allowed_set and p2 in allowed_set:
                    pv = model.NewBoolVar(f"pair_c{classroom['id']}_s{subject['id']}_g{target}_d{day}_p{p1}")
                    model.Add(pv <= slot_vars[p1])
                    model.Add(pv <= slot_vars[p2])
                    model.Add(pv >= slot_vars[p1] + slot_vars[p2] - 1)
                    pair_vars.append(pv)
                    rewards.append(pv * 4000)

            triple_vars = []
            for p1, p2, p3 in contiguous_period_triples:
                if p1 in allowed_set and p2 in allowed_set and p3 in allowed_set:
                    tv = model.NewBoolVar(f"triple_c{classroom['id']}_s{subject['id']}_g{target}_d{day}_p{p1}")
                    model.Add(tv <= slot_vars[p1])
                    model.Add(tv <= slot_vars[p2])
                    model.Add(tv <= slot_vars[p3])
                    model.Add(tv >= slot_vars[p1] + slot_vars[p2] + slot_vars[p3] - 2)
                    triple_vars.append(tv)
                    rewards.append(tv * 3500)

            day_sum = sum(slot_vars.values())

            is_active_day = model.NewBoolVar(f"act_day_c{classroom['id']}_s{subject['id']}_g{target}_d{day}")
            model.Add(day_sum > 0).OnlyEnforceIf(is_active_day)
            model.Add(day_sum == 0).OnlyEnforceIf(is_active_day.Not())
            days_active.append(is_active_day)

            # A contiguidade dos horários dos alunos é garantida globalmente
            # por student_occupancy e pela restrição de início de sequência abaixo.
            # Os blocos da própria disciplina já são incentivados por pares/triplos.
            # Evitamos enumerar todas as combinações p_a < p_m < p_b, que criavam
            # O(n³) restrições por disciplina/dia sem acrescentar outra regra obrigatória.

            if classroom.get("shift") == "Noite":
                # No noturno são válidos blocos de 3, 4 ou 5 aulas.
                # O agrupamento é incentivado por bônus, não limitado a pares.
                model.Add(day_sum <= min(5, len(allowed_today)))
            elif weekly_workload in (2, 4):
                # Aulas em pares são uma preferência, não uma obrigação.
                # A recompensa de pair_vars acima favorece blocos consecutivos,
                # mas turmas com muitos componentes de 2 aulas precisam poder
                # distribuir parte deles em dias diferentes quando a grade não
                # comporta todos os pares (por exemplo, jornadas em blocos 3+3).
                model.Add(day_sum <= 2)

            elif weekly_workload in (3, 5):
                model.Add(day_sum <= 3)
                if (
                    weekly_workload == 3
                    and not subject.get("_prefer_triple_block", False)
                ):
                    model.Add(day_sum <= 2)

        if weekly_workload == 3:
            model.Add(sum(days_active) <= 2)

    # Proibição de janelas sem criar O(n³) restrições por turno.
    # Uma sequência de aulas sem janelas tem no máximo uma transição 0 -> 1.
    # Contar essas transições impõe a contiguidade em O(n) por dia/turma/grupo.
    for classroom in classrooms:
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                allowed_today = _get_allowed_periods_for_day(classroom, day)
                day_occ = [
                    student_occupancy[(classroom["id"], audience, day, period)]
                    for period in allowed_today
                    if (classroom["id"], audience, day, period) in student_occupancy
                ]
                starts = []
                for index, occupancy in enumerate(day_occ):
                    start = model.NewBoolVar(
                        f"starts_c{classroom['id']}_g{audience}_d{day}_i{index}"
                    )
                    if index == 0:
                        model.Add(start == occupancy)
                    else:
                        previous = day_occ[index - 1]
                        model.Add(start >= occupancy - previous)
                        model.Add(start <= occupancy)
                        model.Add(start <= 1 - previous)
                    starts.append(start)

                if starts:
                    model.Add(sum(starts) <= 1)

    for teacher in teachers:
        for day in range(num_days):
            day_occ = [teacher_occupancy[(teacher["id"], day, period)] for period in range(num_periods)]
            model.Add(sum(day_occ) <= max_classes_per_day)

    for classroom, subject, target in units:
        for day in range(num_days):
            for period in range(num_periods):
                no_teacher_key = (
                    classroom["id"], subject["id"], target, day, period
                )
                if no_teacher_key in no_teacher_lesson:
                    penalties.append(no_teacher_lesson[no_teacher_key] * 1000000)

    for classroom, subject, target in units:
        unit_key = (classroom["id"], subject["id"], target)
        for teacher in eligible_teachers[unit_key]:
            score = int(teacher.get("score", 0) or 0)
            if score <= 0:
                continue
            for day in range(num_days):
                for period in range(num_periods):
                    key = (classroom["id"], subject["id"], target, teacher["id"], day, period)
                    if key in lesson:
                        rewards.append(score * lesson[key])

    # "Evitar sexta-feira" é uma preferência, não uma proibição de horários.
    if avoid_friday:
        for key, variable in no_teacher_lesson.items():
            if key[3] == 4:
                penalties.append(variable * 200)
        for key, variable in lesson.items():
            if key[4] == 4:
                penalties.append(variable * 200)

    model.Maximize(sum(rewards) - sum(penalties))

    # Semente construtiva para a geração conjunta:
    # cada turma é resolvida primeiro sem professores. Como a ausência de
    # professor é permitida pelo modelo, a união dessas grades é uma solução
    # global válida para todas as restrições dos alunos. Isso evita obrigar o
    # CP-SAT a descobrir do zero, ao mesmo tempo, centenas de horários e a
    # distribuição dos docentes entre turmas.
    feasibility_seed_schedule = None
    seed_solve_time = 0.0
    seed_branches = 0
    seed_conflicts = 0
    seed_slot_keys = set()
    seed_failure_diagnostic = None

    if len(classrooms) > 1 and not fixed_schedule:
        candidate_seed = []
        seed_is_valid = True

        for classroom in classrooms:
            # A grade-base usa os mesmos docentes habilitados e disponibilidades
            # da validação individual. Depois removemos teacher_id: a semente
            # reserva somente os períodos das aulas, sem criar choques entre
            # turmas quando as grades individuais forem combinadas.
            class_subject_ids = {
                subject["id"]
                for subject in classroom_subjects[classroom["id"]]
            }
            seed_teachers = []
            for teacher in teachers:
                allowed_for_class = [
                    subject_id
                    for subject_id in teacher.get("allowed_subjects", [])
                    if subject_id in class_subject_ids
                ]
                if not allowed_for_class:
                    continue
                seed_teachers.append({
                    **teacher,
                    "allowed_subjects": allowed_for_class,
                })

            seed_result = generate_schedule(
                [classroom],
                subjects,
                seed_teachers,
                sys_config,
                num_days=num_days,
                num_periods=num_periods,
                _feasibility_only=True,
            )
            seed_solve_time += float(seed_result.get("solve_time_seconds", 0) or 0)
            seed_branches += int(seed_result.get("solver_branches", 0) or 0)
            seed_conflicts += int(seed_result.get("solver_conflicts", 0) or 0)

            if seed_result.get("status") != "success":
                seed_is_valid = False
                target_loads = {"Todos": 0, "A": 0, "B": 0}
                for unit_classroom, unit_subject, target in units:
                    if unit_classroom["id"] != classroom["id"]:
                        continue
                    target_loads[target] += int(
                        unit_subject.get("_workload_by_target", {}).get(
                            target, unit_subject["workload"]
                        ) or 0
                    )
                weekly_capacity = sum(
                    len(_get_allowed_periods_for_day(classroom, day))
                    for day in range(num_days)
                )
                if classroom.get("has_groups") and classroom.get("shift") != "Noite":
                    load_detail = (
                        f"A={target_loads['Todos'] + target_loads['A']}, "
                        f"B={target_loads['Todos'] + target_loads['B']}"
                    )
                else:
                    load_detail = str(target_loads["Todos"])
                seed_failure_diagnostic = {
                    "classroom": classroom.get("name", f"Turma {classroom['id']}"),
                    "status": seed_result.get("status"),
                    "weekly_load": load_detail,
                    "weekly_capacity_per_group": weekly_capacity,
                    "solver_message": seed_result.get("message", ""),
                }
                break

            candidate_seed.extend(
                {
                    **item,
                    "teacher_id": None,
                }
                for item in seed_result.get("schedule", [])
            )

        if seed_is_valid:
            feasibility_seed_schedule = candidate_seed
            seed_slot_keys = {
                (
                    item["classroom_id"],
                    item["subject_id"],
                    item.get("student_group", "Todos"),
                    item["day"],
                    item["period"],
                )
                for item in candidate_seed
            }

            # Hint completo para as decisões principais: todas as aulas ficam
            # alocadas, inicialmente sem professor. A fase de otimização pode
            # então atribuir docentes e reorganizar horários sem perder a
            # solução viável que já foi construída.
            for variable in assignment.values():
                model.add_hint(variable, 0)
            for variable in no_teacher_assignment.values():
                model.add_hint(variable, 1)
            for variable in lesson.values():
                model.add_hint(variable, 0)
            for key, variable in no_teacher_lesson.items():
                seed_key = (key[0], key[1], key[2], key[3], key[4])
                model.add_hint(variable, int(seed_key in seed_slot_keys))

    large_model = len(model.Proto().variables) >= 5000
    solution_values = None
    feasibility_time = 0.0
    optimization_time = 0.0
    total_branches = 0
    total_conflicts = 0
    optimization_completed = True
    seed_fallback = False

    if _feasibility_only:
        # As grades-base só precisam demonstrar viabilidade. Não gastamos tempo
        # otimizando preferências que serão resolvidas na etapa global.
        feasibility_model = model.clone()
        feasibility_model.proto.clear_objective()

        feasibility_solver = cp_model.CpSolver()
        feasibility_solver.parameters.max_time_in_seconds = 20.0
        feasibility_solver.parameters.num_search_workers = 8
        feasibility_solver.parameters.stop_after_first_solution = True
        status = feasibility_solver.Solve(feasibility_model)
        feasibility_time = feasibility_solver.WallTime()
        total_branches = feasibility_solver.NumBranches()
        total_conflicts = feasibility_solver.NumConflicts()
        optimization_completed = False

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solution_values = [
                feasibility_solver.value(
                    feasibility_model.get_int_var_from_proto_index(index)
                )
                for index in range(len(model.Proto().variables))
            ]
        solver = feasibility_solver
    elif feasibility_seed_schedule is not None:
        # A semente já satisfaz todas as restrições obrigatórias de turma.
        # A busca global fica dedicada a distribuir professores e melhorar a
        # qualidade, em vez de procurar primeiro uma combinação de horários.
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 240.0
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)
        optimization_time = solver.WallTime()
        total_branches = seed_branches + solver.NumBranches()
        total_conflicts = seed_conflicts + solver.NumConflicts()
        feasibility_time = seed_solve_time
        optimization_completed = status == cp_model.OPTIMAL

        if status == cp_model.UNKNOWN:
            # CP-SAT pode não conseguir melhorar a semente dentro do limite.
            # Nesse caso, preservamos a grade completa já validada, em vez de
            # devolver erro ou deixar a escola sem horário.
            seed_fallback = True
            status = cp_model.FEASIBLE
            optimization_completed = False
    elif large_model:
        # Primeira fase: encontrar qualquer solução que respeite todas as
        # restrições obrigatórias, sem gastar busca tentando melhorar o objetivo.
        feasibility_model = model.clone()
        feasibility_model.proto.clear_objective()

        feasibility_solver = cp_model.CpSolver()
        # A base escolar real tem centenas de aulas e muitas colisões possíveis.
        # 45s encerrava a busca antes de encontrar soluções que existem.
        feasibility_solver.parameters.max_time_in_seconds = 240.0
        feasibility_solver.parameters.num_search_workers = 8
        feasibility_solver.parameters.stop_after_first_solution = True
        status = feasibility_solver.Solve(feasibility_model)
        feasibility_time = feasibility_solver.WallTime()
        total_branches += feasibility_solver.NumBranches()
        total_conflicts += feasibility_solver.NumConflicts()

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            solution_values = [
                feasibility_solver.value(
                    feasibility_model.get_int_var_from_proto_index(index)
                )
                for index in range(len(model.Proto().variables))
            ]
            for index, value in enumerate(solution_values):
                model.add_hint(model.get_int_var_from_proto_index(index), value)

            optimization_solver = cp_model.CpSolver()
            optimization_solver.parameters.max_time_in_seconds = 30.0
            optimization_solver.parameters.num_search_workers = 8
            optimization_status = optimization_solver.Solve(model)
            optimization_time = optimization_solver.WallTime()
            total_branches += optimization_solver.NumBranches()
            total_conflicts += optimization_solver.NumConflicts()

            if optimization_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                solver = optimization_solver
                status = optimization_status
                solution_values = None
            else:
                solver = feasibility_solver
                status = cp_model.FEASIBLE
                optimization_completed = False
        else:
            solver = feasibility_solver
            optimization_completed = False
    else:
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 60.0
        solver.parameters.num_search_workers = 8
        status = solver.Solve(model)
        optimization_time = solver.WallTime()
        total_branches = solver.NumBranches()
        total_conflicts = solver.NumConflicts()
        optimization_completed = status == cp_model.OPTIMAL

    def value_for_solution(variable):
        if solution_values is not None:
            return solution_values[variable.Index()]
        return solver.Value(variable)

    model_metrics = {
        "model_variables": len(model.Proto().variables),
        "model_constraints": len(model.Proto().constraints),
        "solve_time_seconds": feasibility_time + optimization_time,
        "seed_solve_time_seconds": seed_solve_time,
        "used_feasibility_seed": feasibility_seed_schedule is not None,
        "feasibility_time_seconds": feasibility_time,
        "optimization_time_seconds": optimization_time,
        "solver_branches": total_branches,
        "solver_conflicts": total_conflicts,
        "optimization_completed": optimization_completed,
    }

    if status == cp_model.INFEASIBLE:
        if seed_failure_diagnostic:
            classroom_name = seed_failure_diagnostic["classroom"]
            load_detail = seed_failure_diagnostic["weekly_load"]
            capacity = seed_failure_diagnostic["weekly_capacity_per_group"]
            if seed_failure_diagnostic["status"] == "infeasible":
                detail = (
                    f"A turma {classroom_name} já é inviável quando analisada "
                    f"sozinha, sem considerar professores. Carga semanal por "
                    f"grupo: {load_detail}; capacidade da jornada: {capacity} "
                    "períodos. Revise a distribuição das matérias e as regras "
                    "de blocos/intervalos dessa turma."
                )
            else:
                detail = (
                    f"Não foi possível validar individualmente a turma "
                    f"{classroom_name} antes da geração conjunta "
                    f"({seed_failure_diagnostic['status']}). Carga semanal por "
                    f"grupo: {load_detail}; capacidade da jornada: {capacity} "
                    "períodos. Isso não identifica uma impossibilidade por si só."
                )
        else:
            detail = (
                "O modelo comprovou que esta combinação de cargas e regras é "
                "inviável. Confira as cargas semanais, as jornadas permitidas "
                "e eventuais aulas marcadas como fixas."
            )
        return {
            "status": "infeasible",
            "message": detail,
            "infeasibility_diagnostic": seed_failure_diagnostic,
            **model_metrics,
        }

    if status == cp_model.UNKNOWN:
        return {
            "status": "timeout",
            "message": (
                "O otimizador encerrou a busca de viabilidade após 4 minutos sem "
                "encontrar uma grade. Isso não comprova que a grade seja impossível. "
                "Tente gerar por turma ou revise cargas, jornadas e docentes."
            ),
            **model_metrics,
        }

    if status == cp_model.MODEL_INVALID:
        return {
            "status": "error",
            "message": (
                "O otimizador recusou o modelo por uma inconsistência interna. "
                "Consulte o log do backend."
            ),
            **model_metrics,
        }

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "error",
            "message": f"O otimizador retornou um estado inesperado: {status}.",
            **model_metrics,
        }

    schedule = (
        [dict(item) for item in feasibility_seed_schedule]
        if seed_fallback and feasibility_seed_schedule is not None
        else []
    )
    for classroom, subject, target in ([] if seed_fallback else units):
        for day in range(num_days):
            for period in range(num_periods):
                no_teacher_key = (classroom["id"], subject["id"], target, day, period)
                if no_teacher_key in no_teacher_lesson and value_for_solution(no_teacher_lesson[no_teacher_key]) == 1:
                    schedule.append({
                        "classroom_id": classroom["id"],
                        "subject_id": subject["id"],
                        "teacher_id": None,
                        "day": day,
                        "period": period,
                        "student_group": target,
                    })

                unit_key = (classroom["id"], subject["id"], target)
                for teacher in eligible_teachers[unit_key]:
                    lesson_key = (classroom["id"], subject["id"], target, teacher["id"], day, period)
                    if lesson_key in lesson and value_for_solution(lesson[lesson_key]) == 1:
                        schedule.append({
                            "classroom_id": classroom["id"],
                            "subject_id": subject["id"],
                            "teacher_id": teacher["id"],
                            "day": day,
                            "period": period,
                            "student_group": target,
                        })

    def _schedule_unit_counts(items):
        counts = {}
        for item in items or []:
            key = (
                item.get("classroom_id"),
                item.get("subject_id"),
                item.get("student_group") or "Todos",
            )
            counts[key] = counts.get(key, 0) + 1
        return counts

    expected_unit_counts = {
        (
            classroom["id"],
            subject["id"],
            target,
        ): int(
            subject.get("_workload_by_target", {}).get(
                target, subject["workload"]
            ) or 0
        )
        for classroom, subject, target in units
    }
    actual_unit_counts = _schedule_unit_counts(schedule)
    incomplete_units = [
        {
            "classroom_id": key[0],
            "subject_id": key[1],
            "student_group": key[2],
            "expected": expected,
            "actual": actual_unit_counts.get(key, 0),
        }
        for key, expected in expected_unit_counts.items()
        if actual_unit_counts.get(key, 0) != expected
    ]

    schedule_integrity_fallback = False
    if incomplete_units:
        # Nunca devolver uma grade parcial quando a geração global altera a
        # quantidade de aulas de uma matéria/grupo. As grades-base individuais
        # já passaram pelas restrições dos alunos e preservam todas as cargas.
        seed_counts = _schedule_unit_counts(feasibility_seed_schedule)
        seed_mismatches = [
            {
                "classroom_id": key[0],
                "subject_id": key[1],
                "student_group": key[2],
                "expected": expected,
                "actual": seed_counts.get(key, 0),
            }
            for key, expected in expected_unit_counts.items()
            if seed_counts.get(key, 0) != expected
        ]
        seed_expected_total = sum(expected_unit_counts.values())
        seed_actual_total = len(feasibility_seed_schedule or [])
        seed_is_complete = (
            feasibility_seed_schedule is not None
            and not seed_mismatches
            and seed_actual_total == seed_expected_total
        )
        if seed_is_complete:
            schedule = [dict(item) for item in feasibility_seed_schedule]
            seed_fallback = True
            schedule_integrity_fallback = True
            optimization_completed = False
        else:
            classroom_by_id = {
                classroom["id"]: classroom.get("name", str(classroom["id"]))
                for classroom in classrooms
            }
            details = "; ".join(
                f"{classroom_by_id.get(item['classroom_id'], item['classroom_id'])} "
                f"/ matéria {item['subject_id']} / grupo {item['student_group']}: "
                f"{item['actual']}/{item['expected']}"
                for item in incomplete_units[:8]
            )
            return {
                "status": "error",
                "message": (
                    "A geração foi interrompida para não salvar uma grade "
                    "incompleta. A quantidade de aulas não bate com a matriz: "
                    f"{details}. Diagnóstico interno: status_solver={status}, "
                    f"seed_aulas={seed_actual_total}/{seed_expected_total}, "
                    f"falha_na_seed={seed_failure_diagnostic}, "
                    f"divergências_na_seed={seed_mismatches[:8]}."
                ),
                "schedule_integrity_error": incomplete_units,
                "seed_integrity_error": seed_mismatches,
                "seed_failure_diagnostic": seed_failure_diagnostic,
                **model_metrics,
            }

    objective_metrics = {}
    if optimization_completed:
        objective_metrics = {
            "objective_value": solver.ObjectiveValue(),
            "best_objective_bound": solver.BestObjectiveBound(),
        }

    return {
        "status": "success",
        "solution_status": "feasible" if schedule_integrity_fallback else (
            "optimal" if status == cp_model.OPTIMAL else "feasible"
        ),
        "teacher_assignment_fallback": seed_fallback,
        "schedule_integrity_fallback": schedule_integrity_fallback,
        "message": (
            "A grade completa foi preservada, mas a distribuição conjunta "
            "dos professores não pôde ser concluída. Todas as matérias e "
            "cargas foram mantidas; as aulas ficaram sem professor para "
            "evitar descartar conteúdo."
            if schedule_integrity_fallback else ""
        ),
        "schedule": schedule,
        "unstaffed_lessons": sum(item["teacher_id"] is None for item in schedule),
        **objective_metrics,
        **model_metrics,
    }
