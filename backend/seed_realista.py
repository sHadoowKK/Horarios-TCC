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

import argparse
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


def main(only_informatica=False):
    print("Preparando banco DEMO independente...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ensure_database_compatibility()

    db = SessionLocal()
    try:
        info_course = models.Course(name="Informática")
        night_course = None
        agro_course = None
        db.add(info_course)

        if not only_informatica:
            night_course = models.Course(name="TI — curso noturno")
            agro_course = models.Course(name="Agropecuária")
            db.add_all([night_course, agro_course])

        db.flush()

        # Cargas transcritas do quadro original do 3º INFO Integral.
        # São 37 aulas por aluno/semana no recorte da grade de referência.
        # Almoço: 11:40–13:00. Nenhuma aula do Integral é alocada nesse intervalo.
        info_subjects = [
            ("UDA", 2, "Alta", "Técnica", True, "Erika"),
            ("SW2", 3, "Media", "Técnica", True, "Marcel"),
            ("CNW2", 2, "Media", "Técnica", True, "Erika"),
            ("Filosofia", 1, "Baixa", "Ensino Médio", False, "M. Emília"),
            ("Sociologia", 1, "Baixa", "Ensino Médio", False, "M. Emília"),
            ("Espanhol", 2, "Baixa", "Ensino Médio", False, "Célia"),
            ("História", 2, "Baixa", "Ensino Médio", False, "M. Emília"),
            ("DDM2", 2, "Alta", "Técnica", True, "Marcel"),
            ("IRS", 2, "Media", "Técnica", True, "Joesley"),
            ("Matemática", 3, "Alta", "Ensino Médio", False, "Kamila"),
            ("Inglês", 2, "Baixa", "Ensino Médio", False, "Marta"),
            ("EAMT", 3, "Media", "Técnica", True, "Gustavo"),
            ("Português", 3, "Baixa", "Ensino Médio", False, "Marta"),
            ("EACNT", 3, "Media", "Técnica", True, "Fabiane"),
            ("PDTCC", 2, "Media", "Técnica", True, "Marcel"),
            ("GCW", 2, "Media", "Técnica", True, "Higor"),
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

        # O quadro mostra SW2 com 3 aulas no grupo A e 2 no grupo B.
        for setting in info_settings:
            if setting["subject_id"] == subject_by_name["SW2"].id:
                setting["workload_a"] = 3
                setting["workload_b"] = 2

        # SW2 e CNW2 aparecem com professores diferentes entre os grupos A/B.
        info_teacher_assignments.setdefault("Higor", []).append(
            subject_by_name["SW2"].id
        )
        info_teacher_assignments.setdefault("Marcel", []).append(
            subject_by_name["CNW2"].id
        )

        night_settings = []
        if not only_informatica:
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
        agro_class_names = []

        if not only_informatica:
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

            # Seis turmas Agro confirmadas na referência; matriz parcial é provisória.
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
                preferred_subject_sequences=[[
                    subject_by_name["Filosofia"].id,
                    subject_by_name["Sociologia"].id,
                ]],
                split_subject_ids=[],
            ),
        ]
        if not only_informatica:
            classrooms.append(models.Classroom(
                name="TI — Noite",
                shift="Noite",
                course_id=night_course.id,
                has_groups=False,
                subject_settings=night_settings,
                split_subject_ids=[],
            ))
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
            # No modo isolado de Informática, não inventamos dias bloqueados:
            # a disponibilidade oficial individual não ficou preservada nas imagens.
            # Liberamos o Integral de segunda a sexta para testar matéria/professor
            # e a preferência por aulas em pares sem restrições arbitrárias.
            if only_informatica:
                days = list(range(5))
                shift_names = ["Integral"]
                score = teacher_specs[name][2]
            else:
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
        info_total_a = sum(
            int(setting.get("workload_a") or setting["workload"])
            if setting.get("split") else setting["workload"]
            for setting in info_settings
        )
        info_total_b = sum(
            int(setting.get("workload_b") or setting["workload"])
            if setting.get("split") else setting["workload"]
            for setting in info_settings
        )
        night_total = sum(item[1] for item in ti_subjects)
        agro_total_per_group = sum(item[1] for item in agro_subject_specs) if not only_informatica else 0
        if info_total != 37 or (info_total_a, info_total_b) != (37, 36):
            raise RuntimeError(
                f"Cargas inesperadas no 3º INFO: padrão={info_total}, "
                f"grupo A={info_total_a}, grupo B={info_total_b}"
            )
        if not only_informatica and (night_total != 25 or agro_total_per_group != 4):
            raise RuntimeError(
                f"Cargas inesperadas: TI noite={night_total}, Agro={agro_total_per_group}"
            )

        print("Base de demonstração criada com sucesso.")
        print(f"Banco: {DATABASE_PATH}")
        print(f"Cursos: {db.query(models.Course).count()}")
        print(f"Turmas: {db.query(models.Classroom).count()}")
        print(f"Disciplinas: {db.query(models.Subject).count()}")
        print(f"Professores: {db.query(models.Teacher).count()}")
        print("Turma de referência: 3º INFO Integral, com A/B.")
        print(f"Cargas do quadro do 3º INFO: grupo A={info_total_a}, grupo B={info_total_b} aulas/semana.")
        print("Matérias técnicas separadas por grupo; matérias do Ensino Médio compartilhadas.")
        print("Preferência cadastrada: Filosofia seguida de Sociologia.")
        print("SW2 e CNW2 permitem os professores vistos nos grupos A/B.")
        print("Disponibilidades docentes oficiais não constam no quadro; permanecem provisórias.")
        if not only_informatica:
            print("Turmas adicionais: TI Noite + seis turmas Agro.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cria uma base de demonstração isolada do Anatinus."
    )
    parser.add_argument(
        "--informatica-only",
        action="store_true",
        help="cria somente a turma de referência 3º INFO e seus professores/matérias",
    )
    arguments = parser.parse_args()
    main(only_informatica=arguments.informatica_only)
