# Documentação técnica do Anatinus

## Objetivo

O Anatinus cadastra cursos, turmas, disciplinas e docentes e auxilia a distribuição das aulas em uma grade semanal. A geração é formulada como um problema de otimização combinatória resolvido pelo CP-SAT do Google OR-Tools.

## Arquitetura

A interface, desenvolvida em React e TypeScript, envia as operações à API FastAPI. A API valida os dados, aplica as regras do domínio e armazena os cadastros e grades em SQLite por meio do SQLAlchemy. O módulo `backend/app/optimizer.py` constrói o modelo CP-SAT e interpreta o resultado do solucionador.

Os principais componentes são:

- `frontend/src/App.tsx`: fluxo principal e visualização das grades;
- `frontend/src/pages/`: telas de turmas, professores e configurações;
- `backend/app/main.py`: rotas e operações da API;
- `backend/app/models.py`: entidades persistidas;
- `backend/app/schemas.py`: validação de entradas e saídas;
- `backend/app/database.py`: conexão e compatibilidade do banco;
- `backend/app/optimizer.py`: formulação e resolução do problema;
- `backend/app/generation_diagnostics.py`: diagnóstico de problemas de geração.

## Modelo de dados

Os cursos agrupam turmas. Cada turma define sua jornada, disciplinas, cargas semanais e, quando aplicável, a divisão em grupos A e B. A relação entre turma e disciplina permite especificar aulas conjuntas e aulas próprias de cada grupo. Os docentes possuem habilitações por disciplina e disponibilidade por período. A grade salva relaciona turma, disciplina, docente, dia, período e grupo de estudantes.

## Restrições e preferências

O modelo verifica as cargas semanais configuradas, os períodos permitidos para cada jornada, conflitos de ocupação da turma e conflitos de docentes. Também considera habilitações, disponibilidade informada, grupos A/B e intervalos definidos no sistema. As regras gerais podem ser complementadas por limites e períodos permitidos específicos de cada turma.

Preferências como blocos consecutivos, distribuição diária equilibrada e sequências entre disciplinas orientam a busca sem substituir as restrições obrigatórias. O resultado `feasible` indica que foi encontrada uma solução válida; `optimal` indica que o solucionador provou a optimalidade dentro do modelo e do limite de busca configurado.

## Base de demonstração

O arquivo `backend/school_schedule_demo.db` contém a transcrição das matrizes semanais da planilha: 8 cursos, 20 turmas, 102 disciplinas, 51 docentes anonimizados e 695 unidades de aula semanal. A base inclui uma grade salva para o 3º Informática, com 50 aulas e atribuição docente em todas elas.

A base não representa a agenda completa da escola. A planilha não informa disponibilidade semanal completa dos docentes; por isso, a disponibilidade usada para demonstração é sintética. Os quadros MTEC com início às 18h30 e os encontros síncronos mensais não foram convertidos em aulas semanais. As demais turmas possuem cadastros e cargas, sem grades salvas nesta base.

O banco `backend/school_schedule.db` é criado localmente durante o desenvolvimento e não está incluído nesta entrega.

## Testes

Os testes do backend encontram-se nos arquivos `backend/test_*.py`. Execute-os a partir da pasta `backend` com:

```
python -m unittest discover -p "test_*.py"

```

O arquivo `backend/benchmark_optimizer.py` oferece cenários para medir o desempenho do solucionador. Os benchmarks são separados da suíte funcional.
