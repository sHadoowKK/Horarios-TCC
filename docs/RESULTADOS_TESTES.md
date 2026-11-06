# ANATINUS — REGISTRO DE TESTES E RESULTADOS

Atualizado em 06/11/2026. Este documento registra somente resultados observados em CI; ele não substitui a seção de Resultados do TCC.

## 1. Testes automatizados

Execução confirmada no GitHub Actions:

```text
Ran 36 tests in 6.751s
OK
```

A suíte contém 29 cenários do otimizador e 7 testes de integração do backend. O tempo é do runner Linux do GitHub e não deve ser comparado diretamente com medições no computador local.

## 2. Cenário de demonstração do 3º INFO

Foi validado o banco isolado criado por `seed_realista.py --informatica-only`, usando a própria função da API `generate_timetable` (o mesmo fluxo chamado pela interface).

Resultado observado:

- Turma: 3º INFO Integral, com grupos A/B.
- Aulas geradas: 57 alocações de grade.
- Aulas sem professor: 0.
- Estado: `feasible` (solução válida; não foi comprovada como ótima).
- Tempo do solver: 19,31 s.
- A geração foi salva no SQLite e a quantidade de registros persistidos correspondeu à quantidade retornada pela API.
- O teste também conferiu ausência de janelas de alunos.

Esse cenário é o recomendado para a demonstração. A disponibilidade docente utilizada é provisória, pois o quadro de referência não contém a disponibilidade semanal completa de cada professor.

## 3. Validação individual da base com oito turmas

O validador executou cada turma separadamente, conferindo a carga esperada, a quantidade de aulas, ausência de janelas dos alunos e métricas do solver. Resultados do runner:

| Turma | Aulas | Sem professor | Estado | Tempo | Variáveis | Restrições |
|---|---:|---:|---|---:|---:|---:|
| 3º INFO | 57 | 0 | feasible | 19,77 s | 8.085 | 15.262 |
| TI — Noite | 25 | 0 | optimal | 0,47 s | 1.189 | 2.406 |
| 1º PI AGRO A | 36 | 3 | feasible | 18,65 s | 7.260 | 14.340 |
| 1º PI AGRO B | 35 | 3 | feasible | 18,89 s | 7.260 | 14.344 |
| 2º PI AGRO A | 37 | 3 | feasible | 18,86 s | 6.911 | 13.642 |
| 2º PI AGRO B | 33 | 5 | feasible | 18,21 s | 6.559 | 12.971 |
| 3º PI AGRO A | 34 | 0 | feasible | 18,65 s | 6.579 | 12.636 |
| 3º PI AGRO B | 34 | 0 | feasible | 18,79 s | 6.579 | 12.636 |

**Limite desta validação:** as oito turmas foram testadas individualmente. Isso não verifica conflitos de professores entre turmas diferentes. As disponibilidades docentes e parte das cargas de Agro permanecem provisórias; as aulas “Sem professor” encontradas nessas turmas devem ser interpretadas dentro desse contexto.

## 4. Geração da escola inteira

A geração conjunta das oito turmas ainda não foi validada. As tentativas anteriores terminaram em timeout sem encontrar uma solução dentro do limite de busca. Timeout não prova inviabilidade, mas também não permite afirmar que a grade da escola inteira funciona.

Não usar o resultado individual das oito turmas como evidência de uma grade escolar conjunta.

## 5. Build do frontend e aplicativo Windows

- O build de produção do frontend passou no GitHub Actions.
- O empacotamento Windows com PyInstaller concluiu com sucesso em uma execução anterior.
- O passo de publicação do ZIP foi pulado no fluxo de pull request para não tentar consumir mais cota de artefatos enquanto o armazenamento do GitHub Actions está esgotado.
- O script `build-windows.ps1` foi atualizado depois para criar o banco inicial somente com o 3º INFO, gerar a grade pela API e validar sua persistência antes de empacotar. Essa versão atualizada ainda precisa concluir seu próprio workflow.
- O executável ainda precisa ser aberto em um Windows real, extraído de um ZIP completo e testado quanto à persistência, exportação e backup/restauração.

## 6. Benchmarks

O baseline anterior às otimizações permanece:

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

Esse resultado foi medido em 01/10/2026, antes das otimizações. Os benchmarks `small`, `medium` e `large` ainda precisam ser repetidos na versão atual; nenhum ganho percentual deve ser declarado até essa comparação ser feita no mesmo ambiente.

## 7. Testes manuais ainda pendentes

- abrir o executável Windows em pasta limpa;
- testar fluxo completo pela interface;
- conferir visão por turma e por professor;
- testar grupos A/B e a preferência Filosofia → Sociologia visualmente;
- validar exportação Excel (.xlsx) e impressão;
- testar backup e restauração;
- validar no computador e projetor da apresentação;
- obter avaliação de alguém da escola que monta horários.