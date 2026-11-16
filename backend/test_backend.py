import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main, models


def full_availability():
    return {
        str(day): [True] * 16
        for day in range(5)
    }


class BackendIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        Session = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
        )
        self.db = Session()

    def tearDown(self):
        self.db.close()
        models.Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def _basic_school(
        self,
        workload=2,
        complexity="Baixa",
        with_teacher=True,
    ):
        course = models.Course(name="Curso")
        self.db.add(course)
        self.db.flush()

        subject = models.Subject(
            name="Matemática",
            workload=min(workload, 25),
            complexity=complexity,
            category="Ensino Médio",
            course_ids=[course.id],
        )
        self.db.add(subject)
        self.db.flush()

        classroom = models.Classroom(
            name="1º A",
            shift="Manhã",
            course_id=course.id,
            has_groups=False,
            subject_settings=[
                {
                    "subject_id": subject.id,
                    "workload": workload,
                    "split": False,
                }
            ],
            split_subject_ids=[],
        )
        self.db.add(classroom)

        teacher = None
        if with_teacher:
            teacher = models.Teacher(
                name="Professor",
                allowed_subjects=[subject.id],
                availability=full_availability(),
                score=100,
            )
            self.db.add(teacher)

        self.db.commit()

        if teacher is not None:
            self.db.refresh(teacher)

        self.db.refresh(course)
        self.db.refresh(subject)
        self.db.refresh(classroom)

        return course, subject, classroom, teacher

    def test_generate_also_saves_latest_timetable(self):
        _, subject, classroom, teacher = self._basic_school(
            workload=2,
        )

        result = main.generate_timetable(db=self.db)

        self.assertEqual(result["status"], "success")
        self.assertEqual(len(result["schedule"]), 2)

        saved = self.db.query(models.TimetableItem).all()

        self.assertEqual(len(saved), 2)
        self.assertTrue(
            all(
                item.classroom_id == classroom.id
                for item in saved
            )
        )
        self.assertTrue(
            all(
                item.subject_id == subject.id
                for item in saved
            )
        )
        self.assertTrue(
            all(
                item.teacher_id == teacher.id
                for item in saved
            )
        )

    def test_new_generation_replaces_previous_saved_timetable(self):
        _, _, _, _ = self._basic_school(workload=2)

        self.db.add(
            models.TimetableItem(
                classroom_id=999,
                subject_id=999,
                teacher_id=None,
                day=4,
                period=15,
                student_group="Todos",
            )
        )
        self.db.commit()

        result = main.generate_timetable(db=self.db)

        self.assertEqual(result["status"], "success")

        saved = self.db.query(models.TimetableItem).all()
        self.assertEqual(len(saved), 2)
        self.assertTrue(
            all(item.classroom_id != 999 for item in saved)
        )

    def test_delete_teacher_preserves_schedule_as_unstaffed(self):
        _, subject, classroom, teacher = self._basic_school(
            workload=1,
        )

        self.db.add(
            models.TimetableItem(
                classroom_id=classroom.id,
                subject_id=subject.id,
                teacher_id=teacher.id,
                day=0,
                period=0,
                student_group="Todos",
            )
        )
        self.db.commit()

        main.delete_teacher(
            teacher_id=teacher.id,
            db=self.db,
        )

        saved = self.db.query(models.TimetableItem).one()

        self.assertIsNone(saved.teacher_id)
        self.assertIsNone(
            self.db.query(models.Teacher)
            .filter(models.Teacher.id == teacher.id)
            .first()
        )

    def test_preflight_rejects_weekly_workload_above_capacity(self):
        self._basic_school(
            workload=31,
            with_teacher=False,
        )

        with self.assertRaises(HTTPException) as context:
            main.generate_timetable(db=self.db)

        self.assertEqual(
            context.exception.status_code,
            400,
        )
        self.assertIn(
            "31 aulas semanais",
            context.exception.detail,
        )
        self.assertIn(
            "30 períodos disponíveis",
            context.exception.detail,
        )


    def test_subject_can_regenerate_across_every_class_that_uses_it(self):
        course, math, first_class, math_teacher = self._basic_school(
            workload=2,
        )
        history = models.Subject(
            name="História",
            workload=2,
            complexity="Baixa",
            category="Ensino Médio",
            course_ids=[course.id],
        )
        self.db.add(history)
        self.db.flush()

        first_class.subject_settings = [
            *first_class.subject_settings,
            {
                "subject_id": history.id,
                "workload": 2,
                "split": False,
            },
        ]
        second_class = models.Classroom(
            name="2º A",
            shift="Manhã",
            course_id=course.id,
            has_groups=False,
            subject_settings=[
                {"subject_id": math.id, "workload": 2, "split": False},
                {"subject_id": history.id, "workload": 2, "split": False},
            ],
            split_subject_ids=[],
        )
        history_teacher = models.Teacher(
            name="Professor de História",
            allowed_subjects=[history.id],
            availability=full_availability(),
            score=100,
        )
        self.db.add_all([second_class, history_teacher])
        self.db.commit()
        self.db.refresh(first_class)
        self.db.refresh(second_class)

        original = main.generate_timetable(db=self.db)
        self.assertEqual(original["status"], "success")

        original_history = sorted(
            (
                row["classroom_id"],
                row["teacher_id"],
                row["day"],
                row["period"],
                row["student_group"],
            )
            for row in original["schedule"]
            if row["subject_id"] == history.id
        )
        request = main.schemas.TimetableGenerationRequest(
            scope="subject_all",
            subject_id=math.id,
        )
        regenerated = main.generate_timetable(db=self.db, payload=request)
        self.assertEqual(regenerated["status"], "success")
        self.assertIn("2 turma(s)", regenerated["message"])

        regenerated_history = sorted(
            (
                row["classroom_id"],
                row["teacher_id"],
                row["day"],
                row["period"],
                row["student_group"],
            )
            for row in regenerated["schedule"]
            if row["subject_id"] == history.id
        )
        self.assertEqual(regenerated_history, original_history)
        self.assertEqual(
            sum(row["subject_id"] == math.id for row in regenerated["schedule"]),
            4,
        )


    def test_preflight_uses_configured_period_capacity(self):
        self._basic_school(workload=6, with_teacher=False)
        classroom = self.db.query(models.Classroom).first()
        classroom.allowed_periods = [0]
        self.db.commit()

        with self.assertRaises(HTTPException) as context:
            main.generate_timetable(db=self.db)

        self.assertEqual(context.exception.status_code, 400)
        self.assertIn("apenas 5 períodos disponíveis", context.exception.detail)

    def test_night_class_cannot_keep_internal_groups_or_split_loads(self):
        course, subject, classroom, _ = self._basic_school(
            workload=2,
            with_teacher=False,
        )
        classroom.has_groups = True
        classroom.subject_settings = [{
            "subject_id": subject.id,
            "workload": 2,
            "workload_a": 1,
            "workload_b": 1,
            "joint_workload": 2,
            "split": True,
        }]
        self.db.commit()

        payload = main.schemas.ClassroomCreate(
            name=classroom.name,
            shift="Noite",
            allowed_periods=[11, 12, 13, 14, 15],
            course_id=course.id,
            has_groups=True,
            subject_settings=[{
                "subject_id": subject.id,
                "workload": 2,
                "workload_a": 1,
                "workload_b": 1,
                "joint_workload": 2,
                "split": True,
            }],
            split_subject_ids=[subject.id],
        )
        updated = main.update_classroom(
            classroom_id=classroom.id,
            data=payload,
            db=self.db,
        )

        self.assertFalse(updated.has_groups)
        self.assertEqual(updated.allowed_periods, [11, 12, 13, 14, 15])
        setting = updated.subject_settings[0]
        self.assertEqual(setting["workload"], 3)
        self.assertFalse(setting["split"])
        self.assertNotIn("workload_a", setting)
        self.assertNotIn("workload_b", setting)
        self.assertNotIn("joint_workload", setting)

if __name__ == "__main__":
    unittest.main()
