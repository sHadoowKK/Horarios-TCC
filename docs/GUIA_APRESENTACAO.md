# ANATINUS — GUIA DE APRESENTAÇÃO E DEMONSTRAÇÃO

## Objetivo da apresentação

Mostrar que o projeto resolve um problema de **otimização escolar com muitas restrições concorrentes**, e não apenas que possui uma interface bonita.

---

## 1. Demonstração recomendada

### Etapa 1 — Gestão Acadêmica
Mostrar rapidamente:
- cursos;
- turmas;
- disciplinas;
- matriz própria de uma turma;
- carga semanal;
- grupo A/B.

Frase curta:

> "A matriz não é global. Cada turma informa quais disciplinas possui, a carga semanal e se a disciplina ocorre com a turma inteira ou separada em A/B."

### Etapa 2 — Professores
Mostrar:
- disciplinas habilitadas;
- pontuação;
- disponibilidade;
- atalhos por dia e turno.

Frase:

> "A disponibilidade representa quando o professor pode trabalhar aqui. Regras como as 11 horas de interjornada são calculadas pelo solver, não precisam ser marcadas manualmente."

### Etapa 3 — Regras e Preferências
Explicar a diferença:

**Hard**
- não pode violar.

**Soft**
- tenta melhorar, mas pode abrir exceção.

Exemplo:

> "Um professor em duas turmas ao mesmo tempo é proibido. Já o bloco de duas aulas é uma preferência; se a realidade exigir, o sistema pode usar outra distribuição."

### Etapa 4 — Gerar
Clicar em Gerar Nova Grade.

Enquanto calcula:

> "A grade anterior permanece visível e identificada como a última salva."

### Etapa 5 — Resultado por turma
Mostrar:
- aulas;
- intervalos;
- Sem professor;
- blocos.

### Etapa 6 — Resultado por professor
Trocar a visão.

Frase:

> "Aqui o mesmo resultado é reorganizado pela agenda docente, o que facilita conferir conflitos e carga."

### Etapa 7 — Exportação
Mostrar:
- Exportar Excel (.xlsx);
- Imprimir.

---

## Preparação do cenário principal de demonstração

A geração conjunta da base com oito turmas ainda não está validada: o teste atual termina por timeout. Para a apresentação, use o banco isolado do **3º INFO**, que mantém os grupos A/B e a preferência Filosofia → Sociologia.

Na raiz do projeto, execute:

```powershell
cd backend
.\\.venv\\Scripts\\python.exe seed_realista.py --informatica-only
cd ..
.\\start-demo.ps1
```

O script recria somente `backend/school_schedule_demo.db`; não altera o banco normal `school_schedule.db`. O CI também valida a geração do 3º INFO pela API e o salvamento da grade.

Não apresente a geração das oito turmas como concluída. O modo completo permanece uma limitação em investigação. Tenha screenshots da grade do 3º INFO como plano de contingência.

---
## 2. Explicação simples do CP-SAT

Versão de 20 segundos:

> "O Anatinus transforma cada possibilidade de aula em variáveis e informa ao CP-SAT quais combinações são permitidas ou proibidas. Depois define preferências com pesos. O solver procura uma combinação que cumpra as regras obrigatórias e, entre as válidas, tenta melhorar as preferências."

---

## 3. Perguntas prováveis da banca

### "Isso é inteligência artificial?"
Resposta:

> "Não no sentido de IA generativa. O núcleo é programação por restrições e otimização combinatória usando o CP-SAT do Google OR-Tools."

### "Ele sempre encontra a melhor grade?"
Resposta:

> "Se retornar optimal, o solver provou a optimalidade dentro daquele modelo. Também pode retornar uma solução feasible, que é válida mas sem prova de ser a melhor, principalmente quando há limite de tempo."

### "E se não existir professor para uma matéria?"
Resposta:

> "A matéria não desaparece. Ela fica reservada na grade como Sem professor. Essa opção recebe penalidade alta e só é usada quando não há alternativa docente melhor."

### "Por que não bloquear tudo como regra?"
Resposta:

> "Porque uma escola real possui exceções. Se toda preferência virar proibição, o sistema pode tornar uma grade possível artificialmente inviável."

### "Como funciona A/B?"
Resposta:

> "A divisão é configurada por turma e disciplina. Uma matéria pode ser conjunta e outra separada. Quando separada, A e B possuem cargas independentes."

### "Como vocês sabem que funciona?"
Resposta:

> "Temos testes automatizados para regras específicas e cenários integrados, build de produção do frontend, testes manuais do fluxo completo e benchmark separado para desempenho."

### "Por que SQLite?"
Resposta:

> "É adequado ao protótipo local e simplifica implantação durante o TCC. Para ambiente multiusuário em produção seria razoável migrar para um banco servidor."

### "Qual foi a maior dificuldade?"
Resposta sugerida:

> "Transformar regras descritas de forma humana em restrições matemáticas sem deixar o modelo rígido demais. Vários comportamentos tiveram que ser revistos depois de comparar com grades reais."

### "O sistema substitui a coordenação?"
Resposta:

> "Não. Ele automatiza verificação e busca combinatória. A coordenação continua responsável pelas decisões pedagógicas, exceções e validação final."

### "Qual é a principal limitação?"
Resposta:

> "Desempenho e calibração quando a quantidade de restrições cresce, além da necessidade de validar com uma base completa da escola."

---

## 4. Coisas que NÃO devem ser ditas

Evitar:
- "elimina 100% dos erros";
- "reduz 70% do tempo";
- "usa IA";
- "já está pronto para qualquer escola";
- "sempre encontra a grade perfeita";
- "substitui a coordenação";
- "foi testado em toda a escola", se isso ainda não tiver ocorrido.

---

## 5. Plano B para o dia da apresentação

Antes da banca:
1. iniciar backend;
2. iniciar frontend;
3. gerar uma grade uma vez;
4. deixar a grade salva;
5. tirar screenshots;
6. manter o banco de demonstração pronto.

Se a geração ao vivo demorar:
- mostrar a última grade salva;
- explicar que o solver possui limite de tempo;
- usar os screenshots;
- não ficar repetindo o botão de gerar.

---

## 6. Comandos do dia

Backend:

```powershell
cd C:\Projetos\Horarios-TCC\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

Frontend:

```powershell
cd C:\Projetos\Horarios-TCC\frontend
npm run dev
```

Abrir:

```text
http://localhost:5173
```
