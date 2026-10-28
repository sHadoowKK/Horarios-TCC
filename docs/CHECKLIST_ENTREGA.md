# ANATINUS — CHECKLIST DE ENTREGA

## Código

- [ ] git pull
- [ ] executar testes do backend
- [ ] executar build do frontend
- [ ] executar benchmark small
- [ ] executar benchmark medium
- [ ] executar benchmark large
- [ ] testar geração pela interface
- [ ] testar visão por turma
- [ ] testar visão por professor
- [ ] testar carga distinta para grupos A/B (ex.: SW2 A=3, B=2)
- [ ] testar preferência de sequência (ex.: Filosofia → Sociologia)
- [ ] conferir que horários de grupo sem aula ficam em branco
- [ ] testar exportação Excel (`.xlsx`) e verificar larguras/acentos no Excel
- [ ] testar Imprimir
- [ ] testar exclusão de professor com grade salva
- [ ] testar mensagem de pré-validação com uma turma propositalmente impossível
- [ ] confirmar que a matriz do 3º INFO bate com a tabela de referência, incluindo as exceções A/B

## Resultados para registrar

- [ ] número atual de testes
- [ ] tempo dos testes
- [ ] resultado do build
- [ ] benchmark antes/depois das otimizações
- [ ] print da gestão acadêmica
- [ ] print de professores
- [ ] print de regras/preferências
- [ ] print da grade por turma
- [ ] print da grade por professor
- [ ] print de "Sem professor"
- [ ] print de grupos A/B

## TCC

- [ ] retirar afirmações quantitativas não medidas
- [ ] conferir Resumo
- [ ] conferir Abstract
- [ ] atualizar Metodologia com CP-SAT
- [ ] atualizar Resultados com testes atuais
- [ ] atualizar limitações
- [ ] conferir referências
- [ ] atualizar sumário
- [ ] revisar numeração de figuras e quadros
- [ ] conferir ABNT exigida pela escola
- [ ] exportar PDF final
- [ ] abrir o PDF final e conferir página por página

## Apresentação

- [ ] preparar slides
- [ ] definir fala de cada integrante
- [ ] ensaiar demonstração
- [ ] ter screenshots de backup
- [ ] ter banco de demonstração pronto
- [ ] testar em computador/projetor que será usado
- [ ] levar projeto em pendrive/backup
- [ ] confirmar que Python/Node/dependências estarão disponíveis

## Aplicativo desktop Windows

- [ ] Executar o workflow `Build Windows` e confirmar que o pacote foi gerado.
- [ ] Baixar e extrair o ZIP completo em uma pasta limpa.
- [ ] Abrir `Anatinus.exe` sem iniciar manualmente Python ou Node.js.
- [ ] Conferir navegação pelas quatro telas, cadastro e geração de grade.
- [ ] Fechar e reabrir o aplicativo e confirmar que os dados continuam salvos.
- [ ] Conferir o banco em `%LOCALAPPDATA%\\Anatinus\\school_schedule.db`.
- [ ] Testar backup e restauração do banco antes de entregar a versão.
- [ ] Verificar o aplicativo no computador que será usado na apresentação.

## Validação final

- [ ] solicitar que alguém da escola que conhece a montagem de horários avalie uma grade
- [ ] anotar críticas
- [ ] distinguir falha de regra, preferência e usabilidade
- [ ] registrar mudanças feitas após feedback
