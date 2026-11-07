import { BrowserRouter as Router, Routes, Route, NavLink } from 'react-router-dom';
import { Calendar, Users, BookOpen, Settings, Filter, Moon, Sun, Download, Printer, Lock, X } from 'lucide-react';
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
  const [generationSuccess, setGenerationSuccess] = useState(false);
  const [generationMessage, setGenerationMessage] = useState("");
  const [unstaffedDiagnostics, setUnstaffedDiagnostics] = useState<any[]>([]);
  const [generationScope, setGenerationScope] = useState<"all" | "classrooms" | "subject_selected" | "subject_all">("all");
  const [generationClassroomIds, setGenerationClassroomIds] = useState<number[]>([]);
  const [generationSubjectId, setGenerationSubjectId] = useState<number | "">("");

  const [classrooms, setClassrooms] = useState<any[]>([]);
  const [subjects, setSubjects] = useState<any[]>([]);
  const [teachers, setTeachers] = useState<any[]>([]);

  const [viewMode, setViewMode] = useState<"turma" | "professor">("turma");
  const [selectedId, setSelectedId] = useState<number | "">("");

  // Estado para controle da aula selecionada na edição manual
  const [editingLesson, setEditingLesson] = useState<any | null>(null);
  const [selectedTeacherId, setSelectedTeacherId] = useState<number | "">("");
  const [isFixed, setIsFixed] = useState<boolean>(false);
  const [savingLesson, setSavingLesson] = useState(false);

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
    if (classrooms.length === 0) return;

    setGenerationClassroomIds(current => {
      const valid = current.filter(id => classrooms.some(classroom => classroom.id === id));
      if (valid.length > 0) return valid;

      const preferredClassroom =
        classrooms.find(classroom => classroom.id === selectedId)
        || classrooms[0];
      return [preferredClassroom.id];
    });

    const configuredSubjectIds = Array.from(new Set(
      classrooms.flatMap(classroom =>
        (classroom.subject_settings || []).map((setting: any) => Number(setting.subject_id))
      ),
    ));
    setGenerationSubjectId(current =>
      configuredSubjectIds.includes(Number(current))
        ? current
        : (configuredSubjectIds[0] ?? ""),
    );
  }, [classrooms, selectedId]);

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
    const needsSelectedClasses =
      generationScope === "classrooms" || generationScope === "subject_selected";
    const needsSubject =
      generationScope === "subject_selected" || generationScope === "subject_all";

    if (needsSelectedClasses && generationClassroomIds.length === 0) {
      setError("Selecione pelo menos uma turma para regenerar.");
      setGenerationSuccess(false);
      return;
    }

    if (needsSubject && generationSubjectId === "") {
      setError("Selecione a matéria que deseja regenerar.");
      setGenerationSuccess(false);
      return;
    }

    setLoading(true);
    setError("");
    setGenerationSuccess(false);
    setGenerationMessage("");

    try {
      await fetchBaseData(false);

      const request: {
        scope: "all" | "classrooms" | "subject_selected" | "subject_all";
        classroom_ids?: number[];
        subject_id?: number;
      } = { scope: generationScope };

      if (needsSelectedClasses) {
        request.classroom_ids = generationClassroomIds;
      }
      if (needsSubject) {
        request.subject_id = Number(generationSubjectId);
      }

      const response = await api.post("/generate/", request, { timeout: 360000 });
      setSchedule(response.data.schedule);
      setUnstaffedDiagnostics(response.data.unstaffed_diagnostics || []);
      const qualityMessage = response.data.teacher_assignment_fallback
        ? "A distribuição de professores atingiu o limite interno de busca. Os horários das turmas foram preservados, mas as atribuições docentes não foram concluídas; as aulas sem professor não significam necessariamente falta de docentes."
        : response.data.solution_status === "optimal"
          ? "O otimizador comprovou a melhor pontuação possível dentro das regras e pesos configurados."
          : "Foi encontrada uma grade válida, mas o otimizador não comprovou que ela seja a melhor possível. Pode existir outra distribuição com pontuação maior.";
      setGenerationMessage(
        [response.data.message || "Grade gerada.", qualityMessage].join(" "),
      );
      setGenerationSuccess(true);
    } catch (err: any) {
      setGenerationSuccess(false);
      const detail = err.response?.data?.detail;
      const responseText =
        typeof err.response?.data === "string"
          ? err.response.data
          : "";
      const isTimeout =
        err.code === "ECONNABORTED"
        || err.code === "ETIMEDOUT";
      const message = isTimeout
        ? "A geração ultrapassou o limite de espera de 6 minutos. Isso não comprova que a grade seja impossível. Confira se o backend ainda está processando antes de tentar novamente."
        : detail
          || responseText
          || err.message
          || "Erro ao gerar grade";

      setError(`Erro ao gerar grade: ${message}`);
      console.error("Erro ao gerar grade", err);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenEditLesson = (lessonItem: any) => {
    setEditingLesson(lessonItem);
    setSelectedTeacherId(lessonItem.teacher_id ?? "");
    setIsFixed(!!lessonItem.is_fixed);
  };

  const handleSaveLesson = async () => {
    if (!editingLesson || !editingLesson.id) {
      setError("Não é possível alterar uma aula sem ID gravado no banco.");
      setEditingLesson(null);
      return;
    }

    setSavingLesson(true);
    try {
      const payload = {
        teacher_id: selectedTeacherId === "" ? null : Number(selectedTeacherId),
        is_fixed: isFixed,
      };

      const response = await api.put(`/timetable/lessons/${editingLesson.id}`, payload);
      
      setSchedule(prev => prev ? prev.map(item => item.id === editingLesson.id ? response.data : item) : null);
      setUnstaffedDiagnostics([]);
      setEditingLesson(null);
    } catch (err: any) {
      console.error("Erro ao salvar alteração de aula", err);
      alert(err.response?.data?.detail || "Erro ao atualizar aula.");
    } finally {
      setSavingLesson(false);
    }
  };

  const handleExportExcel = () => {
    if (!schedule || schedule.length === 0) {
      return;
    }

    const buildRows = (
      entityId: number,
      mode: "turma" | "professor",
      classroom: any | undefined,
      rowLayout: DisplayRow[],
    ): string[][] => rowLayout.map(row => {
      if (row.kind === "break") {
        return ["@BREAK@" + row.label + " · " + row.name, "", "", "", "", ""];
      }

      const cells = DAYS.map((_, day) => {
        const lessons = schedule.filter(item =>
          item.day === day &&
          item.period === row.period &&
          (mode === "turma" ? item.classroom_id === entityId : item.teacher_id === entityId)
        );

        if (mode === "professor") {
          const item = lessons.find(lessonItem => lessonItem.teacher_id === entityId);
          if (!item) return "";
          const groupLabel = item.student_group && item.student_group !== "Todos"
            ? " · Grupo " + item.student_group
            : "";
          return getClassroomName(item.classroom_id) + "\n" +
            getSubName(item.subject_id) + groupLabel;
        }

        if (classroom?.has_groups) {
          const jointLesson = lessons.find(item => item.student_group === "Todos");
          if (jointLesson) {
            return "TURMA INTEIRA\n" + getSubName(jointLesson.subject_id) +
              "\n" + getProfName(jointLesson.teacher_id);
          }
          const groupA = lessons.find(item => item.student_group === "A");
          const groupB = lessons.find(item => item.student_group === "B");
          if (!groupA && !groupB) return "";
          const formatGroup = (group: "A" | "B", item: any) => item
            ? "GRUPO " + group + "\n" + getSubName(item.subject_id) +
              "\n" + getProfName(item.teacher_id)
            : "";
          return [formatGroup("A", groupA), formatGroup("B", groupB)]
            .filter(Boolean)
            .join("\n\n");
        }

        const item = lessons[0];
        return item ? getSubName(item.subject_id) + "\n" + getProfName(item.teacher_id) : "";
      });

      return [PERIOD_NAMES[row.period] || String(row.period + 1), ...cells];
    });

    const headers = ["Horário", ...DAYS];
    const worksheets = viewMode === "turma"
      ? classrooms
          .filter(classroom => schedule.some(item => item.classroom_id === classroom.id))
          .map(classroom => ({
            name: classroom.name,
            headers,
            rows: buildRows(
              classroom.id,
              "turma",
              classroom,
              JOURNEY_ROWS[classroom.shift || "Manhã"] || JOURNEY_ROWS["Manhã"],
            ),
          }))
      : teachers
          .filter(teacher => schedule.some(item => item.teacher_id === teacher.id))
          .map(teacher => ({
            name: teacher.name,
            headers,
            rows: buildRows(teacher.id, "professor", undefined, PROFESSOR_ROWS),
          }));

    if (worksheets.length === 0) {
      setError("Não há grades para exportar nessa visualização.");
      return;
    }

    const suffix = viewMode === "turma" ? "por-turma" : "por-professor";
    exportTimetableToExcel(worksheets, "anatinus-grades-" + suffix + ".xlsx");
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

  const regenerationSubjectOptions = subjects.filter(subject =>
    classrooms.some(classroom =>
      (classroom.subject_settings || []).some(
        (setting: any) => Number(setting.subject_id) === subject.id,
      ),
    ),
  );

  const regenerationClassroomOptions = generationScope === "subject_selected"
    ? classrooms.filter(classroom =>
        (classroom.subject_settings || []).some(
          (setting: any) => Number(setting.subject_id) === Number(generationSubjectId),
        ),
      )
    : classrooms;

  const allVisibleRegenerationClassesSelected =
    regenerationClassroomOptions.length > 0
    && regenerationClassroomOptions.every(classroom =>
      generationClassroomIds.includes(classroom.id),
    );

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
                            <div 
                              onClick={() => handleOpenEditLesson(jointLesson)}
                              className="relative cursor-pointer flex flex-col items-center justify-center p-2 h-full bg-indigo-50 border border-indigo-100 rounded hover:opacity-80 transition-opacity"
                            >
                              {jointLesson.is_fixed && (
                                <span title="Fixada manualmente" className="absolute top-1 right-1">
                                  <Lock className="w-3 h-3 text-amber-600" />
                                </span>
                              )}
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
                            <div 
                              onClick={() => item && handleOpenEditLesson(item)}
                              className={item
                              ? "relative cursor-pointer min-h-16 flex flex-col items-center justify-center p-1.5 bg-indigo-50 border border-indigo-100 rounded hover:opacity-80 transition-opacity"
                              : "min-h-16"} aria-hidden={!item}>
                              {item && (
                                <>
                                  {item.is_fixed && (
                                    <span title="Fixada manualmente" className="absolute top-1 right-1">
                                      <Lock className="w-3 h-3 text-amber-600" />
                                    </span>
                                  )}
                                  <span className="text-[10px] font-bold uppercase text-indigo-400">
                                    Grupo {group}
                                  </span>
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
                            <div 
                              onClick={() => handleOpenEditLesson(currentLesson)}
                              className="relative cursor-pointer flex flex-col items-center justify-center p-2 h-full bg-indigo-50 border border-indigo-100 rounded hover:opacity-80 transition-opacity"
                            >
                              {currentLesson.is_fixed && (
                                <span title="Fixada manualmente" className="absolute top-1 right-1">
                                  <Lock className="w-3 h-3 text-amber-600" />
                                </span>
                              )}
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
                          <div 
                            onClick={() => handleOpenEditLesson(currentLesson)}
                            className="relative cursor-pointer flex flex-col items-center justify-center p-2 h-full bg-emerald-50 border border-emerald-100 rounded hover:opacity-80 transition-opacity"
                          >
                            {currentLesson.is_fixed && (
                              <span title="Fixada manualmente" className="absolute top-1 right-1">
                                <Lock className="w-3 h-3 text-amber-600" />
                              </span>
                            )}
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
                            title={viewMode === "turma" ? "Exportar uma aba por turma em Excel" : "Exportar uma aba por professor em Excel"}
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
                    </div>
                  </div>

                  <div className="app-generation-controls no-print">
                    <label htmlFor="generation-scope">Gerar novamente:</label>
                    <select
                      id="generation-scope"
                      aria-label="Escopo da geração"
                      className="app-toolbar-select app-generation-scope-select"
                      value={generationScope}
                      onChange={event => {
                        const nextScope = event.target.value as
                          | "all"
                          | "classrooms"
                          | "subject_selected"
                          | "subject_all";
                        setGenerationScope(nextScope);
                        setError("");
                        setGenerationSuccess(false);

                        if (nextScope === "subject_selected" && generationSubjectId !== "") {
                          const matchingIds = classrooms
                            .filter(classroom =>
                              (classroom.subject_settings || []).some(
                                (setting: any) => Number(setting.subject_id) === Number(generationSubjectId),
                              ),
                            )
                            .map(classroom => classroom.id);
                          setGenerationClassroomIds(current => {
                            const retained = current.filter(id => matchingIds.includes(id));
                            return retained.length > 0 ? retained : matchingIds.slice(0, 1);
                          });
                        }
                      }}
                    >
                      <option value="all">Escola inteira</option>
                      <option value="classrooms" disabled={!schedule || schedule.length === 0}>Turmas selecionadas</option>
                      <option value="subject_selected" disabled={!schedule || schedule.length === 0}>Matéria nas turmas selecionadas</option>
                      <option value="subject_all" disabled={!schedule || schedule.length === 0}>Matéria na escola inteira</option>
                    </select>

                    {(generationScope === "subject_selected" || generationScope === "subject_all") && (
                      <select
                        aria-label="Matéria para regeneração"
                        className="app-toolbar-select app-generation-target-select"
                        value={generationSubjectId}
                        onChange={event => {
                          const nextSubjectId = event.target.value === "" ? "" : Number(event.target.value);
                          setGenerationSubjectId(nextSubjectId);
                          setError("");
                          setGenerationSuccess(false);

                          if (generationScope === "subject_selected" && nextSubjectId !== "") {
                            const matchingIds = classrooms
                              .filter(classroom =>
                                (classroom.subject_settings || []).some(
                                  (setting: any) => Number(setting.subject_id) === Number(nextSubjectId),
                                ),
                              )
                              .map(classroom => classroom.id);
                            setGenerationClassroomIds(current => {
                              const retained = current.filter(id => matchingIds.includes(id));
                              return retained.length > 0 ? retained : matchingIds.slice(0, 1);
                            });
                          }
                        }}
                      >
                        <option value="">Selecionar matéria...</option>
                        {regenerationSubjectOptions.map(subject => (
                          <option key={subject.id} value={subject.id}>
                            {subject.name}
                          </option>
                        ))}
                      </select>
                    )}

                    {(generationScope === "classrooms" || generationScope === "subject_selected") && (
                      <div className="app-generation-classroom-picker">
                        <div className="app-generation-classroom-picker-header">
                          <span>
                            Turmas incluídas ({generationClassroomIds.filter(id =>
                              regenerationClassroomOptions.some(classroom => classroom.id === id),
                            ).length})
                          </span>
                          <button
                            type="button"
                            className="app-generation-select-all"
                            onClick={() => {
                              const visibleIds = regenerationClassroomOptions.map(classroom => classroom.id);
                              setGenerationClassroomIds(current =>
                                allVisibleRegenerationClassesSelected
                                  ? current.filter(id => !visibleIds.includes(id))
                                  : Array.from(new Set([...current, ...visibleIds])),
                              );
                              setError("");
                              setGenerationSuccess(false);
                            }}
                          >
                            {allVisibleRegenerationClassesSelected ? "Desmarcar todas" : "Selecionar todas"}
                          </button>
                        </div>
                        <div className="app-generation-classroom-list">
                          {regenerationClassroomOptions.map(classroom => (
                            <label key={classroom.id} className="app-generation-classroom-option">
                              <input
                                type="checkbox"
                                checked={generationClassroomIds.includes(classroom.id)}
                                onChange={event => {
                                  setGenerationClassroomIds(current =>
                                    event.target.checked
                                      ? Array.from(new Set([...current, classroom.id]))
                                      : current.filter(id => id !== classroom.id),
                                  );
                                  setError("");
                                  setGenerationSuccess(false);
                                }}
                                style={{ accentColor: "var(--an-accent)" }}
                              />
                              <span>{classroom.name}</span>
                              <small>{classroom.shift}</small>
                            </label>
                          ))}
                          {regenerationClassroomOptions.length === 0 && (
                            <p className="app-generation-empty">
                              Essa matéria não está configurada em nenhuma turma.
                            </p>
                          )}
                        </div>
                      </div>
                    )}

                    {generationScope === "subject_all" && (
                      <p className="app-generation-scope-note">
                        A matéria será reorganizada em todas as turmas onde está cadastrada. Os demais horários serão preservados.
                      </p>
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
                      {generationMessage || "Grade gerada."}
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
                            const diagnostic = unstaffedDiagnostics.find(entry =>
                              entry.classroom_id === item.classroomId
                              && entry.subject_id === item.subjectId
                              && entry.student_group === item.studentGroup,
                            );
                            return (
                              <li key={`${item.classroomId}-${item.subjectId}-${item.studentGroup}`}>
                                <span>{getClassroomName(item.classroomId)} · {getSubName(item.subjectId)}{groupLabel}</span>
                                <strong>{item.lessons} {item.lessons === 1 ? "aula" : "aulas"}</strong>
                                {diagnostic && (
                                  <div className="app-pending-diagnostic">
                                    <p>{diagnostic.message}</p>
                                    {diagnostic.teachers?.length > 0 && (
                                      <small>
                                        Janelas marcadas como disponíveis no cadastro: {diagnostic.teachers
                                          .map((teacher: any) => `${teacher.name}: ${teacher.available_periods} períodos`)
                                          .join(" · ")}
                                      </small>
                                    )}
                                  </div>
                                )}
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

        {/* Modal para Alterar e Fixar Professor/Aula */}
        {editingLesson && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
            <div className="app-panel w-full max-w-md bg-white p-6 rounded-xl shadow-lg border relative">
              <button
                type="button"
                onClick={() => setEditingLesson(null)}
                className="absolute top-4 right-4 text-gray-500 hover:text-gray-700"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="text-lg font-bold mb-4">Editar Aula</h3>

              <div className="space-y-4">
                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Turma</span>
                  <p className="font-semibold text-gray-900">{getClassroomName(editingLesson.classroom_id)}</p>
                </div>

                <div>
                  <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">Matéria</span>
                  <p className="font-semibold text-gray-900">{getSubName(editingLesson.subject_id)}</p>
                </div>

                <div>
                  <label htmlFor="modal-teacher" className="block text-xs font-semibold text-gray-500 uppercase tracking-wide mb-1">
                    Professor Atribuído
                  </label>
                  <select
                    id="modal-teacher"
                    value={selectedTeacherId}
                    onChange={e => setSelectedTeacherId(e.target.value === "" ? "" : Number(e.target.value))}
                    className="w-full p-2 border rounded-md"
                  >
                    <option value="">Nenhum (Sem Professor)</option>
                    {teachers.map(teacher => (
                      <option key={teacher.id} value={teacher.id}>
                        {teacher.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="flex items-center space-x-2 pt-2">
                  <input
                    type="checkbox"
                    id="is_fixed_checkbox"
                    checked={isFixed}
                    onChange={e => setIsFixed(e.target.checked)}
                    className="w-4 h-4 rounded"
                    style={{ accentColor: "var(--an-accent)" }}
                  />
                  <label htmlFor="is_fixed_checkbox" className="text-sm font-medium cursor-pointer select-none">
                    Fixar aula manual (impede alteração automática)
                  </label>
                </div>

                <div className="flex justify-end space-x-2 pt-4 border-t">
                  <button
                    type="button"
                    onClick={() => setEditingLesson(null)}
                    className="app-action-secondary"
                  >
                    Cancelar
                  </button>
                  <button
                    type="button"
                    onClick={handleSaveLesson}
                    disabled={savingLesson}
                    className="app-action-primary"
                  >
                    {savingLesson ? "A guardar..." : "Guardar Alterações"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;