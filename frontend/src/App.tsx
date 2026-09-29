import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Calendar, Users, BookOpen, Settings, Filter } from 'lucide-react';
import { useState, useEffect } from 'react';
import { api } from './api';
import Turmas from './pages/Turmas';
import Professores from './pages/Professores';
import Config from './pages/Config';

const DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];
const PERIOD_NAMES = [
  "07:10 - 08:00", "08:00 - 08:50", "08:50 - 09:40", "10:00 - 10:50", "10:50 - 11:40",
  "13:00 - 13:50", "13:50 - 14:40", "14:50 - 15:40", "15:40 - 16:30", "16:30 - 17:20",
  "19:00 - 19:50", "19:50 - 20:30", "20:30 - 21:15", "21:30 - 22:15", "22:15 - 23:00"
];
const SHIFT_MAP: Record<string, number[]> = {
  "Manhã": [0, 1, 2, 3, 4],
  "Tarde": [5, 6, 7, 8, 9],
  "Noite": [10, 11, 12, 13, 14]
};

function App() {
  const [schedule, setSchedule] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);

  const [viewMode, setViewMode] = useState<"turma" | "professor">("turma");
  const [selectedId, setSelectedId] = useState<number | "">("");

  useEffect(() => {
    const fetchBaseData = async () => {
      try {
        const [cRes, sRes, tRes, timeRes] = await Promise.all([
          api.get("/classrooms/"),
          api.get("/subjects/"),
          api.get("/teachers/"),
          api.get("/timetable/")
        ]);
        setClassrooms(cRes.data);
        setSubjects(sRes.data);
        setTeachers(tRes.data);
        if (timeRes.data.length > 0) {
          setSchedule(timeRes.data);
        }
        if (cRes.data.length > 0) setSelectedId(cRes.data[0].id);
      } catch (err) {
        console.error("Erro ao buscar dados iniciais", err);
      }
    };
    fetchBaseData();
  }, []);

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    try {
      const response = await api.post("/generate/");
      const newSchedule = response.data.schedule;
      setSchedule(newSchedule);
      // Salva a nova grade automaticamente no banco
      await api.post("/timetable/", newSchedule);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Erro ao gerar grade");
    } finally {
      setLoading(false);
    }
  };

  const getSubName = (id: number) => subjects.find(s => s.id === id)?.name || "N/A";
  const getProfName = (id: number) => teachers.find(t => t.id === id)?.name || "N/A";
  const getClassroomName = (id: number) => classrooms.find(c => c.id === id)?.name || "N/A";

  const renderScheduleGrid = () => {
    if (!schedule) return (
      <div className="flex h-full items-center justify-center text-gray-500 mt-32">
        Nenhuma grade gerada. Clique em "Gerar Grade".
      </div>
    );
    if (!selectedId) return (
      <div className="flex h-full items-center justify-center text-gray-500 mt-32">
        Selecione uma Turma ou Professor para visualizar.
      </div>
    );

    let periodsToShow: number[] = [];
    
    if (viewMode === "turma") {
      const turma = classrooms.find(c => c.id === selectedId);
      periodsToShow = SHIFT_MAP[turma?.shift || "Manhã"];
    } else {
      // Professores vêem o dia todo (15 períodos)
      periodsToShow = Array.from({ length: 15 }, (_, i) => i);
    }

    return (
      <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
        <table className="w-full text-sm text-center">
          <thead className="bg-gray-100 text-gray-600 font-bold border-b">
            <tr>
              <th className="p-3 border-r w-24">Horário</th>
              {DAYS.map(day => <th key={day} className="p-3 border-r last:border-0">{day}</th>)}
            </tr>
          </thead>
          <tbody>
            {periodsToShow.map(p => (
              <tr key={p} className="border-b last:border-0 hover:bg-gray-50">
                <td className="p-3 border-r font-bold text-gray-700 bg-gray-50">
                  {PERIOD_NAMES[p]}
                </td>
                {DAYS.map((_, d) => {
                  let cellContent = null;
                  
                  if (viewMode === "turma") {
                    const lesson = schedule.find(s => s.day === d && s.period === p && s.classroom_id === selectedId);
                    if (lesson) {
                      cellContent = (
                        <div className="flex flex-col items-center justify-center p-2 h-full bg-indigo-50 border border-indigo-100 rounded">
                          <span className="font-bold text-indigo-900">{getSubName(lesson.subject_id)}</span>
                          <span className="text-xs text-indigo-600 mt-1">{getProfName(lesson.teacher_id)}</span>
                        </div>
                      );
                    }
                  } else {
                    // Visão Professor
                    const lesson = schedule.find(s => s.day === d && s.period === p && s.teacher_id === selectedId);
                    if (lesson) {
                      cellContent = (
                        <div className="flex flex-col items-center justify-center p-2 h-full bg-emerald-50 border border-emerald-100 rounded">
                          <span className="font-bold text-emerald-900">{getSubName(lesson.subject_id)}</span>
                          <span className="text-xs text-emerald-700 mt-1">{getClassroomName(lesson.classroom_id)}</span>
                        </div>
                      );
                    }
                  }

                  return (
                    <td key={d} className="p-2 border-r last:border-0 align-top h-20 w-[18%]">
                      {cellContent || <div className="h-full w-full bg-gray-50 rounded border border-dashed border-gray-200"></div>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <Router>
      <div className="flex h-screen bg-gray-50 text-gray-900 w-full text-left">
        <aside className="w-64 bg-white border-r border-gray-200 flex flex-col shrink-0">
          <div className="p-6 border-b border-gray-200">
            <h1 className="text-xl font-bold text-indigo-600 flex items-center gap-2">
              <Calendar className="w-6 h-6" />
              GeradorHorários
            </h1>
          </div>
          <nav className="flex-1 p-4 space-y-2 flex flex-col">
            <Link to="/" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors">
              <Calendar className="w-5 h-5 text-gray-500" />
              <span className="font-medium">Grade Horária</span>
            </Link>
            <Link to="/professores" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors">
              <Users className="w-5 h-5 text-gray-500" />
              <span className="font-medium">Professores</span>
            </Link>
            <Link to="/turmas" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors">
              <BookOpen className="w-5 h-5 text-gray-500" />
              <span className="font-medium">Turmas e Matérias</span>
            </Link>
            <div className="flex-1"></div>
            <Link to="/config" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors mt-auto">
              <Settings className="w-5 h-5 text-gray-500" />
              <span className="font-medium">Regras e Leis</span>
            </Link>
          </nav>
        </aside>

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={
              <div className="p-8 max-w-7xl mx-auto">
                <header className="flex justify-between items-center mb-8">
                  <div>
                    <h2 className="text-3xl font-bold text-gray-800">Grade Horária</h2>
                    <p className="text-gray-500 mt-1">Visualize os horários gerados por turma ou professor.</p>
                  </div>
                  <button 
                    onClick={handleGenerate}
                    disabled={loading}
                    className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-bold shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2">
                    {loading ? (
                      <span className="animate-pulse">Calculando Rotações...</span>
                    ) : (
                      "Gerar Nova Grade"
                    )}
                  </button>
                </header>

                {error && (
                  <div className="mb-6 p-4 bg-red-100 border border-red-200 text-red-700 rounded-lg font-medium">
                    {error}
                  </div>
                )}

                <div className="mb-6 bg-white p-4 rounded-xl border border-gray-200 flex gap-4 items-center shadow-sm">
                  <div className="flex items-center gap-2 text-gray-700 font-semibold">
                    <Filter className="w-5 h-5" /> Filtro de Visão:
                  </div>
                  
                  <select 
                    className="border border-gray-300 rounded-lg p-2 font-medium focus:ring-2 focus:ring-indigo-500 outline-none"
                    value={viewMode}
                    onChange={e => {
                      setViewMode(e.target.value as "turma" | "professor");
                      setSelectedId("");
                    }}
                  >
                    <option value="turma">Visão por Turma</option>
                    <option value="professor">Visão por Professor</option>
                  </select>

                  <select 
                    className="border border-gray-300 rounded-lg p-2 flex-1 focus:ring-2 focus:ring-indigo-500 outline-none"
                    value={selectedId}
                    onChange={e => setSelectedId(Number(e.target.value))}
                  >
                    <option value="">Selecione...</option>
                    {viewMode === "turma" && classrooms.map(c => (
                      <option key={c.id} value={c.id}>{c.name} ({c.shift})</option>
                    ))}
                    {viewMode === "professor" && teachers.map(t => (
                      <option key={t.id} value={t.id}>{t.name}</option>
                    ))}
                  </select>
                </div>

                {renderScheduleGrid()}

              </div>
            } />
            <Route path="/professores" element={<Professores />} />
            <Route path="/turmas" element={<Turmas />} />
            <Route path="/config" element={<Config />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
