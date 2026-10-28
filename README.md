# Anatinus — TCC

O **Anatinus** é um sistema para cadastro de dados acadêmicos e geração automática de grade horária escolar com **React**, **FastAPI**, **SQLite/SQLAlchemy** e **Google OR-Tools (CP-SAT)**.

## Documentação do projeto

- [Documentação técnica do TCC](docs/DOCUMENTACAO_TCC.md): funcionalidades e regras implementadas;
- [Resultados dos testes](docs/RESULTADOS_TESTES.md): evidências e medições já observadas;
- [Guia de apresentação](docs/GUIA_APRESENTACAO.md): demonstração e perguntas da banca;
- [Checklist de entrega](docs/CHECKLIST_ENTREGA.md): pendências de validação;
- [Revisão de código](docs/REVISAO_CODIGO.md): riscos e critérios de mudança;
- [Contexto mestre](docs/CONTEXTO_MESTRE_ANATINUS.md): resumo para continuidade do projeto.

## O que o sistema faz

- cadastra cursos, turmas e disciplinas, incluindo turmas com divisão em grupos A/B;
- permite escolher, em cada turma, quais disciplinas existem, a carga semanal geral ou separada para A/B, e se ficam juntas ou divididas;
- permite configurar preferências de sequência entre matérias distintas, como uma disciplina seguida de outra, sem torná-la obrigatória;
- permite, por disciplina da turma, preferir três aulas consecutivas quando a carga semanal é 3; essa preferência é ajustável e não obrigatória;
- cadastra, edita e remove professores;
- registra disponibilidade de professores em 16 períodos de aula possíveis ao longo do dia;
- atribui disciplinas aos professores habilitados;
- configura regras obrigatórias (Hard) e preferências (Soft);
- gera uma grade evitando conflitos de turma e professor;
- mantém disciplinas na grade mesmo quando ainda não existe professor disponível, exibindo "Sem professor";
- considera carga horária, jornada da turma, disponibilidade, complexidade, grupos A/B, intervalos e janelas;
- salva a última grade no SQLite;
- permite visualizar a grade por turma ou professor;
- exporta a grade completa em arquivo Excel `.xlsx`, com colunas dimensionadas e cabeçalho fixo;
- permite imprimir a visualização atual;
- possui tema claro/escuro com preferência salva no navegador.

## Estrutura do repositório

```text
Horarios-TCC/
├── .github/workflows/
│   └── build-windows.yml       # testa e gera o pacote Windows
├── backend/
│   ├── app/
│   │   ├── desktop.py          # inicializador da janela desktop
│   │   ├── database.py
│   │   ├── main.py             # API e frontend de produção
│   │   ├── models.py
│   │   ├── optimizer.py
│   │   └── schemas.py
│   ├── requirements.txt
│   ├── requirements-desktop.txt
│   ├── seed.py
│   ├── seed_realista.py          # base de teste inspirada nas grades ETEC
│   ├── test_backend.py
│   ├── test_optimizer.py
│   └── benchmark_optimizer.py
├── docs/                       # documentação e material do TCC
├── frontend/
│   ├── public/                 # logos originais e ícone
│   └── src/
│       ├── pages/
│       ├── App.tsx
│       ├── api.ts
│       └── anatinus-design-system.css
├── build-windows.ps1           # empacota a versão desktop
├── start-dev.ps1               # usa o banco local normal
├── start-demo.ps1              # abre o banco realista isolado
├── start-informatica.ps1       # recria e abre somente o 3º INFO
├── verify.ps1                  # testes + build do frontend
├── backup-db.ps1               # backup do banco local
├── README.md
└── .gitignore
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

O seed pequeno não deve ser executado repetidamente no mesmo banco, pois ele cria novos cadastros.

### Base realista inspirada nas grades da ETEC

### Testar somente a turma de Informática

Para comparar o gerador com as matérias e os professores do 3º INFO sem interferência das outras turmas, feche primeiro o Anatinus e execute na raiz:

```powershell
.\start-informatica.ps1
```

O atalho recria o banco DEMO isolado com somente o 3º INFO A/B e abre o aplicativo. Ele interrompe se a API ainda estiver usando o banco, para evitar recriá-lo enquanto está em uso.

O seed usa os 17 componentes e professores que conseguimos ler no quadro original de 3º INFO. As cargas semanais transcritas do quadro são:

| Matéria | Carga semanal | Professor(es) no quadro |
|---|---:|---|
| UDA | 2 por grupo | Erika |
| SW2 | A: 3 · B: 2 | A: Higor · B: Marcel |
| CNW2 | 2 por grupo | A: Erika · B: Marcel |
| Filosofia | 1 | M. Emília |
| Sociologia | 1 | M. Emília |
| Espanhol | 2 | Célia |
| História | 2 | M. Emília |
| DDM2 | 2 por grupo | Marcel |
| IRS | 2 por grupo | Joesley |
| Matemática | 3 | Kamila |
| Inglês | 2 | Marta |
| EAMT | 3 por grupo | Gustavo |
| Português | 3 | Marta |
| EACNT | 3 por grupo | Fabiane |
| PDTCC | 2 por grupo | Marcel |
| GCW | 2 por grupo | Higor |
| Geografia | 2 | Thiago |

A captura mostra cargas de 37 aulas para A e 36 para B, porque SW2 tem cargas diferentes nos dois subgrupos. Filosofia e Sociologia ficam em sequência, com a mesma professora M. Emília; isso está salvo como uma preferência configurável da turma, não como regra fixa no código.

O modo isolado usa o banco de demonstração e substitui somente os dados DEMO; não altera `backend/school_schedule.db`. Como a imagem não contém a disponibilidade semanal completa dos professores, o teste só de Informática deixa os docentes disponíveis nos períodos do Integral de segunda a sexta. O gerador deve reorganizar os horários respeitando as cargas, as matérias e as preferências, não copiar cada posição do quadro original.


Para testar turmas, grupos e professores com um conjunto maior, há um segundo script. Ele cria **um banco separado**, `backend/school_schedule_demo.db`, e nunca apaga `school_schedule.db`.

Feche as janelas do Anatinus antes de recriar essa base e execute, na raiz do projeto:

```powershell
cd backend
.\.venv\Scripts\python.exe seed_realista.py
cd ..
.\start-demo.ps1
```

O `start-demo.ps1` inicia frontend e backend usando somente o banco realista. O banco normal continua separado.

A base inclui:
- **3º INFO Integral**, com os nomes de disciplinas/professores que conseguimos recuperar e grupos A/B: disciplinas técnicas separadas e disciplinas do ensino médio compartilhadas;
- **TI — Noite**, com as cargas anotadas na conversa: SBD 5, PTCC 3, PC2 5, RDS 5, GSO2 3, SI 2 e DSE 2, totalizando 25 aulas;
- **seis turmas Agro** (1º, 2º e 3º PI AGRO A/B), cada uma podendo ter grupos A/B, para exercitar divisões com os componentes M.R.N e P.T.I.C.

**Limitação importante dos dados:** a captura do 3º INFO e a grade noturna de TI foram recuperadas e usadas para transcrever as matérias/cargas visíveis. As disponibilidades individuais dos docentes e a matriz completa dos Agro continuam provisórias para teste. A distribuição noturna de TI é a parte com carga recuperada com exatidão. A base também não armazena salas ou laboratórios, conforme o escopo do Anatinus.

Todos os testes automatizados:

```bash
python -m unittest discover -p "test_*.py"
```

A suíte atual possui **22 testes automatizados**: 18 cenários do solucionador e 4 testes de integração do backend. Entre eles há um cenário de **semana noturna completa com 25 aulas**, baseado em uma grade real usada durante o desenvolvimento.

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


## Atalhos no Windows

Iniciar backend e frontend em terminais separados:

```powershell
.\start-dev.ps1
```

Criar uma cópia local do banco antes de testes ou cadastro em massa:

```powershell
.\backup-db.ps1
```

Por padrão, se o banco do aplicativo desktop existir, ele será copiado; caso contrário, o script usa o banco de desenvolvimento. Para escolher manualmente:

```powershell
.\backup-db.ps1 -Source Desktop
.\backup-db.ps1 -Source Development
```

Os backups ficam em `backups/` com data e hora no nome e não são enviados ao GitHub.

## Aplicativo Windows (.exe)

O Anatinus também pode ser empacotado como aplicativo desktop. O executável inicia a API local, abre a interface em uma janela própria e encerra o servidor quando a janela é fechada.

### Gerar o pacote no Windows

Pré-requisitos recomendados: Python 3.12, Node.js 22/npm e runtime WebView2 do Microsoft Edge.

Na raiz do repositório, execute no PowerShell:

```powershell
.\build-windows.ps1
```

O script instala as dependências de empacotamento, executa os testes do backend, compila o frontend e gera:

`release\Anatinus-Windows-x64.zip`

Extraia o ZIP inteiro e abra `Anatinus.exe`. **Não copie somente o EXE para fora da pasta**, porque ele usa arquivos auxiliares empacotados ao lado dele.

Também existe uma compilação automática pelo GitHub Actions. Após uma execução bem-sucedida, abra **Actions → Build Windows → execução mais recente → Artifacts** e baixe `Anatinus-Windows-x64`.

### Dados e atualização

O banco da versão desktop fica em `%LOCALAPPDATA%\Anatinus\school_schedule.db`, separado dos arquivos temporários do executável. Atualizar o programa não deve apagar os cadastros.

Para levar os cadastros do ambiente de desenvolvimento à primeira execução do EXE, feche o Anatinus e copie o banco `backend\school_schedule.db` para `%LOCALAPPDATA%\Anatinus\school_schedule.db` antes de abrir a versão desktop. Faça primeiro um backup com `backup-db.ps1`.
