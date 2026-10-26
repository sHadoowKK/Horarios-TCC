import { useEffect, useState } from "react";
import { api } from "../api";
import {
  CheckCircle2,
  Save,
  ShieldCheck,
} from "lucide-react";

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

  const handleChange = (
    field: string,
    value: any,
  ) => {
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

        // Regras fixas não podem ser relaxadas.
        max_classes_per_day: Math.min(
          Number(config.max_classes_per_day || 9),
          9,
        ),
        max_consecutive_classes: 6,
        student_gaps_hard: true,
      };

      const response = await api.put(
        "/config/",
        payload,
      );

      setConfig(response.data);
      setSaveMessage({ kind: "success", text: "Preferências salvas." });
    } catch (error) {
      console.error(error);
      setSaveMessage({ kind: "error", text: "Não foi possível salvar. Tente novamente." });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="app-page-state">Carregando...</div>
    );
  }

  if (!config) {
    return (
      <div className="app-page-state" role="alert">Erro ao carregar configurações.</div>
    );
  }

  const fixedRules = [
    {
      title: "11 horas de descanso",
      text: "O professor precisa ter pelo menos 11 horas entre o fim da última aula de um dia e o início da próxima.",
    },
    {
      title: "Máximo de 9 aulas por dia",
      text: "O otimizador nunca ultrapassa 9 aulas diárias para o mesmo professor.",
    },
    {
      title: "6 aulas + 1 hora de descanso",
      text: "Depois de até 6 aulas sem uma pausa de 1 hora, o professor não pode continuar sem o descanso necessário.",
    },
    {
      title: "Aluno sem janela",
      text: "A turma não pode ficar com um horário vazio entre duas aulas. Intervalos e almoço oficiais não contam como janela.",
    },
  ];

  return (
    <div className="app-view app-view-settings p-8 max-w-5xl mx-auto pb-24">
      <h2 className="sr-only">Regras e preferências</h2>
      <div className="app-settings-toolbar">
        <button
          onClick={handleSave}
          disabled={saving}
          className="app-action-primary disabled:opacity-50"
        >
          <Save className="w-4 h-4" />
          {saving ? "Salvando..." : "Salvar"}
        </button>
      </div>
      {saveMessage && (
        <div className={`app-save-feedback app-save-${saveMessage.kind}`} role={saveMessage.kind === "error" ? "alert" : "status"}>
          {saveMessage.text}
        </div>
      )}
      <div className="app-settings-sections space-y-6">
        {/* REGRAS FIXAS */}
        <section className="app-panel app-settings-section bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <div className="flex items-center gap-2 mb-4">
            <ShieldCheck className="w-6 h-6 text-emerald-600" />

            <div>
              <h3 className="text-xl font-bold text-gray-700">
                Regras obrigatórias
              </h3>
            </div>
          </div>

          <div className="app-fixed-rules grid grid-cols-1 md:grid-cols-2 gap-3">
            {fixedRules.map(rule => (
              <div
                key={rule.title}
                className="app-fixed-rule p-4 rounded-lg border border-emerald-100 bg-emerald-50"
              >
                <div className="flex items-center gap-2 text-emerald-800 font-bold">
                  <CheckCircle2 className="w-4 h-4" />
                  {rule.title}
                </div>

                <p className="text-xs text-emerald-800/80 mt-2 leading-relaxed">
                  {rule.text}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* LIMITES QUE PODEM VARIAR */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">
            Limites da escola
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Máximo de aulas por dia do professor
              </label>

              <input
                type="number"
                min="1"
                max="9"
                className="border border-gray-300 p-2 rounded-lg"
                value={config.max_classes_per_day}
                onChange={event =>
                  handleChange(
                    "max_classes_per_day",
                    Math.min(
                      Number(event.target.value),
                      9,
                    ),
                  )
                }
              />

              <p className="text-xs text-gray-500">
                Pode ser menor que 9, mas nunca maior.
              </p>
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Máx. aulas de alta complexidade por dia
              </label>

              <input
                type="number"
                min="0"
                max="15"
                className="border border-gray-300 p-2 rounded-lg"
                value={
                  config.max_high_complexity_per_day
                }
                onChange={event =>
                  handleChange(
                    "max_high_complexity_per_day",
                    Number(event.target.value),
                  )
                }
              />

              <p className="text-xs text-gray-500">
                Regra pedagógica configurável.
              </p>
            </div>
          </div>
        </section>

        {/* PROFESSORES */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">
            Preferências dos professores
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Evitar janelas entre aulas
              </label>

              <select
                className="border border-gray-300 rounded-lg p-2"
                value={
                  config.teacher_gaps_hard
                    ? "hard"
                    : "soft"
                }
                onChange={event =>
                  handleChange(
                    "teacher_gaps_hard",
                    event.target.value === "hard",
                  )
                }
              >
                <option value="soft">
                  Preferir evitar
                </option>
                <option value="hard">
                  Proibir
                </option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Mínimo de aulas quando vier à escola
              </label>

              <input
                type="number"
                min="0"
                max="15"
                className="border border-gray-300 p-2 rounded-lg"
                value={config.min_classes_teachers}
                onChange={event =>
                  handleChange(
                    "min_classes_teachers",
                    Number(event.target.value),
                  )
                }
              />

              <p className="text-xs text-gray-500">
                Preferência: evita deslocamento para
                apenas uma aula.
              </p>
            </div>
          </div>
        </section>

        {/* ALUNOS */}
        <section className="bg-white p-6 rounded-xl shadow-sm border border-gray-200">
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">
            Preferências das turmas
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Mínimo de aulas em um dia ativo
              </label>

              <input
                type="number"
                min="0"
                max="15"
                className="border border-gray-300 p-2 rounded-lg"
                value={config.min_classes_students}
                onChange={event =>
                  handleChange(
                    "min_classes_students",
                    Number(event.target.value),
                  )
                }
              />
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Evitar 1ª aula
              </label>

              <select
                className="border border-gray-300 rounded-lg p-2"
                value={
                  config.avoid_first_period
                    ? "yes"
                    : "no"
                }
                onChange={event =>
                  handleChange(
                    "avoid_first_period",
                    event.target.value === "yes",
                  )
                }
              >
                <option value="no">
                  Não
                </option>
                <option value="yes">
                  Sim, como preferência
                </option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Evitar última aula
              </label>

              <select
                className="border border-gray-300 rounded-lg p-2"
                value={
                  config.avoid_last_period
                    ? "yes"
                    : "no"
                }
                onChange={event =>
                  handleChange(
                    "avoid_last_period",
                    event.target.value === "yes",
                  )
                }
              >
                <option value="no">
                  Não
                </option>
                <option value="yes">
                  Sim, como preferência
                </option>
              </select>
            </div>

            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">
                Evitar sexta-feira
              </label>

              <select
                className="border border-gray-300 rounded-lg p-2"
                value={
                  config.avoid_friday
                    ? "yes"
                    : "no"
                }
                onChange={event =>
                  handleChange(
                    "avoid_friday",
                    event.target.value === "yes",
                  )
                }
              >
                <option value="no">
                  Não
                </option>
                <option value="yes">
                  Sim, como preferência
                </option>
              </select>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
