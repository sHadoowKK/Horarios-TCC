import { useEffect, useState } from "react";
import { api } from "../api";
import { Save, Shield } from "lucide-react";

export default function Config() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const response = await api.get("/config/");
        setConfig(response.data);
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };

    fetchConfig();
  }, []);

  const handleChange = (field: string, value: any) => {
    setSaveMessage(null);
    setConfig({
      ...config,
      [field]: value,
    });
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveMessage(null);

    try {
      const payload = {
        ...config,
        max_classes_per_day: Math.min(Number(config.max_classes_per_day || 9), 9),
        max_consecutive_classes: 6,
        student_gaps_hard: true,
      };

      const response = await api.put("/config/", payload);
      setConfig(response.data);
      setSaveMessage({ kind: "success", text: "Parâmetros e preferências salvos com sucesso." });
    } catch (error) {
      console.error(error);
      setSaveMessage({ kind: "error", text: "Erro ao salvar as configurações. Tente novamente." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="app-workspace" style={{ textAlign: "center", padding: "60px 20px", color: "var(--an-muted)" }}>
        Carregando parâmetros...
      </div>
    );
  }

  if (!config) {
    return (
      <div className="app-workspace" style={{ textAlign: "center", padding: "60px 20px", color: "var(--an-danger)" }}>
        Não foi possível carregar as configurações do sistema.
      </div>
    );
  }

  const fixedRules = [
    {
      title: "11 horas de descanso interjornada",
      text: "Intervalo mínimo legal de 11 horas consecutivas entre o término da última aula em um dia e o início da primeira aula no dia seguinte.",
    },
    {
      title: "Limite máximo de 9 aulas/dia",
      text: "O solver nunca programa mais do que 9 aulas diárias para o mesmo docente em nenhuma circunstância.",
    },
    {
      title: "6 aulas consecutivas + 1h de descanso",
      text: "Após até 6 aulas consecutivas sem pausa, exige-se uma janela mínima de 1 hora de descanso.",
    },
    {
      title: "Proibição de janelas para estudantes",
      text: "A grade dos alunos não pode conter horários vagos entre duas aulas. Intervalos e almoço oficiais não são janelas.",
    },
  ];

  return (
    <div className="app-workspace" style={{ maxWidth: 1040 }}>
      {/* TÍTULO E AÇÃO DE SALVAR */}
      <div className="app-page-title-row">
        <div>
          <h1 className="app-page-title">
            Regras e Parâmetros
            <span className="app-page-subtitle">
              Configuração das restrições legais e preferências pedagógicas do solver
            </span>
          </h1>
        </div>

        <div>
          <button
            type="button"
            onClick={handleSave}
            disabled={saving}
            className="app-btn app-btn-primary"
          >
            <Save style={{ width: 14, height: 14 }} />
            <span>{saving ? "Salvando..." : "Salvar Parâmetros"}</span>
          </button>
        </div>
      </div>

      {saveMessage && (
        <div className={`app-alert app-alert-${saveMessage.kind}`} role={saveMessage.kind === "error" ? "alert" : "status"}>
          <span>{saveMessage.text}</span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
        {/* REGRAS OBRIGATÓRIAS (FIXAS) */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            <Shield style={{ width: 18, height: 18, color: "var(--an-primary)" }} />
            <div>
              <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Restrições Legais Obrigatórias</h2>
              <span style={{ fontSize: 11, color: "var(--an-muted)" }}>
                Restrições rígidas (Hard Constraints) do otimizador — não podem ser relaxadas
              </span>
            </div>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 10 }}>
            {fixedRules.map(rule => (
              <div
                key={rule.title}
                style={{
                  padding: "10px 12px",
                  border: "1px solid var(--an-border)",
                  borderRadius: "var(--an-radius-sm)",
                  backgroundColor: "var(--an-bg)",
                }}
              >
                <strong style={{ display: "block", fontSize: 12, color: "var(--an-text)", marginBottom: 4 }}>
                  {rule.title}
                </strong>
                <p style={{ margin: 0, fontSize: 11, color: "var(--an-muted)", lineHeight: 1.45 }}>
                  {rule.text}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* LIMITES DA ESCOLA */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 14px", paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            Limites Operacionais da Escola
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Máximo de aulas diárias por docente
              </label>
              <input
                type="number"
                min="1"
                max="9"
                className="app-input font-mono"
                style={{ width: "100%" }}
                value={config.max_classes_per_day}
                onChange={e => handleChange("max_classes_per_day", Math.min(Number(e.target.value), 9))}
              />
              <span style={{ display: "block", fontSize: 11, color: "var(--an-muted)", marginTop: 4 }}>
                Limite institucional (entre 1 e 9). O padrão legal máximo é 9.
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Máximo de aulas de alta complexidade por dia
              </label>
              <input
                type="number"
                min="0"
                max="15"
                className="app-input font-mono"
                style={{ width: "100%" }}
                value={config.max_high_complexity_per_day}
                onChange={e => handleChange("max_high_complexity_per_day", Number(e.target.value))}
              />
              <span style={{ display: "block", fontSize: 11, color: "var(--an-muted)", marginTop: 4 }}>
                Equilíbrio cognitivo para os estudantes em disciplinas difíceis.
              </span>
            </div>
          </div>
        </div>

        {/* PREFERÊNCIAS DOS PROFESSORES */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 14px", paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            Preferências Docentes
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Tratamento de janelas para professores
              </label>
              <select
                className="app-select"
                style={{ width: "100%" }}
                value={config.teacher_gaps_hard ? "hard" : "soft"}
                onChange={e => handleChange("teacher_gaps_hard", e.target.value === "hard")}
              >
                <option value="soft">Evitar janelas como preferência (Soft)</option>
                <option value="hard">Proibir janelas terminantemente (Hard)</option>
              </select>
              <span style={{ display: "block", fontSize: 11, color: "var(--an-muted)", marginTop: 4 }}>
                "Proibir" pode dificultar encontrar uma solução viável para a escola inteira.
              </span>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Mínimo de aulas quando o professor vier à escola
              </label>
              <input
                type="number"
                min="0"
                max="15"
                className="app-input font-mono"
                style={{ width: "100%" }}
                value={config.min_classes_teachers}
                onChange={e => handleChange("min_classes_teachers", Number(e.target.value))}
              />
              <span style={{ display: "block", fontSize: 11, color: "var(--an-muted)", marginTop: 4 }}>
                Evita deslocamentos desnecessários para ministrar apenas 1 aula.
              </span>
            </div>
          </div>
        </div>

        {/* PREFERÊNCIAS DAS TURMAS */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <h2 style={{ fontSize: 15, fontWeight: 700, margin: "0 0 14px", paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            Preferências dos Estudantes e Turmas
          </h2>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Mínimo de aulas/dia ativo
              </label>
              <input
                type="number"
                min="0"
                max="15"
                className="app-input font-mono"
                style={{ width: "100%" }}
                value={config.min_classes_students}
                onChange={e => handleChange("min_classes_students", Number(e.target.value))}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Evitar 1ª aula do dia
              </label>
              <select
                className="app-select"
                style={{ width: "100%" }}
                value={config.avoid_first_period ? "yes" : "no"}
                onChange={e => handleChange("avoid_first_period", e.target.value === "yes")}
              >
                <option value="no">Não (normal)</option>
                <option value="yes">Sim (preferência)</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Evitar última aula
              </label>
              <select
                className="app-select"
                style={{ width: "100%" }}
                value={config.avoid_last_period ? "yes" : "no"}
                onChange={e => handleChange("avoid_last_period", e.target.value === "yes")}
              >
                <option value="no">Não (normal)</option>
                <option value="yes">Sim (preferência)</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: "var(--an-text)", marginBottom: 4 }}>
                Evitar sexta-feira
              </label>
              <select
                className="app-select"
                style={{ width: "100%" }}
                value={config.avoid_friday ? "yes" : "no"}
                onChange={e => handleChange("avoid_friday", e.target.value === "yes")}
              >
                <option value="no">Não (normal)</option>
                <option value="yes">Sim (preferência)</option>
              </select>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
