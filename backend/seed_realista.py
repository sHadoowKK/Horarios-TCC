"""Cria uma base separada e repetível para demonstrar o Anatinus.

Executar de dentro de backend:
    python seed_realista.py

Este script recria SOMENTE backend/school_schedule_demo.db.
Nunca apaga nem altera school_schedule.db, que é o banco normal do usuário.

O 3º INFO usa os nomes e exemplos A/B extraídos das imagens; as cargas não
documentadas integralmente são estimativas de teste. O TI Noturno usa as cargas
semanais anotadas na conversa e totaliza 25. O recorte Agro inclui seis turmas
com nomes reais, mas os dois componentes conhecidos só são cargas provisórias.
"""

import os
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name("school_schedule_demo.db")
os.environ["ANATINUS_DATABASE_URL"] = f"sqlite:///{DATABASE_PATH.as_posix()}"

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine, ensure_database_compatibility  # noqa: E402


# Índices de períodos da ETEC; intervalos/almoço não são aulas.
INTEGRAL_PERIODS = (0, 1, 2, 3, 4, 6, 7, 8, 9, 10)
NIGHT_PERIODS = (11, 12, 13, 14, 15)


def make_availability(shifts, available_days=range(5)):
    allowed = set()
    for shift in shifts:
        allowed.update(
            INTEGRAL_PERIODS if shift == "Integral"
            else NIGHT_PERIODS if shift == "Noite"
            else range(6)
        )

    return {
        str(day): [period in allowed and day in available_days for period in range(16)]
        for day in range(5)
    }


def main():
    print("Preparando banco DEMO independente...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ensure_database_compatibility()

    db = SessionLocal()
    try:
        info_course = models.Course(name="Informática")
        night_course = models.Course(name="TI — curso noturno")
        agro_course = models.Course(name="Agropecuária")
        db.add_all([info_course, night_course, agro_course])
        db.flush()

        # As cargas do 3º INFO são provisórias: somam 50 por grupo.
        # O Integral dispõe de 55 períodos semanais (11 por dia), com almoço após 12:30.
        info_subjects = [
            ("UDA", 3, "Alta", "Técnica", True, "Erika"),
            ("SW2", 3, "Media", "Técnica", True, "Marcel"),
            ("CNW2", 3, "Media", "Técnica", True, "Célia"),
            ("Filosofia", 2, "Baixa", "Ensino Médio", False, "M. Emília"),
            ("Sociologia", 2, "Baixa", "Ensino Médio", False, "Célia"),
            ("Espanhol", 2, "Baixa", "Ensino Médio", False, "Fabiane"),
            ("História", 2, "Baixa", "Ensino Médio", False, "M. Emília"),
            ("DDM2", 3, "Alta", "Técnica", True, "Marcel"),
            ("IRS", 3, "Media", "Técnica", True, "Joesley"),
            ("Matemática", 4, "Alta", "Ensino Médio", False, "Kamila"),
            ("Inglês", 3, "Baixa", "Ensino Médio", False, "Gustavo"),
            ("EAMT", 3, "Media", "Técnica", True, "Fabiane"),
            ("Português", 4, "Baixa", "Ensino Médio", False, "Marta"),
            ("EACNT", 3, "Media", "Técnica", True, "Gustavo"),
            ("PDTCC", 4, "Media", "Técnica", True, "Marcel"),
            ("GCW", 4, "Media", "Técnica", True, "Higor"),
            ("Geografia", 2, "Baixa", "Ensino Médio", False, "Thiago"),
        ]

        # O noturno de TI foi extraído do horário conversado: 25 aulas/semana.
        ti_subjects = [
            ("SBD", 5, "Alta", "Camila"),
            ("PTCC", 3, "Media", "Marcel"),
            ("PC2", 5, "Alta", "Marcel"),
            ("RDS", 5, "Media", "Higor"),
            ("GSO2", 3, "Media", "Augusto"),
            ("SI", 2, "Media", "Leonardo"),
            ("DSE", 2, "Media", "Augusto"),
        ]

        subject_by_name = {}
        info_settings = []
        info_teacher_assignments = {}
        for name, workload, complexity, category, split, teacher_name in info_subjects:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category=category,
                course_ids=[info_course.id],
            )
            db.add(subject)
            db.flush()
            subject_by_name[name] = subject
            info_settings.append({
                "subject_id": subject.id,
                "workload": workload,
                "split": split,
            })
            info_teacher_assignments.setdefault(teacher_name, []).append(subject.id)

        night_settings = []
        for name, workload, complexity, teacher_name in ti_subjects:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category="Técnica",
                course_ids=[night_course.id],
            )
            db.add(subject)
            db.flush()
            subject_by_name[name] = subject
            night_settings.append({
                "subject_id": subject.id,
                "workload": workload,
                "split": False,
            })
            info_teacher_assignments.setdefault(teacher_name, []).append(subject.id)

        agro_settings = []
        agro_subject_specs = [
            ("M.R.N", 2, "Media", "Gilson"),
            ("P.T.I.C", 2, "Media", "Joesley"),
        ]
        for name, workload, complexity, teacher_name in agro_subject_specs:
            subject = models.Subject(
                name=name,
                workload=workload,
                complexity=complexity,
                category="Técnica",
                course_ids=[agro_course.id],
            )
            db.add(subject)
            db.flush()
            subject_by_name[name] = subject
            agro_settings.append({
                "subject_id": subject.id,
                "workload": workload,
                "split": True,
            })
            info_teacher_assignments.setdefault(teacher_name, []).append(subject.id)

        # Foram confirmadas seis turmas Agro com divisão interna A/B.
        # Só M.R.N e P.T.I.C ficaram identificadas no recorte extraído;
        # as cargas 2+2 abaixo são provisórias e não devem ser tratadas como
        # carga oficial completa dos cursos. Aulas/salas físicas ficam fora do sistema.
        agro_class_names = [
            "1º PI AGRO A",
            "1º PI AGRO B",
            "2º PI AGRO A",
            "2º PI AGRO B",
            "3º PI AGRO A",
            "3º PI AGRO B",
        ]

        classrooms = [
            models.Classroom(
                name="3º INFO",
                shift="Integral",
                course_id=info_course.id,
                has_groups=True,
                subject_settings=info_settings,
                split_subject_ids=[],
            ),
            models.Classroom(
                name="TI — Noite",
                shift="Noite",
                course_id=night_course.id,
                has_groups=False,
                subject_settings=night_settings,
                split_subject_ids=[],
            ),
        ]
        classrooms.extend(
            models.Classroom(
                name=name,
                shift="Integral",
                course_id=agro_course.id,
                has_groups=True,
                subject_settings=agro_settings,
                split_subject_ids=[],
            )
            for name in agro_class_names
        )
        db.add_all(classrooms)

        # Nomes mantidos conforme os exemplos da imagem/conversa.
        # Disponibilidades distintas são de demonstração, não um registro
        # confirmado da escala real de cada docente.
        teacher_specs = {
            "Erika": ("Integral", [0, 1, 2, 3], 90),
            "Marcel": ("Integral+Noite", [0, 1, 2, 3, 4], 95),
            "M. Emília": ("Integral", [0, 1, 2, 3, 4], 85),
            "Célia": ("Integral", [0, 1, 2, 3, 4], 80),
            "Joesley": ("Integral", [0, 1, 2, 4], 80),
            "Kamila": ("Integral", [0, 1, 2, 3, 4], 90),
            "Marta": ("Integral", [0, 1, 2, 3, 4], 85),
            "Gustavo": ("Integral", [0, 1, 2, 3], 80),
            "Fabiane": ("Integral", [0, 1, 2, 3, 4], 80),
            "Higor": ("Integral+Noite", [0, 1, 2, 3, 4], 95),
            "Thiago": ("Integral", [0, 1, 2, 3, 4], 85),
            "Gilson": ("Integral", [0, 1, 2, 3], 90),
            "Camila": ("Noite", [0, 1, 2, 3, 4], 85),
            "Augusto": ("Noite", [0, 1, 2, 3, 4], 90),
            "Leonardo": ("Noite", [0, 1, 2, 3, 4], 85),
        }

        for name, subject_ids in info_teacher_assignments.items():
            shifts, days, score = teacher_specs[name]
            shift_names = shifts.split("+")
            db.add(models.Teacher(
                name=name,
                allowed_subjects=sorted(set(subject_ids)),
                availability=make_availability(shift_names, days),
                score=score,
            ))

        db.add(models.SystemConfig(
            max_classes_per_day=9,
            max_consecutive_classes=6,
            max_high_complexity_per_day=2,
            student_gaps_hard=True,
            teacher_gaps_hard=False,
            min_classes_students=2,
            min_classes_teachers=2,
            avoid_first_period=False,
            avoid_last_period=False,
            avoid_friday=False,
            max_consec_per_teacher=2,
            max_consec_teacher_mode="ignore",
        ))
        db.commit()

        info_total = sum(item[1] for item in info_subjects)
        night_total = sum(item[1] for item in ti_subjects)
        agro_total_per_group = sum(item[1] for item in agro_subject_specs)
        if info_total != 50 or night_total != 25 or agro_total_per_group != 4:
            raise RuntimeError(
                f"Cargas inesperadas: 3º INFO={info_total}, TI noite={night_total}"
            )

        print("Base realista criada com sucesso.")
        print(f"Banco: {DATABASE_PATH}")
        print(f"Cursos: {db.query(models.Course).count()} (Informática, TI e Agropecuária)")
        print(f"Turmas: {db.query(models.Classroom).count()} (3º INFO, TI Noite e seis Agro)")
        print(f"Disciplinas: {db.query(models.Subject).count()} (17 INFO + 7 TI + 2 Agro)")
        print(f"Professores: {db.query(models.Teacher).count()}")
        print("Carga anotada: 25 períodos semanais na TI Noite.")
        print("Cargas provisórias: distribuição do 3º INFO e 2 componentes Agro por turma.")
        print("Disponibilidades docentes também são estimativas para teste.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
