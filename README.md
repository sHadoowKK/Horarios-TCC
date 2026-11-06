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
- permite regenerar a escola inteira, várias turmas selecionadas ou uma matéria em turmas escolhidas;
- permite regenerar uma matéria em toda a escola, apenas nas turmas em que ela está cadastrada;
- preserva horários ocupados e vazios fora do escopo da regeneração parcial, recusando a operação se a grade antiga não puder ser mantida com as novas configurações;
- mantém disciplinas na grade mesmo quando ainda não existe professor disponível, exibindo "Sem professor";
- considera carga horária, jornada explícita por turma, disponibilidade, complexidade, grupos A/B, intervalos e janelas;
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
│   ├── seed_apresentacao.py      # base fictícia com grade pronta para apresentação
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

### Base fictícia para a apresentação

Na raiz do projeto, execute:

```powershell
.\start-demo.ps1
```

O atalho recria `backend/school_schedule_demo.db`, cadastra dois cursos, três turmas, quinze disciplinas e quinze professores fictícios, define as disponibilidades semanais e gera/salva automaticamente uma grade completa. A demonstração inclui uma turma integral com divisão A/B. Cada grupo tem seis aulas por dia, de segunda a sexta, sem aulas sem professor.

A base é inteiramente inventada e serve apenas para demonstrar o funcionamento do Anatinus. Ela não representa uma escola real nem deve ser usada como cadastro oficial. O banco normal `backend/school_schedule.db` permanece separado.

Para recriar manualmente apenas essa base, feche o Anatinus e execute dentro de `backend`:

```powershell
.\.venv\Scripts\python.exe seed_apresentacao.py
```

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


### Base de regressão inspirada em grades da ETEC

Além da base fictícia, `seed_realista.py` continua disponível para testar as matrizes recuperadas durante o desenvolvimento. Esse seed não é o usado pelo modo de apresentação; ele recria o mesmo arquivo DEMO e, por isso, deve ser executado apenas para testes técnicos, com o Anatinus fechado.

Para validar as oito turmas dessa base de regressão, execute dentro de `backend`:

```powershell
.\.venv\Scripts\python.exe seed_realista.py
.\.venv\Scripts\python.exe validate_demo_generation.py --all-together
```

Depois, execute novamente `start-demo.ps1` para reconstruir a base fictícia antes da apresentação. O banco normal `school_schedule.db` continua separado.

A base inclui:
- **3º INFO Integral**, com os nomes de disciplinas/professores que conseguimos recuperar e grupos A/B: disciplinas técnicas separadas e disciplinas do ensino médio compartilhadas;
- **TI — Noite**, com as cargas anotadas na conversa: SBD 5, PTCC 3, PC2 5, RDS 5, GSO2 3, SI 2 e DSE 2, totalizando 25 aulas;
- **seis turmas Agro independentes** (1º, 2º e 3º PI AGRO A/B). O sufixo A/B identifica duas turmas diferentes; nenhuma delas é criada com subgrupos internos.
- **Jornada explícita por turma**: o 3º INFO usa cinco aulas de manhã e cinco à tarde; as turmas Agro usam seis aulas de manhã e cinco à tarde; TI noturno usa cinco períodos à noite.

**Limitação importante dos dados:** a captura do 3º INFO e a grade noturna de TI foram recuperadas e usadas para transcrever as matérias/cargas visíveis. As disponibilidades individuais dos docentes e parte da matriz de Agro continuam provisórias para teste, sobretudo onde o texto da imagem não está nítido. A jornada de seis aulas de manhã nas turmas Agro é preservada como configuração explícita; não é inferida do nome da turma. A distribuição noturna de TI é a parte com carga recuperada com exatidão. A base também não armazena salas ou laboratórios, conforme o escopo do Anatinus.

Todos os testes automatizados:

```bash
python -m unittest discover -p "test_*.py"
```

A suíte tem **36 testes automatizados**: 29 cenários do otimizador e 7 testes de integração do backend, incluindo regressões para jornadas configuráveis e turno noturno. Entre eles há um cenário de **semana noturna completa com 25 aulas**, baseado em uma grade real usada durante o desenvolvimento.

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

O SQLite é criado automaticamente a partir dos modelos atuais. O arquivo `backend/app/database.py` também aplica migrações de compatibilidade para bancos locais antigos, incluindo a coluna `allowed_periods`. Para novos recursos de maior complexidade, vale adotar Alembic; até lá, qualquer alteração de esquema precisa vir acompanhada de uma migração compatível e de testes.

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

## Regeneração parcial da grade

Na tela **Grade Horária**, o seletor **Gerar novamente** oferece quatro opções:

- **Escola inteira**: recalcula todas as turmas e matérias.
- **Turmas selecionadas**: recalcula todas as matérias das turmas marcadas.
- **Matéria nas turmas selecionadas**: escolha uma matéria e marque uma ou mais turmas que a utilizam.
- **Matéria na escola inteira**: escolha uma matéria e recalcula essa matéria em todas as turmas onde ela está configurada.

Nos modos parciais, o otimizador congela os períodos preenchidos e vazios, os professores e as cargas fora do escopo selecionado. Se a carga ou os cadastros de uma unidade preservada não corresponderem à grade salva, a operação é interrompida com uma mensagem explicativa, em vez de mudar a grade silenciosamente. Gere também a parte afetada ou escolha **Escola inteira**.

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
