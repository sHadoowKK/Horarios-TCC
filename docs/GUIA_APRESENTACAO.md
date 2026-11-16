# ANATINUS — GUIA DE APRESENTAÇÃO

## Base pronta para abrir

O pacote da apresentação já abre com os dados semanais transcritos da planilha:

- 8 cursos;
- 20 turmas;
- 102 disciplinas;
- 51 docentes anonimizados;
- 695 aulas semanais configuradas nas matrizes.

O 3º Informática abre selecionado com uma grade gerada pelo Anatinus: 50 aulas, 22 para a turma inteira, 14 para o grupo A e 14 para o grupo B. As 50 aulas têm docente atribuído. As outras turmas já estão cadastradas com disciplinas, cargas, grupos e habilitações docentes.

Feche instâncias anteriores e execute `Anatinus.exe` extraído do ZIP. O aplicativo copia a base de demonstração para `%LOCALAPPDATA%\Anatinus` na primeira abertura. O banco normal fica nesse mesmo diretório, separado do banco de desenvolvimento.

## Roteiro sugerido

### 1. Mostrar a grade inicial

Comece pelo 3º Informática. Mostre a grade semanal gerada, a divisão A/B e as aulas compartilhadas. Explique que o CP-SAT buscou uma solução válida com as cargas e habilitações configuradas.

### 2. Mostrar a gestão acadêmica

Abra **Turmas** e mostre a lista completa. Selecione uma turma para conferir disciplinas, cargas semanais e separações por grupo. O cadastro completo já está dentro do ZIP, sem digitação durante a apresentação.

### 3. Mostrar os docentes

Abra **Professores** para mostrar as disciplinas habilitadas. Os nomes foram anonimizados. Como a planilha não informa a disponibilidade semanal completa, a base usa disponibilidades sintéticas por turno.

### 4. Explicar regras e preferências

O CP-SAT trata conflitos, cargas e intervalos como restrições do modelo. Preferências, como blocos consecutivos, são usadas para orientar a busca sem eliminar soluções necessárias.

### 5. Mostrar exportação

Use Excel ou impressão somente se essas ações já tiverem sido conferidas no computador da apresentação.

## Limites do recorte

A grade inicial de 50 aulas corresponde somente ao 3º Informática. A base também contém as matrizes das demais turmas, mas a grade de toda a escola não está pré-carregada no pacote. Os professores estão anonimizados e a disponibilidade é sintética, não uma agenda oficial.

Os dois quadros MTEC com início às 18h30 e os sete encontros síncronos mensais da planilha não foram convertidos em aulas semanais: o aplicativo ainda não representa esse turno nem eventos datados. Evite apresentar essa base como cadastro operacional oficial ou afirmar que todas as turmas já foram geradas em conjunto.

O estado `feasible` significa que o solver encontrou uma solução válida segundo o modelo; não significa que provou ser a melhor solução matemática possível.

## Explicação curta do CP-SAT

> "O Anatinus transforma os horários possíveis em variáveis e descreve ao CP-SAT quais combinações são permitidas ou proibidas. Depois atribui pesos às preferências. O solver procura uma combinação que respeite as regras obrigatórias e melhore as preferências."

## Perguntas prováveis

### "Isso é inteligência artificial?"

> "Não no sentido de IA generativa. O núcleo é programação por restrições e otimização combinatória usando o CP-SAT do Google OR-Tools."

### "Ele sempre encontra a melhor grade?"

> "Quando retorna `optimal`, o solver provou a optimalidade dentro daquele modelo. Também pode retornar `feasible`, que é uma solução válida sem prova de que seja a melhor, especialmente quando há limite de tempo."

### "Como funciona A/B?"

> "A divisão é configurada por turma e disciplina. Uma matéria pode ser conjunta e outra separada. Quando separada, A e B possuem cargas independentes."

### "O sistema substitui a coordenação?"

> "Não. Ele automatiza a busca e a verificação de restrições. A coordenação continua responsável pelas decisões pedagógicas, exceções e validação final."

## Antes da banca

1. Extraia o ZIP inteiro.
2. Abra `Anatinus.exe` e confira se a grade do 3º Informática aparece.
3. Abra Turmas e Professores para confirmar os dados carregados.
4. Confira o tema e o ícone da versão branca.
5. Teste Excel e impressão no computador que será usado.
6. Mantenha o ZIP e uma cópia dele em outro local.
