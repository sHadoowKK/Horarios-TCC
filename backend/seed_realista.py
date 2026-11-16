"""Base realista do Anatinus, transcrita da planilha escolar de 03/09/2026.

Uso (a partir de backend/):
    python seed_realista.py                 # diurno + noturno técnico
    python seed_realista.py --diurno-only
    python seed_realista.py --noturno-only
    python seed_realista.py --informatica-only

O script recria SOMENTE school_schedule_demo.db. Nunca altera school_schedule.db.
As células mescladas do quadro representam aula conjunta; colunas A/B não
mescladas representam cargas independentes dos grupos. Os nomes dos docentes
são anonimizados. A planilha contém os horários existentes, não a disponibilidade
semanal completa: por isso a disponibilidade criada aqui é ampla e sintética.

Os dois quadros MTEC (18h30) e as aulas síncronas mensais são preservados como
referência documental, mas não entram no solver semanal: a jornada 18h30 e os
eventos em datas específicas ainda não são representados pelo modelo atual.
"""

import argparse
import os
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

DATABASE_PATH = Path(__file__).resolve().with_name("school_schedule_demo.db")
os.environ["ANATINUS_DATABASE_URL"] = f"sqlite:///{DATABASE_PATH.as_posix()}"

from app import models  # noqa: E402
from app.database import Base, SessionLocal, engine, ensure_database_compatibility  # noqa: E402


# Linhas: turma | disciplina | aulas conjuntas | aulas A | aulas B
MATRIX_ROWS = r"""
1º PI AGRO A|A.P.P.|0|2|2
1º PI AGRO A|ARTE|2|0|0
1º PI AGRO A|BIOLOGIA|2|0|0
1º PI AGRO A|C.P.R.T|1|0|0
1º PI AGRO A|COOP|1|0|0
1º PI AGRO A|EDUCAÇÃO FÍSICA|2|0|0
1º PI AGRO A|FILOSOFIA|1|0|0
1º PI AGRO A|FÍSICA|2|0|0
1º PI AGRO A|GEOGRAFIA|2|0|0
1º PI AGRO A|HISTÓRIA|2|0|0
1º PI AGRO A|INGLÊS|2|0|0
1º PI AGRO A|LÍNGUA PORTUGUESA|3|0|0
1º PI AGRO A|M.R.N|0|2|2
1º PI AGRO A|MATEMÁTICA|3|0|0
1º PI AGRO A|O.V /|0|2|2
1º PI AGRO A|P.P.A|0|2|2
1º PI AGRO A|P.T.I.C|0|2|2
1º PI AGRO A|QUÍMICA|2|0|0
1º PI AGRO A|SOCIOLOGIA|1|0|0
1º PI AGRO B|A.P.P|0|2|2
1º PI AGRO B|ARTE|2|0|0
1º PI AGRO B|BIOLOGIA|2|0|0
1º PI AGRO B|C.P.R.T|1|0|0
1º PI AGRO B|COOP|1|0|0
1º PI AGRO B|EDUCAÇÃO FÍSICA|2|0|0
1º PI AGRO B|FILOSOFIA|1|0|0
1º PI AGRO B|FÍSICA|2|0|0
1º PI AGRO B|GEOGRAFIA|2|0|0
1º PI AGRO B|HISTÓRIA|2|0|0
1º PI AGRO B|INGLÊS|2|0|0
1º PI AGRO B|LÍNGUA PORTUGUESA|3|0|0
1º PI AGRO B|M.R.N|0|2|2
1º PI AGRO B|MATEMÁTICA|3|0|0
1º PI AGRO B|O.V /|0|2|2
1º PI AGRO B|P.P.A A|0|2|2
1º PI AGRO B|P.T.I.C|0|2|2
1º PI AGRO B|QUÍMICA|2|0|0
1º PI AGRO B|SOCIOLOGIA|1|0|0
2º PI AGRO A|BIOLOGIA|2|0|0
2º PI AGRO A|C.A|0|2|2
2º PI AGRO A|C.P.D.P.J.|1|0|0
2º PI AGRO A|E.A.C.N.T|0|0|1
2º PI AGRO A|E.A.M.T|0|2|1
2º PI AGRO A|EDUCAÇÃO FÍSICA|2|0|0
2º PI AGRO A|FÍSICA|2|0|0
2º PI AGRO A|GEOGRAFIA|2|0|0
2º PI AGRO A|HISTÓRIA|2|0|0
2º PI AGRO A|INGLÊS|2|0|0
2º PI AGRO A|L.M.I.S|2|0|0
2º PI AGRO A|L.P.C|2|0|0
2º PI AGRO A|L.R.T|0|2|2
2º PI AGRO A|LÍNGUA PORTUGUESA|3|0|0
2º PI AGRO A|MATEMÁTICA|3|0|0
2º PI AGRO A|N.A.A.N|0|2|2
2º PI AGRO A|N.V|1|0|0
2º PI AGRO A|P.P.A|0|2|2
2º PI AGRO A|QUÍMICA|2|0|0
2º PI AGRO B|BIOLOGIA|2|0|0
2º PI AGRO B|C.A|0|2|2
2º PI AGRO B|CPDPI|1|0|0
2º PI AGRO B|E.A.C.N.T|0|1|1
2º PI AGRO B|E.A.M.T|0|1|1
2º PI AGRO B|EDUCAÇÃO FÍSICA|2|0|0
2º PI AGRO B|FÍSICA|2|0|0
2º PI AGRO B|GEOGRAFIA|2|0|0
2º PI AGRO B|HISTÓRIA|2|0|0
2º PI AGRO B|INGLÊS|2|0|0
2º PI AGRO B|L.M.I.S|2|0|0
2º PI AGRO B|L.P.C|2|0|0
2º PI AGRO B|L.R.T|0|2|2
2º PI AGRO B|LÍNGUA PORTUGUESA|3|0|0
2º PI AGRO B|MATEMÁTICA|3|0|0
2º PI AGRO B|N.A.A.M|0|2|2
2º PI AGRO B|N.V|1|0|0
2º PI AGRO B|P.P.A|0|2|2
2º PI AGRO B|QUÍMICA|2|0|0
3º PI AGRO A|A.R|2|0|0
3º PI AGRO A|A.S|1|0|0
3º PI AGRO A|A.S,|1|0|0
3º PI AGRO A|C.P.|2|0|0
3º PI AGRO A|E.A.C.M.T|2|0|0
3º PI AGRO A|E.A.C.N.T|3|0|0
3º PI AGRO A|E.A.M.T|1|0|0
3º PI AGRO A|E.O.E.T.R|1|0|0
3º PI AGRO A|EDUCAÇÃO FÍSICA|2|0|0
3º PI AGRO A|ESPANHOL|2|0|0
3º PI AGRO A|FILOSOFIA|1|0|0
3º PI AGRO A|FÍSICA|2|0|0
3º PI AGRO A|G.P.A|1|0|0
3º PI AGRO A|INGLÊS|2|0|0
3º PI AGRO A|LÍNGUA PORTUGUESA|3|0|0
3º PI AGRO A|M.I.A|2|0|0
3º PI AGRO A|MATEMÁTICA|3|0|0
3º PI AGRO A|P.D.T.C.C|2|0|0
3º PI AGRO A|S.A.B.E.A|2|0|0
3º PI AGRO A|SOCIOLOGIA|1|0|0
3º PI AGRO B|A.R|2|0|0
3º PI AGRO B|A.S|2|0|0
3º PI AGRO B|E.A.C.N.T|3|0|0
3º PI AGRO B|E.A.M.T|3|0|0
3º PI AGRO B|E.O.E.T.R|1|0|0
3º PI AGRO B|EDUCAÇÃO FÍSICA|2|0|0
3º PI AGRO B|ESPANHOL|2|0|0
3º PI AGRO B|FILOSOFIA|1|0|0
3º PI AGRO B|FÍSICA|2|0|0
3º PI AGRO B|G.P.A.|1|0|0
3º PI AGRO B|INGLÊS|2|0|0
3º PI AGRO B|LÍNGUA PORTUGUESA|3|0|0
3º PI AGRO B|M.I.A|2|0|0
3º PI AGRO B|MATEMÁTICA|3|0|0
3º PI AGRO B|P.C.|2|0|0
3º PI AGRO B|P.D.T.C.C|2|0|0
3º PI AGRO B|S.A.B.E.A|2|0|0
3º PI AGRO B|SOCIOLOGIA|1|0|0
3º INFORMÁTICA|CNW2|0|2|2
3º INFORMÁTICA|DDM2|0|2|2
3º INFORMÁTICA|E.A.M.T|3|0|0
3º INFORMÁTICA|EACNT|3|0|0
3º INFORMÁTICA|ESPANHOL|2|0|0
3º INFORMÁTICA|FILOSOFIA|1|0|0
3º INFORMÁTICA|GCW|0|2|2
3º INFORMÁTICA|GEOGRAFIA|2|0|0
3º INFORMÁTICA|HISTÓRIA|2|0|0
3º INFORMÁTICA|INGLÊS|2|0|0
3º INFORMÁTICA|IR|0|2|2
3º INFORMÁTICA|LÍNGUA PORTUGUESA|3|0|0
3º INFORMÁTICA|MATEMÁTICA|3|0|0
3º INFORMÁTICA|PDTCC|0|2|2
3º INFORMÁTICA|SOCIOLOGIA|1|0|0
3º INFORMÁTICA|SW2|0|2|2
3º INFORMÁTICA|UDA|0|2|2
1º ITINERÁRIO|A.C.P.S.|0|3|3
1º ITINERÁRIO|ARTE|2|0|0
1º ITINERÁRIO|BIOLOGIA|2|0|0
1º ITINERÁRIO|EDUCAÇÃO FÍSICA|2|0|0
1º ITINERÁRIO|FILOSOFIA|1|0|0
1º ITINERÁRIO|FÍSICA|2|0|0
1º ITINERÁRIO|GEOGRAFIA|2|0|0
1º ITINERÁRIO|HISTÓRIA|2|0|0
1º ITINERÁRIO|INGLÊS|1|0|0
1º ITINERÁRIO|LÍNGUA PORTUGUESA|4|0|0
1º ITINERÁRIO|MATEMÁTICA|3|0|0
1º ITINERÁRIO|P.T.I.C.|0|3|3
1º ITINERÁRIO|QUÍMICA|2|0|0
1º ITINERÁRIO|SOCIOLOGIA|1|0|0
2º ITINERÁRIO|BIOLOGIA|2|0|0
2º ITINERÁRIO|E.A.|0|6|6
2º ITINERÁRIO|EDUCAÇÃO FÍSICA|2|0|0
2º ITINERÁRIO|FÍSICA|2|0|0
2º ITINERÁRIO|GEOGRAFIA|2|0|0
2º ITINERÁRIO|HISTÓRIA|2|0|0
2º ITINERÁRIO|INGLÊS|2|0|0
2º ITINERÁRIO|L.P.C|0|5|5
2º ITINERÁRIO|LÍNGUA PORTUGUESA|2|0|0
2º ITINERÁRIO|MATEMÁTICA|2|0|0
2º ITINERÁRIO|P.E.|0|1|1
2º ITINERÁRIO|QUÍMICA|2|0|0
3º ITINERÁRIO|BIOLOGIA|2|0|0
3º ITINERÁRIO|E.A.|0|6|6
3º ITINERÁRIO|ESPANHOL|2|0|0
3º ITINERÁRIO|FÍSICA|2|0|0
3º ITINERÁRIO|INGLÊS|2|0|0
3º ITINERÁRIO|L.M.I.S|0|5|5
3º ITINERÁRIO|LÍNGUA PORTUGUESA|4|0|0
3º ITINERÁRIO|MATEMÁTICA|4|0|0
3º ITINERÁRIO|P.E.|0|1|1
3º ITINERÁRIO|QUÍMICA|2|0|0
1º ALIMENTOS|A.F.Q.A.|0|2|2
1º ALIMENTOS|A.M.A|0|2|2
1º ALIMENTOS|A.S.A|0|2|2
1º ALIMENTOS|ARTE|2|0|0
1º ALIMENTOS|BIOLOGIA|2|0|0
1º ALIMENTOS|EDUCAÇÃO FÍSICA|2|0|0
1º ALIMENTOS|FÍSICA|2|0|0
1º ALIMENTOS|GEOGRAFIA|2|0|0
1º ALIMENTOS|H.S.I.A.|0|2|2
1º ALIMENTOS|HISTÓRIA|2|0|0
1º ALIMENTOS|INGLÊS|2|0|0
1º ALIMENTOS|LÍNGUA PORTUGUESA|2|0|0
1º ALIMENTOS|MATEMÁTICA|2|0|0
1º ALIMENTOS|QUÍMICA|2|0|0
1º ALIMENTOS|T.P.A.|0|2|2
1º ALIMENTOS|TI|0|2|2
1º INFO|GSO 1|0|15|10
1º INFO|PC 1|0|10|15
1º LOGÍSTICA|AI|3|0|0
1º LOGÍSTICA|ECO|2|0|0
1º LOGÍSTICA|LTT|2|0|0
1º LOGÍSTICA|MCS|3|0|0
1º LOGÍSTICA|OIMA|5|0|0
1º LOGÍSTICA|POL|5|0|0
1º LOGÍSTICA|QAL|2|0|0
1º LOGÍSTICA|SÃO|3|0|0
2º LOGÍSTICA|CL|3|0|0
2º LOGÍSTICA|ECI|3|0|0
2º LOGÍSTICA|II|2|0|0
2º LOGÍSTICA|LT|2|0|0
2º LOGÍSTICA|OT|2|0|0
2º LOGÍSTICA|PDTCC|5|0|0
2º LOGÍSTICA|PPCP|5|0|0
2º LOGÍSTICA|TIAL|3|0|0
3º ADMINISTRAÇÃO|AFO|4|0|0
3º ADMINISTRAÇÃO|AP|3|0|0
3º ADMINISTRAÇÃO|CI|3|0|0
3º ADMINISTRAÇÃO|DTCC|3|0|0
3º ADMINISTRAÇÃO|II|2|0|0
3º ADMINISTRAÇÃO|PLE|4|0|0
3º ADMINISTRAÇÃO|PPBS|3|0|0
3º ADMINISTRAÇÃO|TIAA|3|0|0
2º INFORMÁTICA|DSE|2|0|0
2º INFORMÁTICA|GSO2|3|0|0
2º INFORMÁTICA|PC2|5|0|0
2º INFORMÁTICA|PTCC|3|0|0
2º INFORMÁTICA|RDS|5|0|0
2º INFORMÁTICA|SBD|5|0|0
2º INFORMÁTICA|SI|2|0|0
2º AGRONEGÓCIO|AF|3|0|0
2º AGRONEGÓCIO|GA|3|0|0
2º AGRONEGÓCIO|GPAII|5|0|0
2º AGRONEGÓCIO|GPVII|5|0|0
2º AGRONEGÓCIO|LTT|2|0|0
2º AGRONEGÓCIO|PNAI|2|0|0
2º AGRONEGÓCIO|PPA|3|0|0
2º AGRONEGÓCIO|PTCC|2|0|0
2º AÇÚCAR E ÁLCOOL|ACP|5|0|0
2º AÇÚCAR E ÁLCOOL|AI|2|0|0
2º AÇÚCAR E ÁLCOOL|ECO|2|0|0
2º AÇÚCAR E ÁLCOOL|HST|3|0|0
2º AÇÚCAR E ÁLCOOL|OEPII|5|0|0
2º AÇÚCAR E ÁLCOOL|PTCC|2|0|0
2º AÇÚCAR E ÁLCOOL|SUE|3|0|0
2º AÇÚCAR E ÁLCOOL|TPC|3|0|0
3º AÇÚCAR E ÁLCOOL|AIAPAA|3|0|0
3º AÇÚCAR E ÁLCOOL|CQ|5|0|0
3º AÇÚCAR E ÁLCOOL|DTCC|3|0|0
3º AÇÚCAR E ÁLCOOL|II|2|0|0
3º AÇÚCAR E ÁLCOOL|TFA|5|0|0
3º AÇÚCAR E ÁLCOOL|TFAL|5|0|0
3º AÇÚCAR E ÁLCOOL|TSAA|2|0|0
"""

# Docente | disciplinas habilitadas conforme o quadro
TEACHER_ROWS = r"""
ADRIANA|DTCC;PTCC;QUÍMICA
ALINE|E.A.;FILOSOFIA;HISTÓRIA
ALISSON|GEOGRAFIA
ANDRÉIA|AI;L.P.C;P.E.;PC 1
AUGUSTO|CNW2;DSE;GSO2;SW2;UDA
CAMILA|AI;SBD
CÉLIA|ECO;ESPANHOL;LTT;LÍNGUA PORTUGUESA
DETTO|A.C.P.S.;GEOGRAFIA
ELIANA|ACP;HST
ERIKA|UDA
FABIANE|BIOLOGIA;E.A.C.N.T;EACNT;L.M.I.S;L.P.C
FABIO|A.S.A
FAUSTO|E.O.E.T.R
GILSON|C.A;L.R.T;M.R.N;N.V;O.V /
GIOVANA|H.S.I.A.;P.P.A;T.P.A.
GRACILIANO|E.A.M.T;MATEMÁTICA;P.E.;PDTCC
GUILHERME|A.P.P;FÍSICA;PNAI;TPC
GUSTAVO|E.A.M.T
HIGOR|GCW;RDS
IGOR|MCS;OIMA
JANINE|FÍSICA
JOESLEY|AIAPAA;IR;P.T.I.C;P.T.I.C.;TFA;TI
JUCIANE|E.A.M.T
JUCIANI|AFO;E.A.C.M.T;E.A.M.T;ECI;FÍSICA;OT;PPBS;SÃO
JULIANA|INGLÊS;LÍNGUA PORTUGUESA
JULIANE|CI;CL;DTCC;PLE;POL;QAL
KAMILA|MATEMÁTICA
LEONARDO|SI;TIAA;TIAL
M. EMILIA|FILOSOFIA;HISTÓRIA;L.M.I.S;SOCIOLOGIA
MAICKON|A.M.A;A.P.P.;A.R;BIOLOGIA;G.P.A;G.P.A.;MATEMÁTICA;P.D.T.C.C
MARCEL|CNW2;DDM2;GSO 1;PC2;PDTCC;PTCC;SW2
MARCELA|ECO;II;LTT;LÍNGUA PORTUGUESA
MARTA|INGLÊS;LÍNGUA PORTUGUESA
MATHEUS|A.F.Q.A.;MATEMÁTICA;P.P.A;P.P.A A;PPA;PPCP;T.P.A.
PATRÍCIA|OEPII;TFAL;TSAA
PAULO|AF;GA
PEDRO HERNANDES|EDUCAÇÃO FÍSICA
PEDRO K|A.P.P.;E.O.E.T.R;GPAII;GPVII;N.A.A.M;N.A.A.N;S.A.B.E.A
RAPHAEL|CQ;PTCC;SUE
RENATA|FÍSICA
SANDY|BIOLOGIA;QUÍMICA
SILVIO|MATEMÁTICA
SOLANGE|ARTE;C.P.R.T;P.E.
SÉRGIO|AP;LT
TEDO|A.S;A.S,;C.P.;C.P.D.P.I.;COOP;CPDPI;M.I.A;P.C.
THI SOUZA|A.C.P.S.
THIAGO HERNANDES|GEOGRAFIA
THIAGO SAM|E.A.;L.M.I.S
THIAGO SAMP|E.A.
THIAGO SAMPAIO|HISTÓRIA
THIAGO SOUZA|FILOSOFIA;SOCIOLOGIA
"""

# Docente | jornadas observadas. Isto não é a disponibilidade real por dia/período.
TEACHER_SHIFTS = r"""
ADRIANA|Integral;Noite
ALINE|Integral
ALISSON|Integral
ANDRÉIA|Integral;Noite
AUGUSTO|Integral;Noite
CAMILA|Noite
CÉLIA|Integral;Noite
DETTO|Integral
ELIANA|Noite
ERIKA|Integral
FABIANE|Integral
FABIO|Integral
FAUSTO|Integral
GILSON|Integral
GIOVANA|Integral
GRACILIANO|Integral;Noite
GUILHERME|Integral;Noite
GUSTAVO|Integral
HIGOR|Integral;Noite
IGOR|Noite
JANINE|Integral
JOESLEY|Integral;Noite
JUCIANE|Integral
JUCIANI|Integral;Noite
JULIANA|Integral
JULIANE|Noite
KAMILA|Integral
LEONARDO|Noite
M. EMILIA|Integral
MAICKON|Integral
MARCEL|Integral;Noite
MARCELA|Integral;Noite
MARTA|Integral
MATHEUS|Integral;Noite
PATRÍCIA|Noite
PAULO|Noite
PEDRO HERNANDES|Integral
PEDRO K|Integral;Noite
RAPHAEL|Noite
RENATA|Integral
SANDY|Integral
SILVIO|Integral
SOLANGE|Integral
SÉRGIO|Noite
TEDO|Integral
THI SOUZA|Integral
THIAGO HERNANDES|Integral
THIAGO SAM|Integral
THIAGO SAMP|Integral
THIAGO SAMPAIO|Integral
THIAGO SOUZA|Integral
"""


GENERAL_SUBJECTS = {
    "ARTE", "ARTES", "BIOLOGIA", "EDUCACAO FISICA", "ESPANHOL",
    "FILOSOFIA", "FISICA", "GEOGRAFIA", "HISTORIA", "INGLES",
    "LINGUA PORTUGUESA", "MATEMATICA", "QUIMICA", "SOCIOLOGIA",
}

DAY_CLASS_NAMES = {
    "1º PI AGRO A", "1º PI AGRO B", "2º PI AGRO A", "2º PI AGRO B",
    "3º PI AGRO A", "3º PI AGRO B", "3º INFORMÁTICA",
    "1º ITINERÁRIO", "2º ITINERÁRIO", "3º ITINERÁRIO", "1º ALIMENTOS",
}
MORNING_CLASS_NAMES = {
    "1º ITINERÁRIO", "2º ITINERÁRIO", "3º ITINERÁRIO",
}
NIGHT_CLASS_NAMES = {
    "1º INFO", "1º LOGÍSTICA", "2º LOGÍSTICA", "3º ADMINISTRAÇÃO",
    "2º INFORMÁTICA", "2º AGRONEGÓCIO",
    "2º AÇÚCAR E ÁLCOOL", "3º AÇÚCAR E ÁLCOOL",
}


def norm(value):
    value = unicodedata.normalize("NFKD", str(value))
    value = "".join(char for char in value if not unicodedata.combining(char))
    key = re.sub(r"[^A-Z0-9]", "", value.upper())
    # Variação de escrita na planilha para o mesmo componente curricular.
    return {"CPDPJ": "CPDPI"}.get(key, key)


def parse_pair_rows(raw, value_count):
    parsed = {}
    for line_number, line in enumerate(raw.strip().splitlines(), start=1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != value_count:
            raise ValueError(f"Linha de dados inválida ({line_number}): {line}")
        parsed[parts[0]] = parts[1]
    return parsed


def parse_matrix():
    # Soma linhas da mesma disciplina quando a planilha só varia pontuação/acentos.
    matrix = defaultdict(dict)
    for line_number, line in enumerate(MATRIX_ROWS.strip().splitlines(), start=1):
        parts = [part.strip() for part in line.split("|")]
        if len(parts) != 5:
            raise ValueError(f"Linha da matriz inválida ({line_number}): {line}")
        classroom, subject, joint, load_a, load_b = parts
        key = norm(subject)
        entry = matrix[classroom].setdefault(key, {
            "subject": subject,
            "joint": 0,
            "a": 0,
            "b": 0,
        })
        entry["joint"] += int(joint)
        entry["a"] += int(load_a)
        entry["b"] += int(load_b)
    return {
        classroom: list(subjects.values())
        for classroom, subjects in matrix.items()
    }


def course_name(classroom_name):
    name = classroom_name.upper()
    if "AGRO" in name or "AGRONEGÓCIO" in name:
        return "Técnico em Agropecuária" if "PI AGRO" in name else "Técnico em Agronegócio"
    if "INFORMÁTICA" in name or name.startswith("1º INFO"):
        return "Técnico em Informática"
    if "ITINERÁRIO" in name:
        return "Itinerário Formativo"
    if "ALIMENTOS" in name:
        return "Técnico em Alimentos"
    if "LOGÍSTICA" in name:
        return "Técnico em Logística"
    if "ADMINISTRAÇÃO" in name:
        return "Técnico em Administração"
    if "AÇÚCAR E ÁLCOOL" in name:
        return "Técnico em Açúcar e Álcool"
    raise ValueError(f"Curso não identificado para {classroom_name}")


def subject_category(subject_name):
    key = norm(subject_name)
    return "Ensino Médio" if key in {norm(item) for item in GENERAL_SUBJECTS} else "Técnica"


def broad_availability(shifts):
    allowed = set()
    if "Integral" in shifts:
        allowed.update(range(11))
    if "Manhã" in shifts:
        allowed.update(range(6))
    if "Noite" in shifts:
        allowed.update(range(11, 16))
    return {
        str(day): [period in allowed for period in range(16)]
        for day in range(5)
    }


def parse_selected_scenario(mode):
    matrix = parse_matrix()
    original_class_names = list(matrix)
    if mode == "informatica":
        selected = ["3º INFORMÁTICA"]
    elif mode == "diurno":
        selected = [name for name in original_class_names if name in DAY_CLASS_NAMES]
    elif mode == "noturno":
        selected = [name for name in original_class_names if name in NIGHT_CLASS_NAMES]
    else:
        selected = [name for name in original_class_names if name in DAY_CLASS_NAMES | NIGHT_CLASS_NAMES]

    missing = (DAY_CLASS_NAMES | NIGHT_CLASS_NAMES) - set(original_class_names)
    if missing:
        raise RuntimeError(f"Turmas esperadas ausentes na matriz: {sorted(missing)}")

    expanded = []
    for name in selected:
        if name == "1º INFO":
            rows = matrix[name]
            for group in ("A", "B"):
                group_index = group.lower()
                settings = []
                for row in rows:
                    workload = row[group_index]
                    if workload:
                        settings.append({
                            "subject": row["subject"],
                            "joint": 0,
                            "a": workload if group == "A" else 0,
                            "b": workload if group == "B" else 0,
                            "night_cohort": group,
                        })
                expanded.append((f"1º INFO {group}", "Noite", False, settings))
            continue

        shift = (
            "Manhã" if name in MORNING_CLASS_NAMES
            else "Integral" if name in DAY_CLASS_NAMES
            else "Noite"
        )
        rows = matrix[name]
        has_internal_groups = shift in {"Integral", "Manhã"} and any(
            row["a"] or row["b"] for row in rows
        )
        expanded.append((name, shift, has_internal_groups, rows))

    return expanded


def main(mode):
    selected_classes = parse_selected_scenario(mode)
    active_shifts = {shift for _, shift, _, _ in selected_classes}

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    ensure_database_compatibility()

    db = SessionLocal()
    try:
        course_models = {}
        for class_name, _, _, _ in selected_classes:
            name = course_name(class_name)
            if name not in course_models:
                course_models[name] = models.Course(name=name)
        db.add_all(course_models.values())
        db.flush()

        subjects_by_key = {}
        subject_courses = defaultdict(set)
        class_subject_keys = {}
        for class_name, shift, has_groups, rows in selected_classes:
            keys = set()
            for row in rows:
                key = norm(row["subject"])
                if not key:
                    raise RuntimeError(f"Disciplina vazia em {class_name}")
                keys.add(key)
                subject_courses[key].add(course_models[course_name(class_name)].id)
                if key not in subjects_by_key:
                    subjects_by_key[key] = {
                        "name": row["subject"],
                        "category": subject_category(row["subject"]),
                        "workload": 1,
                    }
                effective = (
                    row["joint"] + max(row["a"], row["b"])
                    if shift in {"Integral", "Manhã"} and has_groups
                    else row["a"] if row.get("night_cohort") == "A"
                    else row["b"] if row.get("night_cohort") == "B"
                    else row["joint"]
                )
                subjects_by_key[key]["workload"] = max(
                    subjects_by_key[key]["workload"], effective, 1
                )
            class_subject_keys[class_name] = keys

        subject_models = {}
        for key, data in subjects_by_key.items():
            item = models.Subject(
                name=data["name"],
                workload=data["workload"],
                complexity="Media",
                category=data["category"],
                course_ids=sorted(subject_courses[key]),
            )
            db.add(item)
            subject_models[key] = item
        db.flush()

        teacher_subjects = parse_pair_rows(TEACHER_ROWS, 2)
        teacher_shift_rows = parse_pair_rows(TEACHER_SHIFTS, 2)
        shift_by_teacher = {
            norm(name): {part.strip() for part in shifts.split(";")}
            for name, shifts in teacher_shift_rows.items()
        }

        selected_subject_keys = set(subjects_by_key)
        teacher_specs = []
        for source_teacher, raw_subjects in teacher_subjects.items():
            teacher_key = norm(source_teacher)
            shifts = shift_by_teacher.get(teacher_key, set()) & active_shifts
            allowed_keys = {norm(item) for item in raw_subjects.split(";")}
            allowed_keys &= selected_subject_keys
            if not shifts or not allowed_keys:
                continue
            teacher_specs.append((source_teacher, shifts, allowed_keys))

        teacher_specs.sort(key=lambda item: norm(item[0]))
        covered_subjects = set().union(*(item[2] for item in teacher_specs)) if teacher_specs else set()
        without_teacher = sorted(selected_subject_keys - covered_subjects)
        if without_teacher:
            raise RuntimeError(
                "A planilha não permitiu identificar docente habilitado para: "
                + ", ".join(subjects_by_key[key]["name"] for key in without_teacher)
            )

        teacher_models = []
        for index, (_, shifts, allowed_keys) in enumerate(teacher_specs, start=1):
            teacher_models.append(models.Teacher(
                name=f"Docente {index:02d}",
                allowed_subjects=sorted(subject_models[key].id for key in allowed_keys),
                availability=broad_availability(shifts),
                score=0,
            ))
        db.add_all(teacher_models)

        classroom_models = []
        for class_name, shift, has_groups, rows in selected_classes:
            settings = []
            for row in rows:
                subject_id = subject_models[norm(row["subject"])].id

                if shift == "Noite":
                    workload = (
                        row["a"] if row.get("night_cohort") == "A"
                        else row["b"] if row.get("night_cohort") == "B"
                        else row["joint"]
                    )
                    if workload <= 0:
                        continue
                    settings.append({
                        "subject_id": subject_id,
                        "workload": workload,
                        "split": False,
                    })
                elif has_groups and (row["a"] or row["b"]):
                    settings.append({
                        "subject_id": subject_id,
                        "workload": max(row["a"], row["b"], 1),
                        "joint_workload": row["joint"],
                        "workload_a": row["a"],
                        "workload_b": row["b"],
                        "split": True,
                    })
                else:
                    workload = row["joint"]
                    if workload <= 0:
                        continue
                    settings.append({
                        "subject_id": subject_id,
                        "workload": workload,
                        "split": False,
                    })

            allowed_periods = (
                list(range(6)) if shift == "Manhã"
                else list(range(8)) if class_name == "1º ALIMENTOS"
                else [0, 1, 2, 3, 4, 6, 7, 8, 9, 10] if shift == "Integral"
                else list(range(11, 16))
            )
            allowed_periods_by_day = None
            if class_name == "1º ALIMENTOS":
                # Seis aulas matutinas em todos os dias; somente quarta tem
                # duas aulas à tarde. Não inferir uma tarde cheia nos demais dias.
                allowed_periods_by_day = {
                    "0": [0, 1, 2, 3, 4, 5],
                    "1": [0, 1, 2, 3, 4, 5],
                    "2": [0, 1, 2, 3, 4, 5, 6, 7],
                    "3": [0, 1, 2, 3, 4, 5],
                    "4": [0, 1, 2, 3, 4, 5],
                }

            classroom_models.append(models.Classroom(
                name=class_name,
                shift=shift,
                allowed_periods=allowed_periods,
                allowed_periods_by_day=allowed_periods_by_day,
                course_id=course_models[course_name(class_name)].id,
                has_groups=has_groups if shift in {"Integral", "Manhã"} else False,
                subject_settings=settings,
                preferred_subject_sequences=[],
                split_subject_ids=[],
            ))

        db.add_all(classroom_models)
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

        class_count = db.query(models.Classroom).count()
        subject_count = db.query(models.Subject).count()
        teacher_count = db.query(models.Teacher).count()
        lesson_units = 0
        for classroom in classroom_models:
            for setting in classroom.subject_settings:
                if classroom.has_groups and setting.get("split"):
                    joint = int(setting.get("joint_workload", 0) or 0)
                    lesson_units += joint
                    lesson_units += int(setting.get("workload_a", 0) or 0)
                    lesson_units += int(setting.get("workload_b", 0) or 0)
                else:
                    lesson_units += int(setting["workload"])

        if mode == "all" and (
            class_count != 20
            or subject_count != 102
            or teacher_count != 51
            or lesson_units != 695
        ):
            raise RuntimeError(
                "Contagem diferente da transcrição esperada: "
                f"{class_count} turmas, {subject_count} disciplinas, "
                f"{teacher_count} docentes e {lesson_units} lançamentos"
            )

        print("Base realista criada em banco isolado.")
        print(f"Banco: {DATABASE_PATH}")
        print(f"Cenário: {mode}")
        print(f"Cursos: {db.query(models.Course).count()}")
        print(f"Turmas: {class_count}")
        print(f"Disciplinas: {subject_count}")
        print(f"Professores anonimizados: {teacher_count}")
        print(f"Alocações semanais transcritas da planilha: {lesson_units}")
        print("Disponibilidade: ampla e sintética, não foi fornecida pela planilha.")
        print("Complexidade das disciplinas: neutra (média), pois não consta no quadro.")
        print("Dois quadros MTEC e 7 eventos síncronos mensais não entram no solver semanal.")
        print("A base criada fica separada de school_schedule.db.")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monta base de testes a partir da planilha escolar.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--informatica-only", action="store_true", help="somente 3º INFORMÁTICA diurno")
    group.add_argument("--diurno-only", action="store_true", help="somente as 11 turmas diurnas")
    group.add_argument("--noturno-only", action="store_true", help="somente os cursos técnicos modulares noturnos")
    args = parser.parse_args()
    selected_mode = (
        "informatica" if args.informatica_only
        else "diurno" if args.diurno_only
        else "noturno" if args.noturno_only
        else "all"
    )
    main(selected_mode)
