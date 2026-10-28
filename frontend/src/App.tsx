import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Calendar, Users, BookOpen, Settings, Filter, Moon, Sun, Download, Printer } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from './api';
import { exportTimetableToExcel } from './utils/exportTimetableToExcel';
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
  pause("12:30 - 13:00", "Almoço"),
  lesson(6), lesson(7),
  pause("14:40 - 14:50", "Intervalo"),
  lesson(8), lesson(9), lesson(10),
  lesson(11), lesson(12), lesson(13),
  pause("21:15 - 21:30", "Intervalo"),
  lesson(14), lesson(15),
];

type Theme = "light" | "dark";

function getInitialTheme(): Theme {
  const savedTheme = localStorage.getItem("anatinus-theme");

  if (savedTheme === "light" || savedTheme === "dark") {
    return savedTheme;
  }

  return "dark";
}

function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);
  const [schedule, setSchedule] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [generationSuccess, setGenerationSuccess] =
    useState(false);

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

      setSelectedId(current => {
        if (current !== "") {
          return current;
        }

        return cRes.data.length > 0
          ? cRes.data[0].id
          : "";
      });

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
    const handleAcademicDataChanged = () => {
      fetchBaseData(false);
    };

    window.addEventListener(
      "anatinus:academic-data-changed",
      handleAcademicDataChanged,
    );

    return () => {
      window.removeEventListener(
        "anatinus:academic-data-changed",
        handleAcademicDataChanged,
      );
    };
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle(
      "dark-theme",
      theme === "dark",
    );

    const favicon = document.querySelector<HTMLLinkElement>(
      "#app-favicon",
    );
    if (favicon) {
      favicon.href =
        theme === "dark"
          ? "/anatinus%20final%201%20branco.png"
          : "/Anatinus%20final%201.png";
    }

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
    setGenerationSuccess(false);

    try {
      // Recarrega turmas, disciplinas e professores antes de gerar.
      // Isso evita usar na grade dados antigos que foram alterados
      // em outra página, como Grupos A/B e tipo da disciplina.
      await fetchBaseData(false);

      const response = await api.post("/generate/");
      const newSchedule = response.data.schedule;
      setSchedule(newSchedule);
      setGenerationSuccess(true);
    } catch (err: any) {
      setGenerationSuccess(false);
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

  const handleExportExcel = () => {
    if (!schedule || schedule.length === 0) {
      return;
    }

    const groupOrder = (group: string | null | undefined) =>
      group === "Todos" ? 0 : group === "A" ? 1 : 2;

    const rows = [...schedule]
      .sort(
        (a, b) =>
          a.day - b.day
          || a.period - b.period
          || a.classroom_id - b.classroom_id
          || groupOrder(a.student_group) - groupOrder(b.student_group)
          || getSubName(a.subject_id).localeCompare(getSubName(b.subject_id), "pt-BR"),
      )
      .map(item => [
        String(DAYS[item.day] || item.day),
        String(PERIOD_NAMES[item.period] || item.period),
        getClassroomName(item.classroom_id),
        item.student_group || "Todos",
        getSubName(item.subject_id),
        getProfName(item.teacher_id),
      ]);

    exportTimetableToExcel(
      ["Dia", "Horário", "Turma", "Grupo", "Disciplina", "Professor"],
      rows,
    );
  };

  const handlePrint = () => {
    window.print();
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
        <div className="app-empty-state">
          <div className="app-empty-icon"><Calendar className="w-6 h-6" /></div>
          <h3>Nenhuma grade gerada</h3>
          <p>Use “Gerar grade” para criar os horários.</p>
        </div>
      );
    }

    if (!selectedId) {
      return (
        <div className="app-empty-state app-empty-state-compact">
          <div className="app-empty-icon"><Filter className="w-5 h-5" /></div>
          <h3>Selecione uma turma ou professor</h3>
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
      <div className="app-schedule-frame overflow-x-auto bg-white rounded-xl border border-gray-200 shadow-sm">
        <table className="app-schedule-table w-full text-sm text-center">
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
      <div className="app-shell flex h-screen w-full text-left">
        <aside className="app-sidebar flex flex-col shrink-0">
          <div className="app-brand p-6 border-b border-gray-200">
            <h1 className="app-brand-title text-xl font-bold flex items-center gap-2">
              <img
                src="/Anatinus%20final%201.png"
                alt=""
                aria-hidden="true"
                className="app-logo-light w-8 h-8"
              />
              <img
                src="/anatinus%20final%201%20branco.png"
                alt=""
                aria-hidden="true"
                className="app-logo-dark w-8 h-8"
              />
              <span className="app-brand-name">Anatinus</span>
            </h1>
          </div>

          <nav className="app-nav flex-1 p-4 space-y-2 flex flex-col">
            <NavLink
              to="/"
              title="Grade Horária"
              className={({ isActive }) => `app-nav-link flex items-center space-x-3 p-3 rounded-lg transition-colors ${isActive ? "app-nav-link-active" : ""}`}
            >
              <Calendar className="w-5 h-5 text-gray-500" />
              <span className="app-nav-label font-medium">Grade Horária</span>
            </NavLink>

            <NavLink
              to="/professores"
              title="Professores"
              className={({ isActive }) => `app-nav-link flex items-center space-x-3 p-3 rounded-lg transition-colors ${isActive ? "app-nav-link-active" : ""}`}
            >
              <Users className="w-5 h-5 text-gray-500" />
              <span className="app-nav-label font-medium">Professores</span>
            </NavLink>

            <NavLink
              to="/turmas"
              title="Turmas e Matérias"
              className={({ isActive }) => `app-nav-link flex items-center space-x-3 p-3 rounded-lg transition-colors ${isActive ? "app-nav-link-active" : ""}`}
            >
              <BookOpen className="w-5 h-5 text-gray-500" />
              <span className="app-nav-label font-medium">Turmas e Matérias</span>
            </NavLink>

            <div className="flex-1" />

            <button
              type="button"
              onClick={toggleTheme}
              className="app-theme-toggle w-full flex items-center justify-start p-3 rounded-lg transition-colors"
              title={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
              aria-label={theme === "dark" ? "Usar tema claro" : "Usar tema escuro"}
            >
              <span className="app-theme-label-group flex items-center space-x-3">
                {theme === "dark" ? (
                  <Sun className="w-5 h-5 text-amber-400" />
                ) : (
                  <Moon className="w-5 h-5 text-gray-500" />
                )}
                <span className="app-nav-label font-medium">
                  {theme === "dark" ? "Tema claro" : "Tema escuro"}
                </span>
              </span>


            </button>

            <NavLink
              to="/config"
              title="Regras e Leis"
              className={({ isActive }) => `app-nav-link flex items-center space-x-3 p-3 rounded-lg transition-colors ${isActive ? "app-nav-link-active" : ""}`}
            >
              <Settings className="w-5 h-5 text-gray-500" />
              <span className="app-nav-label font-medium">Regras e Leis</span>
            </NavLink>
          </nav>
        </aside>

        <main className="app-main flex-1 overflow-auto">
          <Routes>
            <Route
              path="/"
              element={
                <div className="app-page p-8 max-w-7xl mx-auto">
                  <h2 className="sr-only">Grade horária</h2>
                  <div className="app-toolbar no-print">
                    <div className="app-view-controls">
                      <select
                        aria-label="Visualizar por"
                        className="app-toolbar-select"
                        value={viewMode}
                        onChange={event => {
                          setViewMode(event.target.value as "turma" | "professor");
                          setSelectedId("");
                        }}
                      >
                        <option value="turma">Por turma</option>
                        <option value="professor">Por professor</option>
                      </select>

                      <select
                        aria-label={viewMode === "turma" ? "Selecionar turma" : "Selecionar professor"}
                        className="app-toolbar-select app-toolbar-select-target"
                        value={selectedId}
                        onChange={event => setSelectedId(event.target.value === "" ? "" : Number(event.target.value))}
                      >
                        <option value="">Selecionar...</option>
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

                    <div className="app-toolbar-actions">
                      {schedule && schedule.length > 0 && (
                        <>
                          <button
                            type="button"
                            onClick={handleExportExcel}
                            className="app-action-secondary"
                            title="Baixar a grade completa em Excel (.xlsx)"
                          >
                            <Download className="w-4 h-4" />
                            Excel
                          </button>
                          <button
                            type="button"
                            onClick={handlePrint}
                            className="app-action-secondary"
                            title="Imprimir a visualização atual"
                          >
                            <Printer className="w-4 h-4" />
                            Imprimir
                          </button>
                        </>
                      )}

                      <button
                        type="button"
                        onClick={handleGenerate}
                        disabled={loading}
                        className="app-action-primary disabled:opacity-50"
                      >
                        {loading ? <span>Gerando...</span> : "Gerar grade"}
                      </button>
                    </div>
                  </div>

                  {error && (
                    <div className="app-status-message app-status-error" role="alert">
                      {error}
                    </div>
                  )}

                  {loading && schedule && (
                    <div className="app-status-message app-status-info" role="status">
                      <strong>Gerando uma nova grade.</strong>
                      <span>A grade anterior continua disponível até o cálculo terminar.</span>
                    </div>
                  )}

                  {!error && generationSuccess && (
                    <div className="app-status-message app-status-success" role="status">
                      Grade gerada.
                    </div>
                  )}

                  {!error && unstaffedLessons > 0 && (
                    <details className="app-pending-details">
                      <summary>
                        <span className="app-pending-marker" aria-hidden="true" />
                        <strong>{unstaffedLessons}</strong>
                        <span>{unstaffedLessons === 1 ? "aula sem professor" : "aulas sem professor"}</span>
                        <span className="app-pending-toggle app-pending-toggle-closed">Ver detalhes</span>
                        <span className="app-pending-toggle app-pending-toggle-open">Ocultar detalhes</span>
                      </summary>
                      <div className="app-pending-body">
                        <p>Esses horários permanecem reservados até a escola atribuir um docente.</p>
                        <ul>
                          {unstaffedSummary.map(item => {
                            const groupLabel = item.studentGroup !== "Todos"
                              ? ` · Grupo ${item.studentGroup}`
                              : "";
                            return (
                              <li key={`${item.classroomId}-${item.subjectId}-${item.studentGroup}`}>
                                <span>{getClassroomName(item.classroomId)} · {getSubName(item.subjectId)}{groupLabel}</span>
                                <strong>{item.lessons} {item.lessons === 1 ? "aula" : "aulas"}</strong>
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    </details>
                  )}
                  <section className="app-schedule-workspace" aria-label="Grade semanal">
                    {schedule && selectedId !== "" && (
                      <header className="app-schedule-workspace-header">
                        <h2>{viewMode === "turma" ? getClassroomName(Number(selectedId)) : getProfName(Number(selectedId))}</h2>
                      </header>
                    )}
                    {renderScheduleGrid()}
                  </section>
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
