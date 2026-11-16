# Anatinus

Sistema de cadastro acadêmico e geração de horários escolares. O projeto reúne uma interface web, uma API local, armazenamento SQLite e um otimizador de horários baseado no Google OR-Tools CP-SAT.

## Tecnologias

- Interface: React, TypeScript, Vite e Tailwind CSS
- API: Python, FastAPI e SQLAlchemy
- Banco de dados: SQLite
- Otimização: Google OR-Tools CP-SAT

## Requisitos

- Python 3.13 para desenvolvimento; Python 3.12 para montar a versão desktop
- Node.js 22
- Windows 10 ou 11 para os scripts PowerShell

A instalação inicial das dependências requer acesso à internet.

## Executar em ambiente de desenvolvimento

No PowerShell, a partir da pasta do projeto, prepare o backend:

```
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

```

Instale as dependências do frontend:

```
cd ..\frontend
npm ci
```

Volte à pasta principal e inicie o sistema:

```
cd ..
.\start-demo.ps1

```

O script prepara a base de demonstração e inicia a API e a interface. A interface fica em `http://localhost:5173`; a documentação da API, em `http://localhost:8000/docs`.

## Base demonstrativa

A base transcreve os quadros semanais da planilha usada no projeto: 8 cursos, 20 turmas, 102 disciplinas, 51 docentes anonimizados e 695 aulas semanais configuradas. Há uma grade salva de 50 aulas para o 3º Informática. As outras turmas têm suas matrizes cadastradas, mas não têm grade salva.

A disponibilidade dos docentes é sintética porque a planilha não informa a agenda semanal completa. Os quadros MTEC com início às 18h30 e os encontros síncronos mensais não estão representados na grade semanal.

O banco demonstrativo está em `backend/school_schedule_demo.db`. 

O banco local `backend/school_schedule.db` não acompanha esta entrega. `backend/seed_realista.py` monta os cadastros transcritos da planilha; `backend/seed_apresentacao_planilha.py` prepara a base completa e gera a grade inicial do 3º Informática. O script `start-demo.ps1` recria a base demonstrativa.

## Verificação

Para executar os testes automatizados do backend:

```
cd backend
.\.venv\Scripts\Activate.ps1
python -m unittest discover -p "test_*.py"

```

Para compilar a interface, execute `npm run build` dentro de `frontend`. O script `build-windows.ps1` prepara a versão desktop para Windows.

## Organização do código

- `backend/app/`: API, persistência, validação e otimizador
- `backend/`: scripts atuais de dados, testes e requisitos Python
- `frontend/src/`: interface, páginas e exportação de planilhas
- `frontend/public/`: logotipos e recursos visuais
- `docs/DOCUMENTACAO_TECNICA.md`: descrição da arquitetura e do modelo
- `.github/workflows/`: validações e compilação automatizadas
