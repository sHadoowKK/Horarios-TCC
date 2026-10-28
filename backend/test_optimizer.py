import unittest

from app.optimizer import generate_schedule


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


def full_availability():
    return {
        str(day): [True] * 16
        for day in range(5)
    }


def empty_availability():
    return {
        str(day): [False] * 16
        for day in range(5)
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


def subject(
    subject_id,
    name,
    workload=1,
    complexity="Baixa",
):
    return {
        "id": subject_id,
        "name": name,
        "course_ids": [1],
        "workload": workload,
        "complexity": complexity,
        "category": "Ensino Médio",
    }


def teacher(
    teacher_id,
    allowed_subjects,
    availability=None,
    score=50,
):
    return {
        "id": teacher_id,
        "name": f"Professor {teacher_id}",
        "allowed_subjects": allowed_subjects,
        "availability": (
            availability
            if availability is not None
            else full_availability()
        ),
        "score": score,
    }


class OptimizerTests(unittest.TestCase):
    def test_classroom_uses_only_selected_subjects(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    }
                ],
            )
        ]

        subjects = [
            subject(1, "Matemática"),
            subject(2, "História"),
        ]

        teachers = [
            teacher(1, [1, 2]),
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["schedule"]), 2)
        self.assertTrue(
            all(
                item["subject_id"] == 1
                for item in result["schedule"]
            )
        )

    def test_can_generate_subject_without_teacher(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    }
                ],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Física")],
            [],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["schedule"]), 2)
        self.assertTrue(
            all(
                item["teacher_id"] is None
                for item in result["schedule"]
            )
        )
        self.assertEqual(
            result["unstaffed_lessons"],
            2,
        )

    def test_prefers_available_teacher_over_unstaffed(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    }
                ],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Matemática")],
            [teacher(1, [1], score=80)],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertTrue(
            all(
                item["teacher_id"] == 1
                for item in result["schedule"]
            )
        )
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )

    def test_split_is_configured_per_classroom_subject(self):
        classrooms = [
            classroom(
                1,
                "3º INFO",
                "Integral",
                [
                    {
                        "subject_id": 1,
                        "workload": 1,
                        "split": True,
                    },
                    {
                        "subject_id": 2,
                        "workload": 1,
                        "split": False,
                    },
                ],
                has_groups=True,
            )
        ]

        subjects = [
            subject(1, "Espanhol"),
            subject(2, "Matemática"),
        ]

        teachers = [
            teacher(1, [1]),
            teacher(2, [1]),
            teacher(3, [2]),
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        split_items = [
            item
            for item in result["schedule"]
            if item["subject_id"] == 1
        ]
        joint_items = [
            item
            for item in result["schedule"]
            if item["subject_id"] == 2
        ]

        self.assertEqual(
            {
                item["student_group"]
                for item in split_items
            },
            {"A", "B"},
        )
        self.assertEqual(len(split_items), 2)

        self.assertEqual(len(joint_items), 1)
        self.assertEqual(
            joint_items[0]["student_group"],
            "Todos",
        )

    def test_exact_eleven_hour_rest_allows_11h20(self):
        availability = empty_availability()
        availability["0"][11] = True  # seg 19:00-19:50
        availability["1"][0] = True   # ter 07:10-08:00

        classrooms = [
            classroom(
                1,
                "Noite",
                "Noite",
                [{
                    "subject_id": 1,
                    "workload": 1,
                    "split": False,
                }],
            ),
            classroom(
                2,
                "Manhã",
                "Manhã",
                [{
                    "subject_id": 2,
                    "workload": 1,
                    "split": False,
                }],
            ),
        ]

        result = generate_schedule(
            classrooms,
            [
                subject(1, "Noturna"),
                subject(2, "Matutina"),
            ],
            [
                teacher(
                    1,
                    [1, 2],
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )

    def test_exact_eleven_hour_rest_blocks_10h40(self):
        availability = empty_availability()
        availability["0"][12] = True  # seg 19:50-20:30
        availability["1"][0] = True   # ter 07:10-08:00

        classrooms = [
            classroom(
                1,
                "Noite",
                "Noite",
                [{
                    "subject_id": 1,
                    "workload": 1,
                    "split": False,
                }],
            ),
            classroom(
                2,
                "Manhã",
                "Manhã",
                [{
                    "subject_id": 2,
                    "workload": 1,
                    "split": False,
                }],
            ),
        ]

        result = generate_schedule(
            classrooms,
            [
                subject(1, "Noturna"),
                subject(2, "Matutina"),
            ],
            [
                teacher(
                    1,
                    [1, 2],
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            1,
        )

    def test_seventh_class_requires_one_hour_break(self):
        availability = empty_availability()

        for period in range(7):
            availability["0"][period] = True

        classrooms = []

        for index in range(6):
            classrooms.append(
                classroom(
                    index + 1,
                    f"Manhã {index + 1}",
                    "Manhã",
                    [{
                        "subject_id": index + 1,
                        "workload": 1,
                        "split": False,
                    }],
                )
            )

        classrooms.append(
            classroom(
                7,
                "Integral",
                "Integral",
                [{
                    "subject_id": 7,
                    "workload": 1,
                    "split": False,
                }],
            )
        )

        subjects = [
            subject(i, f"Disciplina {i}")
            for i in range(1, 8)
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            [
                teacher(
                    1,
                    list(range(1, 8)),
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertGreaterEqual(
            result["unstaffed_lessons"],
            1,
        )

    def test_seventh_class_is_allowed_after_one_hour_break(self):
        availability = empty_availability()

        # Seis aulas durante o dia e uma à noite. Entre 17:20 e 19:00
        # há 1h40 de descanso, portanto a sétima aula deve ser permitida.
        for period in [0, 1, 2, 3, 4, 5, 11]:
            availability["0"][period] = True

        classrooms = [
            classroom(
                index,
                f"Turma {index}",
                "Noite" if index == 7 else "Manhã",
                [{
                    "subject_id": index,
                    "workload": 1,
                    "split": False,
                }],
            )
            for index in range(1, 8)
        ]

        subjects = [
            subject(index, f"Disciplina {index}")
            for index in range(1, 8)
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            [
                teacher(
                    1,
                    list(range(1, 8)),
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )
        self.assertEqual(
            sum(
                item["teacher_id"] == 1
                for item in result["schedule"]
            ),
            7,
        )


    def test_maximum_nine_classes_per_day_is_hard(self):
        availability = empty_availability()

        for period in [0, 1, 2, 3, 4, 6, 7, 8, 9, 10]:
            availability["0"][period] = True

        classrooms = [
            classroom(
                i,
                f"Integral {i}",
                "Integral",
                [{
                    "subject_id": i,
                    "workload": 1,
                    "split": False,
                }],
            )
            for i in range(1, 11)
        ]

        subjects = [
            subject(i, f"Disciplina {i}")
            for i in range(1, 11)
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            [
                teacher(
                    1,
                    list(range(1, 11)),
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            sum(
                item["teacher_id"] == 1
                for item in result["schedule"]
            ),
            9,
        )
        self.assertEqual(
            result["unstaffed_lessons"],
            1,
        )

    def test_realistic_five_class_block_same_teacher_is_allowed(self):
        availability = empty_availability()

        for period in [11, 12, 13, 14, 15]:
            availability["0"][period] = True

        classrooms = [
            classroom(
                1,
                "TI Noite",
                "Noite",
                [{
                    "subject_id": 1,
                    "workload": 5,
                    "split": False,
                }],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "PC2")],
            [
                teacher(
                    1,
                    [1],
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )
        self.assertEqual(len(result["schedule"]), 5)
        self.assertTrue(
            all(
                item["teacher_id"] == 1
                for item in result["schedule"]
            )
        )


    def test_small_school_multiple_classrooms_and_shared_teachers(self):
        """
        Cenário integrado de uma pequena escola.

        Três turmas possuem matérias ministradas por professores que
        também trabalham nas outras turmas. O teste verifica a geração
        conjunta da semana, sem choque de professor ou de turma.
        """
        classrooms = [
            classroom(
                1,
                "1º A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 2,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 3,
                        "workload": 2,
                        "split": False,
                    },
                ],
            ),
            classroom(
                2,
                "2º A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 4,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 3,
                        "workload": 2,
                        "split": False,
                    },
                ],
            ),
            classroom(
                3,
                "3º A",
                "Manhã",
                [
                    {
                        "subject_id": 1,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 2,
                        "workload": 2,
                        "split": False,
                    },
                    {
                        "subject_id": 3,
                        "workload": 2,
                        "split": False,
                    },
                ],
            ),
        ]

        subjects = [
            subject(1, "Matemática", workload=2),
            subject(2, "Português", workload=2),
            subject(3, "História", workload=2),
            subject(4, "Física", workload=2),
        ]

        # Os professores são compartilhados pelas três turmas.
        teachers = [
            teacher(1, [1], score=100),
            teacher(2, [2, 4], score=100),
            teacher(3, [3], score=100),
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )

        # Cada turma possui 6 aulas semanais.
        self.assertEqual(
            len(result["schedule"]),
            18,
        )

        lessons_by_classroom = {
            1: 0,
            2: 0,
            3: 0,
        }

        teacher_slots = {
            1: set(),
            2: set(),
            3: set(),
        }

        classroom_slots = {
            1: set(),
            2: set(),
            3: set(),
        }

        for item in result["schedule"]:
            classroom_id = item["classroom_id"]
            teacher_id = item["teacher_id"]
            slot = (
                item["day"],
                item["period"],
            )

            lessons_by_classroom[
                classroom_id
            ] += 1

            # Nenhuma turma pode receber duas aulas no mesmo horário.
            self.assertNotIn(
                slot,
                classroom_slots[classroom_id],
            )
            classroom_slots[
                classroom_id
            ].add(slot)

            # Nenhum professor pode estar em duas turmas simultaneamente.
            self.assertIsNotNone(teacher_id)
            self.assertNotIn(
                slot,
                teacher_slots[teacher_id],
            )
            teacher_slots[
                teacher_id
            ].add(slot)

        self.assertEqual(
            lessons_by_classroom,
            {
                1: 6,
                2: 6,
                3: 6,
            },
        )

        # Cargas compartilhadas dos professores.
        self.assertEqual(
            len(teacher_slots[1]),
            6,
        )
        self.assertEqual(
            len(teacher_slots[2]),
            6,
        )
        self.assertEqual(
            len(teacher_slots[3]),
            6,
        )


    def test_two_classrooms_compete_for_same_teacher_without_conflict(self):
        """
        Duas turmas diferentes disputam o mesmo professor.

        O professor possui quatro períodos disponíveis na segunda-feira
        e precisa cumprir duas aulas em cada turma. O solver deve usar
        os quatro períodos sem colocar o docente em duas turmas ao mesmo
        tempo.
        """
        availability = empty_availability()

        for period in [0, 1, 2, 3]:
            availability["0"][period] = True

        classrooms = [
            classroom(
                1,
                "1º A",
                "Manhã",
                [{
                    "subject_id": 1,
                    "workload": 2,
                    "split": False,
                }],
            ),
            classroom(
                2,
                "2º A",
                "Manhã",
                [{
                    "subject_id": 2,
                    "workload": 2,
                    "split": False,
                }],
            ),
        ]

        subjects = [
            subject(1, "Matemática 1", workload=2),
            subject(2, "Matemática 2", workload=2),
        ]

        teachers = [
            teacher(
                1,
                [1, 2],
                availability,
                score=100,
            )
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )
        self.assertEqual(
            len(result["schedule"]),
            4,
        )

        teacher_slots = [
            (
                item["day"],
                item["period"],
            )
            for item in result["schedule"]
            if item["teacher_id"] == 1
        ]

        # O mesmo professor nunca pode aparecer em duas turmas
        # no mesmo dia/período.
        self.assertEqual(
            len(teacher_slots),
            len(set(teacher_slots)),
        )

        # Como só existe disponibilidade nesses quatro horários,
        # todos eles precisam ser utilizados.
        self.assertEqual(
            set(teacher_slots),
            {
                (0, 0),
                (0, 1),
                (0, 2),
                (0, 3),
            },
        )

        lessons_by_classroom = {
            1: 0,
            2: 0,
        }

        for item in result["schedule"]:
            lessons_by_classroom[
                item["classroom_id"]
            ] += 1

        self.assertEqual(
            lessons_by_classroom,
            {
                1: 2,
                2: 2,
            },
        )


    def test_integral_groups_can_have_different_subjects_at_same_time(self):
        """
        Cenário estrutural inspirado no 3º INFO Integral.

        A turma possui grupos A/B. UDA e SW2 são separadas, enquanto
        Matemática é conjunta. Como existe apenas um professor para UDA
        e um para SW2, os grupos precisam poder cursar matérias diferentes
        simultaneamente em pelo menos parte da grade.
        """
        classrooms = [
            classroom(
                1,
                "3º INFO",
                "Integral",
                [
                    {
                        "subject_id": 1,
                        "workload": 1,
                        "split": True,
                    },
                    {
                        "subject_id": 2,
                        "workload": 1,
                        "split": True,
                    },
                    {
                        "subject_id": 3,
                        "workload": 2,
                        "split": False,
                    },
                ],
                has_groups=True,
            )
        ]

        subjects = [
            subject(1, "UDA", workload=1),
            subject(2, "SW2", workload=1),
            subject(3, "Matemática", workload=2),
        ]

        teachers = [
            teacher(1, [1], score=100),
            teacher(2, [2], score=100),
            teacher(3, [3], score=100),
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )

        # UDA e SW2 geram uma aula para A e uma para B.
        # Matemática conjunta gera apenas duas aulas para "Todos".
        split_items = [
            item
            for item in result["schedule"]
            if item["subject_id"] in (1, 2)
        ]
        joint_items = [
            item
            for item in result["schedule"]
            if item["subject_id"] == 3
        ]

        self.assertEqual(len(split_items), 4)
        self.assertEqual(len(joint_items), 2)
        self.assertTrue(
            all(
                item["student_group"] in ("A", "B")
                for item in split_items
            )
        )
        self.assertTrue(
            all(
                item["student_group"] == "Todos"
                for item in joint_items
            )
        )

        # Como há um único professor por disciplina separada,
        # A e B não podem fazer a mesma matéria separada simultaneamente.
        for subject_id in (1, 2):
            by_slot = {}

            for item in split_items:
                if item["subject_id"] != subject_id:
                    continue

                slot = (
                    item["day"],
                    item["period"],
                )
                by_slot.setdefault(slot, []).append(
                    item["student_group"]
                )

            self.assertTrue(
                all(
                    len(groups) == 1
                    for groups in by_slot.values()
                )
            )

        # Deve existir ao menos um horário em que A e B estejam ocupados
        # simultaneamente com matérias separadas diferentes.
        split_by_slot = {}

        for item in split_items:
            slot = (
                item["day"],
                item["period"],
            )
            split_by_slot.setdefault(
                slot,
                {},
            )[item["student_group"]] = item["subject_id"]

        simultaneous_different = any(
            slot_items.get("A")
            and slot_items.get("B")
            and slot_items["A"] != slot_items["B"]
            for slot_items in split_by_slot.values()
        )

        self.assertTrue(simultaneous_different)


    def test_real_night_class_complete_week_25_lessons(self):
        """
        Cenário baseado em uma grade noturna real usada no projeto.

        Cargas semanais:
        SBD 5, SI 2, PTCC 3, DSE 2, PC2 5, RDS 5, GSO2 3.
        Total: 25 aulas, exatamente a capacidade semanal do noturno.
        """
        settings = [
            {
                "subject_id": 1,
                "workload": 5,
                "split": False,
            },
            {
                "subject_id": 2,
                "workload": 2,
                "split": False,
            },
            {
                "subject_id": 3,
                "workload": 3,
                "split": False,
            },
            {
                "subject_id": 4,
                "workload": 2,
                "split": False,
            },
            {
                "subject_id": 5,
                "workload": 5,
                "split": False,
            },
            {
                "subject_id": 6,
                "workload": 5,
                "split": False,
            },
            {
                "subject_id": 7,
                "workload": 3,
                "split": False,
            },
        ]

        classrooms = [
            classroom(
                1,
                "TI Noite Completa",
                "Noite",
                settings,
            )
        ]

        subjects = [
            subject(1, "SBD", workload=5),
            subject(2, "SI", workload=2),
            subject(3, "PTCC", workload=3),
            subject(4, "DSE", workload=2),
            subject(5, "PC2", workload=5),
            subject(6, "RDS", workload=5),
            subject(7, "GSO2", workload=3),
        ]

        # Professores correspondem às combinações observadas na grade real:
        # 1 -> SBD
        # 2 -> SI
        # 3 -> PTCC + PC2
        # 4 -> DSE + GSO2
        # 5 -> RDS
        teachers = [
            teacher(1, [1], score=100),
            teacher(2, [2], score=100),
            teacher(3, [3, 5], score=100),
            teacher(4, [4, 7], score=100),
            teacher(5, [6], score=100),
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )
        self.assertEqual(
            len(result["schedule"]),
            25,
        )

        # Uma turma noturna de 25 aulas deve ocupar os 5 períodos
        # dos 5 dias da semana.
        lessons_by_day = {
            day: 0
            for day in range(5)
        }

        lessons_by_subject = {
            subject_id: 0
            for subject_id in range(1, 8)
        }

        for item in result["schedule"]:
            self.assertIn(
                item["period"],
                [11, 12, 13, 14, 15],
            )

            lessons_by_day[item["day"]] += 1
            lessons_by_subject[
                item["subject_id"]
            ] += 1

        self.assertEqual(
            list(lessons_by_day.values()),
            [5, 5, 5, 5, 5],
        )

        self.assertEqual(
            lessons_by_subject,
            {
                1: 5,
                2: 2,
                3: 3,
                4: 2,
                5: 5,
                6: 5,
                7: 3,
            },
        )


    def test_daytime_workload_four_prefers_two_plus_two(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [{
                    "subject_id": 1,
                    "workload": 4,
                    "split": False,
                }],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Português")],
            [teacher(1, [1], score=100)],
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        counts_by_day = {}
        for item in result["schedule"]:
            counts_by_day[item["day"]] = (
                counts_by_day.get(item["day"], 0) + 1
            )

        active_counts = sorted(counts_by_day.values())
        self.assertEqual(active_counts, [2, 2])

    def test_daytime_workload_four_prefers_two_consecutive_pairs(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [{"subject_id": 1, "workload": 4, "split": False}],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Português", workload=4)],
            [teacher(1, [1], score=100)],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        periods_by_day = {}
        for item in result["schedule"]:
            periods_by_day.setdefault(item["day"], []).append(item["period"])

        self.assertEqual(sorted(len(periods) for periods in periods_by_day.values()), [2, 2])
        contiguous_pairs = {(0, 1), (1, 2), (3, 4), (4, 5), (6, 7), (8, 9), (9, 10)}
        for periods in periods_by_day.values():
            self.assertEqual(len(periods), 2)
            self.assertIn(tuple(sorted(periods)), contiguous_pairs)

    def test_daytime_workload_three_prefers_two_plus_one(self):
        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [{
                    "subject_id": 1,
                    "workload": 3,
                    "split": False,
                }],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Português")],
            [teacher(1, [1], score=100)],
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        counts_by_day = {}
        for item in result["schedule"]:
            counts_by_day[item["day"]] = (
                counts_by_day.get(item["day"], 0) + 1
            )

        active_counts = sorted(counts_by_day.values())
        self.assertEqual(active_counts, [1, 2])

    def test_night_workload_three_can_form_triple_block(self):
        classrooms = [
            classroom(
                1,
                "Módulo 1",
                "Noite",
                [{
                    "subject_id": 1,
                    "workload": 3,
                    "split": False,
                }],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Banco de Dados")],
            [teacher(1, [1], score=100)],
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        counts_by_day = {}
        for item in result["schedule"]:
            counts_by_day[item["day"]] = (
                counts_by_day.get(item["day"], 0) + 1
            )

        self.assertEqual(
            max(counts_by_day.values()),
            3,
        )

    def test_daytime_three_same_day_still_possible_if_needed(self):
        availability = empty_availability()
        availability["0"][0] = True
        availability["0"][1] = True
        availability["0"][2] = True

        classrooms = [
            classroom(
                1,
                "1A",
                "Manhã",
                [{
                    "subject_id": 1,
                    "workload": 3,
                    "split": False,
                }],
            )
        ]

        result = generate_schedule(
            classrooms,
            [subject(1, "Português")],
            [
                teacher(
                    1,
                    [1],
                    availability,
                    score=100,
                )
            ],
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(
            result["unstaffed_lessons"],
            0,
        )
        self.assertEqual(
            len(result["schedule"]),
            3,
        )


if __name__ == "__main__":
    unittest.main()
