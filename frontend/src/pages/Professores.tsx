import React, { useState, useEffect } from 'react';
import { api } from '../api';
import { Users, Plus, CheckCircle, XCircle, Edit, Trash2, X, Star } from 'lucide-react';

interface Subject {
  id: number;
  name: string;
}

interface Teacher {
  id: number;
  name: string;
  allowed_subjects: number[];
  availability: Record<string, boolean[]>;
  score: number;
}

const DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];
const PERIOD_NAMES = [
  "07:10 - 08:00", "08:00 - 08:50", "08:50 - 09:40", "10:00 - 10:50", "10:50 - 11:40", "11:40 - 12:30",
  "13:00 - 13:50", "13:50 - 14:40", "14:50 - 15:40", "15:40 - 16:30", "16:30 - 17:20",
  "19:00 - 19:50", "19:50 - 20:30", "20:30 - 21:15", "21:30 - 22:15", "22:15 - 23:00"
];
const SHIFTS = [
  { name: "Manhã", prefix: "M", count: 6, startIndex: 0 },
  { name: "Tarde", prefix: "T", count: 5, startIndex: 6 },
  { name: "Noite", prefix: "N", count: 5, startIndex: 11 }
];

const normalizeAvailabilityDay = (values?: boolean[]) => {
  if (!values) return Array(16).fill(true);
  if (values.length === 16) return [...values];

  // Banco antigo: 5 manhã + 5 tarde + 5 noite.
  // A nova 6ª aula da manhã herda a disponibilidade da última aula matutina antiga.
  if (values.length === 15) {
    return [...values.slice(0, 5), values[4], ...values.slice(5)];
  }

  const normalized = Array(16).fill(true);
  for (let i = 0; i < Math.min(values.length, 16); i++) {
    normalized[i] = values[i];
  }
  return normalized;
};

const initialAvailability = () => {
  const avail: Record<string, boolean[]> = {};
  for (let i = 0; i < 5; i++) {
    avail[i.toString()] = Array(16).fill(true);
  }
  return avail;
};

export default function Professores() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);

  const [editingTeacherId, setEditingTeacherId] = useState<number | null>(null);
  const [newName, setNewName] = useState("");
  const [newScore, setNewScore] = useState(0);
  const [newAllowedSubjects, setNewAllowedSubjects] = useState<number[]>([]);
  const [newAvailability, setNewAvailability] = useState<Record<string, boolean[]>>(initialAvailability());

  const fetchData = async () => {
    try {
      const [tRes, sRes] = await Promise.all([
        api.get("/teachers/"),
        api.get("/subjects/")
      ]);
      setTeachers(tRes.data);
      setSubjects(sRes.data);
    } catch (error) {
      console.error("Erro ao buscar dados:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleToggleSubject = (subjectId: number) => {
    if (newAllowedSubjects.includes(subjectId)) {
      setNewAllowedSubjects(newAllowedSubjects.filter(id => id !== subjectId));
    } else {
      setNewAllowedSubjects([...newAllowedSubjects, subjectId]);
    }
  };

  const handleToggleAvailability = (dayIndex: number, periodIndex: number) => {
    const dayStr = dayIndex.toString();
    const updatedDay = [...newAvailability[dayStr]];
    updatedDay[periodIndex] = !updatedDay[periodIndex];
    setNewAvailability({
      ...newAvailability,
      [dayStr]: updatedDay
    });
  };

  const resetForm = () => {
    setEditingTeacherId(null);
    setNewName("");
    setNewScore(0);
    setNewAllowedSubjects([]);
    setNewAvailability(initialAvailability());
  };

  const handleSaveTeacher = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newName.trim() || newAllowedSubjects.length === 0) return;
    
    const normalizedAvailability: Record<string, boolean[]> = {};
    for (let i = 0; i < 5; i++) {
      const dayKey = i.toString();
      normalizedAvailability[dayKey] = normalizeAvailabilityDay(newAvailability[dayKey]);
    }

    const payload = {
      name: newName,
      score: newScore,
      allowed_subjects: newAllowedSubjects,
      availability: normalizedAvailability
    };

    try {
      if (editingTeacherId) {
        await api.put(`/teachers/${editingTeacherId}`, payload);
      } else {
        await api.post("/teachers/", payload);
      }
      resetForm();
      fetchData();
    } catch (error) {
      console.error("Erro ao salvar professor", error);
    }
  };

  const handleEdit = (teacher: Teacher) => {
    setEditingTeacherId(teacher.id);
    setNewName(teacher.name);
    setNewScore(teacher.score || 0);
    setNewAllowedSubjects([...teacher.allowed_subjects]);
    
    const availCopy: Record<string, boolean[]> = {};
    for (let day = 0; day < 5; day++) {
      const key = day.toString();
      availCopy[key] = normalizeAvailabilityDay(teacher.availability[key]);
    }
    setNewAvailability(availCopy);
    
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleDelete = async (id: number) => {
    if (confirm("Tem certeza que deseja remover este professor?")) {
      try {
        await api.delete(`/teachers/${id}`);
        if (editingTeacherId === id) {
          resetForm();
        }
        fetchData();
      } catch (error) {
        console.error("Erro ao remover professor", error);
      }
    }
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2 mb-8">
        <Users className="w-8 h-8 text-indigo-600" />
        Gestão de Professores
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* FORMULÁRIO */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 text-gray-700">
            {editingTeacherId ? "Editar Professor" : "Cadastrar Novo Professor"}
          </h3>
          <form onSubmit={handleSaveTeacher} className="flex flex-col gap-6">
            
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-semibold text-gray-600 mb-1 block">Nome do Professor</label>
                <input 
                  type="text" 
                  required 
                  placeholder="Ex: João da Silva" 
                  className="w-full border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                  value={newName} 
                  onChange={e => setNewName(e.target.value)} 
                />
              </div>
              <div className="w-32">
                <label className="text-sm font-semibold text-gray-600 mb-1 flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500" /> Pontuação
                </label>
                <input 
                  type="number" 
                  min="0"
                  max="100"
                  className="w-full border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500" 
                  value={newScore} 
                  onChange={e => setNewScore(Number(e.target.value))} 
                />
              </div>
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-600 mb-2 block">Disciplinas que pode lecionar</label>
              <div className="border border-gray-300 p-3 rounded-lg bg-gray-50 max-h-40 overflow-y-auto grid grid-cols-2 gap-2">
                {subjects.map(s => (
                  <label key={s.id} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer bg-white p-2 border rounded shadow-sm hover:bg-gray-50">
                    <input 
                      type="checkbox" 
                      checked={newAllowedSubjects.includes(s.id)} 
                      onChange={() => handleToggleSubject(s.id)}
                      className="accent-indigo-600"
                    />
                    {s.name}
                  </label>
                ))}
                {subjects.length === 0 && <span className="text-xs text-gray-400 col-span-2">Cadastre disciplinas primeiro na aba Turmas.</span>}
              </div>
            </div>

            <div>
              <label className="text-sm font-semibold text-gray-600 mb-2 block">Disponibilidade de Horário (3 Turnos)</label>
              <div className="border border-gray-300 rounded-lg overflow-hidden max-h-[400px] overflow-y-auto">
                <table className="w-full text-sm text-center bg-white relative">
                  <thead className="bg-gray-100 text-gray-600 font-medium sticky top-0 z-10 shadow-sm">
                    <tr>
                      <th className="p-2 border-r border-b">Horário</th>
                      {DAYS.map(day => <th key={day} className="p-2 border-b">{day.substring(0,3)}</th>)}
                    </tr>
                  </thead>
                  <tbody>
                    {SHIFTS.map(shift => (
                      <React.Fragment key={shift.name}>
                        <tr className="bg-indigo-50">
                          <td colSpan={6} className="p-1 font-bold text-indigo-800 text-left pl-3 text-xs border-y">
                            TURNO: {shift.name.toUpperCase()}
                          </td>
                        </tr>
                        {Array.from({ length: shift.count }).map((_, i) => {
                          const pIdx = shift.startIndex + i;
                          return (
                            <tr key={pIdx} className="border-b last:border-0 hover:bg-gray-50">
                              <td className="p-1 border-r text-left font-medium text-gray-700 text-xs pl-3 whitespace-nowrap">
                                {PERIOD_NAMES[pIdx]}
                              </td>
                              {DAYS.map((_, dIdx) => {
                                const dayAvail = newAvailability[dIdx.toString()];
                                const isAvailable = dayAvail ? dayAvail[pIdx] : false;
                                return (
                                  <td 
                                    key={dIdx} 
                                    className={`p-1 cursor-pointer transition-colors ${isAvailable ? 'bg-green-50 hover:bg-green-100' : 'bg-red-50 hover:bg-red-100'}`}
                                    onClick={() => handleToggleAvailability(dIdx, pIdx)}
                                  >
                                    <div className="flex justify-center">
                                      {isAvailable ? (
                                        <CheckCircle className="w-4 h-4 text-green-500" />
                                      ) : (
                                        <XCircle className="w-4 h-4 text-red-400" />
                                      )}
                                    </div>
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        })}
                      </React.Fragment>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex gap-2 mt-auto pt-4">
              <button type="submit" className="flex-1 bg-indigo-600 text-white p-3 rounded-lg hover:bg-indigo-700 flex items-center justify-center gap-2 transition-colors font-medium">
                <Plus className="w-5 h-5" /> {editingTeacherId ? "Salvar Alterações" : "Adicionar Professor"}
              </button>
              {editingTeacherId && (
                <button type="button" onClick={resetForm} className="bg-gray-300 text-gray-700 p-3 rounded-lg hover:bg-gray-400 flex items-center justify-center gap-2 transition-colors font-medium">
                  <X className="w-5 h-5" /> Cancelar
                </button>
              )}
            </div>
          </form>
        </div>

        {/* LISTA DE PROFESSORES */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 text-gray-700 flex items-center justify-between">
            Professores Cadastrados
            <span className="bg-indigo-100 text-indigo-700 text-sm py-1 px-3 rounded-full font-bold">{teachers.length}</span>
          </h3>
          <ul className="space-y-4 flex-1 overflow-y-auto max-h-[700px] pr-2">
            {teachers.map(t => (
              <li key={t.id} className="p-4 bg-gray-50 border border-gray-200 rounded-lg flex flex-col gap-3">
                <div className="flex justify-between items-start border-b border-gray-200 pb-2">
                  <div>
                    <strong className="text-gray-800 text-lg block">{t.name}</strong>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full inline-block">ID: {t.id}</span>
                      <span className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded-full inline-flex items-center gap-1 font-bold">
                        <Star className="w-3 h-3" /> {t.score || 0} pts
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button 
                      onClick={() => handleEdit(t)} 
                      className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg transition-colors"
                      title="Editar"
                    >
                      <Edit className="w-4 h-4" />
                    </button>
                    <button 
                      onClick={() => handleDelete(t.id)} 
                      className="p-2 text-red-600 hover:bg-red-100 rounded-lg transition-colors"
                      title="Remover"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                
                <div>
                  <strong className="text-xs text-gray-500 uppercase mb-1 block">Disciplinas Permitidas</strong>
                  <div className="flex flex-wrap gap-1">
                    {t.allowed_subjects.map(subId => (
                      <span key={subId} className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded">
                        {subjects.find(s => s.id === subId)?.name || `ID ${subId}`}
                      </span>
                    ))}
                    {t.allowed_subjects.length === 0 && <span className="text-xs text-gray-400">Nenhuma</span>}
                  </div>
                </div>

                <div>
                  <strong className="text-xs text-gray-500 uppercase mb-1 block">Dias Disponíveis</strong>
                  <div className="flex gap-2">
                    {DAYS.map((day, dIdx) => {
                      const dayAvail = t.availability[dIdx.toString()];
                      const hasAvail = dayAvail && dayAvail.some(a => a);
                      return (
                        <span key={day} title={day} className={`text-xs font-bold px-2 py-1 rounded-full w-8 text-center ${hasAvail ? 'bg-green-100 text-green-700' : 'bg-gray-200 text-gray-400'}`}>
                          {day.substring(0,3)}
                        </span>
                      );
                    })}
                  </div>
                </div>
              </li>
            ))}
            {teachers.length === 0 && (
              <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                <Users className="w-12 h-12 mb-2 opacity-50" />
                <p>Nenhum professor cadastrado ainda.</p>
              </div>
            )}
          </ul>
        </div>

      </div>
    </div>
  );
}
