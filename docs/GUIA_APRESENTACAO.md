# ANATINUS — GUIA DE APRESENTAÇÃO E DEMONSTRAÇÃO

## Objetivo

Mostrar o cadastro acadêmico, a configuração de professores e a geração automática de uma grade semanal por otimização combinatória com CP-SAT. A demonstração principal utiliza uma base inteiramente fictícia, criada especificamente para a apresentação.

## 1. Cenário principal: base fictícia de 100 aulas

Use a base criada por `backend/seed_apresentacao.py`. Ela contém:

- 2 cursos;
- 3 turmas;
- 15 disciplinas;
- 15 professores fictícios;
- uma turma integral dividida em grupos A/B;
- duas turmas integrais sem divisão;
- 100 aulas geradas e salvas pela API, todas com professor.

Na validação conjunta, cada turma/grupo ficou com seis aulas por dia, de segunda a sexta. A verificação confirmou ausência de conflitos simultâneos de professores, janelas de alunos e violações verificadas de disponibilidade e descanso.

O solver retornou `feasible`: a grade é válida segundo as regras verificadas, mas o programa não provou que ela seja a melhor solução matemática possível. A geração levou aproximadamente 120 segundos no runner do GitHub. Por isso, gere a base antes da apresentação e deixe a grade salva.

### Preparar e abrir

Na raiz do projeto, feche instâncias antigas do Anatinus e execute:

```powershell
.\start-demo.ps1
```

O atalho recria `backend/school_schedule_demo.db`, gera a grade pela API e abre backend, frontend e navegador. O banco normal `backend/school_schedule.db` não é alterado.

**Atenção:** `seed_realista.py` também recria o arquivo `school_schedule_demo.db`, mas com a base de regressão inspirada nas grades da ETEC. Não execute esse seed antes da apresentação principal, pois ele substitui os dados fictícios.

Todos os nomes, professores, disponibilidades e horários dessa base são inventados. Ela demonstra o funcionamento do sistema; não representa uma grade oficial da escola.

## 2. Roteiro da demonstração

### Etapa 1 — Gestão Acadêmica

Mostrar:
- cursos;
- turmas;
- disciplinas;
- matriz própria de uma turma;
- carga semanal;
- grupos A/B.

Frase sugerida:

> "A matriz não é global. Cada turma informa quais disciplinas possui, a carga semanal e se cada matéria ocorre com a turma inteira ou separada em A/B."

### Etapa 2 — Professores

Mostrar:
- disciplinas habilitadas;
- pontuação;
- disponibilidade semanal.

Frase sugerida:

> "A disponibilidade representa os períodos em que o professor pode trabalhar. O solver também considera conflitos entre turmas e regras de descanso."

### Etapa 3 — Regras e preferências

Explicar a diferença:

**Hard:** regras obrigatórias que não podem ser violadas.

**Soft:** preferências que o solver tenta melhorar, mas que podem não ser atendidas integralmente.

Exemplo:

> "Um professor em duas turmas ao mesmo tempo é proibido. Já a distribuição em blocos de duas aulas é uma preferência; outras distribuições podem ser usadas quando necessário."

### Etapa 4 — Grade gerada

Mostrar a grade salva e destacar:
- distribuição de segunda a sexta;
- intervalo e almoço;
- blocos de matérias;
- divisão A/B.

Frase sugerida:

> "A grade foi montada considerando todas as turmas e professores cadastrados nessa base de demonstração, e depois passou por validações de conflitos e janelas."

### Etapa 5 — Visão por professor

Trocar para a visão docente.

Frase sugerida:

> "O mesmo resultado pode ser consultado pela agenda do professor, facilitando a conferência de seus períodos e de conflitos."

### Etapa 6 — Exportação

Demonstrar Excel e impressão somente depois de testar essas funções no computador que será usado na apresentação.

## 3. Cenário técnico adicional: 3º INFO isolado

O 3º INFO Integral A/B também foi validado separadamente pela API:
- 57 alocações;
- zero aulas sem professor;
- carga A/B preservada;
- ausência de janelas de alunos;
- estado `feasible`.

Esse cenário usa matérias e cargas recuperadas do quadro de referência, mas as disponibilidades docentes são provisórias. Pode ser mostrado como teste específico de grupos A/B, desde que fique claro que não é a base fictícia principal nem uma reconstrução oficial completa da disponibilidade dos professores.

Para recriá-lo, feche o Anatinus e execute na raiz:

```powershell
.\start-informatica.ps1
```

Esse atalho recria o banco DEMO somente com o 3º INFO e inicia a aplicação usando o banco já preparado, sem executar o seed fictício por cima. Para voltar à demonstração principal, feche o aplicativo e execute ` .\start-demo.ps1 ` (sem espaço depois da crase inicial).

## 4. O que os resultados significam

A base fictícia de apresentação tem 100 aulas, todas com professor, e passou na validação conjunta.

A base de regressão inspirada na ETEC contém oito turmas e também foi gerada em conjunto, mas o resultado observado teve 291 aulas, das quais 234 com professor e 57 sem professor. Algumas turmas Agro também apresentaram distribuição diária desigual. Essa base é útil para testes técnicos e não deve ser apresentada como uma grade final aprovada.

O estado `feasible` significa que o solver encontrou uma solução válida; não significa que provou optimalidade.

## 5. Explicação simples do CP-SAT

Versão de 20 segundos:

> "O Anatinus transforma os horários possíveis em variáveis e descreve ao CP-SAT quais combinações são permitidas ou proibidas. Depois define preferências com pesos. O solver procura uma combinação que respeite as regras obrigatórias e tente melhorar as preferências."

## 6. Perguntas prováveis da banca

### "Isso é inteligência artificial?"

> "Não no sentido de IA generativa. O núcleo é programação por restrições e otimização combinatória usando o CP-SAT do Google OR-Tools."

### "Ele sempre encontra a melhor grade?"

> "Quando retorna optimal, o solver provou a optimalidade dentro daquele modelo. Também pode retornar feasible, que é uma solução válida sem prova de que seja a melhor, especialmente quando há limite de tempo."

### "E se não existir professor para uma matéria?"

> "A matéria não desaparece. Ela continua na grade como Sem professor. Essa opção recebe uma penalidade alta e deve ser investigada nos dados e nas disponibilidades."

### "Como funciona A/B?"

> "A divisão é configurada por turma e disciplina. Uma matéria pode ser conjunta e outra separada. Quando separada, A e B possuem cargas independentes."

### "O sistema substitui a coordenação?"

> "Não. Ele automatiza a busca e a verificação de restrições. A coordenação continua responsável pelas decisões pedagógicas, exceções e validação final."

### "Qual é a principal limitação?"

> "A qualidade da solução depende da qualidade dos dados cadastrados e do tempo disponível para a busca. A base fictícia foi validada para demonstração; a base completa da escola ainda exige revisão dos dados e avaliação de quem monta os horários."

## 7. O que não afirmar

Evitar:
- "elimina 100% dos erros";
- "reduz 70% do tempo" sem medição;
- "usa IA generativa";
- "está pronto para qualquer escola";
- "sempre encontra a grade perfeita";
- "substitui a coordenação";
- "a grade de oito turmas da ETEC está aprovada".

## 8. Plano B para a apresentação

Antes da banca:
1. executar `start-demo.ps1`;
2. esperar a geração terminar;
3. abrir a grade salva e conferir as três turmas;
4. testar as telas e exportações que serão demonstradas;
5. tirar screenshots da grade e das visões por professor;
6. manter o banco fictício pronto em backup.

Se a geração ao vivo demorar, mostrar a última grade salva e explicar que o solver possui limite de tempo. Não ficar repetindo o botão de gerar.

