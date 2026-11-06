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

## 3. Base de regressão inspirada nas grades da ETEC

A base `seed_realista.py` continua existindo para exercitar o modelo com oito turmas, incluindo 3º INFO, TI Noturno e seis turmas Agro. Parte das cargas e disponibilidades de Agro permanece provisória, e essa base não é a escolhida para a demonstração principal.

Resultado mais recente da geração conjunta em 06/11/2026:

| Indicador | Resultado |
|---|---:|
| Turmas | 8 |
| Aulas previstas e geradas | 291 |
| Aulas com professor | 234 |
| Aulas sem professor | 57 |
| Estado do solver | `feasible` |
| Tempo do solver | 120,80 s |
| Variáveis / restrições | 40.012 / 65.835 |

A validação confirmou as cargas configuradas, persistência SQLite, ausência de conflitos simultâneos de professores, ausência de janelas de alunos e respeito às disponibilidades, aos limites docentes e aos descansos verificados.

**Limitação importante:** essa geração ainda não é uma grade pronta para ser apresentada como horário final da escola. As 57 aulas sem professor incluem matérias sem docente habilitado cadastrado e aulas que não receberam um dos docentes candidatos na otimização conjunta. Além disso, o relatório mostrou distribuição diária bastante desigual em algumas turmas Agro. O teste atual verifica principalmente viabilidade e restrições obrigatórias; não estabelece uma nota mínima de qualidade visual para essa base. Portanto, não afirmar que a grade de regressão de oito turmas está aprovada.

## 4. 3º INFO isolado

O cenário do 3º INFO Integral A/B foi gerado pela própria função da API e persistido no SQLite:

- 57 alocações;
- zero aulas sem professor;
- estado `feasible`;
- tempo aproximado de 18,70 s no runner Linux;
- cargas e separações A/B preservadas.

A disponibilidade docente utilizada é provisória, pois o quadro de referência não contém a disponibilidade semanal completa de cada professor.

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
