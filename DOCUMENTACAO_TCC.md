# ANATINUS — DOCUMENTAÇÃO TÉCNICA PARA O TCC

> Estado consolidado em 19/10/2026. Este arquivo é a fonte de verdade resumida do projeto.  
> Antes de afirmar algo no TCC ou na apresentação, conferir o status abaixo.

## 1. Definição correta do projeto

O **Anatinus** é um sistema web para cadastro de dados acadêmicos e geração automática de grades horárias escolares.

A geração utiliza **otimização combinatória / programação por restrições**, com o solucionador **CP-SAT do Google OR-Tools**.

### Termos recomendados

Use:
- solucionador;
- otimizador;
- programação por restrições;
- otimização combinatória;
- CP-SAT;
- restrições obrigatórias (hard constraints);
- preferências (soft constraints).

Evite dizer que o sistema usa "inteligência artificial" apenas por gerar horários. O núcleo atual é um solver de otimização.

---

## 2. Stack atual

### Frontend
- React;
- TypeScript;
- Vite;
- Tailwind CSS;
- Axios;
- Lucide React.

### Backend
- Python;
- FastAPI;
- Pydantic;
- SQLAlchemy;
- SQLite;
- Uvicorn.

### Otimização
- Google OR-Tools CP-SAT.

### Desenvolvimento
- Git;
- GitHub.

---

## 3. Fluxo atual do sistema

1. Cadastrar cursos.
2. Cadastrar disciplinas.
3. Criar turmas.
4. Definir quais matérias existem em cada turma.
5. Ajustar a carga semanal de cada matéria na própria turma.
6. Marcar se a turma usa grupos A/B.
7. Em cada disciplina da turma, escolher:
   - turma inteira;
   - separada A/B.
8. Cadastrar professores.
9. Informar disciplinas que cada professor pode lecionar.
10. Informar pontuação docente.
11. Informar disponibilidade semanal.
12. Ajustar preferências configuráveis.
13. Gerar a grade.
14. Visualizar por turma ou professor.
15. Exportar CSV ou imprimir a visualização.

---

## 4. Regras obrigatórias implementadas

### Conflitos básicos
- professor não pode estar em duas aulas simultaneamente;
- turma/grupo não pode receber duas aulas simultaneamente;
- carga semanal configurada deve ser cumprida;
- aula só pode ser posicionada em período válido da jornada da turma.

### Jornadas
- Manhã;
- Integral;
- Noite.

Intervalos e almoço aparecem visualmente, mas não são períodos onde o solver coloca aulas.

### Docentes
- disponibilidade manual;
- indisponibilidade pode representar trabalho em outra escola;
- interjornada mínima de 11 horas calculada com horários reais;
- máximo absoluto de 9 aulas por dia;
- após até 6 aulas sem pausa suficiente, é necessário descanso de pelo menos 1 hora antes de continuar.

### Alunos
- janelas internas são proibidas;
- intervalos e almoço oficiais não contam como janela.

### Falta de professor
Uma disciplina **não desaparece** da grade se ainda não houver professor.

A aula pode ser gerada com:
- teacher_id = null;
- exibição "Sem professor".

Essa alternativa recebe penalidade alta, portanto o solver prefere um professor válido sempre que possível.

---

## 5. Preferências implementadas

As preferências influenciam a qualidade da solução, mas não são tratadas automaticamente como proibições.

### Distribuição por disciplina

#### Manhã / Integral
- bloco de 2 aulas é o formato preferido;
- uma aula isolada é permitida;
- 3 ou mais no mesmo dia recebem penalidade maior, mas continuam possíveis.

Exemplo desejado para 4 aulas:
- 2 + 2.

#### Noite
Blocos de 3, 4 ou 5 aulas são aceitos normalmente porque aparecem em grades reais analisadas.

### Outras preferências
- evitar janelas de professor;
- mínimo de aulas quando professor vai à escola;
- aproximar ocupação dos grupos A/B;
- evitar primeiro período;
- evitar último período;
- evitar sexta-feira;
- priorizar docentes pela pontuação.

---

## 6. Grupos A/B

A divisão A/B pertence à **turma + disciplina**, e não à categoria da matéria.

Uma turma pode:
- não possuir grupos;
- possuir grupos A/B.

Para uma matéria da turma com grupos:

### Turma inteira
A e B têm aula juntos. A aula ocupa os dois grupos.

### Separada A/B
Cada grupo possui uma carga independente.

Isso permite:
- mesma matéria em horários diferentes;
- matérias diferentes simultaneamente;
- professores diferentes;
- um grupo livre enquanto o outro possui aula, quando necessário.

O nome da turma terminar em A ou B não significa que seja o mesmo conceito de grupo interno.

---

## 7. Matriz por turma

Cada turma possui sua própria lista de matérias.

A disciplina possui uma carga padrão, mas a carga real usada pelo solver fica na configuração da turma.

O campo antigo "Categoria — Ensino Médio/Técnica" foi retirado da interface porque não participa mais das regras.

Os **cursos associados** continuam úteis como filtro de quais disciplinas podem aparecer como candidatas para uma turma.

---

## 8. Escopo que NÃO faz parte da versão atual

Não afirmar que estas funções existem:

- autenticação/login;
- dashboard administrativo;
- aplicativo móvel;
- envio de notificações;
- salas e laboratórios;
- alocação de estudantes individualmente;
- IA generativa;
- integração com sistemas externos da escola;
- implantação multiusuário em produção.

Salas e laboratórios foram deliberadamente retirados do escopo atual.

---

## 9. Persistência

Banco atual:
- SQLite.

A última grade é armazenada no banco.

A partir da revisão de outubro, a rota de geração salva a nova grade no próprio backend, reduzindo risco de a interface receber o resultado e falhar antes de persistir.

Ao apagar um professor, aulas salvas que apontavam para ele passam a "Sem professor" em vez de ficar com referência quebrada.

---

## 10. Desempenho e otimizações

O solver possui limite de tempo por geração.

Foram realizadas duas otimizações estruturais importantes:

### Regra 6 aulas + descanso
A implementação inicial enumerava milhares de combinações possíveis de 7 aulas.

A implementação atual usa contadores de sequência entre períodos com descanso inferior a 60 minutos, mantendo a regra com muito menos restrições.

### Professores inelegíveis
A implementação inicial criava variáveis para todo professor em toda disciplina e depois fixava em zero quem não pudesse lecionar.

A implementação atual só cria variáveis para professores realmente habilitados naquela disciplina.

O benchmark deve ser executado novamente após essas mudanças para medir o ganho.

---

## 11. Pré-validação

Antes de montar o modelo, o backend detecta alguns cenários impossíveis, por exemplo:

- carga semanal da turma maior que a quantidade de períodos disponíveis;
- quantidade semanal de matérias de alta complexidade incompatível com o limite diário configurado.

Isso evita gastar o tempo completo do solver em impossibilidades simples.

---

## 12. Resultado do solver

Estados tratados separadamente:

- optimal: solução ótima comprovada;
- feasible: solução válida encontrada sem prova de optimalidade;
- infeasible: o modelo provou que não há solução;
- timeout/unknown: a busca terminou sem conclusão dentro do tempo;
- model invalid / error: erro estrutural interno.

Importante para o TCC:

**timeout não significa grade impossível.**

---

## 13. Limitações atuais

- desempenho ainda precisa ser medido em base escolar completa;
- pesos das preferências ainda podem ser calibrados;
- SQLite é adequado ao protótipo, mas não representa uma implantação multiusuário;
- não existe explicação automática completa de qual conjunto mínimo de regras causou uma inviabilidade;
- ainda falta comparação controlada de tempo entre processo manual e Anatinus;
- a validação final depende de dados reais mais amplos e avaliação de quem monta os horários.

---

## 14. Regra para escrita do TCC

Não afirmar:
- "reduziu 70%";
- "elimina todos os erros";
- "sempre gera a melhor grade";
- "capacidade plena";
- "IA";
- "reduziu drasticamente o tempo";

sem experimento que sustente a afirmação.

Formulações seguras:
- "nos cenários testados";
- "as restrições implementadas foram respeitadas";
- "o sistema demonstrou capacidade de...";
- "os resultados preliminares indicam...";
- "a validação completa permanece como etapa do projeto".

---

## 15. Comandos principais

### Backend

```powershell
cd C:\Projetos\Horarios-TCC\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

### Frontend

```powershell
cd C:\Projetos\Horarios-TCC\frontend
npm run dev
```

### Testes

```powershell
cd C:\Projetos\Horarios-TCC\backend
.\.venv\Scripts\Activate.ps1
python -m unittest test_optimizer.py
```

### Build frontend

```powershell
cd C:\Projetos\Horarios-TCC\frontend
npm run build
```

### Benchmark

```powershell
cd C:\Projetos\Horarios-TCC\backend
.\.venv\Scripts\Activate.ps1
python benchmark_optimizer.py --size small
python benchmark_optimizer.py --size medium
python benchmark_optimizer.py --size large
```
