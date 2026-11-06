# ANATINUS — CHECKLIST DE ENTREGA

Última conferência técnica: 06/11/2026. Itens marcados foram verificados no GitHub Actions. Testes que exigem a interface gráfica em um computador Windows real permanecem abertos.

## Código e validação

- [x] 36 testes automatizados do backend passaram no GitHub Actions (4,776 s no runner Linux).
- [x] Build de produção do frontend passou (1.952 módulos transformados).
- [x] Build Windows com PyInstaller concluiu no runner.
- [x] Smoke test do EXE em AppData limpo: API local iniciou e 57 aulas do cenário 3º INFO ficaram acessíveis pela rota /timetable/.
- [x] Geração isolada do 3º INFO: 57 aulas, zero sem professor, estado feasible.
- [x] Base fictícia principal gerada pela API: 2 cursos, 3 turmas, 15 disciplinas, 15 professores, 100 aulas salvas, 100 com professor.
- [x] Validação conjunta da base fictícia: 100 aulas, zero conflitos de professor, zero janelas dos alunos, disponibilidade e descansos verificados; seis aulas por dia em cada turma/grupo.
- [x] Base de regressão de oito turmas gerada em conjunto e validada nas restrições obrigatórias: 291 aulas, 234 com professor e 57 sem professor; estado feasible; 120,80 s; 40.012 variáveis e 65.835 restrições.
- [ ] Melhorar a atribuição docente e a distribuição diária da base de regressão de oito turmas. Ela ainda não é uma grade final aprovada; parte dos dados de Agro e disponibilidades continua provisória.
- [ ] Executar benchmarks small, medium e large na mesma máquina do baseline e comparar os resultados.

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
- [x] Registrar a base fictícia de apresentação: 100 aulas, todas com professor, 6 aulas/dia, sem conflitos e sem janelas.
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
- [x] Definir a base fictícia de 100 aulas como cenário principal da demonstração.
- [ ] Testar no computador e projetor que serão usados.
- [ ] Levar projeto e banco de demonstração em pendrive/backup.

## Aplicativo desktop Windows

- [x] Workflow Build Windows gerou Anatinus.exe e release/Anatinus-Windows-x64.zip no runner.
- [x] Smoke test em AppData limpo confirmou inicialização da API e acesso às 57 aulas.
- [ ] Publicar e baixar o ZIP como artefato do GitHub Actions. A publicação em eventos pull_request permanece desativada; o workflow será habilitado para push na branch de trabalho.
- [ ] Baixar e extrair o ZIP completo em uma pasta limpa.
- [ ] Abrir Anatinus.exe sem iniciar manualmente Python ou Node.js no Windows real.
- [ ] Conferir navegação, cadastro, geração e exportação.
- [ ] Fechar e reabrir o aplicativo e confirmar que os dados continuam salvos.
- [ ] Conferir o banco em %LOCALAPPDATA%\\Anatinus\\school_schedule.db.
- [ ] Verificar o aplicativo no computador da apresentação.

## Validação externa

- [ ] Solicitar que alguém da escola que conhece a montagem de horários avalie uma grade real.
- [ ] Anotar críticas e separar falhas de regras, preferências e usabilidade.
- [ ] Registrar mudanças feitas após feedback.
