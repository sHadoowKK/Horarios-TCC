# Anatinus — TCC

O **Anatinus** é um sistema para cadastro de dados acadêmicos e geração automática de grade horária escolar com **React**, **FastAPI**, **SQLite/SQLAlchemy** e **Google OR-Tools (CP-SAT)**.

## O que o sistema faz

- cadastra cursos, turmas e disciplinas, incluindo turmas com divisão em grupos A/B;
- cadastra, edita e remove professores;
- registra disponibilidade de professores em 16 períodos de aula possíveis ao longo do dia;
- atribui disciplinas aos professores habilitados;
- configura regras obrigatórias (Hard) e preferências (Soft);
- gera uma grade evitando conflitos de turma e professor;
- considera carga horária, jornada da turma, disponibilidade, complexidade, grupos A/B, intervalos e janelas;
- salva a última grade no SQLite;
- permite visualizar a grade por turma ou professor.

## Estrutura

```text
Horarios-TCC/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── optimizer.py
│   │   └── schemas.py
│   ├── requirements.txt
│   ├── seed.py
│   └── test_optimizer.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Config.tsx
│   │   │   ├── Professores.tsx
│   │   │   └── Turmas.tsx
│   │   ├── api.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── styles.css
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── .gitignore
└── README.md
```

## Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

A API abre em `http://localhost:8000` e a documentação em `http://localhost:8000/docs`.

Para dados de demonstração, com o backend ligado:

```bash
python seed.py
```

Teste do otimizador:

```bash
python -m unittest test_optimizer.py
```

## Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

A interface abre em `http://localhost:5173`.

## Observação sobre o banco

O SQLite é criado automaticamente a partir dos modelos atuais. Como esta é uma base limpa, não há uma sequência de scripts `migrate1`, `migrate2` etc. Se o modelo do banco mudar durante o desenvolvimento, será necessário decidir entre recriar o banco local ou adotar uma ferramenta de migração como Alembic.

## Regras do otimizador

O CP-SAT trata, entre outras, as seguintes condições:

- uma turma não pode ter duas aulas no mesmo período;
- um professor não pode dar duas aulas simultâneas;
- a carga horária semanal de cada disciplina deve ser cumprida;
- aulas só podem ocorrer nos períodos válidos da jornada da turma (Manhã, Integral ou Noite);
- indisponibilidades de professores são respeitadas;
- existe limite diário e consecutivo para professores, com intervalos oficiais quebrando a sequência;
- disciplinas de alta complexidade têm limite diário;
- três aulas consecutivas da mesma disciplina são evitadas por regra obrigatória, respeitando intervalos;
- janelas podem ser Hard ou Soft;
- preferências Soft podem evitar primeira aula, última aula e sexta-feira;
- a pontuação do professor participa da função objetivo.

A regra de interjornada usada aqui é uma simplificação por turnos: professor que trabalha no período noturno não é alocado na manhã do dia seguinte.

## Jornadas e horários

O modelo atual representa três jornadas de turma:

- **Manhã:** 6 aulas, de 07:10 a 12:30;
- **Integral:** 5 aulas pela manhã e 5 à tarde, com almoço de 11:40 a 13:00;
- **Noite:** 5 aulas, de 19:00 a 23:00.

Intervalos e almoço aparecem visualmente na grade, mas não são períodos onde o solver possa colocar uma disciplina.

## Turmas divididas em grupos

Uma turma pode ser cadastrada como simples ou como uma turma que utiliza **Grupo A** e **Grupo B**.

A divisão é configurada **por turma e por disciplina**. Para cada disciplina de uma turma com grupos, quem monta o horário escolhe:

- **Turma inteira:** A e B têm a aula juntos no mesmo horário;
- **Separada A/B:** cada grupo recebe a carga semanal da disciplina de forma independente.

A categoria da disciplina (**Ensino Médio** ou **Técnica**) é apenas informativa e não determina automaticamente a divisão.

Quando uma disciplina é separada:

- A e B precisam cumprir a carga semanal configurada;
- os grupos podem ter a mesma matéria no mesmo horário;
- podem ter matérias diferentes simultaneamente;
- apenas um dos grupos pode estar em aula em determinado horário;
- os professores dos grupos podem ser diferentes.

Uma aula marcada como **Turma inteira** ocupa os dois grupos e impede outra aula de A ou B no mesmo horário.
