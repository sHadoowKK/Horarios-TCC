import unittest

from app.optimizer import generate_schedule


class OptimizerTests(unittest.TestCase):
    def test_generates_basic_schedule(self):
        classrooms = [{"id": 1, "name": "1A", "course_id": 1, "shift": "Manhã"}]
        subjects = [{"id": 1, "name": "Matemática", "course_ids": [1], "workload": 2, "complexity": "Alta"}]
        teachers = [{
            "id": 1,
            "name": "Professor",
            "allowed_subjects": [1],
            "availability": {str(d): [True] * 15 for d in range(5)},
            "score": 50,
        }]
        config = {
            "max_classes_per_day": 5,
            "max_consecutive_classes": 5,
            "max_high_complexity_per_day": 2,
            "student_gaps_hard": True,
            "teacher_gaps_hard": False,
            "min_classes_students": 1,
            "min_classes_teachers": 1,
            "avoid_edges": False,
            "avoid_friday": False,
            "max_consec_per_teacher": 2,
            "max_consec_teacher_mode": "hard",
        }

        result = generate_schedule(classrooms, subjects, teachers, config)
        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["schedule"]), 2)
        self.assertTrue(all(item["period"] < 5 for item in result["schedule"]))

    def test_respects_teacher_unavailability(self):
        availability = {str(d): [False] * 15 for d in range(5)}
        availability["0"][0] = True
        classrooms = [{"id": 1, "name": "1A", "course_id": 1, "shift": "Manhã"}]
        subjects = [{"id": 1, "name": "Matemática", "course_ids": [1], "workload": 1, "complexity": "Baixa"}]
        teachers = [{"id": 1, "name": "Professor", "allowed_subjects": [1], "availability": availability, "score": 0}]
        config = {
            "max_classes_per_day": 5,
            "max_consecutive_classes": 5,
            "max_high_complexity_per_day": 5,
            "student_gaps_hard": True,
            "teacher_gaps_hard": False,
            "min_classes_students": 1,
            "min_classes_teachers": 1,
            "avoid_edges": False,
            "avoid_friday": False,
            "max_consec_per_teacher": 2,
            "max_consec_teacher_mode": "hard",
        }

        result = generate_schedule(classrooms, subjects, teachers, config)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["schedule"][0]["day"], 0)
        self.assertEqual(result["schedule"][0]["period"], 0)


if __name__ == "__main__":
    unittest.main()
