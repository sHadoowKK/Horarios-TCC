import argparse
import time

from app.optimizer import generate_schedule


def full_availability():
    return {
        str(day): [True] * 16
        for day in range(5)
    }


def shift_availability(periods):
    day = [False] * 16

    for period in periods:
        day[period] = True

    return {
        str(day_index): day[:]
        for day_index in range(5)
    }


def default_config():
    return {
        "max_classes_per_day": 9,
        "max_high_complexity_per_day": 10,
        "teacher_gaps_hard": False,
        "min_classes_students": 1,
        "min_classes_teachers": 1,
        "avoid_first_period": False,
        "avoid_last_period": False,
        "avoid_friday": False,
        "max_consec_per_teacher": 2,
        "max_consec_teacher_mode": "ignore",
    }


def subject(subject_id, name, workload=2, complexity="Baixa"):
    return {
        "id": subject_id,
        "name": name,
        "course_ids": [1],
        "workload": workload,
        "complexity": complexity,
        "category": "Ensino Médio",
    }


def classroom(
    classroom_id,
    name,
    shift,
    settings,
    has_groups=False,
):
    return {
        "id": classroom_id,
        "name": name,
        "course_id": 1,
        "shift": shift,
        "has_groups": has_groups,
        "subject_settings": settings,
    }


def teacher(
    teacher_id,
    name,
    allowed_subjects,
    availability,
    score=80,
):
    return {
        "id": teacher_id,
        "name": name,
        "allowed_subjects": allowed_subjects,
        "availability": availability,
        "score": score,
    }


def make_settings(subject_ids, workload=2):
    return [
        {
            "subject_id": subject_id,
            "workload": workload,
            "split": False,
        }
        for subject_id in subject_ids
    ]


def build_scenario(size):
    """
    Cenário sintético para medir carga do solver.

    Não representa a matriz oficial de nenhuma escola. A função existe
    apenas para produzir uma carga repetível de turmas, professores e
    restrições, permitindo comparar desempenho entre versões.
    """
    if size == "small":
        morning_count = 3
        integral_count = 1
        night_count = 1
    elif size == "medium":
        morning_count = 5
        integral_count = 2
        night_count = 2
    elif size == "large":
        morning_count = 8
        integral_count = 3
        night_count = 3
    else:
        raise ValueError("Tamanho inválido")

    subjects = [
        subject(1, "Matemática", 4, "Alta"),
        subject(2, "Português", 4, "Media"),
        subject(3, "História", 2, "Baixa"),
        subject(4, "Física", 2, "Alta"),
        subject(5, "Química", 2, "Alta"),
        subject(6, "Geografia", 2, "Media"),
        subject(7, "Inglês", 2, "Media"),
        subject(8, "Programação", 4, "Alta"),
        subject(9, "Banco de Dados", 3, "Media"),
        subject(10, "Sistemas", 3, "Media"),
        subject(11, "Projeto", 3, "Media"),
        subject(12, "Redes", 3, "Media"),
    ]

    classrooms = []
    classroom_id = 1

    # Turmas da manhã: 18 aulas cada.
    for index in range(morning_count):
        classrooms.append(
            classroom(
                classroom_id,
                f"Manhã {index + 1}",
                "Manhã",
                [
                    {"subject_id": 1, "workload": 4, "split": False},
                    {"subject_id": 2, "workload": 4, "split": False},
                    {"subject_id": 3, "workload": 2, "split": False},
                    {"subject_id": 4, "workload": 2, "split": False},
                    {"subject_id": 5, "workload": 2, "split": False},
                    {"subject_id": 6, "workload": 2, "split": False},
                    {"subject_id": 7, "workload": 2, "split": False},
                ],
            )
        )
        classroom_id += 1

    # Turmas integrais com A/B em duas disciplinas técnicas.
    # Carga física total = 26 aulas, mas os grupos separados geram
    # quatro unidades extras de carga para o solver.
    for index in range(integral_count):
        classrooms.append(
            classroom(
                classroom_id,
                f"Integral {index + 1}",
                "Integral",
                [
                    {"subject_id": 1, "workload": 4, "split": False},
                    {"subject_id": 2, "workload": 4, "split": False},
                    {"subject_id": 3, "workload": 2, "split": False},
                    {"subject_id": 4, "workload": 2, "split": False},
                    {"subject_id": 6, "workload": 2, "split": False},
                    {"subject_id": 7, "workload": 2, "split": False},
                    {"subject_id": 8, "workload": 2, "split": True},
                    {"subject_id": 9, "workload": 2, "split": True},
                    {"subject_id": 10, "workload": 2, "split": False},
                ],
                has_groups=True,
            )
        )
        classroom_id += 1

    # Turmas noturnas: 25 aulas completas.
    for index in range(night_count):
        classrooms.append(
            classroom(
                classroom_id,
                f"Noite {index + 1}",
                "Noite",
                [
                    {"subject_id": 8, "workload": 5, "split": False},
                    {"subject_id": 9, "workload": 5, "split": False},
                    {"subject_id": 10, "workload": 5, "split": False},
                    {"subject_id": 11, "workload": 5, "split": False},
                    {"subject_id": 12, "workload": 5, "split": False},
                ],
            )
        )
        classroom_id += 1

    morning_integral = shift_availability(
        [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    )
    night = shift_availability([11, 12, 13, 14, 15])

    # Professores duplicados por área aumentam as alternativas do solver,
    # mas sem deixar a capacidade semanal apertada demais.
    teachers = [
        teacher(1, "Matemática A", [1], morning_integral, 95),
        teacher(2, "Matemática B", [1], morning_integral, 85),
        teacher(3, "Linguagens A", [2, 7], morning_integral, 95),
        teacher(4, "Linguagens B", [2, 7], morning_integral, 80),
        teacher(5, "Humanas A", [3, 6], morning_integral, 90),
        teacher(6, "Humanas B", [3, 6], morning_integral, 75),
        teacher(7, "Ciências A", [4, 5], morning_integral, 90),
        teacher(8, "Ciências B", [4, 5], morning_integral, 75),
        teacher(9, "Técnica Dia A", [8, 9, 10], morning_integral, 90),
        teacher(10, "Técnica Dia B", [8, 9, 10], morning_integral, 80),
        teacher(11, "Técnica Noite A", [8, 9], night, 95),
        teacher(12, "Técnica Noite B", [10, 11], night, 90),
        teacher(13, "Técnica Noite C", [11, 12], night, 85),
        teacher(14, "Técnica Noite D", [8, 12], night, 80),
    ]

    return classrooms, subjects, teachers


def expected_lesson_count(classrooms):
    total = 0

    for classroom in classrooms:
        for setting in classroom["subject_settings"]:
            multiplier = (
                2
                if classroom.get("has_groups")
                and setting.get("split")
                else 1
            )
            total += setting["workload"] * multiplier

    return total


def main():
    parser = argparse.ArgumentParser(
        description="Benchmark sintético do solver do Anatinus."
    )
    parser.add_argument(
        "--size",
        choices=["small", "medium", "large"],
        default="medium",
        help="Tamanho do cenário sintético.",
    )
    args = parser.parse_args()

    classrooms, subjects, teachers = build_scenario(args.size)
    expected = expected_lesson_count(classrooms)

    print("Benchmark sintético do Anatinus")
    print(f"Cenário: {args.size}")
    print(f"Turmas: {len(classrooms)}")
    print(f"Disciplinas no catálogo: {len(subjects)}")
    print(f"Professores: {len(teachers)}")
    print(f"Aulas/unidades esperadas: {expected}")
    print("Executando solver...")

    started = time.perf_counter()

    result = generate_schedule(
        classrooms,
        subjects,
        teachers,
        default_config(),
    )

    wall_time = time.perf_counter() - started

    print()
    print(f"Status: {result['status']}")
    print(f"Tempo total medido: {wall_time:.3f}s")

    if result["status"] != "success":
        print(f"Mensagem: {result.get('message', 'sem mensagem')}")
        print(f"Tempo do solver: {result.get('solve_time_seconds', 0):.3f}s")
        print(
            "Tempo de busca por viabilidade: "
            f"{result.get('feasibility_time_seconds', 0):.3f}s"
        )
        print(
            "Tempo de otimização: "
            f"{result.get('optimization_time_seconds', 0):.3f}s"
        )
        print(f"Variáveis do modelo: {result.get('model_variables', 'n/d')}")
        print(f"Restrições do modelo: {result.get('model_constraints', 'n/d')}")
        print(f"Ramificações: {result.get('solver_branches', 'n/d')}")
        print(f"Conflitos: {result.get('solver_conflicts', 'n/d')}")
        return

    print(
        "Estado da solução: "
        f"{result.get('solution_status', 'desconhecido')}"
    )
    print(
        "Tempo informado pelo solver: "
        f"{result.get('solve_time_seconds', 0):.3f}s"
    )
    print(
        "Variáveis do modelo: "
        f"{result.get('model_variables', 'n/d')}"
    )
    print(
        "Restrições do modelo: "
        f"{result.get('model_constraints', 'n/d')}"
    )
    print(
        "Objetivo: "
        f"{result.get('objective_value', 'n/d')}"
    )
    print(
        "Melhor limite do objetivo: "
        f"{result.get('best_objective_bound', 'n/d')}"
    )
    print(f"Aulas geradas: {len(result['schedule'])}")
    print(
        "Aulas sem professor: "
        f"{result.get('unstaffed_lessons', 0)}"
    )

    if len(result["schedule"]) != expected:
        print(
            "AVISO: quantidade gerada difere da quantidade esperada."
        )


if __name__ == "__main__":
    main()
