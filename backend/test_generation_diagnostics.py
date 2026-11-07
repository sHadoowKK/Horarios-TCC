import unittest

from app.generation_diagnostics import build_unstaffed_diagnostics


def classroom():
    return {
        "id": 1,
        "name": "1º DS",
        "shift": "Manhã",
        "allowed_periods": [0, 1],
    }


def subject():
    return {"id": 10, "name": "Matemática"}


def teacher(teacher_id=5, availability=None):
    return {
        "id": teacher_id,
        "name": f"Professor {teacher_id}",
        "allowed_subjects": [10],
        "availability": availability or {
            str(day): [True] * 16
            for day in range(5)
        },
    }


def unstaffed_schedule(lessons=3):
    return [
        {
            "classroom_id": 1,
            "subject_id": 10,
            "student_group": "Todos",
            "teacher_id": None,
            "day": 0,
            "period": index % 2,
        }
        for index in range(lessons)
    ]


class GenerationDiagnosticsTests(unittest.TestCase):
    def diagnose(self, teachers, schedule=None, fixed_schedule=None):
        return build_unstaffed_diagnostics(
            [classroom()],
            [subject()],
            teachers,
            schedule if schedule is not None else unstaffed_schedule(),
            fixed_schedule=fixed_schedule,
        )[0]

    def test_reports_subject_without_qualified_teacher(self):
        result = self.diagnose([])

        self.assertEqual(result["reason_code"], "no_qualified_teacher")
        self.assertIn("Nenhum professor está habilitado", result["message"])

    def test_reports_qualified_teachers_without_available_periods(self):
        availability = {
            str(day): [False] * 16
            for day in range(5)
        }
        result = self.diagnose([teacher(availability=availability)])

        self.assertEqual(result["reason_code"], "no_available_periods")
        self.assertEqual(result["teachers"][0]["available_periods"], 0)

    def test_reports_weekly_availability_below_required_workload(self):
        availability = {
            str(day): [False] * 16
            for day in range(5)
        }
        availability["0"][0] = True
        availability["1"][0] = True
        result = self.diagnose([teacher(availability=availability)])

        self.assertEqual(result["reason_code"], "insufficient_availability")
        self.assertIn("apenas 2 períodos livres", result["message"])

    def test_reports_global_constraints_without_claiming_a_unique_cause(self):
        result = self.diagnose([teacher()])

        self.assertEqual(result["reason_code"], "global_constraints")
        self.assertIn("não isolou uma causa única", result["message"])

    def test_reports_fixed_unstaffed_lesson_as_preserved(self):
        fixed = unstaffed_schedule(1)
        result = self.diagnose(
            [teacher()],
            fixed_schedule=fixed,
        )

        self.assertEqual(result["reason_code"], "preserved_unstaffed")
        self.assertIn("fixada ou foi preservada", result["message"])


if __name__ == "__main__":
    unittest.main()
