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
    1190, # 12: Noturno Mod 2ª (19:50)
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
    1190, # 11: 19:50
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


def _get_allowed_periods(classroom):
    """Alias compatível com testes/código que usam o nome interno antigo."""
    return get_allowed_periods(classroom)


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
        allowed_periods = set(_get_allowed_periods(classroom))
        unit_periods = (
            candidate_periods
            if candidate_periods is not None
            else sorted(allowed_periods)
        )
        none_key = (classroom["id"], subject["id"], target)
        no_teacher_assignment[none_key] = model.NewBoolVar(f"N_c{classroom['id']}_s{subject['id']}_g{target}")

        for day in range(num_days):
            for period in unit_periods:
                key = (classroom["id"], subject["id"], target, day, period)
                no_teacher_lesson[key] = model.NewBoolVar(f"U_c{classroom['id']}_s{subject['id']}_g{target}_d{day}_p{period}")
                model.Add(no_teacher_lesson[key] <= no_teacher_assignment[none_key])

                if period not in allowed_periods:
                    model.Add(no_teacher_lesson[key] == 0)

        unit_key = (classroom["id"], subject["id"], target)
        for teacher in eligible_teachers[unit_key]:
            assignment_key = (classroom["id"], subject["id"], target, teacher["id"])
            assignment[assignment_key] = model.NewBoolVar(f"A_c{classroom['id']}_s{subject['id']}_g{target}_t{teacher['id']}")
            availability = teacher.get("availability", {})

            for day in range(num_days):
                day_availability = availability.get(str(day))
                for period in unit_periods:
                    # Na geração inicial, slots fora da disponibilidade docente
                    # são omitidos, não criados como variáveis travadas em zero.
                    if candidate_periods is None and day_availability is not None:
                        if period >= len(day_availability) or not day_availability[period]:
                            continue

                    key = (classroom["id"], subject["id"], target, teacher["id"], day, period)
                    lesson[key] = model.NewBoolVar(f"Y_c{classroom['id']}_s{subject['id']}_g{target}_t{teacher['id']}_d{day}_p{period}")
                    model.Add(lesson[key] <= assignment[assignment_key])

                    if period not in allowed_periods:
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
        allowed_periods = _get_allowed_periods(classroom)
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for period in allowed_periods:
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

    # Preferência para sincronizar divisões A/B com matérias diferentes.
    # Isso ajuda a manter ambos os grupos ocupados sem duplicar a mesma matéria
    # com um professor que só pode estar em um grupo por vez.
    for classroom in classrooms:
        if (
            not classroom.get("has_groups", False)
            or classroom.get("shift") == "Noite"
        ):
            continue

        subjects = classroom_subjects[classroom["id"]]
        group_a_units = [
            subject for subject in subjects
            if "A" in _targets_for(classroom, subject)
        ]
        group_b_units = [
            subject for subject in subjects
            if "B" in _targets_for(classroom, subject)
        ]
        allowed_periods = _get_allowed_periods(classroom)

        for subject_a in group_a_units:
            for subject_b in group_b_units:
                if subject_a["id"] == subject_b["id"]:
                    continue

                for day in range(num_days):
                    for period in allowed_periods:
                        vars_a = vars_for_unit_at(
                            classroom, subject_a, "A", day, period
                        )
                        vars_b = vars_for_unit_at(
                            classroom, subject_b, "B", day, period
                        )
                        if not vars_a or not vars_b:
                            continue

                        parallel = model.NewBoolVar(
                            f"parallel_groups_c{classroom['id']}_"
                            f"sa{subject_a['id']}_sb{subject_b['id']}_"
                            f"d{day}_p{period}"
                        )
                        occupied_a = sum(vars_a)
                        occupied_b = sum(vars_b)
                        model.Add(parallel <= occupied_a)
                        model.Add(parallel <= occupied_b)
                        model.Add(
                            parallel >= occupied_a + occupied_b - 1
                        )
                        rewards.append(parallel * 1200)

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
            allowed_periods = _get_allowed_periods(classroom)
            for day in range(num_days):
                sum_a = sum(student_occupancy[(classroom["id"], "A", day, p)] for p in allowed_periods if (classroom["id"], "A", day, p) in student_occupancy)
                sum_b = sum(student_occupancy[(classroom["id"], "B", day, p)] for p in allowed_periods if (classroom["id"], "B", day, p) in student_occupancy)
                model.Add(sum_a - sum_b <= 2)
                model.Add(sum_b - sum_a <= 2)

    # MÍNIMO DE 2 AULAS POR TURNO
    for classroom in classrooms:
        allowed_periods = _get_allowed_periods(classroom)
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                for turn_name, turn_periods in TURNS_DEFINITIONS.items():
                    valid_turn_periods = [p for p in turn_periods if p in allowed_periods]
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
        allowed_periods = _get_allowed_periods(classroom)
        allowed_set = set(allowed_periods)
        weekly_workload = int(subject.get("_workload_by_target", {}).get(target, subject["workload"]))

        days_active = []

        for day in range(num_days):
            slot_vars = {}
            for period in allowed_periods:
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

            for i in range(len(allowed_periods) - 2):
                p_a = allowed_periods[i]
                for j in range(i + 1, len(allowed_periods) - 1):
                    p_m = allowed_periods[j]
                    for k in range(j + 1, len(allowed_periods)):
                        p_b = allowed_periods[k]
                        model.Add(slot_vars[p_a] + slot_vars[p_b] - 1 <= slot_vars[p_m])

            if classroom.get("shift") == "Noite":
                # No noturno são válidos blocos de 3, 4 ou 5 aulas.
                # O agrupamento é incentivado por bônus, não limitado a pares.
                model.Add(day_sum <= min(5, len(allowed_periods)))
            elif weekly_workload in (2, 4):
                if pair_vars:
                    model.Add(day_sum == 2 * sum(pair_vars))
                else:
                    model.Add(day_sum == 0)
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
        allowed_periods = _get_allowed_periods(classroom)
        for audience in _audiences_for(classroom):
            for day in range(num_days):
                day_occ = [
                    student_occupancy[(classroom["id"], audience, day, period)]
                    for period in allowed_periods
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

    solver = cp_model.CpSolver()
    # Grades de escola inteira têm milhares de variáveis. Primeiro precisamos
    # obter uma solução válida em vez de gastar todo o tempo provando que ela
    # é ótima; modelos menores continuam buscando o ótimo normalmente.
    solver.parameters.max_time_in_seconds = 60.0
    solver.parameters.num_search_workers = 8
    large_model = len(model.Proto().variables) >= 5000
    if large_model:
        solver.parameters.stop_after_first_solution = True
    status = solver.Solve(model)

    if status == cp_model.INFEASIBLE:
        return {
            "status": "infeasible",
            "message": (
                "O modelo comprovou que esta combinação de cargas e regras é "
                "inviável. Confira as cargas semanais e as jornadas permitidas."
            ),
        }

    if status == cp_model.UNKNOWN:
        return {
            "status": "timeout",
            "message": (
                "O otimizador atingiu o limite de 60 segundos sem encontrar "
                "uma grade viável. Isso não comprova que a grade seja impossível. "
                "Tente gerar por turma ou reduza temporariamente o escopo."
            ),
        }

    if status == cp_model.MODEL_INVALID:
        return {
            "status": "error",
            "message": (
                "O otimizador recusou o modelo por uma inconsistência interna. "
                "Consulte o log do backend."
            ),
        }

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {
            "status": "error",
            "message": f"O otimizador retornou um estado inesperado: {status}.",
        }

    schedule = []
    for classroom, subject, target in units:
        for day in range(num_days):
            for period in range(num_periods):
                no_teacher_key = (classroom["id"], subject["id"], target, day, period)
                if no_teacher_key in no_teacher_lesson and solver.Value(no_teacher_lesson[no_teacher_key]) == 1:
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
                    if lesson_key in lesson and solver.Value(lesson[lesson_key]) == 1:
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
        "solution_status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "schedule": schedule,
        "unstaffed_lessons": sum(item["teacher_id"] is None for item in schedule),
    }