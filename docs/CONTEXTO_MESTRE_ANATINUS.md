# ANATINUS — CONTEXTO MESTRE PARA CONTINUIDADE

> Use este arquivo quando o projeto precisar continuar em outro chat, outra conta ou com outra pessoa.

## Projeto

Nome: **Anatinus**

Objetivo: sistema web para cadastro de dados acadêmicos e geração automática de grades horárias escolares.

Repositório privado: `sHadoowKK/Horarios-TCC`

Pasta local principal no Windows:

```text
C:\Projetos\Horarios-TCC
```

## Tecnologia

Frontend:
- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- Axios;
- Lucide React.

Backend:
- Python;
- FastAPI;
- Pydantic;
- SQLAlchemy;
- SQLite;
- Uvicorn.

Otimização:
- Google OR-Tools CP-SAT.

O sistema deve ser descrito como **otimização combinatória / programação por restrições**, e não simplesmente como IA.

## Estado verificado em 06/11/2026

- PR #7 aberta em draft na branch `gemini-atualizado-20261029-1451`; não foi mesclada na `main`.
- 36 testes automatizados do backend passaram na última execução verificada do CI (29 cenários do solver e 7 testes de integração).
- Build de produção do frontend passou.
- Build Windows com PyInstaller e o smoke test anterior em AppData limpo passaram no runner do GitHub. A revisão atual do smoke test exige exatamente 100 aulas fictícias; a nova execução ainda está pendente.
- A base fictícia de apresentação gerou 100 aulas pela API, todas com professor, e passou na validação conjunta.
- A base de regressão ETEC com oito turmas gerou 291 aulas, 234 com professor e 57 sem professor. Restrições obrigatórias foram validadas, mas a distribuição docente/diária ainda não deve ser apresentada como grade final.
- O texto escrito do TCC não foi alterado nesta rodada.

O workflow Windows agora está configurado para também executar em push na branch de trabalho e publicar o ZIP fora de eventos pull_request. A publicação do próximo artefato ainda precisa ser confirmada/baixada.

## Base fictícia principal para apresentação

Script: `backend/seed_apresentacao.py` e atalho `start-demo.ps1`.

- 2 cursos, 3 turmas, 15 disciplinas, 15 professores.
- 1º DS Integral com grupos A/B, 2º DS Integral e 1º ADM Integral.
- 100 aulas geradas e persistidas pela API; 100 com professor, 0 sem professor.
- A validação conjunta confirmou seis aulas por dia em cada turma/grupo, ausência de conflitos docentes, ausência de janelas de alunos e as verificações de disponibilidade/descanso.
- Estado `feasible`, cerca de 120,6 s no runner; não foi provada optimalidade.
- Todos os dados são inventados. O banco `school_schedule_demo.db` fica separado de `school_schedule.db`.

O atalho `start-demo.ps1` recria a base fictícia antes de abrir a interface. Para usar o recorte separado do 3º INFO, execute `start-informatica.ps1`; esse atalho usa `start-demo.ps1 -SkipSeed` para não sobrescrever o banco que acabou de preparar.

A base ETEC de oito turmas usa também `school_schedule_demo.db`, por isso é um cenário de regressão alternativo: não execute seus seeds imediatamente antes da apresentação principal sem recriar a base fictícia.

## Jornadas

Manhã:
- 07:10–08:00
- 08:00–08:50
- 08:50–09:40
- intervalo
- 10:00–10:50
- 10:50–11:40
- 11:40–12:30

Integral:
- manhã até 11:40;
- almoço 11:40–13:00;
- 13:00–13:50
- 13:50–14:40
- intervalo
- 14:50–15:40
- 15:40–16:30
- 16:30–17:20

Noite:
- 19:00–19:50
- 19:50–20:30
- 20:30–21:15
- intervalo
- 21:30–22:15
- 22:15–23:00

## Regras centrais

Hard:
- professor não ocupa duas turmas simultaneamente;
- turma/grupo não recebe duas aulas simultâneas;
- carga semanal deve ser cumprida;
- jornada da turma é respeitada;
- disponibilidade docente é respeitada;
- interjornada mínima de 11 horas;
- máximo de 9 aulas por professor/dia;
- após sequência de até 6 aulas, precisa existir pausa de pelo menos 1h antes de continuar;
- alunos não têm janelas internas.

Soft / configuráveis:
- reduzir janelas de professor;
- mínimo de aulas quando docente vai à escola;
- priorizar pontuação docente;
- aproximar grupos A/B;
- evitar primeiro/último período e sexta;
- diurno prefere blocos de duas aulas.

## Distribuição de matérias

Manhã/Integral:
- 2 aulas da mesma matéria no dia é ideal;
- 1 aula isolada é permitida;
- 3+ no mesmo dia é menos desejável, mas possível.

Noite:
- blocos de 3, 4 e 5 são normais e não devem ser proibidos.

## Sem professor

Se não houver docente:
- a matéria continua na grade;
- `teacher_id = null`;
- interface mostra **Sem professor**;
- alternativa recebe penalidade alta para ser evitada quando houver professor válido.

## Matriz e grupos

Cada turma possui sua própria matriz.

A disciplina global fornece apenas valores padrão.

Para turma com A/B:
- Turma inteira: A e B juntos;
- Separada A/B: cargas independentes.

A/B pode:
- ter matérias diferentes no mesmo horário;
- ter professores diferentes;
- ter um grupo livre quando necessário.

O sufixo A/B no nome de uma turma não significa o mesmo que os grupos internos.

## Fora do escopo

- salas;
- laboratórios;
- estudantes individualmente;
- login/autenticação na versão atual;
- multiusuário em produção;
- IA generativa.

## Scripts úteis

Iniciar desenvolvimento:

```powershell
.\start-dev.ps1
```

Backup:

```powershell
.\backup-db.ps1
```

Verificação:

```powershell
.\verify.ps1
```

Benchmark:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python benchmark_optimizer.py --size small
python benchmark_optimizer.py --size medium
python benchmark_optimizer.py --size large
```

## Benchmark conhecido

Antes das duas otimizações estruturais:

- cenário small;
- 5 turmas;
- 14 professores;
- 105 aulas/unidades;
- 0 aulas sem professor;
- solução optimal;
- 16,305 s no solver;
- 19,009 s total.

Esse benchmark precisa ser repetido na mesma máquina para medir o ganho real da versão atual.

## Matriz de referência — 3º INFO

O seed `backend/seed_realista.py --informatica-only` transcreve as matérias e cargas legíveis da imagem original de 3º INFO integral:

- Matemática: 3; Português: 3 no quadro transcrito; UDA: 2; SW2: A=3/B=2; CNW2: 2; DDM2: 2; IRS: 2; EAMT: 3; EACNT: 3; PDTCC: 2; GCW: 2; Filosofia: 1; Sociologia: 1; Espanhol: 2; História: 2; Inglês: 2; Geografia: 2.
- Professores elegíveis transcritos do quadro: UDA/Erika; SW2/Higor (A) e Marcel (B); CNW2/Erika (A) e Marcel (B); Filosofia e Sociologia/M. Emília; Espanhol/Célia; História/M. Emília; DDM2/Marcel; IRS/Joesley; Matemática/Kamila; Inglês e Português/Marta; EAMT/Gustavo; EACNT/Fabiane; PDTCC/Marcel; GCW/Higor; Geografia/Thiago.
- O 3º INFO guarda uma preferência Soft Filosofia → Sociologia. A interface permite configurar outras sequências entre matérias, sem codificar nomes específicos no otimizador.
- SW2 é o exemplo confirmado de cargas diferentes: 3 aulas para A e 2 para B. A validação do gerador calcula a capacidade de cada grupo de forma independente.
- As disponibilidades docentes da imagem não são suficientes para reconstruir a disponibilidade individual de toda a semana; para o teste isolado de Informática, os professores estão liberados em todos os dias/períodos do Integral de segunda a sexta. Isso é uma hipótese de teste, não disponibilidade oficial.

## Empacotamento desktop Windows

A branch atual de trabalho da PR é `gemini-atualizado-20261029-1451`.

- `backend/app/desktop.py` inicia FastAPI e abre a interface numa janela PyWebView.
- `backend/app/main.py` serve o frontend compilado quando o pacote desktop está em execução.
- `frontend/src/api.ts` usa a API na mesma origem na build de produção.
- `backend/app/database.py` guarda os dados desktop em `%LOCALAPPDATA%\\Anatinus\\school_schedule.db`.
- `build-windows.ps1` executa testes, build, empacotamento e smoke test.
- O CI Windows concluiu o build e smoke test em AppData limpo; o ZIP foi criado no runner, mas o upload foi pulado no evento pull_request.
- `.github/workflows/build-windows.yml` foi configurado para executar também em push na branch atual e publicar o artefato fora de pull_request. Confirmar o próximo artefato antes de considerar essa entrega concluída.

O pacote Windows só deve ser considerado pronto depois de baixar, extrair e testar o ZIP em um Windows real, inclusive navegação, Excel, impressão e persistência.

## Arquivos de documentação

- `../README.md`
- `DOCUMENTACAO_TCC.md`
- `RESULTADOS_TESTES.md`
- `GUIA_APRESENTACAO.md`
- `CHECKLIST_ENTREGA.md`
- `REVISAO_CODIGO.md`
- este arquivo.

## TCC

A versão escrita deve conter:
- introdução;
- problema;
- objetivos;
- justificativa;
- hipótese;
- referencial teórico;
- metodologia;
- resultados e discussão;
- considerações finais;
- referências;
- apêndices.

Evitar alegações não medidas como:
- redução de 70%;
- eliminação de todos os conflitos;
- melhor grade garantida;
- sistema pronto para qualquer escola.

## Próximos passos prioritários

1. confirmar e baixar o ZIP do Windows gerado no próximo push da branch;
2. abrir o EXE em Windows real e testar interface, Excel, impressão, backup e restauração;
3. repetir benchmarks small/medium/large na mesma máquina do baseline;
4. revisar e calibrar a geração de regressão das oito turmas com dados docentes mais completos;
5. obter avaliação de alguém da escola que monta horários;
6. triar as três vulnerabilidades de alta severidade reportadas pelo npm no install do frontend, sem aplicar atualizações automáticas sem validação;
7. terminar apêndice, conclusão, referências e formatação final do TCC;
8. ensaiar a demonstração com a base fictícia de 100 aulas.
