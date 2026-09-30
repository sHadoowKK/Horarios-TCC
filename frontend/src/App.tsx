import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Calendar, Users, BookOpen, Settings, Filter, Moon, Sun } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from './api';
import Turmas from './pages/Turmas';
import Professores from './pages/Professores';
import Config from './pages/Config';

const DAYS = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"];

const PERIOD_NAMES = [
  "07:10 - 08:00",
  "08:00 - 08:50",
  "08:50 - 09:40",
  "10:00 - 10:50",
  "10:50 - 11:40",
  "11:40 - 12:30",
  "13:00 - 13:50",
  "13:50 - 14:40",
  "14:50 - 15:40",
  "15:40 - 16:30",
  "16:30 - 17:20",
  "19:00 - 19:50",
  "19:50 - 20:30",
  "20:30 - 21:15",
  "21:30 - 22:15",
  "22:15 - 23:00",
];

type DisplayRow =
  | { kind: "lesson"; period: number }
  | { kind: "break"; label: string; name: string };

const lesson = (period: number): DisplayRow => ({ kind: "lesson", period });
const pause = (label: string, name: string): DisplayRow => ({ kind: "break", label, name });

const JOURNEY_ROWS: Record<string, DisplayRow[]> = {
  "Manhã": [
    lesson(0), lesson(1), lesson(2),
    pause("09:40 - 10:00", "Intervalo"),
    lesson(3), lesson(4), lesson(5),
  ],
  "Integral": [
    lesson(0), lesson(1), lesson(2),
    pause("09:40 - 10:00", "Intervalo"),
    lesson(3), lesson(4),
    pause("11:40 - 13:00", "Almoço"),
    lesson(6), lesson(7),
    pause("14:40 - 14:50", "Intervalo"),
    lesson(8), lesson(9), lesson(10),
  ],
  // Compatibilidade visual temporária até bancos antigos serem migrados.
  "Tarde": [
    lesson(6), lesson(7),
    pause("14:40 - 14:50", "Intervalo"),
    lesson(8), lesson(9), lesson(10),
  ],
  "Noite": [
    lesson(11), lesson(12), lesson(13),
    pause("21:15 - 21:30", "Intervalo"),
    lesson(14), lesson(15),
  ],
};

const PROFESSOR_ROWS: DisplayRow[] = [
  lesson(0), lesson(1), lesson(2),
  pause("09:40 - 10:00", "Intervalo"),
  lesson(3), lesson(4), lesson(5),
  lesson(6), lesson(7),
  pause("14:40 - 14:50", "Intervalo"),
  lesson(8), lesson(9), lesson(10),
  lesson(11), lesson(12), lesson(13),
  pause("21:15 - 21:30", "Intervalo"),
  lesson(14), lesson(15),
];

type Theme = "light" | "dark";

interface GenerationInfo {
  solveTimeSeconds?: number;
  solutionStatus?: string;
}

function getInitialTheme(): Theme {
  const savedTheme = localStorage.getItem("anatinus-theme");

  if (savedTheme === "light" || savedTheme === "dark") {
    return savedTheme;
  }

  return window.matchMedia?.("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [schedule, setSchedule] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [generationInfo, setGenerationInfo] =
    useState<GenerationInfo | null>(null);

  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);

  const [viewMode, setViewMode] = useState<"turma" | "professor">("turma");
  const [selectedId, setSelectedId] = useState<number | "">("");

  const fetchBaseData = async (loadSavedSchedule = true) => {
    try {
      const requests = [
        api.get("/classrooms/"),
        api.get("/subjects/"),
        api.get("/teachers/"),
      ];

      const [cRes, sRes, tRes] = await Promise.all(requests);

      setClassrooms(cRes.data);
      setSubjects(sRes.data);
      setTeachers(tRes.data);

      if (!selectedId && cRes.data.length > 0) {
        setSelectedId(cRes.data[0].id);
      }

      if (loadSavedSchedule) {
        const timeRes = await api.get("/timetable/");
        if (timeRes.data.length > 0) {
          setSchedule(timeRes.data);
        }
      }
    } catch (err) {
      console.error("Erro ao buscar dados acadêmicos", err);
    }
  };

  useEffect(() => {
    fetchBaseData();
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle(
      "dark-theme",
      theme === "dark",
    );
    localStorage.setItem("anatinus-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(current =>
      current === "dark" ? "light" : "dark",
    );
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");

    try {
      // Recarrega turmas, disciplinas e professores antes de gerar.
      // Isso evita usar na grade dados antigos que foram alterados
      // em outra página, como Grupos A/B e tipo da disciplina.
      await fetchBaseData(false);

      const response = await api.post("/generate/");
      const newSchedule = response.data.schedule;
      setSchedule(newSchedule);
      setGenerationInfo({
        solveTimeSeconds:
          response.data.solve_time_seconds,
        solutionStatus:
          response.data.solution_status,
      });

      // Salva a grade mais recente para ela reaparecer ao abrir o sistema.
      await api.post("/timetable/", newSchedule);
    } catch (err: any) {
      setGenerationInfo(null);
      const detail = err.response?.data?.detail;
      const responseText =
        typeof err.response?.data === "string"
          ? err.response.data
          : "";
      const message =
        detail
        || responseText
        || err.message
        || "Erro ao gerar grade";

      setError(`Erro ao gerar grade: ${message}`);
      console.error("Erro ao gerar grade", err);
    } finally {
      setLoading(false);
    }
  };

  const getSubName = (id: number) =>
    subjects.find(subject => subject.id === id)?.name || "N/A";

  const getProfName = (id: number | null | undefined) => {
    if (id === null || id === undefined) {
      return "Sem professor";
    }

    return (
      teachers.find(teacher => teacher.id === id)?.name
      || "Professor não encontrado"
    );
  };

  const getClassroomName = (id: number) =>
    classrooms.find(classroom => classroom.id === id)?.name || "N/A";

  const unstaffedLessons =
    schedule?.filter(item => item.teacher_id == null).length || 0;

  const unstaffedSummary = Object.values(
    (schedule || [])
      .filter(item => item.teacher_id == null)
      .reduce(
        (groups: Record<string, any>, item: any) => {
          const key = [
            item.classroom_id,
            item.subject_id,
            item.student_group || "Todos",
          ].join(":");

          if (!groups[key]) {
            groups[key] = {
              classroomId: item.classroom_id,
              subjectId: item.subject_id,
              studentGroup:
                item.student_group || "Todos",
              lessons: 0,
            };
          }

          groups[key].lessons += 1;
          return groups;
        },
        {},
      ),
  ) as Array<{
    classroomId: number;
    subjectId: number;
    studentGroup: string;
    lessons: number;
  }>;

  const renderScheduleGrid = () => {
    if (!schedule) {
      return (
        <div className="flex h-full items-center justify-center text-gray-500 mt-32">
          Nenhuma grade gerada. Clique em "Gerar Nova Grade".
        </div>
      );
    }

    if (!selectedId) {
      return (
        <div className="flex h-full items-center justify-center text-gray-500 mt-32">
          Selecione uma turma ou professor para visualizar.
        </div>
      );
    }

    let rows: DisplayRow[];

    if (viewMode === "turma") {
      const classroom = classrooms.find(item => item.id === selectedId);
      rows = JOURNEY_ROWS[classroom?.shift || "Manhã"] || JOURNEY_ROWS["Manhã"];
    } else {
      rows = PROFESSOR_ROWS;
    }

    return (
      <div className="overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
        <table className="w-full text-sm text-center">
          <thead className="bg-gray-100 text-gray-600 font-bold border-b">
            <tr>
              <th className="p-3 border-r w-28">Horário</th>
              {DAYS.map(day => (
                <th key={day} className="p-3 border-r last:border-0">{day}</th>
              ))}
            </tr>
          </thead>

          <tbody>
            {rows.map((row, rowIndex) => {
              if (row.kind === "break") {
                return (
                  <tr key={`break-${row.label}-${rowIndex}`} className="border-b bg-slate-100">
                    <td className="px-3 py-2 border-r font-semibold text-slate-500 whitespace-nowrap">
                      {row.label}
                    </td>
                    <td colSpan={5} className="px-3 py-2 text-xs font-bold uppercase tracking-widest text-slate-500">
                      {row.name}
                    </td>
                  </tr>
                );
              }

              const period = row.period;

              return (
                <tr key={period} className="border-b last:border-0 hover:bg-gray-50">
                  <td className="p-3 border-r font-bold text-gray-700 bg-gray-50 whitespace-nowrap">
                    {PERIOD_NAMES[period]}
                  </td>

                  {DAYS.map((_, day) => {
                    let cellContent = null;

                    if (viewMode === "turma") {
                      const classroom = classrooms.find(
                        item => item.id === selectedId
                      );

                      const lessons = schedule.filter(
                        item =>
                          item.day === day &&
                          item.period === period &&
                          item.classroom_id === selectedId
                      );

                      if (classroom?.has_groups) {
                        const jointLesson = lessons.find(
                          item => item.student_group === "Todos"
                        );
                        const groupA = lessons.find(
                          item => item.student_group === "A"
                        );
                        const groupB = lessons.find(
                          item => item.student_group === "B"
                        );

                        if (jointLesson) {
                          cellContent = (
                            <div className="flex flex-col items-center justify-center p-2 h-full bg-indigo-50 border border-indigo-100 rounded">
                              <span className="text-[10px] font-bold uppercase tracking-wide text-indigo-400 mb-1">
                                Turma inteira
                              </span>
                              <span className="font-bold text-indigo-900">
                                {getSubName(jointLesson.subject_id)}
                              </span>
                              <span className={`text-xs mt-1 ${
                                jointLesson.teacher_id == null
                                  ? "text-red-600 font-bold"
                                  : "text-indigo-600"
                              }`}>
                                {getProfName(jointLesson.teacher_id)}
                              </span>
                            </div>
                          );
                        } else {
                          const renderGroup = (group: "A" | "B", item: any) => (
                            <div className="min-h-16 flex flex-col items-center justify-center p-1.5 bg-indigo-50 border border-indigo-100 rounded">
                              <span className="text-[10px] font-bold uppercase text-indigo-400">
                                Grupo {group}
                              </span>
                              {item ? (
                                <>
                                  <span className="text-xs font-bold text-indigo-900 mt-0.5 leading-tight">
                                    {getSubName(item.subject_id)}
                                  </span>
                                  <span className={`text-[10px] mt-0.5 leading-tight ${
                                    item.teacher_id == null
                                      ? "text-red-600 font-bold"
                                      : "text-indigo-600"
                                  }`}>
                                    {getProfName(item.teacher_id)}
                                  </span>
                                </>
                              ) : (
                                <span className="text-[10px] text-gray-400 mt-1">
                                  Livre
                                </span>
                              )}
                            </div>
                          );

                          cellContent = (
                            <div className="grid grid-cols-2 gap-1 h-full">
                              {renderGroup("A", groupA)}
                              {renderGroup("B", groupB)}
                            </div>
                          );
                        }
                      } else {
                        const currentLesson = lessons[0];

                        if (currentLesson) {
                          cellContent = (
                            <div className="flex flex-col items-center justify-center p-2 h-full bg-indigo-50 border border-indigo-100 rounded">
                              <span className="font-bold text-indigo-900">
                                {getSubName(currentLesson.subject_id)}
                              </span>
                              <span className={`text-xs mt-1 ${
                                currentLesson.teacher_id == null
                                  ? "text-red-600 font-bold"
                                  : "text-indigo-600"
                              }`}>
                                {getProfName(currentLesson.teacher_id)}
                              </span>
                            </div>
                          );
                        }
                      }
                    } else {
                      const currentLesson = schedule.find(
                        item =>
                          item.day === day &&
                          item.period === period &&
                          item.teacher_id === selectedId
                      );

                      if (currentLesson) {
                        const groupLabel =
                          currentLesson.student_group &&
                          currentLesson.student_group !== "Todos"
                            ? ` · Grupo ${currentLesson.student_group}`
                            : "";

                        cellContent = (
                          <div className="flex flex-col items-center justify-center p-2 h-full bg-emerald-50 border border-emerald-100 rounded">
                            <span className="font-bold text-emerald-900">
                              {getSubName(currentLesson.subject_id)}
                            </span>
                            <span className="text-xs text-emerald-700 mt-1">
                              {getClassroomName(currentLesson.classroom_id)}
                              {groupLabel}
                            </span>
                          </div>
                        );
                      }
                    }

                    return (
                      <td
                        key={day}
                        className="p-2 border-r last:border-0 align-top h-20 w-[18%]"
                      >
                        {cellContent || (
                          <div className="h-full w-full bg-gray-50 rounded border border-dashed border-gray-200" />
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
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
              <img
                src="/anatinus.svg"
                alt=""
                className="w-8 h-8"
              />
              Anatinus
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

            <div className="flex-1" />

            <button
              type="button"
              onClick={toggleTheme}
              className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 transition-colors"
              title={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              aria-label={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
            >
              <span className="flex items-center space-x-3">
                {theme === "dark" ? (
                  <Sun className="w-5 h-5 text-amber-400" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-500" />
                )}
                <span className="font-medium">
                  {theme === "dark" ? "Tema claro" : "Tema escuro"}
                </span>
              </span>

              <span
                className={`theme-switch ${
                  theme === "dark" ? "theme-switch-on" : ""
                }`}
                aria-hidden="true"
              >
                <span className="theme-switch-knob" />
              </span>
            </button>

            <Link to="/config" className="flex items-center space-x-3 p-3 rounded-lg hover:bg-gray-100 transition-colors">
              <Settings className="w-5 h-5 text-gray-500" />
              <span className="font-medium">Regras e Leis</span>
            </Link>
          </nav>
        </aside>

        <main className="flex-1 overflow-auto">
          <Routes>
            <Route
              path="/"
              element={
                <div className="p-8 max-w-7xl mx-auto">
                  <header className="flex justify-between items-center mb-8">
                    <div>
                      <h2 className="text-3xl font-bold text-gray-800">Grade Horária</h2>
                      <p className="text-gray-500 mt-1">
                        Visualize os horários gerados por turma ou professor.
                      </p>
                    </div>

                    <button
                      onClick={handleGenerate}
                      disabled={loading}
                      className="bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-3 rounded-lg font-bold shadow-sm transition-colors disabled:opacity-50 flex items-center gap-2"
                    >
                      {loading ? (
                        <span className="animate-pulse">Calculando Grade...</span>
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

                  {!error && generationInfo && (
                    <div className="mb-4 px-4 py-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-lg text-sm">
                      <strong>Grade gerada.</strong>
                      {typeof generationInfo.solveTimeSeconds === "number" && (
                        <span className="ml-1">
                          Cálculo em {generationInfo.solveTimeSeconds.toFixed(2)}s.
                        </span>
                      )}
                    </div>
                  )}

                  {!error && unstaffedLessons > 0 && (
                    <div className="mb-6 p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-lg">
                      <div>
                        <strong>
                          {unstaffedLessons} {unstaffedLessons === 1 ? "aula está" : "aulas estão"} sem professor.
                        </strong>
                        <span className="ml-1">
                          A grade continua válida; esses horários ficam reservados até a escola atribuir um docente.
                        </span>
                      </div>

                      <div className="flex flex-wrap gap-2 mt-3">
                        {unstaffedSummary.map(item => {
                          const groupLabel =
                            item.studentGroup !== "Todos"
                              ? ` · Grupo ${item.studentGroup}`
                              : "";

                          return (
                            <span
                              key={`${item.classroomId}-${item.subjectId}-${item.studentGroup}`}
                              className="text-xs px-2 py-1 rounded bg-white border border-amber-200"
                            >
                              {getClassroomName(item.classroomId)}
                              {" · "}
                              {getSubName(item.subjectId)}
                              {groupLabel}
                              {" — "}
                              {item.lessons} {item.lessons === 1 ? "aula" : "aulas"}
                            </span>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  <div className="mb-6 bg-white p-4 rounded-xl border border-gray-200 flex gap-4 items-center shadow-sm">
                    <div className="flex items-center gap-2 text-gray-700 font-semibold">
                      <Filter className="w-5 h-5" />
                      Filtro de Visão:
                    </div>

                    <select
                      className="border border-gray-300 rounded-lg p-2 font-medium focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={viewMode}
                      onChange={event => {
                        setViewMode(event.target.value as "turma" | "professor");
                        setSelectedId("");
                      }}
                    >
                      <option value="turma">Visão por Turma</option>
                      <option value="professor">Visão por Professor</option>
                    </select>

                    <select
                      className="border border-gray-300 rounded-lg p-2 flex-1 focus:ring-2 focus:ring-indigo-500 outline-none"
                      value={selectedId}
                      onChange={event => setSelectedId(Number(event.target.value))}
                    >
                      <option value="">Selecione...</option>

                      {viewMode === "turma" && classrooms.map(classroom => (
                        <option key={classroom.id} value={classroom.id}>
                          {classroom.name} ({classroom.shift}{classroom.has_groups ? " · Grupos A/B" : ""})
                        </option>
                      ))}

                      {viewMode === "professor" && teachers.map(teacher => (
                        <option key={teacher.id} value={teacher.id}>
                          {teacher.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  {renderScheduleGrid()}
                </div>
              }
            />

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
