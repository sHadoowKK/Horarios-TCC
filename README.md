# Anatinus — TCC

O **Anatinus** é um sistema para cadastro de dados acadêmicos e geração automática de grade horária escolar com **React**, **FastAPI**, **SQLite/SQLAlchemy** e **Google OR-Tools (CP-SAT)**.

## Documentação do projeto

- [DOCUMENTACAO_TCC.md](DOCUMENTACAO_TCC.md): estado técnico e decisões do sistema;
- [RESULTADOS_TESTES.md](RESULTADOS_TESTES.md): evidências e medições;
- [GUIA_APRESENTACAO.md](GUIA_APRESENTACAO.md): roteiro de demo e perguntas da banca;
- [CHECKLIST_ENTREGA.md](CHECKLIST_ENTREGA.md): lista final de validação.

## O que o sistema faz

- cadastra cursos, turmas e disciplinas, incluindo turmas com divisão em grupos A/B;
- permite escolher, em cada turma, quais disciplinas realmente existem, sua carga semanal e se ficam juntas ou separadas em A/B;
- cadastra, edita e remove professores;
- registra disponibilidade de professores em 16 períodos de aula possíveis ao longo do dia;
- atribui disciplinas aos professores habilitados;
- configura regras obrigatórias (Hard) e preferências (Soft);
- gera uma grade evitando conflitos de turma e professor;
- mantém disciplinas na grade mesmo quando ainda não existe professor disponível, exibindo "Sem professor";
- considera carga horária, jornada da turma, disponibilidade, complexidade, grupos A/B, intervalos e janelas;
- salva a última grade no SQLite;
- permite visualizar a grade por turma ou professor;
- exporta a grade completa em CSV;
- permite imprimir a visualização atual;
- possui tema claro/escuro com preferência salva no navegador.

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

Para dados de demonstração, com o backend ligado e **somente em um banco vazio**:

```bash
python seed.py
```

O seed não deve ser executado repetidamente no mesmo banco, pois ele cria novos cadastros.

Teste do otimizador:

```bash
python -m unittest test_optimizer.py
```

A suíte também inclui um cenário de **semana noturna completa com 25 aulas**, baseado em uma grade real usada durante o desenvolvimento. Esse teste verifica se todas as cargas são atendidas, se os cinco períodos noturnos são preenchidos em cada dia e se nenhuma aula fica sem professor quando todos os docentes necessários estão disponíveis.

### Benchmark de carga

Além dos testes funcionais, existe um benchmark **sintético** separado para medir o comportamento do solver com volumes maiores. Ele não representa a matriz oficial da escola e não é executado junto com os testes rápidos.

```bash
python benchmark_optimizer.py --size small
python benchmark_optimizer.py --size medium
python benchmark_optimizer.py --size large
```

O benchmark informa quantidade de turmas, professores, aulas previstas, estado da solução, tempo de resolução e quantidade de aulas sem professor. Isso permite comparar desempenho entre versões sem transformar tempo de execução em um teste frágil.

## Frontend

Em outro terminal:

```bash
cd frontend
npm install
npm run dev
```

A interface abre em `http://localhost:5173`.

Para usar outro endereço de API, copie `frontend/.env.example` para `frontend/.env` e altere `VITE_API_URL`.

## Observação sobre o banco

O SQLite é criado automaticamente a partir dos modelos atuais. Como esta é uma base limpa, não há uma sequência de scripts `migrate1`, `migrate2` etc. Se o modelo do banco mudar durante o desenvolvimento, será necessário decidir entre recriar o banco local ou adotar uma ferramenta de migração como Alembic.

## Regras do otimizador

O CP-SAT trata, entre outras, as seguintes condições:

- uma turma ou grupo não pode ter duas aulas no mesmo período;
- um professor não pode dar duas aulas simultâneas;
- a carga horária semanal configurada para cada turma deve ser cumprida;
- aulas só podem ocorrer nos períodos válidos da jornada da turma (Manhã, Integral ou Noite);
- indisponibilidades de professores são respeitadas, inclusive horários bloqueados por trabalho em outra escola;
- a interjornada é calculada pelos horários reais e exige pelo menos **11 horas** entre o fim de uma aula e o início da próxima no dia seguinte;
- um professor pode ter no máximo **9 aulas por dia**;
- depois de até **6 aulas sem uma pausa de 1 hora**, não pode continuar sem o descanso necessário;
- janelas para alunos são proibidas; intervalo e almoço oficiais não contam como janela;
- janelas de professores podem ser tratadas como preferência ou regra obrigatória;
- disciplinas de alta complexidade podem ter limite diário configurável;
- divisões A/B são aproximadas no mesmo horário quando possível, mas um grupo pode ficar livre quando necessário;
- a pontuação docente dá prioridade a professores com maior pontuação quando mais de um puder assumir a disciplina;
- se nenhum professor puder assumir uma disciplina, a grade ainda pode ser gerada e as aulas aparecem como **Sem professor**.

Na distribuição das disciplinas, turmas de **Manhã/Integral** têm preferência por blocos de **2 aulas**, evitando espalhar uma matéria em várias aulas únicas e evitando blocos de 3 ou mais quando houver alternativa. Essa é uma preferência, não uma proibição. No **Noite**, blocos de 3, 4 ou 5 aulas são aceitos normalmente para representar grades reais de cursos noturnos.

## Jornadas e horários

O modelo atual representa três jornadas de turma:

- **Manhã:** 6 aulas, de 07:10 a 12:30;
- **Integral:** 5 aulas pela manhã e 5 à tarde, com almoço de 11:40 a 13:00;
- **Noite:** 5 aulas, de 19:00 a 23:00.

Intervalos e almoço aparecem visualmente na grade, mas não são períodos onde o solver possa colocar uma disciplina.

## Matriz de cada turma e grupos A/B

Cada turma possui sua própria matriz. O usuário escolhe quais disciplinas realmente fazem parte dela e informa a carga semanal de cada uma. A carga cadastrada na disciplina funciona apenas como valor padrão ao adicioná-la a uma turma.

Uma turma também pode utilizar **Grupo A** e **Grupo B**. Nesse caso, para cada disciplina presente nela, quem monta o horário escolhe:

- **Turma inteira:** A e B têm a aula juntos no mesmo horário;
- **Separada A/B:** cada grupo recebe a carga semanal da disciplina de forma independente.

A antiga categoria da disciplina (**Ensino Médio** ou **Técnica**) deixou de aparecer na interface porque não participa mais das regras. O que define onde a disciplina pode ser usada são os **cursos associados**, e o modo **Turma inteira / Separada A/B** é configurado dentro de cada turma.

Quando uma disciplina é separada:

- A e B precisam cumprir a carga semanal configurada;
- os grupos podem ter a mesma matéria no mesmo horário;
- podem ter matérias diferentes simultaneamente;
- apenas um dos grupos pode estar em aula em determinado horário;
- os professores dos grupos podem ser diferentes.

Uma aula marcada como **Turma inteira** ocupa os dois grupos e impede outra aula de A ou B no mesmo horário.


## Fluxo de configuração recomendado

Para reduzir trabalho manual, o fluxo pensado para quem monta a grade é:

1. cadastrar cursos;
2. cadastrar o catálogo de disciplinas;
3. criar as turmas;
4. abrir **Matérias da turma** e selecionar somente as disciplinas presentes, ajustando carga e divisão A/B; turmas do mesmo curso também podem copiar essa configuração umas das outras;
5. cadastrar professores, pontuação, disciplinas que podem lecionar e disponibilidade;
6. ajustar apenas as preferências que podem variar;
7. gerar a grade.

Regras obrigatórias ficam embutidas no otimizador para não depender de o usuário lembrar de configurá-las.


## Cadastro rápido de professores

A tela de professores foi preparada para reduzir trabalho repetitivo:

- busca por disciplina;
- seleção e limpeza em massa das disciplinas visíveis;
- disponibilidade recolhível;
- botão para liberar ou bloquear todos os horários;
- clique no nome do dia para liberar/bloquear o dia inteiro;
- clique no nome do turno para liberar/bloquear esse turno na semana inteira;
- disponibilidade pode ser cadastrada mesmo antes de definir as disciplinas do professor;
- horários ocupados em outra escola são representados simplesmente como indisponíveis.


## Manutenção dos cadastros

Cursos, turmas e disciplinas podem ser removidos pela própria interface.

- uma turma removida também remove apenas os horários salvos daquela turma;
- uma disciplina removida é retirada das matrizes das turmas, das permissões dos professores e da grade salva;
- um curso só pode ser removido quando não houver turmas ligadas a ele; a associação do curso nas disciplinas é limpa automaticamente.

Essas exclusões evitam deixar referências quebradas no banco.


## Correção dos cadastros

Os cadastros principais também podem ser corrigidos sem precisar apagar e refazer tudo:

- curso: nome editável;
- turma: nome, jornada e curso editáveis;
- disciplina: nome, carga padrão, complexidade e cursos associados editáveis.

Ao trocar o curso de uma turma ou retirar uma disciplina de um curso, o backend remove automaticamente combinações que deixariam de ser válidas, evitando matérias escondidas na matriz.


## Simplificação do cadastro de disciplinas

O campo visual de **Categoria** foi removido por ser redundante. A disciplina passa a ser configurada pelo que realmente interfere no uso:

- nome;
- carga semanal padrão;
- complexidade;
- cursos associados.

O campo antigo continua temporariamente no banco apenas para compatibilidade com versões anteriores, sem influência sobre a geração da grade.


## Verificação rápida antes de entregar

No PowerShell, a partir da raiz do projeto:

```powershell
.\verify.ps1
```

O script executa:
1. testes automatizados do backend;
2. build de produção do frontend.

Ele para imediatamente se uma das etapas falhar.
