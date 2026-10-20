# ANATINUS — REVISÃO DE CÓDIGO E RISCOS TÉCNICOS

> Revisão consolidada em 19/10/2026, após a suíte chegar a 22 testes automatizados e o GitHub Actions ficar verde.

## Estado geral

O projeto está em um ponto estável para continuidade do TCC:

- 18 testes do solucionador;
- 4 testes de integração do backend;
- build de produção do frontend verificado;
- integração contínua no GitHub;
- benchmark sintético separado dos testes funcionais;
- salvamento da grade realizado no backend junto com a geração;
- pré-validação de impossibilidades simples;
- backup local e scripts de verificação disponíveis.

Não há, neste momento, um bloqueador conhecido que impeça o fluxo principal cadastro → geração → persistência → visualização.

## Pontos fortes atuais

### Separação de responsabilidades
- React/TypeScript cuida da interface;
- FastAPI centraliza regras de negócio e persistência;
- SQLite/SQLAlchemy armazenam os dados;
- CP-SAT concentra a busca combinatória.

### Modelo de grade
- matriz pertence à turma;
- carga real pertence à relação turma + disciplina;
- grupos A/B são configurados por turma + disciplina;
- ausência de professor não torna a grade automaticamente inviável.

### Proteções implementadas
- conflito de professor;
- conflito de turma/grupo;
- jornada válida;
- carga semanal;
- interjornada;
- máximo diário;
- descanso após sequência longa;
- janelas de alunos;
- disponibilidade;
- preservação de aula sem professor.

## Melhorias de desempenho já aplicadas

### Regra de descanso
A implementação antiga enumerava combinações de sete aulas. A atual usa contadores de sequência e reduz o número de restrições.

### Professores inelegíveis
O modelo atual só cria variáveis de aula para professores habilitados na disciplina, evitando grande quantidade de variáveis fixadas em zero.

## Pontos que ainda merecem atenção

### 1. Escalabilidade
O benchmark small anterior às otimizações levou 16,305 s dentro do solver na máquina de desenvolvimento. A medição precisa ser repetida após as otimizações antes de concluir o ganho.

### 2. Diagnóstico de inviabilidade
O backend já detecta algumas impossibilidades antes do CP-SAT, mas ainda não produz um conjunto mínimo de restrições conflitantes quando o solver prova o modelo inviável.

### 3. Validação dos cadastros
A interface impede a maior parte dos dados incoerentes, porém uma versão futura pode endurecer a API para validar de forma explícita:
- IDs de cursos inexistentes;
- IDs de disciplinas inexistentes;
- formato completo da disponibilidade;
- referências acadêmicas enviadas por clientes externos à interface.

### 4. Banco de dados
SQLite é suficiente para o protótipo e TCC. Uma implantação com vários usuários simultâneos deveria estudar banco servidor, autenticação e migrações formais.

### 5. Tipagem do frontend
Ainda existem pontos com tipos amplos na interface. Não impedem o funcionamento, mas uma etapa futura pode substituir any por interfaces específicas para aumentar segurança de manutenção.

### 6. Pesos da função objetivo
As preferências possuem pesos definidos empiricamente. Eles devem ser calibrados com mais dados reais e feedback de quem monta o horário.

## O que NÃO deve ser refeito sem motivo

As decisões abaixo foram tomadas após testes com situações reais e não devem ser revertidas apenas por simplificação:

- matéria sem professor continua na grade;
- categoria Ensino Médio/Técnica não decide A/B;
- matriz é específica por turma;
- diurno prefere 2+2, mas não proíbe exceções;
- noturno aceita blocos de 3, 4 e 5;
- A/B pode ter matérias diferentes simultaneamente;
- nome da turma terminado em A/B não é o mesmo que grupo interno A/B;
- salas e laboratórios estão fora do escopo atual.

## Critério para uma mudança futura

Antes de alterar o solver:

1. registrar o caso que está errado;
2. decidir se é regra obrigatória ou preferência;
3. criar um teste que reproduza o caso;
4. fazer a alteração;
5. executar todos os testes;
6. executar o build do frontend;
7. comparar benchmark quando a alteração atingir o modelo CP-SAT.

Isso evita corrigir um cenário e quebrar silenciosamente outro.
