import React, { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import {
  CheckCircle,
  ChevronDown,
  ChevronUp,
  Clock3,
  Edit,
  Plus,
  Search,
  Star,
  Trash2,
  Users,
  X,
  XCircle,
} from "lucide-react";

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

const DAYS = [
  "Segunda",
  "Terça",
  "Quarta",
  "Quinta",
  "Sexta",
];

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

const SHIFTS = [
  {
    name: "Manhã",
    startIndex: 0,
    count: 6,
  },
  {
    name: "Tarde",
    startIndex: 6,
    count: 5,
  },
  {
    name: "Noite",
    startIndex: 11,
    count: 5,
  },
];

const normalizeAvailabilityDay = (values?: boolean[]) => {
  if (!values) return Array(16).fill(true);
  if (values.length === 16) return [...values];

  if (values.length === 15) {
    return [
      ...values.slice(0, 5),
      values[4],
      ...values.slice(5),
    ];
  }

  const normalized = Array(16).fill(true);
  for (let i = 0; i < Math.min(values.length, 16); i++) {
    normalized[i] = values[i];
  }
  return normalized;
};

const initialAvailability = () => {
  const availability: Record<string, boolean[]> = {};
  for (let day = 0; day < 5; day++) {
    availability[day.toString()] = Array(16).fill(true);
  }
  return availability;
};

const cloneAvailability = (availability: Record<string, boolean[]>) => {
  const result: Record<string, boolean[]> = {};
  for (let day = 0; day < 5; day++) {
    const key = day.toString();
    result[key] = normalizeAvailabilityDay(availability[key]);
  }
  return result;
};

export default function Professores() {
  const [teachers, setTeachers] = useState<Teacher[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);

  const [editingTeacherId, setEditingTeacherId] = useState<number | null>(null);

  const [newName, setNewName] = useState("");
  const [newScore, setNewScore] = useState(0);
  const [newAllowedSubjects, setNewAllowedSubjects] = useState<number[]>([]);
  const [newAvailability, setNewAvailability] = useState<Record<string, boolean[]>>(initialAvailability());

  const [subjectSearch, setSubjectSearch] = useState("");
  const [availabilityExpanded, setAvailabilityExpanded] = useState(false);
  const [formError, setFormError] = useState("");

  const fetchData = async () => {
    try {
      const [teacherResponse, subjectResponse] = await Promise.all([
        api.get("/teachers/"),
        api.get("/subjects/"),
      ]);
      setTeachers(teacherResponse.data);
      setSubjects(subjectResponse.data);
    } catch (error) {
      console.error("Erro ao buscar dados:", error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredSubjects = useMemo(() => {
    const query = subjectSearch.trim().toLocaleLowerCase("pt-BR");
    if (!query) return subjects;
    return subjects.filter(subject =>
      subject.name.toLocaleLowerCase("pt-BR").includes(query),
    );
  }, [subjects, subjectSearch]);

  const availablePeriodCount = useMemo(
    () =>
      Object.values(newAvailability).reduce(
        (total, day) => total + day.filter(Boolean).length,
        0,
      ),
    [newAvailability],
  );

  const handleToggleSubject = (subjectId: number) => {
    setNewAllowedSubjects(current =>
      current.includes(subjectId)
        ? current.filter(id => id !== subjectId)
        : [...current, subjectId],
    );
  };

  const selectVisibleSubjects = () => {
    setNewAllowedSubjects(current =>
      Array.from(new Set([...current, ...filteredSubjects.map(s => s.id)])),
    );
  };

  const clearVisibleSubjects = () => {
    const visibleIds = new Set(filteredSubjects.map(s => s.id));
    setNewAllowedSubjects(current => current.filter(id => !visibleIds.has(id)));
  };

  const handleToggleAvailability = (dayIndex: number, periodIndex: number) => {
    const dayKey = dayIndex.toString();
    setNewAvailability(current => {
      const updatedDay = [...normalizeAvailabilityDay(current[dayKey])];
      updatedDay[periodIndex] = !updatedDay[periodIndex];
      return {
        ...current,
        [dayKey]: updatedDay,
      };
    });
  };

  const setAllAvailability = (available: boolean) => {
    const next: Record<string, boolean[]> = {};
    for (let day = 0; day < 5; day++) {
      next[day.toString()] = Array(16).fill(available);
    }
    setNewAvailability(next);
  };

  const toggleWholeDay = (dayIndex: number) => {
    const dayKey = dayIndex.toString();
    setNewAvailability(current => {
      const day = normalizeAvailabilityDay(current[dayKey]);
      const allAvailable = day.every(Boolean);
      return {
        ...current,
        [dayKey]: Array(16).fill(!allAvailable),
      };
    });
  };

  const toggleWholeShift = (shiftStart: number, shiftCount: number) => {
    setNewAvailability(current => {
      const next = cloneAvailability(current);
      const cells = [];
      for (let day = 0; day < 5; day++) {
        const dayKey = day.toString();
        for (let offset = 0; offset < shiftCount; offset++) {
          cells.push(next[dayKey][shiftStart + offset]);
        }
      }
      const allAvailable = cells.every(Boolean);
      const newValue = !allAvailable;

      for (let day = 0; day < 5; day++) {
        const dayKey = day.toString();
        for (let offset = 0; offset < shiftCount; offset++) {
          next[dayKey][shiftStart + offset] = newValue;
        }
      }
      return next;
    });
  };

  const resetForm = () => {
    setEditingTeacherId(null);
    setNewName("");
    setNewScore(0);
    setNewAllowedSubjects([]);
    setNewAvailability(initialAvailability());
    setSubjectSearch("");
    setAvailabilityExpanded(false);
    setFormError("");
  };

  const handleSaveTeacher = async (event: React.FormEvent) => {
    event.preventDefault();
    setFormError("");

    if (!newName.trim()) {
      setFormError("Informe o nome do professor.");
      return;
    }

    const payload = {
      name: newName.trim(),
      score: newScore,
      allowed_subjects: newAllowedSubjects,
      availability: cloneAvailability(newAvailability),
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
      setFormError("Não foi possível salvar o professor.");
    }
  };

  const handleEdit = (teacher: Teacher) => {
    setEditingTeacherId(teacher.id);
    setNewName(teacher.name);
    setNewScore(teacher.score || 0);
    setNewAllowedSubjects([...teacher.allowed_subjects]);
    setNewAvailability(cloneAvailability(teacher.availability));
    setSubjectSearch("");
    setAvailabilityExpanded(false);
    setFormError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Tem certeza que deseja remover este professor?")) {
      return;
    }
    try {
      await api.delete(`/teachers/${id}`);
      if (editingTeacherId === id) resetForm();
      fetchData();
    } catch (error) {
      console.error("Erro ao remover professor", error);
    }
  };

  const availabilitySummary = (teacher: Teacher) => {
    let available = 0;
    for (let day = 0; day < 5; day++) {
      available += normalizeAvailabilityDay(teacher.availability[day.toString()]).filter(Boolean).length;
    }
    return available;
  };

  return (
    <div className="app-workspace">
      {/* TÍTULO DA PÁGINA */}
      <div className="app-page-title-row">
        <div>
          <h1 className="app-page-title">
            Professores
            <span className="app-page-subtitle">
              Cadastro de docentes, atribuições de matérias e janelas de disponibilidade
            </span>
          </h1>
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))", gap: 20, alignItems: "start" }}>
        {/* FORMULÁRIO */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <h2 style={{ fontSize: 16, fontWeight: 700, margin: "0 0 16px", paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            {editingTeacherId ? "Editar Professor" : "Cadastrar Novo Professor"}
          </h2>

          <form onSubmit={handleSaveTeacher} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 140px", gap: 12 }}>
              <div>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                  Nome do Professor
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ex: Prof. Dr. Silva"
                  className="app-input"
                  style={{ width: "100%" }}
                  value={newName}
                  onChange={e => setNewName(e.target.value)}
                />
              </div>

              <div>
                <label style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, fontWeight: 600, color: "var(--an-muted)", marginBottom: 4, textTransform: "uppercase" }}>
                  <Star style={{ width: 13, height: 13, color: "var(--an-warning)" }} />
                  Prioridade (pts)
                </label>
                <input
                  type="number"
                  min="0"
                  max="100"
                  className="app-input font-mono"
                  style={{ width: "100%" }}
                  value={newScore}
                  onChange={e => setNewScore(Number(e.target.value))}
                />
              </div>
            </div>

            {/* SELEÇÃO DE DISCIPLINAS */}
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
                <div>
                  <label style={{ fontSize: 11, fontWeight: 600, color: "var(--an-muted)", textTransform: "uppercase" }}>
                    Disciplinas que pode lecionar
                  </label>
                  <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)", marginLeft: 6 }}>
                    ({newAllowedSubjects.length} selecionadas)
                  </span>
                </div>
                <div style={{ display: "flex", gap: 6 }}>
                  <button
                    type="button"
                    onClick={selectVisibleSubjects}
                    className="app-btn app-btn-secondary"
                    style={{ height: 26, fontSize: 11, padding: "0 8px" }}
                  >
                    Marcar visíveis
                  </button>
                  <button
                    type="button"
                    onClick={clearVisibleSubjects}
                    className="app-btn app-btn-secondary"
                    style={{ height: 26, fontSize: 11, padding: "0 8px" }}
                  >
                    Desmarcar
                  </button>
                </div>
              </div>

              <div style={{ position: "relative", marginBottom: 8 }}>
                <Search style={{ position: "absolute", left: 10, top: 10, width: 14, height: 14, color: "var(--an-muted)" }} />
                <input
                  type="text"
                  value={subjectSearch}
                  onChange={e => setSubjectSearch(e.target.value)}
                  placeholder="Buscar disciplina..."
                  className="app-input"
                  style={{ width: "100%", paddingLeft: 30 }}
                />
              </div>

              <div
                style={{
                  border: "1px solid var(--an-border)",
                  borderRadius: "var(--an-radius-sm)",
                  backgroundColor: "var(--an-bg)",
                  maxHeight: 180,
                  overflowY: "auto",
                  padding: 6,
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fill, minmax(180px, 1fr))",
                  gap: 4,
                }}
              >
                {filteredSubjects.map(subject => (
                  <label
                    key={subject.id}
                    style={{
                      display: "flex",
                      alignItems: "center",
                      gap: 8,
                      fontSize: 12,
                      padding: "5px 8px",
                      backgroundColor: "var(--an-surface)",
                      border: "1px solid var(--an-border)",
                      borderRadius: "var(--an-radius-sm)",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={newAllowedSubjects.includes(subject.id)}
                      onChange={() => handleToggleSubject(subject.id)}
                      style={{ accentColor: "var(--an-primary)" }}
                    />
                    <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                      {subject.name}
                    </span>
                  </label>
                ))}
                {filteredSubjects.length === 0 && (
                  <span style={{ fontSize: 12, color: "var(--an-muted)", padding: 8, gridColumn: "1 / -1" }}>
                    Nenhuma disciplina encontrada.
                  </span>
                )}
              </div>
            </div>

            {/* DISPONIBILIDADE HORÁRIA */}
            <div style={{ border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)", overflow: "hidden" }}>
              <button
                type="button"
                onClick={() => setAvailabilityExpanded(curr => !curr)}
                style={{
                  width: "100%",
                  padding: "10px 14px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  backgroundColor: "var(--an-surface-hover)",
                  border: "none",
                  cursor: "pointer",
                  color: "var(--an-text)",
                }}
              >
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <Clock3 style={{ width: 16, height: 16, color: "var(--an-primary)" }} />
                  <div style={{ textAlign: "left" }}>
                    <strong style={{ display: "block", fontSize: 13 }}>Matriz de Disponibilidade Semanal</strong>
                    <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)" }}>
                      {availablePeriodCount}/80 períodos disponíveis
                    </span>
                  </div>
                </div>
                {availabilityExpanded ? <ChevronUp style={{ width: 16, height: 16 }} /> : <ChevronDown style={{ width: 16, height: 16 }} />}
              </button>

              {availabilityExpanded && (
                <div style={{ padding: 12, backgroundColor: "var(--an-surface)", borderTop: "1px solid var(--an-border)" }}>
                  <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                    <button
                      type="button"
                      onClick={() => setAllAvailability(true)}
                      className="app-btn app-btn-secondary"
                      style={{ height: 26, fontSize: 11 }}
                    >
                      Disponível em tudo
                    </button>
                    <button
                      type="button"
                      onClick={() => setAllAvailability(false)}
                      className="app-btn app-btn-secondary"
                      style={{ height: 26, fontSize: 11 }}
                    >
                      Bloquear tudo
                    </button>
                  </div>

                  <div style={{ border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)", overflowX: "auto", maxHeight: 360 }}>
                    <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
                      <thead>
                        <tr style={{ backgroundColor: "var(--an-surface-hover)", borderBottom: "1px solid var(--an-border)" }}>
                          <th style={{ padding: "6px 8px", textAlign: "left", width: 100 }}>Horário</th>
                          {DAYS.map((day, dayIndex) => (
                            <th key={day} style={{ padding: 0, textAlign: "center" }}>
                              <button
                                type="button"
                                onClick={() => toggleWholeDay(dayIndex)}
                                title="Alternar dia inteiro"
                                style={{ width: "100%", padding: "6px 4px", background: "none", border: "none", cursor: "pointer", fontWeight: 600, color: "var(--an-text)" }}
                              >
                                {day.substring(0, 3)}
                              </button>
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {SHIFTS.map(shift => (
                          <React.Fragment key={shift.name}>
                            <tr style={{ backgroundColor: "var(--an-bg)", borderTop: "1px solid var(--an-border)", borderBottom: "1px solid var(--an-border)" }}>
                              <td colSpan={6} style={{ padding: "4px 8px" }}>
                                <button
                                  type="button"
                                  onClick={() => toggleWholeShift(shift.startIndex, shift.count)}
                                  style={{ background: "none", border: "none", cursor: "pointer", fontSize: 10, fontWeight: 700, textTransform: "uppercase", color: "var(--an-primary)", padding: 0 }}
                                  title="Alternar este turno na semana inteira"
                                >
                                  TURNO: {shift.name}
                                </button>
                              </td>
                            </tr>
                            {Array.from({ length: shift.count }).map((_, idx) => {
                              const periodIndex = shift.startIndex + idx;
                              return (
                                <tr key={periodIndex} style={{ borderBottom: "1px solid var(--an-border)" }}>
                                  <td className="font-mono" style={{ padding: "4px 8px", fontSize: 10, color: "var(--an-muted)", whiteSpace: "nowrap" }}>
                                    {PERIOD_NAMES[periodIndex]}
                                  </td>
                                  {DAYS.map((_, dayIndex) => {
                                    const isAvailable = newAvailability[dayIndex.toString()]?.[periodIndex];
                                    return (
                                      <td
                                        key={dayIndex}
                                        onClick={() => handleToggleAvailability(dayIndex, periodIndex)}
                                        style={{
                                          padding: 4,
                                          textAlign: "center",
                                          cursor: "pointer",
                                          backgroundColor: isAvailable ? "var(--an-success-soft)" : "var(--an-danger-soft)",
                                          borderLeft: "1px solid var(--an-border)",
                                        }}
                                      >
                                        <div style={{ display: "flex", justifyContent: "center" }}>
                                          {isAvailable ? (
                                            <CheckCircle style={{ width: 14, height: 14, color: "var(--an-success)" }} />
                                          ) : (
                                            <XCircle style={{ width: 14, height: 14, color: "var(--an-danger)" }} />
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
              )}
            </div>

            {formError && (
              <div className="app-alert app-alert-error" style={{ margin: 0 }}>
                {formError}
              </div>
            )}

            <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
              <button type="submit" className="app-btn app-btn-primary" style={{ flex: 1 }}>
                <Plus style={{ width: 15, height: 15 }} />
                <span>{editingTeacherId ? "Salvar Alterações" : "Adicionar Professor"}</span>
              </button>
              {editingTeacherId && (
                <button type="button" onClick={resetForm} className="app-btn app-btn-secondary">
                  <X style={{ width: 15, height: 15 }} />
                  <span>Cancelar</span>
                </button>
              )}
            </div>
          </form>
        </div>

        {/* LISTA DE PROFESSORES */}
        <div style={{ backgroundColor: "var(--an-surface)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-md)", padding: 18 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16, paddingBottom: 10, borderBottom: "1px solid var(--an-border)" }}>
            <h2 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Professores Cadastrados</h2>
            <span className="font-mono" style={{ fontSize: 12, fontWeight: 700, padding: "2px 8px", backgroundColor: "var(--an-surface-hover)", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)" }}>
              {teachers.length}
            </span>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 10, maxHeight: 720, overflowY: "auto" }}>
            {teachers.map(teacher => (
              <div
                key={teacher.id}
                style={{
                  border: "1px solid var(--an-border)",
                  borderRadius: "var(--an-radius-sm)",
                  padding: "10px 12px",
                  backgroundColor: "var(--an-bg)",
                  display: "flex",
                  flexDirection: "column",
                  gap: 8,
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
                  <div>
                    <strong style={{ fontSize: 14, color: "var(--an-text)", display: "block" }}>
                      {teacher.name}
                    </strong>
                    <div style={{ display: "flex", gap: 8, marginTop: 4, alignItems: "center" }}>
                      <span className="font-mono" style={{ fontSize: 11, padding: "2px 6px", border: "1px solid var(--an-border)", borderRadius: "var(--an-radius-sm)", backgroundColor: "var(--an-surface)" }}>
                        {teacher.score || 0} pts
                      </span>
                      <span className="font-mono" style={{ fontSize: 11, color: "var(--an-muted)" }}>
                        {availabilitySummary(teacher)}/80 períodos
                      </span>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: 4 }}>
                    <button
                      type="button"
                      onClick={() => handleEdit(teacher)}
                      className="app-btn app-btn-secondary"
                      style={{ width: 28, height: 28, padding: 0 }}
                      title="Editar professor"
                    >
                      <Edit style={{ width: 14, height: 14 }} />
                    </button>
                    <button
                      type="button"
                      onClick={() => handleDelete(teacher.id)}
                      className="app-btn app-btn-danger"
                      style={{ width: 28, height: 28, padding: 0 }}
                      title="Remover professor"
                    >
                      <Trash2 style={{ width: 14, height: 14 }} />
                    </button>
                  </div>
                </div>

                <div>
                  <span style={{ fontSize: 10, fontWeight: 600, color: "var(--an-muted)", textTransform: "uppercase", display: "block", marginBottom: 3 }}>
                    Disciplinas atribuídas
                  </span>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                    {teacher.allowed_subjects.map(sId => (
                      <span
                        key={sId}
                        style={{
                          fontSize: 11,
                          padding: "2px 6px",
                          backgroundColor: "var(--an-surface)",
                          border: "1px solid var(--an-border)",
                          borderRadius: "var(--an-radius-sm)",
                        }}
                      >
                        {subjects.find(s => s.id === sId)?.name || `ID ${sId}`}
                      </span>
                    ))}
                    {teacher.allowed_subjects.length === 0 && (
                      <span style={{ fontSize: 11, color: "var(--an-muted)" }}>Nenhuma</span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {teachers.length === 0 && (
              <div style={{ textAlign: "center", padding: 32, color: "var(--an-muted)" }}>
                <Users style={{ width: 32, height: 32, margin: "0 auto 8px", opacity: 0.4 }} />
                <p style={{ margin: 0, fontSize: 13 }}>Nenhum professor cadastrado ainda.</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
