import { useState, useEffect } from 'react';
import { api } from '../api';
import { Save } from 'lucide-react';

export default function Config() {
  const [config, setConfig] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await api.get("/config/");
        setConfig(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchConfig();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put("/config/", config);
      alert("Configurações salvas com sucesso!");
    } catch (err) {
      console.error(err);
      alert("Erro ao salvar.");
    } finally {
      setSaving(false);
    }
  };

  const handleChange = (field: string, value: any) => {
    setConfig({ ...config, [field]: value });
  };

  if (loading) return <div className="p-8">Carregando...</div>;
  if (!config) return <div className="p-8">Erro ao carregar configurações.</div>;

  return (
    <div className="p-8 max-w-4xl mx-auto pb-24">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-3xl font-bold text-gray-800">Regras e Leis</h2>
          <p className="text-gray-500 mt-1">Configure os limites e pesos da Inteligência Artificial</p>
        </div>
        <button 
          onClick={handleSave}
          disabled={saving}
          className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg font-bold flex items-center gap-2">
          <Save className="w-5 h-5" />
          {saving ? "Salvando..." : "Salvar Configurações"}
        </button>
      </div>

      <div className="space-y-8 bg-white p-8 rounded-xl shadow-sm border border-gray-200">
        
        {/* REGRAS TRABALHISTAS */}
        <div>
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">Regras Trabalhistas (Professores)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Máximo de Aulas por Dia (Professor)</label>
              <input type="number" className="border border-gray-300 p-2 rounded-lg" value={config.max_classes_per_day} onChange={e => handleChange("max_classes_per_day", Number(e.target.value))} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Máximo de Aulas Consecutivas</label>
              <input type="number" className="border border-gray-300 p-2 rounded-lg" value={config.max_consecutive_classes} onChange={e => handleChange("max_consecutive_classes", Number(e.target.value))} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Mínimo de Aulas por Dia (Preferência Soft)</label>
              <input type="number" className="border border-gray-300 p-2 rounded-lg" value={config.min_classes_teachers} onChange={e => handleChange("min_classes_teachers", Number(e.target.value))} />
              <p className="text-xs text-gray-500">Evita que o professor vá à escola para dar apenas 1 aula.</p>
            </div>
          </div>
        </div>

        {/* REGRAS PEDAGÓGICAS */}
        <div>
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">Regras Pedagógicas (Alunos)</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Máx. Disciplinas de Alta Complexidade / Dia</label>
              <input type="number" className="border border-gray-300 p-2 rounded-lg" value={config.max_high_complexity_per_day} onChange={e => handleChange("max_high_complexity_per_day", Number(e.target.value))} />
            </div>
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Mínimo de Aulas por Dia (Preferência Soft)</label>
              <input type="number" className="border border-gray-300 p-2 rounded-lg" value={config.min_classes_students} onChange={e => handleChange("min_classes_students", Number(e.target.value))} />
              <p className="text-xs text-gray-500">Evita que a turma vá à escola para ter apenas poucas aulas.</p>
            </div>
            <div className="flex flex-col gap-2">
              <label className="font-semibold text-gray-700">Máx. Aulas Seguidas do Mesmo Professor</label>
              <div className="flex gap-2">
                <input type="number" className="border border-gray-300 p-2 rounded-lg w-20" value={config.max_consec_per_teacher} onChange={e => handleChange("max_consec_per_teacher", Number(e.target.value))} />
                <select className="border border-gray-300 rounded-lg p-2 flex-1 text-sm font-bold" value={config.max_consec_teacher_mode} onChange={e => handleChange("max_consec_teacher_mode", e.target.value)}>
                  <option value="ignore">IGNORAR REGRA</option>
                  <option value="soft">PREFERÍVEL EVITAR (Soft)</option>
                  <option value="hard">OBRIGATÓRIO EVITAR (Hard)</option>
                </select>
              </div>
              <p className="text-xs text-gray-500">Impede que a mesma turma tenha 3 ou 4 aulas seguidas com o mesmo professor.</p>
            </div>
          </div>
        </div>

        {/* PREFERÊNCIAS E JANELAS */}
        <div>
          <h3 className="text-xl font-bold text-gray-700 mb-4 border-b pb-2">Janelas e Preferências</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            
            <div className="flex flex-col gap-3 p-4 border rounded-lg bg-gray-50">
              <label className="font-bold text-gray-700">Janelas para Alunos</label>
              <select className="border border-gray-300 rounded p-2" value={config.student_gaps_hard ? "true" : "false"} onChange={e => handleChange("student_gaps_hard", e.target.value === "true")}>
                <option value="true">OBRIGATÓRIO EVITAR (Hard)</option>
                <option value="false">PREFERÍVEL EVITAR (Soft)</option>
              </select>
            </div>

            <div className="flex flex-col gap-3 p-4 border rounded-lg bg-gray-50">
              <label className="font-bold text-gray-700">Janelas para Professores</label>
              <select className="border border-gray-300 rounded p-2" value={config.teacher_gaps_hard ? "true" : "false"} onChange={e => handleChange("teacher_gaps_hard", e.target.value === "true")}>
                <option value="true">OBRIGATÓRIO EVITAR (Hard)</option>
                <option value="false">PREFERÍVEL EVITAR (Soft)</option>
              </select>
            </div>

            <div className="flex flex-col gap-3 p-4 border rounded-lg bg-gray-50">
              <label className="font-bold text-gray-700">Alunos: Evitar 1ª Aula (Soft)</label>
              <select className="border border-gray-300 rounded p-2" value={config.avoid_first_period ? "true" : "false"} onChange={e => handleChange("avoid_first_period", e.target.value === "true")}>
                <option value="false">NÃO</option>
                <option value="true">SIM</option>
              </select>
            </div>

            <div className="flex flex-col gap-3 p-4 border rounded-lg bg-gray-50">
              <label className="font-bold text-gray-700">Alunos: Evitar Última Aula (Soft)</label>
              <select className="border border-gray-300 rounded p-2" value={config.avoid_last_period ? "true" : "false"} onChange={e => handleChange("avoid_last_period", e.target.value === "true")}>
                <option value="false">NÃO</option>
                <option value="true">SIM</option>
              </select>
            </div>

            <div className="flex flex-col gap-3 p-4 border rounded-lg bg-gray-50">
              <label className="font-bold text-gray-700">Alunos: Evitar Aulas de Sexta-feira (Soft)</label>
              <select className="border border-gray-300 rounded p-2" value={config.avoid_friday ? "true" : "false"} onChange={e => handleChange("avoid_friday", e.target.value === "true")}>
                <option value="false">NÃO</option>
                <option value="true">SIM</option>
              </select>
            </div>

          </div>
        </div>
        
      </div>
    </div>
  );
}
