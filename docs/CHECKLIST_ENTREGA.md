# ANATINUS — CHECKLIST DE ENTREGA

Última conferência técnica: 06/11/2026. Itens marcados foram verificados em CI; itens manuais continuam abertos até serem executados no computador de demonstração.

## Código

- [x] 36 testes automatizados do backend passaram no GitHub Actions.
- [x] Build de produção do frontend passou no GitHub Actions.
- [x] Build do executável Windows terminou com sucesso no runner do GitHub.
- [x] Smoke test do EXE em AppData limpo: API local iniciou e encontrou 57 aulas salvas.
- [x] Validação isolada das 8 turmas da base demonstrativa passou, sem janelas de alunos.
- [x] Teste de carga semanal noturna de 25 aulas continua coberto pelos testes automatizados.
- [x] Gerar a escola inteira em conjunto: 8 turmas e 291 aulas validadas pela API; 250 com professor e 41 sem professor; sem conflitos docentes, janelas de alunos ou violações das regras de disponibilidade/descanso verificadas.
- [ ] Executar benchmarks small, medium e large e comparar com o baseline.
- [ ] Testar geração pela interface no computador local.
- [ ] Testar visão por turma e por professor na interface.
- [ ] Testar carga distinta para grupos A/B (ex.: SW2 A=3, B=2) visualmente.
- [ ] Conferir preferência de sequência Filosofia → Sociologia no resultado visual.
- [ ] Conferir que horários de grupo sem aula ficam em branco.
- [ ] Testar exportação Excel (.xlsx), larguras e acentos.
- [ ] Testar impressão em A4 horizontal.
- [ ] Testar exclusão de professor com grade salva pela interface.
- [ ] Testar mensagem de pré-validação com uma turma propositalmente impossível.
- [ ] Conferir a matriz do 3º INFO com a tabela de referência, incluindo exceções A/B.

## Evidências técnicas

- [x] Registrar quantidade e tempo da suíte automatizada: 36 testes, 6,751 s no runner Linux do GitHub.
- [x] Registrar build do frontend concluído.
- [x] Registrar empacotamento Windows concluído no runner.
- [x] Registrar validação individual das oito turmas e suas métricas.
- [x] Registrar geração conjunta das oito turmas: 291 aulas (250 com professor, 41 sem professor), estado feasible, 134,87 s, 39.967 variáveis e 65.790 restrições.
- [x] Registrar validação conjunta de carga por turma, janelas dos alunos, conflitos docentes, disponibilidade, limite diário, turnos, pausas e 11 h de descanso.
- [ ] Executar e registrar benchmarks depois das otimizações.
- [ ] Capturar prints da gestão acadêmica, professores e regras/preferências.
- [ ] Capturar print da grade por turma e por professor.
- [ ] Capturar print de “Sem professor” e de grupos A/B.

## TCC escrito

Não alterado nesta rodada, conforme combinado.

- [ ] Apêndice.
- [ ] Conclusão.
- [ ] Referências.
- [ ] Revisão final de resumo, abstract, metodologia, resultados, limitações, ABNT e PDF.

## Apresentação

- [ ] Revisar slides e falas com base nos resultados técnicos finais.
- [ ] Ensaiar demonstração.
- [ ] Ter screenshots de backup.
- [ ] Usar a base isolada do 3º INFO como cenário principal de demonstração.
- [ ] Testar no computador/projetor que será usado.
- [ ] Levar projeto e banco de demonstração em pendrive/backup.
- [ ] Confirmar que o ambiente necessário estará disponível.

## Aplicativo desktop Windows

- [x] Workflow Build Windows empacotou Anatinus.exe e o ZIP no runner.
- [ ] Obter o ZIP em uma execução que publique artefatos. A publicação em PR foi desativada para evitar novas tentativas enquanto a cota de armazenamento do GitHub está esgotada.
- [ ] Baixar e extrair o ZIP completo em uma pasta limpa.
- [ ] Abrir Anatinus.exe sem iniciar manualmente Python ou Node.js.
- [ ] Conferir navegação, cadastro, geração e exportação.
- [ ] Fechar e reabrir o aplicativo e confirmar que os dados continuam salvos.
- [ ] Conferir o banco em %LOCALAPPDATA%\\Anatinus\\school_schedule.db.
- [ ] Testar backup e restauração do banco.
- [ ] Verificar o aplicativo no computador da apresentação.

## Validação externa

- [ ] Solicitar que alguém da escola que conhece a montagem de horários avalie uma grade.
- [ ] Anotar críticas.
- [ ] Distinguir falha de regra, preferência e usabilidade.
- [ ] Registrar mudanças feitas após feedback.
