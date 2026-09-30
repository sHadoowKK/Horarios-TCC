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


if __name__ == "__main__":
    unittest.main()
