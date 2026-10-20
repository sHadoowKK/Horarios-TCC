# ANATINUS — REGISTRO DE TESTES E RESULTADOS

Este arquivo separa **o que já foi observado** do que ainda precisa ser repetido após alterações no solver.

## 1. Testes automatizados

### Execução confirmada após as otimizações de desempenho

O GitHub Actions executou automaticamente a suíte no commit de verificação de 19/10/2026, já incluindo a nova modelagem da regra de descanso e a remoção de variáveis de professores inelegíveis:

```text
Ran 18 tests in 1.562s
OK
```

O tempo acima pertence ao runner do GitHub e não deve ser comparado diretamente com medições feitas no computador local. O dado relevante aqui é que **os 18 testes passaram após as alterações estruturais do solver**.

### Casos cobertos

- turma utiliza apenas matérias selecionadas;
- disciplina sem professor continua na grade;
- professor válido é preferido a "Sem professor";
- divisão A/B por turma + disciplina;
- interjornada de 11h20 permitida;
- interjornada de 10h40 bloqueada;
- 7ª aula sem pausa de 1h bloqueada;
- 7ª aula após pausa >= 1h permitida;
- máximo de 9 aulas/dia;
- bloco noturno de 5 aulas permitido;
- carga diurna 4 tende a 2+2;
- carga diurna 3 tende a 2+1;
- bloco triplo noturno permitido;
- triplo diurno ainda possível se necessário;
- semana noturna completa de 25 aulas;
- grupos A/B com matérias diferentes simultaneamente;
- duas turmas concorrendo pelo mesmo professor;
- cenário integrado com várias turmas e professores compartilhados.

---

## 2. Build do frontend

O build local já havia sido validado em 01/10/2026. Após as alterações mais recentes, o GitHub Actions executou novamente a compilação de produção e concluiu com sucesso:

```text
✓ 1988 modules transformed.
✓ built
```

O tempo do build depende do ambiente e não é usado como métrica de desempenho do Anatinus.

---

## 3. Teste manual do fluxo completo

Confirmado manualmente:

- cadastro de cursos;
- cadastro de turmas;
- cadastro de disciplinas;
- categoria removida da interface;
- matriz específica por turma;
- professores e disponibilidade;
- geração de grade;
- exibição de "Sem professor";
- visão por turma;
- visão por professor;
- salvamento da grade;
- atualização de listas sem F5;
- tema escuro.

Também foi observado que a grade antiga permanecia visível durante uma nova geração. A interface foi modificada para avisar explicitamente que se trata da última grade salva enquanto o cálculo está em andamento.

---

## 4. Benchmark base ANTES das otimizações

Resultado do cenário sintético small informado em 01/10/2026:

```text
Cenário: small
Turmas: 5
Disciplinas no catálogo: 12
Professores: 14
Aulas/unidades esperadas: 105

Status: success
Tempo total medido: 19.009s
Estado da solução: optimal
Tempo informado pelo solver: 16.305s
Aulas geradas: 105
Aulas sem professor: 0
```

Esse resultado serve como **baseline anterior** às seguintes otimizações:

1. substituição da enumeração de combinações da regra de descanso por contadores de sequência;
2. remoção de variáveis de professores inelegíveis.

### Próxima medição obrigatória

Executar novamente:

```powershell
python benchmark_optimizer.py --size small
python benchmark_optimizer.py --size medium
python benchmark_optimizer.py --size large
```

Registrar:
- status;
- tempo total;
- tempo do solver;
- variáveis do modelo;
- restrições do modelo;
- objective value;
- best objective bound;
- aulas geradas;
- aulas sem professor.

Não comparar tempos de máquinas diferentes como se fossem equivalentes.

---

## 5. Evidências úteis para Resultados e Discussão

### Falta de professor
A interface já demonstrou grades válidas com disciplinas exibidas como "Sem professor", sem impedir o restante do horário.

### Distribuição 2+2
Foi observado em testes que quatro aulas diurnas de uma disciplina podem ser favorecidas em distribuição 2+2 em vez de 1+1+1+1.

### Visão por professor
Foi verificado que a visualização agrega aulas de diferentes turmas e grupos sem duplicar o professor em um mesmo período.

### Timeout
Foi observado um timeout de 20 segundos quando frontend e solver possuíam limites coincidentes. Depois:
- frontend passou a esperar 60s;
- solver passou a ter limite de 30s;
- timeout foi separado de infeasibilidade.

---

## 6. O que ainda falta medir de forma séria

- tempo manual para criar uma grade comparável;
- tempo de configuração no Anatinus;
- tempo de geração em base real completa;
- quantidade de ajustes manuais necessários após geração;
- opinião de quem efetivamente monta a grade;
- taxa de "Sem professor" em dados reais;
- comportamento com todas as turmas e professores da instituição.

Esses dados são necessários antes de fazer afirmações quantitativas no TCC.
