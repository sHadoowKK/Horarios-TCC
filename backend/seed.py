import requests

BASE = "http://localhost:8000"


def make_availability(shifts):
    day = [False] * 16
    if "M" in shifts:
        day[0:6] = [True] * 6
    if "T" in shifts:
        day[6:11] = [True] * 5
    if "N" in shifts:
        day[11:16] = [True] * 5
    return {str(day_index): day[:] for day_index in range(5)}


print("Criando cursos...")
medio = requests.post(f"{BASE}/courses/", json={"name": "Ensino Médio"}).json()
tecnico = requests.post(f"{BASE}/courses/", json={"name": "Técnico em Informática"}).json()

print("Criando turmas...")
requests.post(f"{BASE}/classrooms/", json={"name": "1º Ano A", "course_id": medio["id"], "shift": "Manhã"})
requests.post(f"{BASE}/classrooms/", json={"name": "1º Ano B", "course_id": medio["id"], "shift": "Integral"})
requests.post(f"{BASE}/classrooms/", json={"name": "Módulo 1", "course_id": tecnico["id"], "shift": "Noite"})

print("Criando disciplinas...")
mat = requests.post(f"{BASE}/subjects/", json={"name": "Matemática", "course_ids": [medio["id"], tecnico["id"]], "workload": 4, "complexity": "Alta"}).json()
port = requests.post(f"{BASE}/subjects/", json={"name": "Português", "course_ids": [medio["id"], tecnico["id"]], "workload": 4, "complexity": "Media"}).json()
fis = requests.post(f"{BASE}/subjects/", json={"name": "Física", "course_ids": [medio["id"]], "workload": 2, "complexity": "Alta"}).json()
hist = requests.post(f"{BASE}/subjects/", json={"name": "História", "course_ids": [medio["id"]], "workload": 2, "complexity": "Baixa"}).json()
logica = requests.post(f"{BASE}/subjects/", json={"name": "Lógica de Programação", "course_ids": [tecnico["id"]], "workload": 4, "complexity": "Alta"}).json()
bd = requests.post(f"{BASE}/subjects/", json={"name": "Banco de Dados", "course_ids": [tecnico["id"]], "workload": 3, "complexity": "Alta"}).json()

print("Criando professores...")
teachers = [
    ("Prof. Carlos", [mat["id"], fis["id"]], ["M", "T"], 80),
    ("Profa. Ana", [port["id"], hist["id"]], ["M", "T"], 95),
    ("Prof. Linus", [logica["id"], bd["id"]], ["N"], 85),
    ("Prof. Newton", [mat["id"], fis["id"]], ["M", "T", "N"], 60),
    ("Profa. Helena", [port["id"], hist["id"]], ["M", "T", "N"], 70),
]

for name, subjects, shifts, score in teachers:
    requests.post(
        f"{BASE}/teachers/",
        json={
            "name": name,
            "allowed_subjects": subjects,
            "availability": make_availability(shifts),
            "score": score,
        },
    )

print("Dados de demonstração criados.")
