# Anatinus — Sistema de Gestão de Horários Escolares ETEC
## Especificação Visual e Diretrizes de Redesign (`design.md`)

> **Classificação**: Documentação Técnica de Design System & Redesign Visual da Aplicação Real  
> **Repositório Base**: `sHadoowKK/Horarios-TCC`  
> **Stack Oficial**: React 19 + TypeScript + Vite + Tailwind CSS v4 (`@tailwindcss/vite`) + React Router v7 (`react-router-dom`) + Lucide React  
> **Backend & Solver**: FastAPI + SQLite (SQLAlchemy) + Google OR-Tools CP-SAT  
> **Princípio Central**: **Redesign visual da aplicação real existente**, preservando 100% dos contratos de dados, endpoints de API (`/timetable/`, `/teachers/`, `/classrooms/`, `/subjects/`, `/courses/`, `/config/`, `/generate/`), fluxos operacionais e regras do solver combinatório — sem criar módulos fictícios ou alterar a arquitetura técnica.

---

## 1. Visão Geral e Filosofia de Design

O **Anatinus** é uma ferramenta técnica de precisão acadêmica voltada à elaboração, validação e otimização de matrizes curriculares e horários escolares em instituições de ensino técnico e médio integrado (padrão ETEC / Centro Paula Souza).

### 1.1 Personalidade Visual: "Academic Rationalist" (Racionalismo Acadêmico Suíço)
- **Foco na Grade Semanal e Alta Densidade Informativa**: Prioridade absoluta para a visualização clara da grade semanal (`<table>` semântica e legível), evitando rolagem vertical desnecessária e dispensando layouts de dashboard com cards flutuantes genéricos.
- **Geometria Estrutural e Firme**: Cantos com micro-raios funcionais (`2px` a `4px`), ausência de sombras difusas (flat design de precisão editorial) e separadores de borda nítidos de `1px solid var(--an-border)`.
- **Navegação Horizontal Integrada**: Uso estrito de um cabeçalho superior unificado de 48px a 50px (`.app-header`), mantendo 100% da largura útil da tela dedicada à visualização de dados e eliminando sidebars verticais.
- **Tipografia Híbrida de Precisão**: 
  - `Inter` para rótulos, botões, tabelas e comandos de navegação.
  - `JetBrains Mono` (`.font-mono`) para intervalos de tempo oficiais (`07:10 - 08:00`, etc.), pontuações numéricas, contadores de períodos e inputs de carga horária.

---

## 2. Tokens de Design e Temas (Claro e Escuro)

Os tokens do Anatinus utilizam o prefixo `--an-*` em CSS Custom Properties e mapeamento direto no arquivo `src/anatinus-design-system.css`.

### 2.1 Tema Claro (Oficial — Caderno Técnico & Papel Acadêmico)
Inspirado na precisão editorial e papéis marfim/cinza técnico, evitando o branco puro ofuscante em fundos amplos:

| Token CSS | Valor Hex | Finalidade |
| :--- | :--- | :--- |
| `--an-bg` | `#F2F1ED` | Fundo geral da aplicação e área de trabalho |
| `--an-surface` | `#FFFFFF` | Superfície de cartões estruturais, cabeçalho e tabela |
| `--an-surface-hover` | `#ECEAE4` | Estados hover, cabeçalhos de tabela (`th`) e separadores |
| `--an-surface-active` | `#E4E1D9` | Estados pressionados e linhas ativas |
| `--an-primary` | `#B52D35` | Vinho Institucional / Carmim ETEC (Ações primárias, foco) |
| `--an-primary-hover` | `#9B242B` | Hover de botões primários |
| `--an-primary-active` | `#801C22` | Estado pressionado do botão primário |
| `--an-primary-soft` | `#F9ECEE` | Fundo sutil de seleção e hover em aulas da grade |
| `--an-primary-text` | `#FFFFFF` | Texto em botões e elementos primários |
| `--an-secondary` | `#292B30` | Grafite profundo para textos principais e elementos escuros |
| `--an-secondary-hover`| `#1E2024` | Hover de elementos secundários escuros |
| `--an-secondary-soft` | `#E8E7E4` | Fundo neutro secundário |
| `--an-border` | `#D5D3CE` | Linhas de divisão padrão, bordas de tabela e inputs |
| `--an-border-strong` | `#BCB9B1` | Bordas enfatizadas e modais |
| `--an-text` | `#292B30` | Tipografia principal (alto contraste legível) |
| `--an-muted` | `#777873` | Rótulos secundários, turnos, horários e legendas |
| `--an-success` | `#327653` | Verde Floresta (sucessos, períodos disponíveis do docente) |
| `--an-success-soft` | `#E9F4ED` | Fundo de períodos disponíveis na matriz de disponibilidade |
| `--an-warning` | `#B47B27` | Âmbar Ocre (aulas fixadas manualmente com cadeado `Lock`) |
| `--an-warning-soft` | `#FDF6E9` | Alertas de diagnóstico e aulas sem professor |
| `--an-danger` | `#B52D35` | Vermelho Carmim (aulas sem professor, remoção, erros) |
| `--an-danger-soft` | `#F9ECEE` | Fundo de indisponibilidade docente e alertas de erro |

### 2.2 Tema Escuro (Oficial — Technical Low-Glare Slate)
Desenvolvido para coordenadores e analistas em sessões de trabalho prolongadas:

| Token CSS | Valor Hex | Finalidade |
| :--- | :--- | :--- |
| `--an-bg` | `#171A20` | Fundo geral da janela |
| `--an-surface` | `#20252D` | Superfície da grade, cabeçalho e painéis |
| `--an-surface-hover` | `#292F3A` | Hover em linhas, slots e cabeçalhos de tabela |
| `--an-surface-active` | `#323A47` | Estados de clique e seleção |
| `--an-primary` | `#568ACB` | Azul Aço Técnico / Cobalt Soft (ações primárias) |
| `--an-primary-hover` | `#699BDC` | Hover do botão primário |
| `--an-primary-active` | `#4777B2` | Estado pressionado do botão primário |
| `--an-primary-soft` | `#1F2D3F` | Fundo sutil de destaque em células e seleção |
| `--an-primary-text` | `#FFFFFF` | Texto em botões primários |
| `--an-secondary` | `#D8DCE3` | Branco acinzentado técnico para tipografia principal |
| `--an-secondary-hover`| `#FFFFFF` | Destaque máximo em texto |
| `--an-secondary-soft` | `#282E38` | Superfície de apoio neutra |
| `--an-border` | `#3A414C` | Linhas de tabela e separadores no tema escuro |
| `--an-border-strong` | `#4F5867` | Bordas estruturais e modais |
| `--an-text` | `#D8DCE3` | Texto principal de leitura descansada |
| `--an-muted` | `#929BA8` | Rótulos secundários, turnos e timestamps |
| `--an-success` | `#69A985` | Verde Sálvia técnico |
| `--an-success-soft` | `#1B2F25` | Fundo de período disponível |
| `--an-warning` | `#D4A454` | Ouro Antigo técnico (aulas com Lock de fixação) |
| `--an-warning-soft` | `#382C18` | Fundo de alertas diagnósticos |
| `--an-danger` | `#D56A70` | Coral Carmim (aulas sem professor, exclusões) |
| `--an-danger-soft` | `#381E21` | Fundo de período bloqueado |

---

## 3. Identidade Visual e Componentes Compartilhados

### 3.1 Identidade da Marca (Logotipo do Ornitorrinco)
- O logotipo histórico do Anatinus (**Ornitorrinco**) existente em `frontend/public/`:
  - No tema claro: `/Anatinus%20final%201.png` (renderizado via classe `.app-logo-light`).
  - No tema escuro: `/anatinus%20final%201%20branco.png` (renderizado via classe `.app-logo-dark`).
- Altura controlada de exatos `24px` no cabeçalho com alinhamento vertical ótico ao lado do wordmark "Anatinus" (`15px`, semi-bold, letter-spacing `-0.02em`).

### 3.2 Cabeçalho Superior Unificado (`.app-header`)
- **Altura**: Exatos `48px` a `50px`.
- **Estrutura**: Marca à esquerda (logo + nome), links de navegação horizontais ao centro (`NavLink` com classe ativa `.active`) e botão de alternância de tema (Sol/Lua) à direita.
- **Itens de Navegação e Rotas Oficiais**:
  - `Grade Horária` (rota `/`, ícone `Calendar`)
  - `Professores` (rota `/professores`, ícone `Users`)
  - `Turmas e Matérias` (rota `/turmas`, ícone `BookOpen`)
  - `Regras e Parâmetros` (rota `/config`, ícone `Settings`)
- **Estado Ativo**: Borda de `1px solid var(--an-border)`, fundo `var(--an-surface-hover)`, texto em peso `600`.

### 3.3 Formulários, Botões e Inputs Técnicos
- **Altura padrão dos controles**: `32px` a `34px`.
- **Botão Primário (`.app-btn-primary`)**: Fundo `var(--an-primary)`, texto branco, raio `2px`, sem sombra difusa.
- **Botão Secundário (`.app-btn-secondary`)**: Fundo `var(--an-surface)`, borda `1px solid var(--an-border)`, texto `var(--an-text)`.
- **Botão de Perigo (`.app-btn-danger`)**: Fundo suave `var(--an-danger-soft)` com texto e ícone em `var(--an-danger)`.
- **Inputs e Selects (`.app-input`, `.app-select`)**: Borda limpa de `1px solid var(--an-border)`, foco com outline sutil de `1px solid var(--an-primary)`.

### 3.4 Modal de Edição de Aula (`.app-modal`)
- Largura máxima de `440px`, centralizado em backdrop semitransparente (`rgba(0, 0, 0, 0.45)`).
- Apresenta nome da disciplina, identificação da turma/grupo, dropdown de seleção do docente atribuído e checkbox para fixação manual da aula (`is_fixed`), finalizando com botões Cancelar e Salvar Alterações.

---

## 4. Especificações das Telas Existentes

### 4.1 Tela Principal: Grade Horária (`App.tsx` — Rota `/`)
A tela de maior relevância operacional do sistema.

1. **Linha de Título e Ações Técnicas**:
   - Título explícito: "Grade Horária" acompanhado do subtítulo dinâmico da entidade selecionada (ex: `3º INFO A (Manhã)` ou nome do docente).
   - Botões utilitários de exportação e impressão (exibidos quando há grade gerada):
     - **Exportar Excel** (`exportTimetableToExcel`): gera arquivo `.xlsx` com abas separadas por turma ou professor.
     - **Imprimir** (`window.print()`): dispara impressão formatada via CSS `@media print` para A4 Paisagem.
2. **Barra de Controle de Visualização e Filtros**:
   - Dropdown de alternância de modo: `Visualizar por Turma` / `Visualizar por Professor`.
   - Campo de busca instantânea (`input type="search"`): filtra turmas pelo nome ou turno (visível apenas no modo turma).
   - Dropdown seletor principal: lista as turmas com indicativo de turno e tag de Grupos A/B, ou a lista de professores.
   - Botão de ação primária: **Gerar grade** (com estado desabilitado e texto "Otimizando horários..." durante a busca do solver CP-SAT).
3. **Painel de Escopo de Otimização (Regeneração Parcial ou Completa)**:
   - Dropdown seletor de escopo com as 4 opções suportadas pela API (`/generate/`):
     - `Escola inteira (completa)` (`scope: "all"`)
     - `Turmas selecionadas` (`scope: "classrooms"`)
     - `Matéria nas turmas selecionadas` (`scope: "subject_selected"`)
     - `Matéria na escola inteira` (`scope: "subject_all"`)
   - Seletor de matéria para os escopos focados em disciplina (`generationSubjectId`).
   - Seletor em grade de turmas (`.app-classroom-picker`) com checkboxes e botões de lote (`Selecionar todas` / `Desmarcar todas`).
4. **Matriz Semanal de Horários (Tabela Oficial)**:
   - Estrutura semântica `<table>` com layout fixo e 5 colunas de dias (`Segunda` a `Sexta`).
   - **Coluna de Horário**: Largura fixa de `120px` a `130px`, exibindo os intervalos oficiais em `JetBrains Mono`:
     - Períodos 0 a 5 (Manhã): `07:10 - 08:00`, `08:00 - 08:50`, `08:50 - 09:40`, `10:00 - 10:50`, `10:50 - 11:40`, `11:40 - 12:30`.
     - Períodos 6 a 10 (Tarde): `13:00 - 13:50`, `13:50 - 14:40`, `14:50 - 15:40`, `15:40 - 16:30`, `16:30 - 17:20`.
     - Períodos 11 a 15 (Noite): `19:00 - 19:45`, `19:45 - 20:30`, `20:30 - 21:15`, `21:30 - 22:15`, `22:15 - 23:00`.
   - **Linhas de Pausa (Intervalo e Almoço)**:
     - `09:40 - 10:00 · Intervalo`
     - `11:40 - 13:00` ou `12:30 - 13:00 · Almoço` (conforme a jornada da turma integral)
     - `14:40 - 14:50 · Intervalo`
     - `21:15 - 21:30 · Intervalo`
   - **Células de Aula (Slots)**:
     - Altura mínima equilibrada de `58px` a `64px`.
     - Nome da disciplina em semi-bold (`12.5px`), nome do docente logo abaixo (`11px`).
     - Aulas sem docente indicado em Carmim com classe `.unstaffed`.
     - Ícone `Lock` discreto no canto superior direito para aulas fixadas pelo usuário (`is_fixed`).
     - **Divisão Prática (Grupos A e B)**: Quando a turma possui divisão, exibe duas sub-células lado a lado (`Grupo A` e `Grupo B`), permitindo clique independente para edição de qualquer uma das metades. Quando a aula for conjunta, exibe a tag "Turma inteira".
5. **Diagnóstico de Aulas Desprovidas de Docente**:
   - Acordeão de aviso suave (`.app-unstaffed-accordion`) informando a contagem de aulas sem professor atribuído na solução atual.

---

### 4.2 Tela de Professores (`pages/Professores.tsx` — Rota `/professores`)
Layout em duas colunas funcionais:

1. **Coluna Esquerda: Cadastro e Edição de Docente**:
   - Campos de Nome e Prioridade/Score (em pontuação de 0 a 100).
   - **Seleção de Disciplinas Habilitadas**:
     - Campo de busca instantânea de disciplinas.
     - Botões em lote: `Marcar visíveis` e `Desmarcar`.
     - Lista compacta em grade com checkboxes das disciplinas que o docente pode lecionar.
   - **Matriz Semanal de Disponibilidade (Auditada: 5 dias × 16 períodos = 80 células)**:
     - Componente expansível (acordeão) indicando o total de períodos disponíveis (ex: `80/80 períodos disponíveis`).
     - Controles em lote: botões `Disponível em tudo` e `Bloquear tudo`.
     - Tabela de 5 dias (Segunda a Sexta) × 16 horários (períodos 0 a 15).
     - **Atalhos de Linha/Coluna existentes no código real**:
       - Clique no cabeçalho do dia da semana (Seg a Sex): alterna a disponibilidade de todos os 16 períodos daquele dia (`toggleWholeDay`).
       - Clique no cabeçalho do turno (Manhã, Tarde, Noite): alterna todos os períodos daquele turno na semana inteira (`toggleWholeShift`).
       - Clique na célula individual: alterna o período entre Disponível (`CheckCircle`, fundo `--an-success-soft`) e Bloqueado (`XCircle`, fundo `--an-danger-soft`).
2. **Coluna Direita: Lista de Professores Cadastrados**:
   - Cabeçalho com totalizador numérico.
   - Lista vertical de cards sóbrios contendo: nome do docente, badge de pontuação (ex: `10 pts`), resumo de disponibilidade (ex: `45/80 períodos`), badges das disciplinas habilitadas e botões de ação rápida para Editar (`Edit`) e Excluir (`Trash2`).

---

### 4.3 Tela de Turmas e Matrizes Curriculares (`pages/Turmas.tsx` — Rota `/turmas`)
Layout balanceado em 3 seções:

1. **Cursos Oferecidos**:
   - Formulário para adicionar novo curso (ex: `Técnico em Informática`, `Ensino Médio`).
   - Lista de cursos com edição inline do nome (`Edit` / `Save` / `X`) e exclusão segura.
2. **Turmas Cadastradas e Configuração de Matrizes**:
   - Formulário de criação de turma: Nome (ex: `3º INFO A`), Turno (`Manhã`, `Integral`, `Noite`), Curso correspondente e checkbox `Permitir Grupos A/B` (disponível para turnos Manhã e Integral).
   - Lista expansível de turmas com turno e quantidade de matérias configuradas.
   - **Matriz Curricular da Turma (quando expandida)**:
     - Botões de atalho: `Incluir todas as disciplinas` e `Limpar matriz`.
     - **Ferramenta de Cópia de Matriz Existente**: Dropdown seletor e botão `Copy` para duplicar as disciplinas e cargas de outra turma compatível do mesmo curso.
     - **Grade de Disciplinas da Matriz**:
       - Checkbox para ativar/desativar a disciplina na turma.
       - Campo de carga horária semanal (número de 1 a 25 aulas).
       - Para turmas com divisão A/B: campos separados para `GA` e `GB`, e seletor entre `Turma inteira` ou `Separada A/B`.
       - Checkbox `Preferir 3 aulas seguidas` (ativo quando a matéria possui carga igual a 3).
     - **Configuração de Sequências Preferidas**:
       - Formulário para definir pares de precedência pedagógica (ex: 1ª matéria `Filosofia` seguida de 2ª matéria `Sociologia`).
       - Lista de badges das sequências ativas com botão `X` para remoção.
3. **Catálogo Geral de Disciplinas**:
   - Formulário para cadastro de disciplina: Nome, Carga horária padrão, Complexidade (`Facil`, `Media`, `Dificil`) e associação aos Cursos correspondentes.
   - Tabela/lista de disciplinas com edição e remoção.

---

### 4.4 Tela de Regras e Parâmetros (`Config.tsx` — Rota `/config`)
Configuração e ajuste fino dos parâmetros do solver CP-SAT:

1. **Restrições Legais Obrigatórias (Auditadas contra o código real do solver)**:
   - Destaque em cartão estrutural com ícone `Shield`:
     - *11 horas de descanso interjornada*: descanso mínimo obrigatório entre o fim da jornada de um dia e o início da do dia seguinte.
     - *Limite máximo de 9 aulas/dia*: limite estrito programado no solver para a jornada diária do docente (`max_classes_per_day <= 9`).
     - *6 aulas consecutivas + 1h de descanso*: janela obrigatória após até 6 aulas consecutivas sem intervalo (`max_consecutive_classes: 6`).
     - *Proibição terminante de janelas para estudantes*: o solver impõe `student_gaps_hard: true` (a grade dos alunos não pode conter horários vagos).
2. **Limites Operacionais da Escola**:
   - `Máximo de aulas diárias por docente`: input numérico ajustável entre 1 e 9.
   - `Máximo de aulas de alta complexidade por dia`: input numérico para equilíbrio cognitivo dos estudantes.
3. **Preferências Docentes**:
   - `Tratamento de janelas para professores`: seletor entre `Evitar janelas como preferência (Soft)` ou `Proibir janelas terminantemente (Hard)`.
   - `Mínimo de aulas quando o professor vier à escola`: input numérico para evitar deslocamentos com apenas 1 aula.
4. **Preferências dos Estudantes e Turmas**:
   - `Mínimo de aulas/dia ativo`: input numérico.
   - `Evitar 1ª aula do dia`: seletor Sim/Não.
   - `Evitar última aula`: seletor Sim/Não.
   - `Evitar sexta-feira`: seletor Sim/Não.
5. **Ação de Persistência**:
   - Botão **Salvar Parâmetros** enviando payload via `PUT /config/` com mensagem de feedback de sucesso ou erro.

---

## 5. Regras de Implementação para o Desenvolvedor Frontend

1. **Preservação de Dependências e Arquitetura**:
   - Utilizar estritamente `@tailwindcss/vite` e `anatinus-design-system.css`.
   - Manter as rotas definidas no `App.tsx` com `react-router-dom` v7 (`/`, `/professores`, `/turmas`, `/config`).
   - Não adicionar bibliotecas pesadas de componentes externos que alterem a identidade visual do sistema.
2. **Contratos de Dados e API**:
   - As chamadas `api.get`, `api.post`, `api.put` e `api.delete` em `/timetable/`, `/teachers/`, `/classrooms/`, `/subjects/`, `/courses/`, `/config/` e `/generate/` devem permanecer idênticas aos esquemas Pydantic do backend FastAPI.
3. **Acessibilidade e Usabilidade**:
   - Manter contraste mínimo WCAG AA em ambos os temas.
   - Utilizar elementos semânticos de formulário (`<select>`, `<input>`, `<button type="button">`, `<table>`, `<thead>`, `<tbody>`).
   - Assegurar que os seletores tenham atributos `aria-label` adequados.
4. **Impressão em Papel**:
   - O arquivo CSS inclui a especificação `@media print` para formato **A4 Paisagem (A4 Landscape)**, ocultando automaticamente cabeçalho, barras de ação, modais e alertas, gerando uma folha de ponto perfeitamente legível para a secretaria escolar.
