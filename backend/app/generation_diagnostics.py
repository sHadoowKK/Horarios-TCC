from collections import defaultdict

from .optimizer import get_allowed_periods


def _unit_key(item):
    return (
        item.get("classroom_id"),
        item.get("subject_id"),
        item.get("student_group") or "Todos",
    )


def _available_period_count(teacher, allowed_periods, num_days=5):
    availability = teacher.get("availability") or {}
    count = 0

    for day in range(num_days):
        day_availability = availability.get(str(day))
        for period in allowed_periods:
            # O otimizador interpreta dias sem configuração como disponibilidade
            # aberta. Mantemos a mesma regra neste diagnóstico.
            if day_availability is None:
                count += 1
            elif (
                isinstance(day_availability, (list, tuple))
                and period < len(day_availability)
                and bool(day_availability[period])
            ):
                count += 1

    return count


def build_unstaffed_diagnostics(
    classrooms,
    subjects,
    teachers,
    schedule,
    fixed_schedule=None,
    teacher_assignment_fallback=False,
):
    """Explica por que as unidades que ficaram sem docente não receberam professor.

    A análise usa as mesmas regras de disponibilidade e habilitação do otimizador.
    Ela identifica causas comprováveis e sinaliza explicitamente quando o conflito
    depende da combinação global de turmas/regras e não pode ser isolado com certeza.
    """
    classroom_by_id = {item["id"]: item for item in classrooms}
    subject_by_id = {item["id"]: item for item in subjects}
    teacher_by_subject = defaultdict(list)

    for teacher in teachers:
        for subject_id in teacher.get("allowed_subjects") or []:
            teacher_by_subject[subject_id].append(teacher)

    unstaffed_by_unit = defaultdict(int)
    for item in schedule or []:
        if item.get("teacher_id") is None:
            unstaffed_by_unit[_unit_key(item)] += 1

    fixed_unstaffed_units = {
        _unit_key(item)
        for item in (fixed_schedule or [])
        if item.get("teacher_id") is None
    }

    diagnostics = []
    for key, lesson_count in sorted(unstaffed_by_unit.items()):
        classroom_id, subject_id, student_group = key
        classroom = classroom_by_id.get(classroom_id, {})
        subject = subject_by_id.get(subject_id, {})
        classroom_name = classroom.get("name", f"Turma {classroom_id}")
        subject_name = subject.get("name", f"Disciplina {subject_id}")

        diagnostic = {
            "classroom_id": classroom_id,
            "subject_id": subject_id,
            "student_group": student_group,
            "lessons": lesson_count,
            "teachers": [],
        }

        if key in fixed_unstaffed_units:
            diagnostic.update({
                "reason_code": "preserved_unstaffed",
                "message": (
                    "Uma aula desta matéria já estava fixada ou foi preservada "
                    "sem professor. Para respeitar esse horário, o modelo manteve "
                    "a carga da unidade sem docente nesta geração."
                ),
            })
            diagnostics.append(diagnostic)
            continue

        eligible = teacher_by_subject.get(subject_id, [])
        if not eligible:
            diagnostic.update({
                "reason_code": "no_qualified_teacher",
                "message": (
                    f"Nenhum professor está habilitado para {subject_name}. "
                    "Cadastre um docente ou marque essa disciplina na lista de "
                    "matérias que algum professor pode lecionar."
                ),
            })
            diagnostics.append(diagnostic)
            continue

        allowed_periods = get_allowed_periods(classroom)
        availability_rows = [
            {
                "teacher_id": teacher.get("id"),
                "name": teacher.get("name", "Professor sem nome"),
                "available_periods": _available_period_count(
                    teacher,
                    allowed_periods,
                ),
            }
            for teacher in eligible
        ]
        availability_rows.sort(
            key=lambda item: (-item["available_periods"], item["name"])
        )
        diagnostic["teachers"] = availability_rows
        best_teacher = availability_rows[0]
        best_count = best_teacher["available_periods"]

        if best_count == 0:
            names = ", ".join(item["name"] for item in availability_rows)
            diagnostic.update({
                "reason_code": "no_available_periods",
                "message": (
                    f"Há professor(es) habilitado(s) para {subject_name}, mas "
                    f"nenhum tem períodos disponíveis no turno de {classroom_name}. "
                    f"Confira a disponibilidade cadastrada: {names}."
                ),
            })
        elif best_count < lesson_count:
            diagnostic.update({
                "reason_code": "insufficient_availability",
                "message": (
                    f"A carga exige {lesson_count} aulas semanais, mas o professor "
                    f"habilitado com mais janelas marcadas como disponíveis "
                    f"({best_teacher['name']}) tem apenas {best_count} na jornada "
                    f"de {classroom_name}. Revise a disponibilidade cadastrada "
                    "ou habilite outro docente."
                ),
            })
        elif teacher_assignment_fallback:
            diagnostic.update({
                "reason_code": "teacher_search_timeout",
                "message": (
                    f"O otimizador atingiu o limite interno de busca enquanto "
                    f"tentava distribuir professores para {lesson_count} aulas "
                    f"de {subject_name}. A grade da turma foi mantida, mas a "
                    "atribuição docente não foi concluída. Isso não comprova "
                    "que os professores sejam incompatíveis ou estejam sem "
                    "horários; tente gerar turmas menores ou revisar a carga "
                    "de processamento. Os períodos abaixo são apenas os que "
                    "estão marcados como disponíveis no cadastro."
                ),
            })
        else:
            diagnostic.update({
                "reason_code": "global_constraints",
                "message": (
                    f"O cadastro mostra {best_count} períodos marcados como "
                    f"disponíveis para os professores habilitados para {lesson_count} "
                    f"aulas de {subject_name} na jornada de {classroom_name}, mas "
                    "isso não garante que esses horários estejam livres após "
                    "considerar as demais turmas e regras. O conflito pode envolver "
                    "choque com outras aulas, limite diário, descanso entre jornadas "
                    "ou outras regras. A análise não isolou uma causa única; "
                    "confira também os horários dos professores listados abaixo."
                ),
            })

        diagnostics.append(diagnostic)

    return diagnostics
