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
  "19:00 - 19:45",
  "19:45 - 20:30",
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

const getClassroomJourneyRows = (classroom?: any): DisplayRow[] => {
  const shift = classroom?.shift || "Manhã";
  const defaults = JOURNEY_ROWS[shift] || JOURNEY_ROWS["Manhã"];
  if (shift !== "Integral" || !Array.isArray(classroom?.allowed_periods)) {
    return defaults;
  }

  const allowed = new Set<number>(classroom.allowed_periods.map(Number));
  const rows: DisplayRow[] = [];
  const addLessons = (periods: number[]) => {
    periods.forEach(period => {
      if (allowed.has(period)) rows.push(lesson(period));
    });
  };

  addLessons([0, 1, 2]);
  if ([3, 4, 5].some(period => allowed.has(period))) {
    rows.push(pause("09:40 - 10:00", "Intervalo"));
  }
  addLessons([3, 4, 5]);

  const hasAfternoon = [6, 7, 8, 9, 10].some(period => allowed.has(period));
  if (hasAfternoon) {
    rows.push(
      pause(
        allowed.has(5) ? "12:30 - 13:00" : "11:40 - 13:00",
        "Almoço",
      ),
    );
    addLessons([6, 7]);
    if (allowed.has(8) || allowed.has(9) || allowed.has(10)) {
      rows.push(pause("14:40 - 14:50", "Intervalo"));
    }
    addLessons([8, 9, 10]);
  }

  return rows.length > 0 ? rows : defaults;
};

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
  const [classroomSearch, setClassroomSearch] = useState("");

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

      let savedTimetable: any[] | null = null;
      if (loadSavedSchedule) {
        const timeRes = await api.get("/timetable/");
        savedTimetable = timeRes.data;
        setSchedule(timeRes.data.length > 0 ? timeRes.data : null);
      }

      setClassrooms(cRes.data);
      setSubjects(sRes.data);
      setTeachers(tRes.data);

      setSelectedId(current => {
        if (
          current !== "" &&
          (!savedTimetable || savedTimetable.some(item => item.classroom_id === current))
        ) {
          return current;
        }

        const classroomWithSchedule = savedTimetable?.find(item =>
          cRes.data.some((classroom: { id: number }) => classroom.id === item.classroom_id),
        )?.classroom_id;
        return classroomWithSchedule ?? cRes.data[0]?.id ?? "";
      });
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
        classrooms.find(classroom => classroom.id === selectedId) || classrooms[0];
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

    window.addEventListener("anatinus:academic-data-changed", handleAcademicDataChanged);
    return () => {
      window.removeEventListener("anatinus:academic-data-changed", handleAcademicDataChanged);
    };
  }, []);

  useEffect(() => {
    document.documentElement.classList.toggle("dark-theme", theme === "dark");

    const favicon = document.querySelector<HTMLLinkElement>("#app-favicon");
    if (favicon) {
      favicon.href =
        theme === "dark"
          ? "/anatinus%20final%201%20branco.png"
          : "/Anatinus%20final%201.png";
    }

    localStorage.setItem("anatinus-theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(current => (current === "dark" ? "light" : "dark"));
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
        ? "A distribuição de professores atingiu o limite de busca. Horários preservados."
        : response.data.solution_status === "optimal"
          ? "Otimização comprovada com a melhor pontuação possível."
          : "Grade válida gerada com sucesso.";
      setGenerationMessage(
        [response.data.message || "Grade gerada.", qualityMessage].join(" "),
      );
      setGenerationSuccess(true);
    } catch (err: any) {
      setGenerationSuccess(false);
      const detail = err.response?.data?.detail;
      const responseText = typeof err.response?.data === "string" ? err.response.data : "";
      const isTimeout = err.code === "ECONNABORTED" || err.code === "ETIMEDOUT";
      const message = isTimeout
        ? "A geração ultrapassou o limite de espera de 6 minutos."
        : detail || responseText || err.message || "Erro ao gerar grade";

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
    if (!schedule || schedule.length === 0) return;

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
              getClassroomJourneyRows(classroom),
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
    return teachers.find(teacher => teacher.id === id)?.name || "Professor não encontrado";
  };

  const getClassroomName = (id: number) =>
    classrooms.find(classroom => classroom.id === id)?.name || "N/A";

  const filteredClassrooms = classrooms.filter(classroom => {
    const query = classroomSearch.trim().toLocaleLowerCase("pt-BR");
    if (!query) return true;
    return `${classroom.name} ${classroom.shift}`.toLocaleLowerCase("pt-BR").includes(query);
  });

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
    regenerationClassroomOptions.length > 0 &&
    regenerationClassroomOptions.every(classroom =>
      generationClassroomIds.includes(classroom.id),
    );

  const unstaffedLessons = schedule?.filter(item => item.teacher_id == null).length || 0;

  const unstaffedSummary = Object.values(
    (schedule || [])
      .filter(item => item.teacher_id == null)
      .reduce((groups: Record<string, any>, item: any) => {
        const key = [item.classroom_id, item.subject_id, item.student_group || "Todos"].join(":");
        if (!groups[key]) {
          groups[key] = {
            classroomId: item.classroom_id,
            subjectId: item.subject_id,
            studentGroup: item.student_group || "Todos",
            lessons: 0,
          };
        }
        groups[key].lessons += 1;
        return groups;
      }, {}),
  ) as Array<{
    classroomId: number;
    subjectId: number;
    studentGroup: string;
    lessons: number;
  }>;

  const renderScheduleGrid = () => {
    if (!schedule) {
      return (
        <div style={{ padding: "48px 24px", textAlign: "center", color: "var(--an-muted)" }}>
          <Calendar style={{ width: 36, height: 36, margin: "0 auto 12px", opacity: 0.5 }} />
          <p style={{ fontSize: 15, fontWeight: 600, color: "var(--an-text)", margin: "0 0 4px" }}>
            Nenhuma grade horária gerada
          </p>
          <p style={{ fontSize: 13, margin: 0 }}>
            Utilize o botão "Gerar grade" acima para executar a otimização de horários.
          </p>
        </div>
      );
    }

    if (!selectedId) {
      return (
        <div style={{ padding: "36px 24px", textAlign: "center", color: "var(--an-muted)" }}>
          <Filter style={{ width: 28, height: 28, margin: "0 auto 8px", opacity: 0.5 }} />
          <p style={{ fontSize: 14, fontWeight: 500, margin: 0 }}>
            Selecione uma turma ou professor para visualizar a grade semanal.
          </p>
        </div>
      );
    }

    let rows: DisplayRow[];
    if (viewMode === "turma") {
      const classroom = classrooms.find(item => item.id === selectedId);
      rows = getClassroomJourneyRows(classroom);
    } else {
      rows = PROFESSOR_ROWS;
    }

    return (
      <table className="app-timetable">
        <thead>
          <tr>
            <th className="app-timetable-col-time">Horário</th>
            {DAYS.map(day => (
              <th key={day}>{day}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => {
            if (row.kind === "break") {
              return (
                <tr key={`break-${row.label}-${rowIndex}`} className="app-timetable-break-row">
                  <td className="app-timetable-col-time">{row.label}</td>
                  <td colSpan={5} className="app-timetable-break-cell">
                    {row.name}
                  </td>
                </tr>
              );
            }

            const period = row.period;

            return (
              <tr key={period}>
                <td className="app-timetable-col-time">
                  {PERIOD_NAMES[period]}
                </td>
                {DAYS.map((_, day) => {
                  let cellContent = null;

                  if (viewMode === "turma") {
                    const classroom = classrooms.find(item => item.id === selectedId);
                    const lessons = schedule.filter(
                      item =>
                        item.day === day &&
                        item.period === period &&
                        item.classroom_id === selectedId,
                    );

                    if (classroom?.has_groups) {
                      const jointLesson = lessons.find(item => item.student_group === "Todos");
                      const groupA = lessons.find(item => item.student_group === "A");
                      const groupB = lessons.find(item => item.student_group === "B");

                      if (jointLesson) {
                        cellContent = (
                          <div
                            onClick={() => handleOpenEditLesson(jointLesson)}
                            className="app-lesson-slot"
                            title="Clique para editar ou fixar aula"
                          >
                            {jointLesson.is_fixed && (
                              <span title="Aula fixada manualmente" className="app-lesson-fixed-icon">
                                <Lock style={{ width: 12, height: 12 }} />
                              </span>
                            )}
                            <span className="app-lesson-tag">Turma inteira</span>
                            <span className="app-lesson-subject">
                              {getSubName(jointLesson.subject_id)}
                            </span>
                            <span className={`app-lesson-teacher ${jointLesson.teacher_id == null ? "unstaffed" : ""}`}>
                              {getProfName(jointLesson.teacher_id)}
                            </span>
                          </div>
                        );
                      } else {
                        const renderGroup = (group: "A" | "B", item: any) => (
                          <div
                            onClick={() => item && handleOpenEditLesson(item)}
                            className={item ? "app-lesson-slot" : "app-lesson-empty-cell"}
                            style={{ flex: 1, minHeight: 48 }}
                          >
                            {item && (
                              <>
                                {item.is_fixed && (
                                  <span title="Fixada" className="app-lesson-fixed-icon">
                                    <Lock style={{ width: 11, height: 11 }} />
                                  </span>
                                )}
                                <span className="app-lesson-tag">Grupo {group}</span>
                                <span className="app-lesson-subject" style={{ fontSize: 11 }}>
                                  {getSubName(item.subject_id)}
                                </span>
                                <span className={`app-lesson-teacher ${item.teacher_id == null ? "unstaffed" : ""}`} style={{ fontSize: 10 }}>
                                  {getProfName(item.teacher_id)}
                                </span>
                              </>
                            )}
                          </div>
                        );

                        cellContent = (
                          <div style={{ display: "flex", gap: 4, height: "100%" }}>
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
                            className="app-lesson-slot"
                            title="Clique para editar ou fixar aula"
                          >
                            {currentLesson.is_fixed && (
                              <span title="Aula fixada manualmente" className="app-lesson-fixed-icon">
                                <Lock style={{ width: 12, height: 12 }} />
                              </span>
                            )}
                            <span className="app-lesson-subject">
                              {getSubName(currentLesson.subject_id)}
                            </span>
                            <span className={`app-lesson-teacher ${currentLesson.teacher_id == null ? "unstaffed" : ""}`}>
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
                        item.teacher_id === selectedId,
                    );

                    if (currentLesson) {
                      const groupLabel =
                        currentLesson.student_group && currentLesson.student_group !== "Todos"
                          ? ` · G${currentLesson.student_group}`
                          : "";

                      cellContent = (
                        <div
                          onClick={() => handleOpenEditLesson(currentLesson)}
                          className="app-lesson-slot"
                          title="Clique para editar ou fixar aula"
                        >
                          {currentLesson.is_fixed && (
                            <span title="Aula fixada manualmente" className="app-lesson-fixed-icon">
                              <Lock style={{ width: 12, height: 12 }} />
                            </span>
                          )}
                          <span className="app-lesson-subject">
                            {getSubName(currentLesson.subject_id)}
                          </span>
                          <span className="app-lesson-teacher">
                            {getClassroomName(currentLesson.classroom_id)}{groupLabel}
                          </span>
                        </div>
                      );
                    }
                  }

                  return (
                    <td key={day} style={{ height: 68 }}>
                      {cellContent || <div className="app-lesson-empty-cell" />}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  };

  return (
    <Router>
      <div className="app-shell">
        {/* CABEÇALHO SUPERIOR COMPACTO (Substitui a antiga sidebar SaaS) */}
        <header className="app-header">
          <div className="app-header-brand">
            <img
              src="/Anatinus%20final%201.png"
              alt="Anatinus"
              className="app-logo-light"
            />
            <img
              src="/anatinus%20final%201%20branco.png"
              alt="Anatinus"
              className="app-logo-dark"
            />
            <span className="app-header-brand-title">Anatinus</span>
          </div>

          <nav className="app-header-nav">
            <NavLink
              to="/"
              className={({ isActive }) => `app-nav-item ${isActive ? "active" : ""}`}
            >
              <Calendar />
              <span>Grade Horária</span>
            </NavLink>

            <NavLink
              to="/professores"
              className={({ isActive }) => `app-nav-item ${isActive ? "active" : ""}`}
            >
              <Users />
              <span>Professores</span>
            </NavLink>

            <NavLink
              to="/turmas"
              className={({ isActive }) => `app-nav-item ${isActive ? "active" : ""}`}
            >
              <BookOpen />
              <span>Turmas e Matérias</span>
            </NavLink>

            <NavLink
              to="/config"
              className={({ isActive }) => `app-nav-item ${isActive ? "active" : ""}`}
            >
              <Settings />
              <span>Regras e Leis</span>
            </NavLink>
          </nav>

          <div className="app-header-actions">
            <button
              type="button"
              onClick={toggleTheme}
              className="app-theme-btn"
              title={theme === "dark" ? "Mudar para tema claro" : "Mudar para tema escuro"}
              aria-label="Alternar tema"
            >
              {theme === "dark" ? (
                <Sun style={{ width: 16, height: 16, color: "#D4A454" }} />
              ) : (
                <Moon style={{ width: 16, height: 16 }} />
              )}
            </button>
          </div>
        </header>

        {/* ÁREA DE TRABALHO PRINCIPAL */}
        <main className="app-main">
          <Routes>
            <Route
              path="/"
              element={
                <div className="app-workspace">
                  {/* Título de tela explícito e profissional */}
                  <div className="app-page-title-row no-print">
                    <div>
                      <h1 className="app-page-title">
                        Grade Horária
                        <span className="app-page-subtitle">
                          {viewMode === "turma"
                            ? (classrooms.find(c => c.id === selectedId)?.name || "Selecione uma turma")
                            : (teachers.find(t => t.id === selectedId)?.name || "Selecione um professor")}
                        </span>
                      </h1>
                    </div>

                    <div className="app-control-group">
                      {schedule && schedule.length > 0 && (
                        <>
                          <button
                            type="button"
                            onClick={handleExportExcel}
                            className="app-btn app-btn-secondary"
                            title="Exportar pasta de trabalho Excel"
                          >
                            <Download style={{ width: 14, height: 14 }} />
                            <span>Exportar Excel</span>
                          </button>
                          <button
                            type="button"
                            onClick={handlePrint}
                            className="app-btn app-btn-secondary"
                            title="Imprimir visualização atual"
                          >
                            <Printer style={{ width: 14, height: 14 }} />
                            <span>Imprimir</span>
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* BARRA DE CONTROLE: VISUALIZAÇÃO E FILTROS */}
                  <div className="app-control-bar no-print">
                    <div className="app-control-group">
                      <select
                        aria-label="Modo de visualização"
                        className="app-select"
                        value={viewMode}
                        onChange={e => {
                          setViewMode(e.target.value as "turma" | "professor");
                          setSelectedId("");
                        }}
                      >
                        <option value="turma">Visualizar por Turma</option>
                        <option value="professor">Visualizar por Professor</option>
                      </select>

                      {viewMode === "turma" && (
                        <input
                          type="search"
                          aria-label="Filtrar turmas"
                          placeholder="Filtrar turma ou turno..."
                          className="app-input"
                          style={{ width: 180 }}
                          value={classroomSearch}
                          onChange={e => {
                            const query = e.target.value;
                            setClassroomSearch(query);
                            const normalized = query.trim().toLocaleLowerCase("pt-BR");
                            const matches = classrooms.filter(c =>
                              `${c.name} ${c.shift}`.toLocaleLowerCase("pt-BR").includes(normalized),
                            );
                            if (!matches.some(c => c.id === selectedId)) {
                              setSelectedId(matches[0]?.id ?? "");
                            }
                          }}
                        />
                      )}

                      <select
                        aria-label={viewMode === "turma" ? "Selecionar turma" : "Selecionar professor"}
                        className="app-select"
                        style={{ minWidth: 220 }}
                        value={selectedId}
                        onChange={e => setSelectedId(e.target.value === "" ? "" : Number(e.target.value))}
                      >
                        <option value="">Selecionar...</option>
                        {viewMode === "turma" &&
                          filteredClassrooms.map(c => (
                            <option key={c.id} value={c.id}>
                              {c.name} ({c.shift}{c.has_groups ? " · Grupos A/B" : ""})
                            </option>
                          ))}
                        {viewMode === "professor" &&
                          teachers.map(t => (
                            <option key={t.id} value={t.id}>
                              {t.name}
                            </option>
                          ))}
                      </select>
                    </div>

                    <div className="app-control-group">
                      <button
                        type="button"
                        onClick={handleGenerate}
                        disabled={loading}
                        className="app-btn app-btn-primary"
                      >
                        <Calendar style={{ width: 14, height: 14 }} />
                        <span>{loading ? "Otimizando horários..." : "Gerar grade"}</span>
                      </button>
                    </div>
                  </div>

                  {/* PAINEL DE ESCOPO / REGENERAÇÃO */}
                  <div className="app-scope-panel no-print">
                    <div className="app-scope-row">
                      <span className="app-scope-label">Escopo da geração:</span>
                      <select
                        aria-label="Escopo da geração"
                        className="app-select"
                        value={generationScope}
                        onChange={e => {
                          const nextScope = e.target.value as any;
                          setGenerationScope(nextScope);
                          setError("");
                          setGenerationSuccess(false);

                          if (nextScope === "subject_selected" && generationSubjectId !== "") {
                            const matchingIds = classrooms
                              .filter(c => (c.subject_settings || []).some((s: any) => Number(s.subject_id) === Number(generationSubjectId)))
                              .map(c => c.id);
                            setGenerationClassroomIds(curr => {
                              const ret = curr.filter(id => matchingIds.includes(id));
                              return ret.length > 0 ? ret : matchingIds.slice(0, 1);
                            });
                          }
                        }}
                      >
                        <option value="all">Escola inteira (completa)</option>
                        <option value="classrooms" disabled={!schedule || schedule.length === 0}>
                          Turmas selecionadas
                        </option>
                        <option value="subject_selected" disabled={!schedule || schedule.length === 0}>
                          Matéria nas turmas selecionadas
                        </option>
                        <option value="subject_all" disabled={!schedule || schedule.length === 0}>
                          Matéria na escola inteira
                        </option>
                      </select>

                      {(generationScope === "subject_selected" || generationScope === "subject_all") && (
                        <select
                          aria-label="Matéria para regeneração"
                          className="app-select"
                          value={generationSubjectId}
                          onChange={e => {
                            const nextSubjectId = e.target.value === "" ? "" : Number(e.target.value);
                            setGenerationSubjectId(nextSubjectId);
                            setError("");
                            setGenerationSuccess(false);

                            if (generationScope === "subject_selected" && nextSubjectId !== "") {
                              const matchingIds = classrooms
                                .filter(c => (c.subject_settings || []).some((s: any) => Number(s.subject_id) === Number(nextSubjectId)))
                                .map(c => c.id);
                              setGenerationClassroomIds(curr => {
                                const ret = curr.filter(id => matchingIds.includes(id));
                                return ret.length > 0 ? ret : matchingIds.slice(0, 1);
                              });
                            }
                          }}
                        >
                          <option value="">Selecionar matéria...</option>
                          {regenerationSubjectOptions.map(s => (
                            <option key={s.id} value={s.id}>
                              {s.name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>

                    {(generationScope === "classrooms" || generationScope === "subject_selected") && (
                      <div className="app-classroom-picker">
                        <div className="app-classroom-picker-header">
                          <span>
                            Turmas incluídas ({generationClassroomIds.filter(id => regenerationClassroomOptions.some(c => c.id === id)).length})
                          </span>
                          <button
                            type="button"
                            className="app-btn app-btn-secondary"
                            style={{ height: 26, fontSize: 11, padding: "0 8px" }}
                            onClick={() => {
                              const visibleIds = regenerationClassroomOptions.map(c => c.id);
                              setGenerationClassroomIds(curr =>
                                allVisibleRegenerationClassesSelected
                                  ? curr.filter(id => !visibleIds.includes(id))
                                  : Array.from(new Set([...curr, ...visibleIds]))
                              );
                              setError("");
                              setGenerationSuccess(false);
                            }}
                          >
                            {allVisibleRegenerationClassesSelected ? "Desmarcar todas" : "Selecionar todas"}
                          </button>
                        </div>
                        <div className="app-classroom-picker-grid">
                          {regenerationClassroomOptions.map(c => (
                            <label key={c.id} className="app-classroom-checkbox-item">
                              <input
                                type="checkbox"
                                checked={generationClassroomIds.includes(c.id)}
                                onChange={e => {
                                  setGenerationClassroomIds(curr =>
                                    e.target.checked
                                      ? Array.from(new Set([...curr, c.id]))
                                      : curr.filter(id => id !== c.id)
                                  );
                                  setError("");
                                  setGenerationSuccess(false);
                                }}
                                style={{ accentColor: "var(--an-primary)" }}
                              />
                              <span style={{ fontWeight: 500 }}>{c.name}</span>
                              <span style={{ fontSize: 10, color: "var(--an-muted)", marginLeft: "auto" }}>
                                {c.shift}
                              </span>
                            </label>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* MENSAGENS E ALERTAS */}
                  {error && (
                    <div className="app-alert app-alert-error no-print" role="alert">
                      <span>{error}</span>
                    </div>
                  )}

                  {loading && schedule && (
                    <div className="app-alert app-alert-info no-print" role="status">
                      <span>Otimizando nova grade horária. A visualização anterior permanece ativa enquanto o cálculo é executado.</span>
                    </div>
                  )}

                  {!error && generationSuccess && (
                    <div className="app-alert app-alert-success no-print" role="status">
                      <span>{generationMessage || "Grade gerada com sucesso."}</span>
                    </div>
                  )}

                  {!error && unstaffedLessons > 0 && (
                    <details className="app-unstaffed-accordion no-print">
                      <summary className="app-unstaffed-summary">
                        <span>
                          {unstaffedLessons} {unstaffedLessons === 1 ? "aula sem professor atribuído" : "aulas sem professor atribuído"}
                        </span>
                        <span style={{ fontSize: 11, fontWeight: 500 }}>Ver detalhes</span>
                      </summary>
                      <div className="app-unstaffed-list">
                        <ul style={{ margin: 0, padding: "0 0 0 16px", display: "flex", flexDirection: "column", gap: 6 }}>
                          {unstaffedSummary.map(item => {
                            const groupLabel = item.studentGroup !== "Todos" ? ` · Grupo ${item.studentGroup}` : "";
                            const diagnostic = unstaffedDiagnostics.find(
                              entry =>
                                entry.classroom_id === item.classroomId &&
                                entry.subject_id === item.subjectId &&
                                entry.student_group === item.studentGroup,
                            );
                            return (
                              <li key={`${item.classroomId}-${item.subjectId}-${item.studentGroup}`}>
                                <strong>{getClassroomName(item.classroomId)}</strong> — {getSubName(item.subjectId)}{groupLabel} ({item.lessons} {item.lessons === 1 ? "aula" : "aulas"})
                                {diagnostic && (
                                  <p style={{ margin: "2px 0 0", fontSize: 11, color: "var(--an-muted)" }}>
                                    {diagnostic.message}
                                  </p>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </div>
                    </details>
                  )}

                  {/* GRADE HORÁRIA TABULAR */}
                  <div className="app-timetable-container">
                    <div className="app-timetable-header">
                      <h2 className="app-timetable-title">
                        {viewMode === "turma"
                          ? getClassroomName(Number(selectedId))
                          : getProfName(Number(selectedId))}
                      </h2>
                      <span className="font-mono" style={{ fontSize: 12, color: "var(--an-muted)" }}>
                        Horário Semanal
                      </span>
                    </div>
                    {renderScheduleGrid()}
                  </div>
                </div>
              }
            />

            <Route path="/professores" element={<Professores />} />
            <Route path="/turmas" element={<Turmas />} />
            <Route path="/config" element={<Config />} />
          </Routes>
        </main>

        {/* MODAL PARA ALTERAR E FIXAR AULA */}
        {editingLesson && (
          <div className="app-modal-backdrop">
            <div className="app-modal">
              <div className="app-modal-header">
                <h3 className="app-modal-title">Editar Aula</h3>
                <button
                  type="button"
                  onClick={() => setEditingLesson(null)}
                  style={{ background: "none", border: "none", cursor: "pointer", color: "var(--an-muted)" }}
                >
                  <X style={{ width: 18, height: 18 }} />
                </button>
              </div>

              <div className="app-modal-body">
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--an-muted)", display: "block", marginBottom: 2 }}>
                    Turma
                  </label>
                  <p style={{ margin: 0, fontWeight: 600 }}>{getClassroomName(editingLesson.classroom_id)}</p>
                </div>

                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--an-muted)", display: "block", marginBottom: 2 }}>
                    Disciplina
                  </label>
                  <p style={{ margin: 0, fontWeight: 600 }}>{getSubName(editingLesson.subject_id)}</p>
                </div>

                <div>
                  <label htmlFor="modal-teacher" style={{ fontSize: 11, fontWeight: 600, color: "var(--an-muted)", display: "block", marginBottom: 4 }}>
                    Professor Atribuído
                  </label>
                  <select
                    id="modal-teacher"
                    value={selectedTeacherId}
                    onChange={e => setSelectedTeacherId(e.target.value === "" ? "" : Number(e.target.value))}
                    className="app-select"
                    style={{ width: "100%" }}
                  >
                    <option value="">Sem professor atribuído</option>
                    {teachers.map(t => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                  </select>
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 6 }}>
                  <input
                    type="checkbox"
                    id="is_fixed_checkbox"
                    checked={isFixed}
                    onChange={e => setIsFixed(e.target.checked)}
                    style={{ accentColor: "var(--an-primary)", width: 16, height: 16 }}
                  />
                  <label htmlFor="is_fixed_checkbox" style={{ fontSize: 13, cursor: "pointer" }}>
                    Fixar aula manual (impede alterações automáticas do otimizador)
                  </label>
                </div>
              </div>

              <div className="app-modal-footer">
                <button
                  type="button"
                  onClick={() => setEditingLesson(null)}
                  className="app-btn app-btn-secondary"
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  onClick={handleSaveLesson}
                  disabled={savingLesson}
                  className="app-btn app-btn-primary"
                >
                  {savingLesson ? "Salvando..." : "Salvar Alterações"}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </Router>
  );
}

export default App;
