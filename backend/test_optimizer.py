import unittest

from app.optimizer import generate_schedule


def default_config():
    return {
        "max_classes_per_day": 9,
        "max_consecutive_classes": 5,
        "max_high_complexity_per_day": 5,
        "student_gaps_hard": True,
        "teacher_gaps_hard": False,
        "min_classes_students": 1,
        "min_classes_teachers": 1,
        "avoid_first_period": False,
        "avoid_last_period": False,
        "avoid_friday": False,
        "max_consec_per_teacher": 2,
        "max_consec_teacher_mode": "hard",
    }


def full_availability():
    return {str(day): [True] * 16 for day in range(5)}


class OptimizerTests(unittest.TestCase):
    def test_generates_basic_morning_schedule(self):
        classrooms = [
            {
                "id": 1,
                "name": "1A",
                "course_id": 1,
                "shift": "Manhã",
                "has_groups": False,
            }
        ]
        subjects = [
            {
                "id": 1,
                "name": "Matemática",
                "course_ids": [1],
                "workload": 2,
                "complexity": "Alta",
                "category": "Ensino Médio",
            }
        ]
        teachers = [
            {
                "id": 1,
                "name": "Professor",
                "allowed_subjects": [1],
                "availability": full_availability(),
                "score": 50,
            }
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
            all(item["period"] in range(0, 6) for item in result["schedule"])
        )
        self.assertTrue(
            all(item["student_group"] == "Todos" for item in result["schedule"])
        )

    def test_respects_teacher_unavailability(self):
        availability = {
            str(day): [False] * 16
            for day in range(5)
        }
        availability["0"][0] = True

        classrooms = [
            {
                "id": 1,
                "name": "1A",
                "course_id": 1,
                "shift": "Manhã",
                "has_groups": False,
            }
        ]
        subjects = [
            {
                "id": 1,
                "name": "Matemática",
                "course_ids": [1],
                "workload": 1,
                "complexity": "Baixa",
                "category": "Ensino Médio",
            }
        ]
        teachers = [
            {
                "id": 1,
                "name": "Professor",
                "allowed_subjects": [1],
                "availability": availability,
                "score": 0,
            }
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["schedule"][0]["day"], 0)
        self.assertEqual(result["schedule"][0]["period"], 0)

    def test_integral_does_not_use_morning_sixth_period_or_night(self):
        classrooms = [
            {
                "id": 1,
                "name": "Integral",
                "course_id": 1,
                "shift": "Integral",
                "has_groups": False,
            }
        ]
        subjects = [
            {
                "id": 1,
                "name": "Matemática",
                "course_ids": [1],
                "workload": 6,
                "complexity": "Baixa",
                "category": "Ensino Médio",
            }
        ]
        teachers = [
            {
                "id": 1,
                "name": "Professor",
                "allowed_subjects": [1],
                "availability": full_availability(),
                "score": 0,
            }
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        allowed = {0, 1, 2, 3, 4, 6, 7, 8, 9, 10}
        self.assertTrue(
            all(item["period"] in allowed for item in result["schedule"])
        )
        self.assertNotIn(
            5,
            [item["period"] for item in result["schedule"]],
        )

    def test_split_classroom_duplicates_technical_workload_by_group(self):
        classrooms = [
            {
                "id": 1,
                "name": "3º INFO",
                "course_id": 1,
                "shift": "Integral",
                "has_groups": True,
            }
        ]
        subjects = [
            {
                "id": 1,
                "name": "Matemática",
                "course_ids": [1],
                "workload": 1,
                "complexity": "Baixa",
                "category": "Ensino Médio",
            },
            {
                "id": 2,
                "name": "UDA",
                "course_ids": [1],
                "workload": 2,
                "complexity": "Baixa",
                "category": "Técnica",
            },
        ]
        teachers = [
            {
                "id": 1,
                "name": "Professor Geral",
                "allowed_subjects": [1],
                "availability": full_availability(),
                "score": 50,
            },
            {
                "id": 2,
                "name": "Professor Técnico 1",
                "allowed_subjects": [2],
                "availability": full_availability(),
                "score": 50,
            },
            {
                "id": 3,
                "name": "Professor Técnico 2",
                "allowed_subjects": [2],
                "availability": full_availability(),
                "score": 50,
            },
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")

        general = [
            item
            for item in result["schedule"]
            if item["subject_id"] == 1
        ]
        technical = [
            item
            for item in result["schedule"]
            if item["subject_id"] == 2
        ]

        self.assertEqual(len(general), 1)
        self.assertEqual(general[0]["student_group"], "Todos")

        group_a = [
            item
            for item in technical
            if item["student_group"] == "A"
        ]
        group_b = [
            item
            for item in technical
            if item["student_group"] == "B"
        ]

        self.assertEqual(len(group_a), 2)
        self.assertEqual(len(group_b), 2)

    def test_groups_can_have_technical_classes_at_same_time(self):
        availability = {
            str(day): [False] * 16
            for day in range(5)
        }
        availability["0"][0] = True

        classrooms = [
            {
                "id": 1,
                "name": "3º INFO",
                "course_id": 1,
                "shift": "Manhã",
                "has_groups": True,
            }
        ]
        subjects = [
            {
                "id": 1,
                "name": "UDA",
                "course_ids": [1],
                "workload": 1,
                "complexity": "Baixa",
                "category": "Técnica",
            }
        ]
        teachers = [
            {
                "id": 1,
                "name": "Professor A",
                "allowed_subjects": [1],
                "availability": availability,
                "score": 50,
            },
            {
                "id": 2,
                "name": "Professor B",
                "allowed_subjects": [1],
                "availability": availability,
                "score": 50,
            },
        ]

        result = generate_schedule(
            classrooms,
            subjects,
            teachers,
            default_config(),
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["schedule"]), 2)

        self.assertEqual(
            {item["student_group"] for item in result["schedule"]},
            {"A", "B"},
        )
        self.assertTrue(
            all(
                item["day"] == 0 and item["period"] == 0
                for item in result["schedule"]
            )
        )


if __name__ == "__main__":
    unittest.main()
