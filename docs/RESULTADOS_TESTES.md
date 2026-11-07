# ANATINUS — REGISTRO DE TESTES E RESULTADOS

Atualizado em 06/11/2026. Este documento registra resultados observados no GitHub Actions e separa a base fictícia de apresentação da base de regressão inspirada na ETEC. Não substitui a seção de Resultados do TCC.

## 1. Testes automatizados e build

Na execução mais recente do GitHub Actions:

```text
Ran 36 tests in 4.776s
OK
```

A suíte contém 29 cenários do otimizador e 7 testes de integração do backend. O tempo é do runner Linux do GitHub e não deve ser comparado diretamente com medições no computador local.

O build de produção do frontend passou (1.952 módulos transformados). O build Windows também concluiu o empacotamento com PyInstaller e executou o smoke test do Anatinus.exe em um AppData limpo.

Durante o `npm install` do CI, o npm reportou três vulnerabilidades de alta severidade nas dependências do frontend. Elas ainda não foram triadas nem corrigidas nesta rodada; não apliquei `npm audit fix` automaticamente para evitar atualizações potencialmente incompatíveis sem validação.

## 2. Base fictícia principal para a apresentação

O modo de apresentação usa `backend/seed_apresentacao.py`. Os dados são inteiramente inventados e ficam em `backend/school_schedule_demo.db`, separados do banco de desenvolvimento e de qualquer cadastro real.

Resultado observado em 06/11/2026:

| Indicador | Resultado |
|---|---:|
| Cursos | 2 |
| Turmas | 3 |
| Disciplinas | 15 |
| Professores | 15 |
| Aulas geradas e salvas | 100 |
| Aulas com professor | 100 |
| Aulas sem professor | 0 |
| Estado do solver | `feasible` |
| Tempo do solver | 120,55 s |
| Variáveis / restrições | 9.338 / 16.979 |

A validação conjunta da mesma base, repetida pela API, confirmou novamente as 100 aulas, todas com professor, e persistência correspondente no SQLite. O relatório diário confirmou seis aulas por dia, de segunda a sexta, em cada turma/grupo: 1º DS Integral A, 1º DS Integral B, 2º DS Integral e 1º ADM Integral. Não foram encontrados conflitos de professores, indisponibilidades violadas, janelas de alunos ou violações das regras de descanso verificadas.

A distribuição visual ficou consistente para demonstração: as aulas de duas horas aparecem majoritariamente em blocos duplos; disciplinas com três aulas semanais aparecem em combinações de uma e duas aulas. A solução é válida, mas `feasible` não significa que o solver provou optimalidade.

**Este é o cenário recomendado para a apresentação.** O atalho `start-demo.ps1` recria essa base antes de abrir a interface. A recriação leva cerca de dois minutos no runner testado.

## 3. Base realista transcrita da planilha escolar

O script `backend/seed_realista.py` foi substituído por uma transcrição da planilha **03-09.26 - Horários Diurno-Noturno e Síncronas**, atualizada em 03/09/2026 às 13h. O script não copia os horários prontos para o resultado: usa as matrizes, as cargas e as associações disciplina/docente como entradas para que o Anatinus gere uma nova distribuição.

Resumo da transcrição:

| Indicador | Resultado |
|---|---:|
| Quadros de turma preenchidos na planilha | 21 |
| Quadros diurnos usados no solver | 11 |
| Quadros técnicos modulares noturnos usados no solver | 8 |
| Registros de turma no banco após separar 1º INFO A/B | 20 |
| Grafias de disciplinas normalizadas no quadro | 103 |
| Disciplinas no catálogo após unificar uma variação evidente de abreviação | 102 |
| Docentes identificados e anonimizados | 51 |
| Lançamentos semanais transcritos | 695 |

O primeiro INFO noturno aparece em duas colunas de cargas diferentes. Como o modelo não divide turmas noturnas em grupos, o seed cria duas turmas independentes — `1º INFO A` e `1º INFO B` — cada uma com 25 aulas semanais.

As células mescladas dos quadros diurnos representam aulas para a turma toda. Células independentes nas colunas A/B representam cargas próprias dos grupos. Exemplos conferidos:

| Turma | Aulas conjuntas | Específicas A | Específicas B | Carga de cada grupo |
|---|---:|---:|---:|---:|
| 1º PI AGRO A/B | 26 | 10 | 10 | 36 |
| 2º PI AGRO A/B | 26 | 10 | 10 | 36 |
| 3º INFORMÁTICA | 22 | 14 | 14 | 36 |
| 1º ITINERÁRIO | 24 | 6 | 6 | 30 |
| 2º ITINERÁRIO | 18 | 12 | 12 | 30 |
| 3º ITINERÁRIO | 18 | 12 | 12 | 30 |
| 1º ALIMENTOS | 20 | 12 | 12 | 32 |

Os dois quadros MTEC (com início às 18h30) e os sete registros de aulas síncronas mensais não entram nessa base semanal. O modelo atual não representa a jornada própria das turmas MTEC nem encontros que acontecem apenas em datas específicas. Eles não foram convertidos artificialmente em aulas semanais.

### Limitações que permanecem explícitas

- A planilha mostra horários existentes e associação de docentes às disciplinas; ela **não informa a disponibilidade semanal completa de cada docente**. O seed usa disponibilidade ampla e sintética nos turnos em que o docente aparece, apenas para permitir o teste do gerador. Isso não deve ser confundido com a disponibilidade real da escola.
- Os nomes dos docentes são substituídos por identificadores como `Docente 01`, preservando as associações de habilitação sem expor nomes pessoais.
- O quadro não informa nível de complexidade das disciplinas. O seed usa complexidade neutra (`Media`) e não inventa pesos pedagógicos.
- Algumas abreviações que diferem apenas por pontuação foram normalizadas. As formas `C.P.D.P.J` e `CPDPI` foram unificadas como uma única disciplina porque a lista de habilitações registra essa mesma matéria como `CPDPI`.
- A planilha é uma referência de entrada; o horário gerado pelo Anatinus deve ser uma nova solução, não uma reprodução do quadro original.

Comandos disponíveis, executados dentro de `backend`:

```powershell
python seed_realista.py
python seed_realista.py --diurno-only
python seed_realista.py --noturno-only
python seed_realista.py --informatica-only
```

Todos recriam somente `school_schedule_demo.db`; o banco normal `school_schedule.db` não é alterado. A geração do horário deve ser acionada depois pela interface.

## 4. Cenários anteriores de regressão

Os números registrados abaixo são resultados históricos da versão anterior do seed e não descrevem a nova transcrição da planilha. Eles permanecem como evidência dos testes já executados, mas precisam ser repetidos usando a base atual antes de qualquer conclusão sobre desempenho ou qualidade da grade.

### Geração anterior com oito turmas

| Indicador | Resultado histórico |
|---|---:|
| Turmas | 8 |
| Aulas previstas e geradas | 291 |
| Aulas com professor | 234 |
| Aulas sem professor | 57 |
| Estado do solver | `feasible` |
| Tempo do solver | 120,80 s |
| Variáveis / restrições | 40.012 / 65.835 |

A validação confirmou cargas, persistência SQLite, ausência de conflitos simultâneos de professores, ausência de janelas de alunos e respeito às disponibilidades configuradas, aos limites docentes e aos descansos verificados.

**Limitação importante:** essa geração histórica não era uma grade final aceitável. Havia 57 aulas sem professor e distribuição diária desigual em algumas turmas Agro. Não declarar essa base antiga como aprovada.

### 3º INFO isolado, versão anterior

O cenário anterior do 3º INFO foi gerado e persistido pela API com 57 alocações e zero aulas sem professor. Esse número não deve ser confundido com a nova matriz corrigida da planilha, cuja carga é 36 aulas para cada grupo A/B.

## 5. Aplicativo Windows

- O script `build-windows.ps1` gerou `Anatinus.exe` e `release/Anatinus-Windows-x64.zip` no runner Windows.
- O smoke test abriu o EXE com AppData limpo, iniciou a API local e confirmou 57 aulas acessíveis pela rota `/timetable/`.
- O job Windows terminou com sucesso em 06/11/2026.
- O upload do ZIP foi pulado no evento de pull request para evitar consumo de cota. O arquivo foi criado no runner, mas não ficou disponível como artefato para download.
- Ainda falta abrir a janela gráfica em um Windows real e testar navegação, Excel, impressão, backup/restauração e o computador/projetor da apresentação.

## 6. Benchmarks

O baseline conhecido antes das otimizações permanece:

```text
Cenário: small
Turmas: 5
Disciplinas no catálogo: 12
Professores: 14
Aulas/unidades esperadas: 105
Status: success
Tempo total: 19,009 s
Tempo do solver: 16,305 s
Estado: optimal
Aulas geradas: 105
Aulas sem professor: 0
```

Esse resultado foi medido em 01/10/2026, antes das otimizações. Os benchmarks `small`, `medium` e `large` ainda precisam ser repetidos na mesma máquina para comparação justa. Nenhum ganho percentual deve ser declarado antes dessas medições.

## 7. Pendências manuais e de entrega

- abrir a janela gráfica do EXE em Windows real;
- testar fluxo completo pela interface e visões por turma/professor;
- conferir A/B e Filosofia → Sociologia visualmente;
- validar exportação Excel (.xlsx), impressão e backup/restauração;
- obter avaliação de alguém da escola que monta horários;
- repetir benchmarks small, medium e large;
- testar no computador/projetor da apresentação;
- concluir apêndice, conclusão e referências do TCC escrito.

O texto escrito do TCC não foi alterado nesta rodada.
