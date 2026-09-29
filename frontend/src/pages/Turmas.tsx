import { useState, useEffect } from 'react';
import { api } from '../api';
import { BookOpen, School, Layers, Plus } from 'lucide-react';

interface Course {
  id: number;
  name: string;
}

interface Classroom {
  id: number;
  name: string;
  shift: string;
  course_id: number;
}

interface Subject {
  id: number;
  name: string;
  workload: number;
  complexity: string;
  course_ids: number[];
}

export default function Turmas() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);

  const [newCourseName, setNewCourseName] = useState("");
  
  const [newClassName, setNewClassName] = useState("");
  const [newClassShift, setNewClassShift] = useState("Manhã");
  const [newClassCourseId, setNewClassCourseId] = useState("");

  const [newSubName, setNewSubName] = useState("");
  const [newSubWorkload, setNewSubWorkload] = useState(4);
  const [newSubComplexity, setNewSubComplexity] = useState("Media");
  const [newSubCourseIds, setNewSubCourseIds] = useState<number[]>([]);

  const fetchData = async () => {
    try {
      const [cRes, clRes, sRes] = await Promise.all([
        api.get("/courses/"),
        api.get("/classrooms/"),
        api.get("/subjects/")
      ]);
      setCourses(cRes.data);
      setClassrooms(clRes.data);
      setSubjects(sRes.data);
    } catch (error) {
      console.error("Erro ao buscar dados:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddCourse = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCourseName.trim()) return;
    await api.post("/courses/", { name: newCourseName });
    setNewCourseName("");
    fetchData();
  };

  const handleAddClassroom = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newClassName.trim() || !newClassCourseId) return;
    await api.post("/classrooms/", { 
      name: newClassName, 
      shift: newClassShift, 
      course_id: Number(newClassCourseId) 
    });
    setNewClassName("");
    fetchData();
  };

  const handleAddSubject = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubName.trim() || newSubCourseIds.length === 0) return;
    await api.post("/subjects/", { 
      name: newSubName, 
      workload: Number(newSubWorkload), 
      complexity: newSubComplexity, 
      course_ids: newSubCourseIds 
    });
    setNewSubName("");
    setNewSubWorkload(4);
    setNewSubCourseIds([]);
    fetchData();
  };

  return (
    <div className="p-8 space-y-8 max-w-7xl mx-auto">
      <h2 className="text-3xl font-bold text-gray-800 flex items-center gap-2 mb-8">
        <BookOpen className="w-8 h-8 text-indigo-600" />
        Gestão Acadêmica
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* CURSOS */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <School className="w-5 h-5 text-blue-500" /> Cursos
          </h3>
          <form onSubmit={handleAddCourse} className="mb-6 flex gap-2">
            <input 
              type="text" 
              required 
              placeholder="Nome do Curso" 
              className="flex-1 border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500" 
              value={newCourseName} 
              onChange={e => setNewCourseName(e.target.value)} 
            />
            <button type="submit" className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors">
              <Plus className="w-5 h-5" />
            </button>
          </form>
          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[400px] pr-2">
            {courses.map(c => (
              <li key={c.id} className="p-3 bg-gray-50 border border-gray-100 rounded-lg flex justify-between items-center">
                <span className="font-medium text-gray-800">{c.name}</span>
                <span className="text-xs text-gray-400 bg-gray-200 px-2 py-1 rounded-full">ID: {c.id}</span>
              </li>
            ))}
            {courses.length === 0 && <p className="text-sm text-gray-500 text-center py-4">Nenhum curso cadastrado.</p>}
          </ul>
        </div>

        {/* TURMAS */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <Layers className="w-5 h-5 text-emerald-500" /> Turmas
          </h3>
          <form onSubmit={handleAddClassroom} className="mb-6 flex flex-col gap-3">
            <input 
              type="text" 
              required 
              placeholder="Nome da Turma (ex: 1º Ano A)" 
              className="border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500" 
              value={newClassName} 
              onChange={e => setNewClassName(e.target.value)} 
            />
            <div className="flex gap-2">
              <select 
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                value={newClassShift} 
                onChange={e => setNewClassShift(e.target.value)}
              >
                <option value="Manhã">Manhã</option>
                <option value="Tarde">Tarde</option>
                <option value="Noite">Noite</option>
              </select>
              <select 
                required 
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500" 
                value={newClassCourseId} 
                onChange={e => setNewClassCourseId(e.target.value)}
              >
                <option value="" disabled>Selecione o Curso</option>
                {courses.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <button type="submit" className="bg-emerald-600 text-white p-2 rounded-lg hover:bg-emerald-700 flex items-center justify-center gap-1 transition-colors">
              <Plus className="w-4 h-4" /> Adicionar Turma
            </button>
          </form>
          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[400px] pr-2">
            {classrooms.map(t => (
              <li key={t.id} className="p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm flex flex-col gap-1">
                <div className="flex justify-between">
                  <strong className="text-gray-800 text-base">{t.name}</strong>
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">{t.shift}</span>
                </div>
                <div className="text-xs text-emerald-600 font-medium">
                  Curso: {courses.find(c => c.id === t.course_id)?.name || t.course_id}
                </div>
              </li>
            ))}
            {classrooms.length === 0 && <p className="text-sm text-gray-500 text-center py-4">Nenhuma turma cadastrada.</p>}
          </ul>
        </div>

        {/* MATÉRIAS */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <BookOpen className="w-5 h-5 text-purple-500" /> Disciplinas
          </h3>
          <form onSubmit={handleAddSubject} className="mb-6 flex flex-col gap-3">
            <input 
              type="text" 
              required 
              placeholder="Nome (ex: Matemática)" 
              className="border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500" 
              value={newSubName} 
              onChange={e => setNewSubName(e.target.value)} 
            />
            <div className="flex gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase">Aulas/Sem</label>
                <input 
                  type="number" 
                  min="1" 
                  required 
                  className="border border-gray-300 p-2 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  value={newSubWorkload} 
                  onChange={e => setNewSubWorkload(Number(e.target.value))} 
                />
              </div>
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase">Complexidade</label>
                <select 
                  className="border border-gray-300 p-2 rounded-lg w-full bg-white focus:outline-none focus:ring-2 focus:ring-purple-500" 
                  value={newSubComplexity} 
                  onChange={e => setNewSubComplexity(e.target.value)}
                >
                  <option value="Alta">Alta</option>
                  <option value="Media">Média</option>
                  <option value="Baixa">Baixa</option>
                </select>
              </div>
            </div>
            
            <div className="border border-gray-300 p-2 rounded-lg bg-white max-h-32 overflow-y-auto flex flex-col gap-1">
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1">Cursos Associados</label>
              {courses.map(c => (
                <label key={c.id} className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input 
                    type="checkbox" 
                    checked={newSubCourseIds.includes(c.id)} 
                    onChange={e => {
                      if (e.target.checked) setNewSubCourseIds([...newSubCourseIds, c.id]);
                      else setNewSubCourseIds(newSubCourseIds.filter(id => id !== c.id));
                    }} 
                  />
                  {c.name}
                </label>
              ))}
              {courses.length === 0 && <span className="text-xs text-gray-400">Cadastre cursos primeiro</span>}
            </div>

            <button type="submit" className="bg-purple-600 text-white p-2 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-1 transition-colors mt-2">
              <Plus className="w-4 h-4" /> Adicionar Disciplina
            </button>
          </form>
          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[400px] pr-2">
            {subjects.map(s => (
              <li key={s.id} className="p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm flex flex-col gap-2">
                <div className="flex justify-between items-start">
                  <div>
                    <strong className="text-gray-800 text-base block">{s.name}</strong>
                    <span className="text-xs text-gray-500">{s.workload} aulas semanais</span>
                  </div>
                  <span className={`text-[10px] uppercase font-bold px-2 py-1 rounded-full ${s.complexity === 'Alta' ? 'bg-red-100 text-red-700' : s.complexity === 'Media' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}`}>
                    {s.complexity}
                  </span>
                </div>
                <div className="text-xs text-purple-600 font-medium">
                  Cursos: {s.course_ids?.map(id => courses.find(c => c.id === id)?.name || id).join(', ') || 'Nenhum'}
                </div>
              </li>
            ))}
            {subjects.length === 0 && <p className="text-sm text-gray-500 text-center py-4">Nenhuma disciplina cadastrada.</p>}
          </ul>
        </div>

      </div>
    </div>
  );
}
