# ANATINUS — CHECKLIST DE ENTREGA

Última conferência técnica local: 09/11/2026. O pacote foi recompilado com a base da planilha e a correção para bancos vazios. A conferência visual do executável desta correção no computador/projetor permanece aberta.

## Atualização da base de apresentação — 09/11/2026

- [x] Base derivada da planilha: 8 cursos, 20 turmas, 102 disciplinas, 51 docentes anonimizados e 695 aulas semanais configuradas.
- [x] Grade inicial do 3º Informática: 50 aulas, todos os grupos preenchidos e zero aulas sem professor.
- [x] Build de produção do frontend e suíte local do backend: 45 testes passaram.
- [x] Executável Windows compilado com a versão branca da marca.
- [x] Recuperação de banco SQLite vazio verificada no modo congelado: 20 turmas e 50 aulas demonstrativas carregadas.
- [ ] Confirmar a abertura do executável recompilado pela interface Windows no computador da apresentação.
- [x] ZIP Windows criado e armazenado em `release/Anatinus-Windows-x64.zip`.
- [ ] Abrir visualmente a interface e conferir a grade no computador da apresentação.

Observações sobre a fonte: a planilha não fornece disponibilidade individual de docentes, então ela foi preenchida de forma ampla e sintética. Dois quadros MTEC com início às 18h30 e sete eventos síncronos mensais foram deixados de fora da grade semanal porque o sistema ainda não representa esses horários/eventos.

## Código e validação

- [x] 36 testes automatizados do backend passaram no GitHub Actions (4,776 s no runner Linux).
- [x] Build de produção do frontend passou (1.952 módulos transformados).
- [x] Build Windows com PyInstaller concluiu no runner.
- [x] Smoke test anterior do EXE em AppData limpo: API local iniciou e respondeu; essa versão aceitava pelo menos 50 aulas.
- [ ] Smoke test estrito do executável após a correção para banco local vazio.
- [x] Geração isolada do 3º INFO: 57 aulas, zero sem professor, estado feasible.
- [x] Base fictícia principal gerada pela API: 2 cursos, 3 turmas, 15 disciplinas, 15 professores, 100 aulas salvas, 100 com professor.
- [x] Validação conjunta da base fictícia: 100 aulas, zero conflitos de professor, zero janelas dos alunos, disponibilidade e descansos verificados; seis aulas por dia em cada turma/grupo.
- [x] Base de regressão de oito turmas gerada em conjunto e validada nas restrições obrigatórias: 291 aulas, 234 com professor e 57 sem professor; estado feasible; 120,80 s; 40.012 variáveis e 65.835 restrições.
- [ ] Melhorar a atribuição docente e a distribuição diária da base de regressão de oito turmas. Ela ainda não é uma grade final aprovada; parte dos dados de Agro e disponibilidades continua provisória.
- [ ] Executar benchmarks small, medium e large na mesma máquina do baseline e comparar os resultados.
- [ ] Triar as três vulnerabilidades de alta severidade reportadas pelo npm durante a instalação das dependências do frontend.

## Interface, exportação e persistência

- [ ] Abrir o Anatinus pela interface no computador local.
- [ ] Conferir visão por turma e por professor.
- [ ] Conferir grupos A/B e a diferença de carga SW2 A=3 / B=2 visualmente.
- [ ] Conferir preferência Filosofia → Sociologia no resultado visual.
- [ ] Conferir que horários de grupo sem aula ficam em branco.
- [ ] Testar exportação Excel (.xlsx), larguras e acentos.
- [ ] Testar impressão em A4 horizontal.
- [ ] Testar exclusão de professor com grade salva.
- [ ] Testar mensagem de pré-validação com uma turma propositalmente impossível.
- [ ] Testar backup e restauração do banco.

## Evidências técnicas

- [x] Registrar a suíte automatizada: 36 testes, 4,776 s no runner Linux.
- [x] Registrar build do frontend e build do Windows.
- [x] Registrar smoke test do EXE em AppData limpo.
- [x] Registrar a base de apresentação atual derivada da planilha: 20 turmas cadastradas e uma grade demonstrativa de 50 aulas do 3º Informática, todas com professor.
- [x] Registrar a base ETEC de regressão separadamente: 291 aulas, 234 com professor e 57 sem professor.
- [ ] Capturar prints da gestão acadêmica, professores e regras/preferências.
- [ ] Capturar prints da grade por turma, por professor e de A/B.

## TCC escrito

O texto escrito do TCC não foi alterado nesta rodada.

- [ ] Apêndice.
- [ ] Conclusão.
- [ ] Referências.
- [ ] Revisão final de resumo, abstract, metodologia, resultados, limitações e ABNT.
- [ ] Exportar PDF e conferir o documento completo.

## Apresentação

- [ ] Revisar slides e falas com os resultados técnicos atualizados.
- [ ] Ensaiar a demonstração.
- [ ] Ter screenshots de backup.
- [x] Definir a base derivada da planilha e a grade do 3º Informática como cenário principal da demonstração.
- [ ] Testar no computador e projetor que serão usados.
- [ ] Levar projeto e banco de demonstração em pendrive/backup.

## Aplicativo desktop Windows

- [x] Workflow Build Windows gerou Anatinus.exe e release/Anatinus-Windows-x64.zip no runner.
- [x] Smoke test anterior em AppData limpo confirmou a inicialização da API local.
- [x] Confirmar que a revisão atual do smoke test carregou a base da planilha e as 50 aulas do 3º Informática.
- [ ] Publicar e baixar o ZIP como artefato do GitHub Actions. A publicação em eventos pull_request permanece desativada; o workflow será habilitado para push na branch de trabalho.
- [x] ZIP atual criado localmente; ainda falta extraí-lo e abrir no computador da apresentação.
- [ ] Abrir Anatinus.exe sem iniciar manualmente Python ou Node.js no Windows real.
- [ ] Conferir navegação, cadastro, geração e exportação.
- [ ] Fechar e reabrir o aplicativo e confirmar que os dados continuam salvos.
- [ ] Conferir o banco em %LOCALAPPDATA%\\Anatinus\\school_schedule.db.
- [ ] Verificar o aplicativo no computador da apresentação.

## Validação externa

- [ ] Solicitar que alguém da escola que conhece a montagem de horários avalie uma grade real.
- [ ] Anotar críticas e separar falhas de regras, preferências e usabilidade.
- [ ] Registrar mudanças feitas após feedback.
