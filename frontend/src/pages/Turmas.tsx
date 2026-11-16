import React, { useEffect, useState } from "react";
import { api } from "../api";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
  Copy,
  Edit,
  Layers,
  Plus,
  Save,
  School,
  Trash2,
  X,
} from "lucide-react";

interface Course {
  id: number;
  name: string;
}

interface ClassroomSubjectSetting {
  subject_id: number;
  workload: number;
  workload_a?: number | null;
  workload_b?: number | null;
  joint_workload?: number | null;
  split: boolean;
  prefer_triple_block?: boolean | null;
}

interface Classroom {
  id: number;
  name: string;
  shift: string;
  allowed_periods?: number[] | null;
  allowed_periods_by_day?: Record<string, number[]> | null;
  course_id: number;
  has_groups: boolean;
  subject_settings: ClassroomSubjectSetting[];
  preferred_subject_sequences?: number[][];
  split_subject_ids?: number[];
}

interface Subject {
  id: number;
  name: string;
  workload: number;
  complexity: string;
  category: "Ensino Médio" | "Técnica";
  course_ids: number[];
}

const STANDARD_INTEGRAL_PERIODS = [0, 1, 2, 3, 4, 6, 7, 8, 9, 10];

const periodsForShift = (shift: string): number[] => {
  if (shift === "Noite") return [11, 12, 13, 14, 15];
  if (shift === "Tarde") return [6, 7, 8, 9, 10];
  if (shift === "Integral") return [...STANDARD_INTEGRAL_PERIODS];
  return [0, 1, 2, 3, 4, 5];
};

export default function Turmas() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [expandedClassrooms, setExpandedClassrooms] = useState<Set<number>>(new Set());
  const [copySourceByClassroom, setCopySourceByClassroom] = useState<Record<number, string>>({});
  const [sequenceDraftByClassroom, setSequenceDraftByClassroom] = useState<Record<number, { first: string; second: string }>>({});

  const [newCourseName, setNewCourseName] = useState("");
  const [editingCourseId, setEditingCourseId] = useState<number | null>(null);
  const [editingCourseName, setEditingCourseName] = useState("");

  const [editingClassroomId, setEditingClassroomId] = useState<number | null>(null);
  const [classroomDraft, setClassroomDraft] = useState({
    name: "",
    shift: "Manhã",
    course_id: 0,
    allowed_periods: periodsForShift("Manhã"),
  });

  const [editingSubjectId, setEditingSubjectId] = useState<number | null>(null);
  const [subjectDraft, setSubjectDraft] = useState<{
    name: string;
    workload: number;
    complexity: string;
    course_ids: number[];
  }>({
    name: "",
    workload: 1,
    complexity: "Media",
    course_ids: [],
  });

  const [newClassName, setNewClassName] = useState("");
  const [newClassShift, setNewClassShift] = useState("Manhã");
  const [newClassCourseId, setNewClassCourseId] = useState("");
  const [newClassHasGroups, setNewClassHasGroups] = useState(false);

  const [newSubName, setNewSubName] = useState("");
  const [newSubWorkload, setNewSubWorkload] = useState(4);
  const [newSubComplexity, setNewSubComplexity] = useState("Media");
  const [newSubCourseIds, setNewSubCourseIds] = useState<number[]>([]);

  const fetchData = async () => {
    try {
      const [courseRes, classroomRes, subjectRes] = await Promise.all([
        api.get("/courses/"),
        api.get("/classrooms/"),
        api.get("/subjects/"),
      ]);
      setCourses(courseRes.data);
      setClassrooms(classroomRes.data);
      setSubjects(subjectRes.data);
    } catch (error) {
      console.error("Erro ao buscar dados:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAddCourse = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newCourseName.trim()) return;
    await api.post("/courses/", { name: newCourseName.trim() });
    setNewCourseName("");
    fetchData();
  };

  const startCourseEdit = (course: Course) => {
    setEditingCourseId(course.id);
    setEditingCourseName(course.name);
  };

  const saveCourseEdit = async (course: Course) => {
    const name = editingCourseName.trim();
    if (!name) return;
    await api.put(`/courses/${course.id}`, { name });
    setEditingCourseId(null);
    setEditingCourseName("");
    fetchData();
  };

  const handleDeleteCourse = async (course: Course) => {
    if (!confirm(`Remover o curso "${course.name}"?`)) return;
    try {
      await api.delete(`/courses/${course.id}`);
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Não foi possível remover o curso.");
    }
  };

  const startClassroomEdit = (classroom: Classroom) => {
    setEditingClassroomId(classroom.id);
    const allowedPeriods = classroom.allowed_periods ?? periodsForShift(classroom.shift);
    setClassroomDraft({
      name: classroom.name,
      shift: classroom.shift,
      course_id: classroom.course_id,
      allowed_periods: [...allowedPeriods],
    });
  };

  const saveClassroom = async (classroom: Classroom, changes: Partial<Classroom>) => {
    await api.put(`/classrooms/${classroom.id}`, {
      name: changes.name ?? classroom.name,
      shift: changes.shift ?? classroom.shift,
      allowed_periods:
        changes.allowed_periods ?? classroom.allowed_periods ?? periodsForShift(classroom.shift),
      allowed_periods_by_day:
        changes.allowed_periods_by_day !== undefined
          ? changes.allowed_periods_by_day
          : classroom.allowed_periods_by_day ?? null,
      course_id: changes.course_id ?? classroom.course_id,
      has_groups: changes.has_groups ?? classroom.has_groups,
      subject_settings: changes.subject_settings ?? classroom.subject_settings ?? [],
      split_subject_ids: changes.split_subject_ids ?? classroom.split_subject_ids ?? [],
      preferred_subject_sequences:
        changes.preferred_subject_sequences ?? classroom.preferred_subject_sequences ?? [],
    });
    fetchData();
  };

  const saveClassroomEdit = async (classroom: Classroom) => {
    const name = classroomDraft.name.trim();
    if (!name || !classroomDraft.course_id) return;

    const validSubjectIds = new Set(
      subjects
        .filter(subject => subject.course_ids?.includes(classroomDraft.course_id))
        .map(subject => subject.id),
    );

    await saveClassroom(classroom, {
      name,
      shift: classroomDraft.shift,
      course_id: classroomDraft.course_id,
      allowed_periods: classroomDraft.allowed_periods,
      allowed_periods_by_day:
        classroomDraft.shift === classroom.shift ? classroom.allowed_periods_by_day ?? null : null,
      subject_settings: (classroom.subject_settings || []).filter(s => validSubjectIds.has(s.subject_id)),
    });

    setEditingClassroomId(null);
  };

  const handleDeleteClassroom = async (classroom: Classroom) => {
    if (!confirm(`Remover a turma "${classroom.name}" e seus horários?`)) return;
    try {
      await api.delete(`/classrooms/${classroom.id}`);
      setExpandedClassrooms(curr => {
        const next = new Set(curr);
        next.delete(classroom.id);
        return next;
      });
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Não foi possível remover a turma.");
    }
  };

  const handleAddClassroom = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newClassName.trim() || !newClassCourseId) return;

    await api.post("/classrooms/", {
      name: newClassName.trim(),
      shift: newClassShift,
      allowed_periods: periodsForShift(newClassShift),
      allowed_periods_by_day: null,
      course_id: Number(newClassCourseId),
      has_groups: newClassHasGroups,
      subject_settings: [],
      split_subject_ids: [],
    });

    setNewClassName("");
    setNewClassHasGroups(false);
    fetchData();
  };

  const toggleClassroomDetails = (classroomId: number) => {
    setExpandedClassrooms(curr => {
      const next = new Set(curr);
      if (next.has(classroomId)) next.delete(classroomId);
      else next.add(classroomId);
      return next;
    });
  };

  const subjectsForClassroom = (classroom: Classroom) =>
    subjects.filter(s => s.course_ids?.includes(classroom.course_id));

  const settingFor = (classroom: Classroom, subjectId: number) =>
    (classroom.subject_settings || []).find(s => s.subject_id === subjectId);

  const handleToggleClassSubject = async (classroom: Classroom, subject: Subject) => {
    const current = classroom.subject_settings || [];
    const existing = settingFor(classroom, subject.id);

    const next = existing
      ? current.filter(s => s.subject_id !== subject.id)
      : [
          ...current,
          {
            subject_id: subject.id,
            workload: subject.workload,
            split: false,
            prefer_triple_block: subject.workload === 3 ? true : undefined,
          },
        ];

    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleSubjectWorkload = async (classroom: Classroom, subjectId: number, workload: number) => {
    if (!Number.isFinite(workload)) return;
    const safeWorkload = Math.min(Math.max(Math.round(workload), 1), 25);
    const next = (classroom.subject_settings || []).map(s =>
      s.subject_id === subjectId ? { ...s, workload: safeWorkload } : s,
    );
    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleSubjectGroupWorkload = async (
    classroom: Classroom,
    subjectId: number,
    group: "A" | "B",
    workload: number,
  ) => {
    if (!Number.isFinite(workload)) return;
    const safeWorkload = Math.min(Math.max(Math.round(workload), 1), 25);
    const key = group === "A" ? "workload_a" : "workload_b";
    const next = (classroom.subject_settings || []).map(s =>
      s.subject_id === subjectId ? { ...s, [key]: safeWorkload } : s,
    );
    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleTripleBlockPreference = async (
    classroom: Classroom,
    subjectId: number,
    preferTripleBlock: boolean,
  ) => {
    const next = (classroom.subject_settings || []).map(s =>
      s.subject_id === subjectId ? { ...s, prefer_triple_block: preferTripleBlock } : s,
    );
    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleSubjectSplit = async (classroom: Classroom, subjectId: number, split: boolean) => {
    const next = (classroom.subject_settings || []).map(s =>
      s.subject_id === subjectId ? { ...s, split } : s,
    );
    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleUseAllSubjects = async (classroom: Classroom) => {
    const candidates = subjectsForClassroom(classroom);
    const current = classroom.subject_settings || [];
    const next = candidates.map(subject => {
      const existing = current.find(s => s.subject_id === subject.id);
      return (
        existing || {
          subject_id: subject.id,
          workload: subject.workload,
          split: false,
          prefer_triple_block: subject.workload === 3 ? true : undefined,
        }
      );
    });
    await saveClassroom(classroom, { subject_settings: next });
  };

  const handleClearSubjects = async (classroom: Classroom) => {
    await saveClassroom(classroom, { subject_settings: [] });
  };

  const handleAddPreferredSequence = async (classroom: Classroom) => {
    const draft = sequenceDraftByClassroom[classroom.id] || { first: "", second: "" };
    const firstId = Number(draft.first);
    const secondId = Number(draft.second);
    if (!firstId || !secondId || firstId === secondId) return;

    const firstSetting = settingFor(classroom, firstId);
    const secondSetting = settingFor(classroom, secondId);
    if (!firstSetting || !secondSetting) return;
    if (firstSetting.split !== secondSetting.split) {
      alert("Escolha matérias da mesma organização: ambas de turma inteira ou ambas separadas A/B.");
      return;
    }

    const current = classroom.preferred_subject_sequences || [];
    if (current.some(pair => pair[0] === firstId && pair[1] === secondId)) return;

    await saveClassroom(classroom, {
      preferred_subject_sequences: [...current, [firstId, secondId]],
    });
    setSequenceDraftByClassroom(c => ({ ...c, [classroom.id]: { first: "", second: "" } }));
  };

  const handleRemovePreferredSequence = async (classroom: Classroom, index: number) => {
    const current = classroom.preferred_subject_sequences || [];
    await saveClassroom(classroom, {
      preferred_subject_sequences: current.filter((_, i) => i !== index),
    });
  };

  const handleCopySubjects = async (targetClassroom: Classroom) => {
    const sourceId = Number(copySourceByClassroom[targetClassroom.id]);
    const sourceClassroom = classrooms.find(c => c.id === sourceId);
    if (!sourceClassroom) return;

    if (
      (targetClassroom.subject_settings || []).length > 0 &&
      !confirm(`Substituir a matriz de ${targetClassroom.name} pela de ${sourceClassroom.name}?`)
    ) {
      return;
    }

    const validSubjectIds = new Set(subjectsForClassroom(targetClassroom).map(s => s.id));
    const copiedSettings = (sourceClassroom.subject_settings || [])
      .filter(s => validSubjectIds.has(s.subject_id))
      .map(s => ({ ...s, split: targetClassroom.has_groups ? s.split : false }));

    await saveClassroom(targetClassroom, {
      subject_settings: copiedSettings,
      preferred_subject_sequences: sourceClassroom.preferred_subject_sequences || [],
    });

    setCopySourceByClassroom(c => ({ ...c, [targetClassroom.id]: "" }));
  };

  const handleAddSubject = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newSubName.trim() || newSubCourseIds.length === 0) return;

    await api.post("/subjects/", {
      name: newSubName.trim(),
      workload: Number(newSubWorkload),
      complexity: newSubComplexity,
      category: "Ensino Médio",
      course_ids: newSubCourseIds,
    });

    setNewSubName("");
    setNewSubWorkload(4);
    setNewSubCourseIds([]);
    fetchData();
  };

  const startSubjectEdit = (subject: Subject) => {
    setEditingSubjectId(subject.id);
    setSubjectDraft({
      name: subject.name,
      workload: subject.workload,
      complexity: subject.complexity,
      course_ids: [...(subject.course_ids || [])],
    });
  };

  const saveSubjectEdit = async (subject: Subject) => {
    const name = subjectDraft.name.trim();
    if (!name || subjectDraft.course_ids.length === 0) {
      alert("Informe o nome e mantenha pelo menos um curso associado.");
      return;
    }

    await api.put(`/subjects/${subject.id}`, {
      name,
      workload: Math.max(1, Math.round(Number(subjectDraft.workload))),
      complexity: subjectDraft.complexity,
      category: subject.category || "Ensino Médio",
      course_ids: subjectDraft.course_ids,
    });

    setEditingSubjectId(null);
    fetchData();
  };

  const handleDeleteSubject = async (subject: Subject) => {
    if (!confirm(`Remover a disciplina "${subject.name}"? Ela será retirada das matrizes associadas.`)) return;
    try {
      await api.delete(`/subjects/${subject.id}`);
      fetchData();
    } catch (error: any) {
      alert(error.response?.data?.detail || "Não foi possível remover a disciplina.");
    }
  };

  return (
    <div className="app-workspace">
      {/* TÍTULO DA PÁGINA */}
      <div className="app-page-title-row">
        <div>
          <h1 className="app-page-title">
            Turmas e Matrizes Curriculares
            <span className="app-page-subtitle">
              Gestão de cursos, turmas, divisões A/B e parametrização das disciplinas
            </span>
          </h1>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: 20, alignItems: "start" }}>
        {/* COLUNA 1: CURSOS */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            <School style={{ width: 16, height: 16, color: "var(--an-primary)" }} />
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Cursos Oferecidos</h2>
          </div>

          <form onSubmit={handleAddCourse} style={{ display: "flex", gap: 8, marginBottom: 14 }}>
            <input
              type="text"
              required
              placeholder="Nome do curso..."
              className="app-input"
              style={{ flex: 1 }}
              value={newCourseName}
              onChange={e => setNewCourseName(e.target.value)}
            />
            <button type="submit" className="app-btn app-btn-primary" style={{ padding: "0 10px" }} title="Adicionar curso">
              <Plus style={{ width: 15, height: 15 }} />
            </button>
          </form>

          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {courses.map(course => (
              <div
                key={course.id}
                style={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "8px 10px",
                  backgroundColor: "var(--an-bg)",
                  border: "1px solid var(--an-border)",
                  borderRadius: "var(--an-radius-sm)",
                  gap: 8,
                }}
              >
                {editingCourseId === course.id ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 6, width: "100%" }}>
                    <input
                      value={editingCourseName}
                      onChange={e => setEditingCourseName(e.target.value)}
                      className="app-input"
                      style={{ height: 28, flex: 1 }}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={() => saveCourseEdit(course)}
                      className="app-btn app-btn-primary"
                      style={{ height: 28, padding: "0 8px" }}
                    >
                      <Save style={{ width: 13, height: 13 }} />
                    </button>
                    <button
                      type="button"
                      onClick={() => setEditingCourseId(null)}
                      className="app-btn app-btn-secondary"
                      style={{ height: 28, padding: "0 8px" }}
                    >
                      <X style={{ width: 13, height: 13 }} />
                    </button>
                  </div>
                ) : (
                  <>
                    <span style={{ fontSize: 13, fontWeight: 600, color: "var(--an-text)" }}>{course.name}</span>
                    <div style={{ display: "flex", gap: 4 }}>
                      <button
                        type="button"
                        onClick={() => startCourseEdit(course)}
                        className="app-btn app-btn-secondary"
                        style={{ height: 26, width: 26, padding: 0 }}
                        title="Editar curso"
                      >
                        <Edit style={{ width: 13, height: 13 }} />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDeleteCourse(course)}
                        className="app-btn app-btn-danger"
                        style={{ height: 26, width: 26, padding: 0 }}
                        title="Remover curso"
                      >
                        <Trash2 style={{ width: 13, height: 13 }} />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}
            {courses.length === 0 && (
              <p style={{ margin: 0, fontSize: 12, color: "var(--an-muted)", textAlign: "center", padding: 12 }}>
                Nenhum curso cadastrado.
              </p>
            )}
          </div>
        </div>

        {/* COLUNA 2: TURMAS */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18, gridColumn: "span 2" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            <Layers style={{ width: 16, height: 16, color: "var(--an-primary)" }} />
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Turmas e Matrizes Curriculares</h2>
          </div>

          <form onSubmit={handleAddClassroom} style={{ display: "flex", flexWrap: "wrap", gap: 10, marginBottom: 18, padding: 12, backgroundColor: "var(--an-bg)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)" }}>
            <input
              type="text"
              required
              placeholder="Nome da Turma (ex: 3º INFO A)"
              className="app-input"
              style={{ flex: "1 1 200px" }}
              value={newClassName}
              onChange={e => setNewClassName(e.target.value)}
            />
            <select
              className="app-select"
              style={{ width: 110 }}
              value={newClassShift}
              onChange={e => {
                const shift = e.target.value;
                setNewClassShift(shift);
                if (shift === "Noite") setNewClassHasGroups(false);
              }}
            >
              <option value="Manhã">Manhã</option>
              <option value="Integral">Integral</option>
              <option value="Noite">Noite</option>
            </select>
            <select
              required
              className="app-select"
              style={{ flex: "1 1 180px" }}
              value={newClassCourseId}
              onChange={e => setNewClassCourseId(e.target.value)}
            >
              <option value="" disabled>Curso correspondente...</option>
              {courses.map(c => (
                <option key={c.id} value={c.id}>{c.name}</option>
              ))}
            </select>

            {newClassShift !== "Noite" && (
              <label style={{ display: "inline-flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer", userSelect: "none" }}>
                <input
                  type="checkbox"
                  checked={newClassHasGroups}
                  onChange={e => setNewClassHasGroups(e.target.checked)}
                  style={{ accentColor: "var(--an-primary)" }}
                />
                Permitir Grupos A/B
              </label>
            )}

            <button type="submit" className="app-btn app-btn-primary" style={{ marginLeft: "auto" }}>
              <Plus style={{ width: 14, height: 14 }} />
              <span>Adicionar Turma</span>
            </button>
          </form>

          {/* LISTA DE TURMAS */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {classrooms.map(classroom => {
              const candidates = subjectsForClassroom(classroom);
              const selectedCount = classroom.subject_settings?.length || 0;
              const isExpanded = expandedClassrooms.has(classroom.id);
              const copySources = classrooms.filter(
                other => other.id !== classroom.id && other.course_id === classroom.course_id && (other.subject_settings || []).length > 0,
              );

              return (
                <div
                  key={classroom.id}
                  style={{
                    border: "1px solid var(--an-border)",
                    borderRadius: "var(--an-radius-sm)",
                    backgroundColor: "var(--an-surface)",
                    overflow: "hidden",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "space-between",
                      padding: "10px 14px",
                      backgroundColor: isExpanded ? "var(--an-surface-hover)" : "var(--an-bg)",
                      borderBottom: isExpanded ? "1px solid var(--an-border)" : "none",
                    }}
                  >
                    {editingClassroomId === classroom.id ? (
                      <div style={{ display: "flex", gap: 8, alignItems: "center", flex: 1 }}>
                        <input
                          value={classroomDraft.name}
                          onChange={e => setClassroomDraft(c => ({ ...c, name: e.target.value }))}
                          className="app-input"
                          style={{ height: 28, flex: 1 }}
                        />
                        <select
                          value={classroomDraft.shift}
                          onChange={e => {
                            const shift = e.target.value;
                            setClassroomDraft(c => ({ ...c, shift, allowed_periods: periodsForShift(shift) }));
                          }}
                          className="app-select"
                          style={{ height: 28 }}
                        >
                          <option value="Manhã">Manhã</option>
                          <option value="Integral">Integral</option>
                          <option value="Noite">Noite</option>
                        </select>
                        <button
                          type="button"
                          onClick={() => saveClassroomEdit(classroom)}
                          className="app-btn app-btn-primary"
                          style={{ height: 28, padding: "0 8px" }}
                        >
                          <Save style={{ width: 13, height: 13 }} />
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingClassroomId(null)}
                          className="app-btn app-btn-secondary"
                          style={{ height: 28, padding: "0 8px" }}
                        >
                          <X style={{ width: 13, height: 13 }} />
                        </button>
                      </div>
                    ) : (
                      <>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                          <button
                            type="button"
                            onClick={() => toggleClassroomDetails(classroom.id)}
                            style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--an-text)", display: "flex", alignItems: "center", gap: 6 }}
                          >
                            {isExpanded ? <ChevronUp style={{ width: 16, height: 16 }} /> : <ChevronDown style={{ width: 16, height: 16 }} />}
                            <strong style={{ fontSize: 14 }}>{classroom.name}</strong>
                          </button>
                          <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)", padding: "2px 6px", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)" }}>
                            {classroom.shift}
                          </span>
                          {classroom.has_groups && (
                            <span style={{ fontSize: 11, color: "var(--an-primary)", fontWeight: 600 }}>
                              Grupos A/B
                            </span>
                          )}
                          <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)" }}>
                            ({selectedCount} matérias)
                          </span>
                        </div>

                        <div style={{ display: "flex", gap: 4 }}>
                          <button
                            type="button"
                            onClick={() => startClassroomEdit(classroom)}
                            className="app-btn app-btn-secondary"
                            style={{ height: 26, width: 26, padding: 0 }}
                            title="Editar turma"
                          >
                            <Edit style={{ width: 13, height: 13 }} />
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteClassroom(classroom)}
                            className="app-btn app-btn-danger"
                            style={{ height: 26, width: 26, padding: 0 }}
                            title="Remover turma"
                          >
                            <Trash2 style={{ width: 13, height: 13 }} />
                          </button>
                        </div>
                      </>
                    )}
                  </div>

                  {/* CORPO EXPANDIDO: MATRIZ CURRICULAR */}
                  {isExpanded && (
                    <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 14 }}>
                      <div style={{ display: "flex", flexWrap: "wrap", justifyContent: "space-between", alignItems: "center", gap: 8, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
                        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                          <button
                            type="button"
                            onClick={() => handleUseAllSubjects(classroom)}
                            className="app-btn app-btn-secondary"
                            style={{ height: 26, fontSize: 11 }}
                          >
                            Incluir todas as disciplinas
                          </button>
                          <button
                            type="button"
                            onClick={() => handleClearSubjects(classroom)}
                            className="app-btn app-btn-secondary"
                            style={{ height: 26, fontSize: 11 }}
                          >
                            Limpar matriz
                          </button>
                        </div>

                        {copySources.length > 0 && (
                          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <select
                              value={copySourceByClassroom[classroom.id] || ""}
                              onChange={e => setCopySourceByClassroom(c => ({ ...c, [classroom.id]: e.target.value }))}
                              className="app-select"
                              style={{ height: 28, fontSize: 11 }}
                            >
                              <option value="">Copiar matriz de...</option>
                              {copySources.map(s => (
                                <option key={s.id} value={s.id}>{s.name} ({s.shift})</option>
                              ))}
                            </select>
                            <button
                              type="button"
                              disabled={!copySourceByClassroom[classroom.id]}
                              onClick={() => handleCopySubjects(classroom)}
                              className="app-btn app-btn-secondary"
                              style={{ height: 28, padding: "0 8px" }}
                              title="Copiar matriz"
                            >
                              <Copy style={{ width: 13, height: 13 }} />
                            </button>
                          </div>
                        )}
                      </div>

                      {/* ITENS DA MATRIZ CURRICULAR */}
                      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 8 }}>
                        {candidates.map(subject => {
                          const setting = settingFor(classroom, subject.id);
                          const isSelected = Boolean(setting);
                          const subjectLoads = setting
                            ? setting.split
                              ? [setting.workload_a ?? setting.workload, setting.workload_b ?? setting.workload]
                              : [setting.workload]
                            : [];
                          const canPreferTripleBlock = subjectLoads.includes(3);
                          const prefersTripleBlock = setting ? setting.prefer_triple_block ?? canPreferTripleBlock : false;

                          return (
                            <div
                              key={subject.id}
                              style={{
                                border: "1px solid var(--an-border)",
                                borderRadius: "var(--an-radius-sm)",
                                padding: 8,
                                backgroundColor: isSelected ? "var(--an-surface)" : "var(--an-bg)",
                                opacity: isSelected ? 1 : 0.65,
                              }}
                            >
                              <label style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer", fontSize: 12 }}>
                                <input
                                  type="checkbox"
                                  checked={isSelected}
                                  onChange={() => handleToggleClassSubject(classroom, subject)}
                                  style={{ accentColor: "var(--an-primary)" }}
                                />
                                <span style={{ fontWeight: 600, flex: 1 }}>{subject.name}</span>
                              </label>

                              {setting && (
                                <div style={{ marginTop: 8, paddingLeft: 22, display: "flex", flexDirection: "column", gap: 6 }}>
                                  {setting.split ? (
                                    <div style={{ display: "flex", gap: 8 }}>
                                      {(["A", "B"] as const).map(group => (
                                        <label key={group} style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "var(--an-muted)" }}>
                                          <span>G{group}:</span>
                                          <input
                                            type="number"
                                            min="1"
                                            max="25"
                                            defaultValue={group === "A" ? setting.workload_a ?? setting.workload : setting.workload_b ?? setting.workload}
                                            onBlur={e => handleSubjectGroupWorkload(classroom, subject.id, group, Number(e.target.value))}
                                            className="app-input font-mono"
                                            style={{ width: 44, height: 26, padding: "0 4px", textAlign: "center" }}
                                          />
                                        </label>
                                      ))}
                                    </div>
                                  ) : (
                                    <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, color: "var(--an-muted)" }}>
                                      <span>Aulas semanais:</span>
                                      <input
                                        type="number"
                                        min="1"
                                        max="25"
                                        defaultValue={setting.workload}
                                        onBlur={e => handleSubjectWorkload(classroom, subject.id, Number(e.target.value))}
                                        className="app-input font-mono"
                                        style={{ width: 48, height: 26, padding: "0 4px", textAlign: "center" }}
                                      />
                                    </label>
                                  )}

                                  {canPreferTripleBlock && (
                                    <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11, cursor: "pointer" }}>
                                      <input
                                        type="checkbox"
                                        checked={prefersTripleBlock}
                                        onChange={e => handleTripleBlockPreference(classroom, subject.id, e.target.checked)}
                                        style={{ accentColor: "var(--an-primary)" }}
                                      />
                                      <span>Preferir 3 aulas seguidas</span>
                                    </label>
                                  )}

                                  {classroom.has_groups && (
                                    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11 }}>
                                      <span style={{ color: "var(--an-muted)" }}>Divisão:</span>
                                      <select
                                        value={setting.split ? "split" : "all"}
                                        onChange={e => handleSubjectSplit(classroom, subject.id, e.target.value === "split")}
                                        className="app-select"
                                        style={{ height: 24, fontSize: 11, padding: "0 4px" }}
                                      >
                                        <option value="all">Turma inteira</option>
                                        <option value="split">Separada A/B</option>
                                      </select>
                                    </div>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>

                      {/* SEQUÊNCIAS PREFERIDAS */}
                      {(classroom.subject_settings || []).length >= 2 && (
                        <div style={{ marginTop: 8, paddingTop: 12, borderTop: "1px solid var(--an-border)" }}>
                          <span style={{ fontSize: 12, fontWeight: 700, display: "block", marginBottom: 2 }}>
                            Preferência de Sequência entre Matérias
                          </span>
                          <p style={{ margin: "0 0 8px", fontSize: 11, color: "var(--an-muted)" }}>
                            Otimiza para que a 1ª matéria ocorra preferencialmente antes da 2ª (ex: Filosofia antes de Sociologia).
                          </p>

                          <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 8 }}>
                            <select
                              value={sequenceDraftByClassroom[classroom.id]?.first || ""}
                              onChange={e => setSequenceDraftByClassroom(c => ({ ...c, [classroom.id]: { first: e.target.value, second: "" } }))}
                              className="app-select"
                              style={{ height: 28, fontSize: 11 }}
                            >
                              <option value="">1ª Matéria...</option>
                              {(classroom.subject_settings || []).map(s => {
                                const sub = candidates.find(item => item.id === s.subject_id);
                                return sub ? <option key={sub.id} value={sub.id}>{sub.name}</option> : null;
                              })}
                            </select>
                            <span style={{ fontSize: 11, color: "var(--an-muted)" }}>seguida de</span>
                            <select
                              value={sequenceDraftByClassroom[classroom.id]?.second || ""}
                              disabled={!sequenceDraftByClassroom[classroom.id]?.first}
                              onChange={e => setSequenceDraftByClassroom(c => ({ ...c, [classroom.id]: { ...(c[classroom.id] || { first: "", second: "" }), second: e.target.value } }))}
                              className="app-select"
                              style={{ height: 28, fontSize: 11 }}
                            >
                              <option value="">2ª Matéria...</option>
                              {(classroom.subject_settings || [])
                                .filter(s => {
                                  const draft = sequenceDraftByClassroom[classroom.id];
                                  const firstS = settingFor(classroom, Number(draft?.first));
                                  return s.subject_id !== Number(draft?.first) && firstS && s.split === firstS.split;
                                })
                                .map(s => {
                                  const sub = candidates.find(item => item.id === s.subject_id);
                                  return sub ? <option key={sub.id} value={sub.id}>{sub.name}</option> : null;
                                })}
                            </select>
                            <button
                              type="button"
                              disabled={!sequenceDraftByClassroom[classroom.id]?.first || !sequenceDraftByClassroom[classroom.id]?.second}
                              onClick={() => handleAddPreferredSequence(classroom)}
                              className="app-btn app-btn-secondary"
                              style={{ height: 28, fontSize: 11 }}
                            >
                              Adicionar Sequência
                            </button>
                          </div>

                          <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                            {(classroom.preferred_subject_sequences || []).map((pair, idx) => (
                              <span
                                key={idx}
                                style={{
                                  display: "inline-flex",
                                  alignItems: "center",
                                  gap: 6,
                                  padding: "3px 8px",
                                  backgroundColor: "var(--an-bg)",
                                  border: "1px solid var(--an-border)",
                                  borderRadius: "var(--an-radius-sm)",
                                  fontSize: 11,
                                }}
                              >
                                <strong>{candidates.find(s => s.id === pair[0])?.name || pair[0]}</strong>
                                <span style={{ color: "var(--an-muted)" }}>→</span>
                                <strong>{candidates.find(s => s.id === pair[1])?.name || pair[1]}</strong>
                                <button
                                  type="button"
                                  onClick={() => handleRemovePreferredSequence(classroom, idx)}
                                  style={{ background: "none", border: "none", cursor: "pointer", padding: 0, color: "var(--an-muted)", display: "flex" }}
                                >
                                  <X style={{ width: 12, height: 12 }} />
                                </button>
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* COLUNA 3: CADASTRO GLOBAL DE DISCIPLINAS */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18, gridColumn: "span 3" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            <BookOpen style={{ width: 16, height: 16, color: "var(--an-primary)" }} />
            <h2 style={{ fontSize: 15, fontWeight: 700, margin: 0 }}>Catálogo de Disciplinas Escolares</h2>
          </div>

          <form onSubmit={handleAddSubject} style={{ display: "grid", gridTemplateColumns: "1.2fr 120px 140px 1fr auto", gap: 10, alignItems: "end", marginBottom: 18 }}>
            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                Nome da Disciplina
              </label>
              <input
                type="text"
                required
                placeholder="Ex: Física Aplicada"
                className="app-input"
                style={{ width: "100%" }}
                value={newSubName}
                onChange={e => setNewSubName(e.target.value)}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                Carga padrão
              </label>
              <input
                type="number"
                min="1"
                required
                className="app-input font-mono"
                style={{ width: "100%" }}
                value={newSubWorkload}
                onChange={e => setNewSubWorkload(Number(e.target.value))}
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                Complexidade
              </label>
              <select
                className="app-select"
                style={{ width: "100%" }}
                value={newSubComplexity}
                onChange={e => setNewSubComplexity(e.target.value)}
              >
                <option value="Alta">Alta</option>
                <option value="Media">Média</option>
                <option value="Baixa">Baixa</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                Cursos Associados
              </label>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6, maxHeight: 34, overflowY: "auto", padding: "4px 8px", backgroundColor: "var(--an-bg)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)" }}>
                {courses.map(c => (
                  <label key={c.id} style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, cursor: "pointer" }}>
                    <input
                      type="checkbox"
                      checked={newSubCourseIds.includes(c.id)}
                      onChange={e => {
                        if (e.target.checked) setNewSubCourseIds([...newSubCourseIds, c.id]);
                        else setNewSubCourseIds(newSubCourseIds.filter(id => id !== c.id));
                      }}
                      style={{ accentColor: "var(--an-primary)" }}
                    />
                    <span>{c.name}</span>
                  </label>
                ))}
              </div>
            </div>

            <button type="submit" className="app-btn app-btn-primary" style={{ height: 34 }}>
              <Plus style={{ width: 14, height: 14 }} />
              <span>Adicionar Disciplina</span>
            </button>
          </form>

          {/* LISTA EM GRID DE DISCIPLINAS */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 8 }}>
            {subjects.map(subject => (
              <div
                key={subject.id}
                style={{
                  border: "1px solid var(--an-border)",
                  borderRadius: "var(--an-radius-sm)",
                  padding: "8px 12px",
                  backgroundColor: "var(--an-bg)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 6,
                }}
              >
                {editingSubjectId === subject.id ? (
                  <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                    <input
                      value={subjectDraft.name}
                      onChange={e => setSubjectDraft(c => ({ ...c, name: e.target.value }))}
                      className="app-input"
                      style={{ height: 28 }}
                    />
                    <div style={{ display: "flex", gap: 6 }}>
                      <input
                        type="number"
                        min="1"
                        value={subjectDraft.workload}
                        onChange={e => setSubjectDraft(c => ({ ...c, workload: Number(e.target.value) }))}
                        className="app-input font-mono"
                        style={{ width: 60, height: 28 }}
                      />
                      <select
                        value={subjectDraft.complexity}
                        onChange={e => setSubjectDraft(c => ({ ...c, complexity: e.target.value }))}
                        className="app-select"
                        style={{ flex: 1, height: 28 }}
                      >
                        <option value="Alta">Alta</option>
                        <option value="Media">Média</option>
                        <option value="Baixa">Baixa</option>
                      </select>
                    </div>
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: 4 }}>
                      <button
                        type="button"
                        onClick={() => saveSubjectEdit(subject)}
                        className="app-btn app-btn-primary"
                        style={{ height: 26, fontSize: 11 }}
                      >
                        Salvar
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingSubjectId(null)}
                        className="app-btn app-btn-secondary"
                        style={{ height: 26, fontSize: 11 }}
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                      <div>
                        <strong style={{ fontSize: 13, color: "var(--an-text)", display: "block" }}>{subject.name}</strong>
                        <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)" }}>
                          {subject.workload} aulas semanais
                        </span>
                      </div>
                      <div style={{ display: "flex", gap: 4, alignItems: "center" }}>
                        <span
                          className="font-mono"
                          style={{
                            fontSize: 10,
                            fontWeight: 600,
                            padding: "2px 6px",
                            borderRadius: "var(--an-radius-sm)",
                            backgroundColor:
                              subject.complexity === "Alta"
                                ? "var(--an-danger-soft)"
                                : subject.complexity === "Media"
                                  ? "var(--an-warning-soft)"
                                  : "var(--an-success-soft)",
                            color:
                              subject.complexity === "Alta"
                                ? "var(--an-danger)"
                                : subject.complexity === "Media"
                                  ? "var(--an-warning)"
                                  : "var(--an-success)",
                          }}
                        >
                          {subject.complexity}
                        </span>
                        <button
                          type="button"
                          onClick={() => startSubjectEdit(subject)}
                          className="app-btn app-btn-secondary"
                          style={{ width: 24, height: 24, padding: 0 }}
                          title="Editar disciplina"
                        >
                          <Edit style={{ width: 12, height: 12 }} />
                        </button>
                        <button
                          type="button"
                          onClick={() => handleDeleteSubject(subject)}
                          className="app-btn app-btn-danger"
                          style={{ width: 24, height: 24, padding: 0 }}
                          title="Remover disciplina"
                        >
                          <Trash2 style={{ width: 12, height: 12 }} />
                        </button>
                      </div>
                    </div>
                    <div style={{ fontSize: 11, color: "var(--an-muted)" }}>
                      Cursos: {subject.course_ids?.map(id => courses.find(c => c.id === id)?.name || id).join(", ") || "Nenhum"}
                    </div>
                  </>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
