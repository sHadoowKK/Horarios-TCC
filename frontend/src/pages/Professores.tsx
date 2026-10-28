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

const normalizeAvailabilityDay = (
  values?: boolean[],
) => {
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

  for (
    let i = 0;
    i < Math.min(values.length, 16);
    i++
  ) {
    normalized[i] = values[i];
  }

  return normalized;
};

const initialAvailability = () => {
  const availability: Record<string, boolean[]> = {};

  for (let day = 0; day < 5; day++) {
    availability[day.toString()] =
      Array(16).fill(true);
  }

  return availability;
};

const cloneAvailability = (
  availability: Record<string, boolean[]>,
) => {
  const result: Record<string, boolean[]> = {};

  for (let day = 0; day < 5; day++) {
    const key = day.toString();
    result[key] = normalizeAvailabilityDay(
      availability[key],
    );
  }

  return result;
};

export default function Professores() {
  const [teachers, setTeachers] =
    useState<Teacher[]>([]);
  const [subjects, setSubjects] =
    useState<Subject[]>([]);

  const [
    editingTeacherId,
    setEditingTeacherId,
  ] = useState<number | null>(null);

  const [newName, setNewName] = useState("");
  const [newScore, setNewScore] = useState(0);
  const [
    newAllowedSubjects,
    setNewAllowedSubjects,
  ] = useState<number[]>([]);
  const [
    newAvailability,
    setNewAvailability,
  ] = useState<Record<string, boolean[]>>(
    initialAvailability(),
  );

  const [subjectSearch, setSubjectSearch] =
    useState("");
  const [
    availabilityExpanded,
    setAvailabilityExpanded,
  ] = useState(false);
  const [formError, setFormError] = useState("");

  const fetchData = async () => {
    try {
      const [teacherResponse, subjectResponse] =
        await Promise.all([
          api.get("/teachers/"),
          api.get("/subjects/"),
        ]);

      setTeachers(teacherResponse.data);
      setSubjects(subjectResponse.data);
    } catch (error) {
      console.error(
        "Erro ao buscar dados:",
        error,
      );
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredSubjects = useMemo(() => {
    const query = subjectSearch
      .trim()
      .toLocaleLowerCase("pt-BR");

    if (!query) return subjects;

    return subjects.filter(subject =>
      subject.name
        .toLocaleLowerCase("pt-BR")
        .includes(query),
    );
  }, [subjects, subjectSearch]);

  const availablePeriodCount = useMemo(
    () =>
      Object.values(newAvailability).reduce(
        (total, day) =>
          total
          + day.filter(Boolean).length,
        0,
      ),
    [newAvailability],
  );

  const handleToggleSubject = (
    subjectId: number,
  ) => {
    setNewAllowedSubjects(current =>
      current.includes(subjectId)
        ? current.filter(id => id !== subjectId)
        : [...current, subjectId],
    );
  };

  const selectVisibleSubjects = () => {
    setNewAllowedSubjects(current =>
      Array.from(
        new Set([
          ...current,
          ...filteredSubjects.map(
            subject => subject.id,
          ),
        ]),
      ),
    );
  };

  const clearVisibleSubjects = () => {
    const visibleIds = new Set(
      filteredSubjects.map(
        subject => subject.id,
      ),
    );

    setNewAllowedSubjects(current =>
      current.filter(
        id => !visibleIds.has(id),
      ),
    );
  };

  const handleToggleAvailability = (
    dayIndex: number,
    periodIndex: number,
  ) => {
    const dayKey = dayIndex.toString();

    setNewAvailability(current => {
      const updatedDay = [
        ...normalizeAvailabilityDay(
          current[dayKey],
        ),
      ];

      updatedDay[periodIndex] =
        !updatedDay[periodIndex];

      return {
        ...current,
        [dayKey]: updatedDay,
      };
    });
  };

  const setAllAvailability = (
    available: boolean,
  ) => {
    const next: Record<string, boolean[]> = {};

    for (let day = 0; day < 5; day++) {
      next[day.toString()] =
        Array(16).fill(available);
    }

    setNewAvailability(next);
  };

  const toggleWholeDay = (
    dayIndex: number,
  ) => {
    const dayKey = dayIndex.toString();

    setNewAvailability(current => {
      const day = normalizeAvailabilityDay(
        current[dayKey],
      );
      const allAvailable =
        day.every(Boolean);

      return {
        ...current,
        [dayKey]: Array(16).fill(
          !allAvailable,
        ),
      };
    });
  };

  const toggleWholeShift = (
    shiftStart: number,
    shiftCount: number,
  ) => {
    setNewAvailability(current => {
      const next = cloneAvailability(current);

      const cells = [];

      for (let day = 0; day < 5; day++) {
        const dayKey = day.toString();

        for (
          let offset = 0;
          offset < shiftCount;
          offset++
        ) {
          cells.push(
            next[dayKey][
              shiftStart + offset
            ],
          );
        }
      }

      const allAvailable =
        cells.every(Boolean);
      const newValue = !allAvailable;

      for (let day = 0; day < 5; day++) {
        const dayKey = day.toString();

        for (
          let offset = 0;
          offset < shiftCount;
          offset++
        ) {
          next[dayKey][
            shiftStart + offset
          ] = newValue;
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
    setNewAvailability(
      initialAvailability(),
    );
    setSubjectSearch("");
    setAvailabilityExpanded(false);
    setFormError("");
  };

  const handleSaveTeacher = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();
    setFormError("");

    if (!newName.trim()) {
      setFormError(
        "Informe o nome do professor.",
      );
      return;
    }

    const payload = {
      name: newName.trim(),
      score: newScore,
      allowed_subjects:
        newAllowedSubjects,
      availability:
        cloneAvailability(
          newAvailability,
        ),
    };

    try {
      if (editingTeacherId) {
        await api.put(
          `/teachers/${editingTeacherId}`,
          payload,
        );
      } else {
        await api.post(
          "/teachers/",
          payload,
        );
      }

      resetForm();
      fetchData();
    } catch (error) {
      console.error(
        "Erro ao salvar professor",
        error,
      );
      setFormError(
        "Não foi possível salvar o professor.",
      );
    }
  };

  const handleEdit = (
    teacher: Teacher,
  ) => {
    setEditingTeacherId(teacher.id);
    setNewName(teacher.name);
    setNewScore(teacher.score || 0);
    setNewAllowedSubjects([
      ...teacher.allowed_subjects,
    ]);
    setNewAvailability(
      cloneAvailability(
        teacher.availability,
      ),
    );
    setSubjectSearch("");
    setAvailabilityExpanded(false);
    setFormError("");

    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  };

  const handleDelete = async (
    id: number,
  ) => {
    if (
      !confirm(
        "Tem certeza que deseja remover este professor?",
      )
    ) {
      return;
    }

    try {
      await api.delete(
        `/teachers/${id}`,
      );

      if (editingTeacherId === id) {
        resetForm();
      }

      fetchData();
    } catch (error) {
      console.error(
        "Erro ao remover professor",
        error,
      );
    }
  };

  const availabilitySummary = (
    teacher: Teacher,
  ) => {
    let available = 0;

    for (let day = 0; day < 5; day++) {
      available += normalizeAvailabilityDay(
        teacher.availability[
          day.toString()
        ],
      ).filter(Boolean).length;
    }

    return available;
  };

  return (
    <div className="app-view app-view-teachers p-8 max-w-7xl mx-auto">
      <h2 className="sr-only">Professores</h2>
      <div className="app-people-layout grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* FORMULÁRIO */}
        <div className="app-panel app-panel-form bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 text-gray-700">
            {editingTeacherId
              ? "Editar Professor"
              : "Cadastrar Novo Professor"}
          </h3>

          <form
            onSubmit={handleSaveTeacher}
            className="flex flex-col gap-6"
          >
            <div className="flex gap-4">
              <div className="flex-1">
                <label className="text-sm font-semibold text-gray-600 mb-1 block">
                  Nome do Professor
                </label>

                <input
                  type="text"
                  required
                  placeholder="Ex: João da Silva"
                  className="w-full border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={newName}
                  onChange={event =>
                    setNewName(
                      event.target.value,
                    )
                  }
                />
              </div>

              <div className="w-36">
                <label className="text-sm font-semibold text-gray-600 mb-1 flex items-center gap-1">
                  <Star className="w-4 h-4 text-yellow-500" />
                  Pontuação docente
                </label>

                <input
                  type="number"
                  min="0"
                  max="100"
                  className="w-full border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={newScore}
                  onChange={event =>
                    setNewScore(
                      Number(
                        event.target.value,
                      ),
                    )
                  }
                />

                <p className="text-[11px] text-gray-400 mt-1">
                  Maior pontuação = maior
                  prioridade quando houver mais
                  de um professor possível.
                </p>
              </div>
            </div>

            {/* DISCIPLINAS */}
            <div>
              <div className="flex justify-between gap-3 items-end mb-2">
                <div>
                  <label className="text-sm font-semibold text-gray-600 block">
                    Disciplinas que pode lecionar
                  </label>

                  <span className="text-xs text-gray-400">
                    {newAllowedSubjects.length}
                    {" "}
                    selecionada
                    {newAllowedSubjects.length === 1
                      ? ""
                      : "s"}
                  </span>
                </div>

                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={
                      selectVisibleSubjects
                    }
                    className="text-xs px-2 py-1 border border-indigo-200 bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100"
                  >
                    Selecionar visíveis
                  </button>

                  <button
                    type="button"
                    onClick={
                      clearVisibleSubjects
                    }
                    className="text-xs px-2 py-1 border border-gray-200 bg-white text-gray-600 rounded hover:bg-gray-100"
                  >
                    Limpar visíveis
                  </button>
                </div>
              </div>

              <div className="relative mb-2">
                <Search className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" />

                <input
                  type="text"
                  value={subjectSearch}
                  onChange={event =>
                    setSubjectSearch(
                      event.target.value,
                    )
                  }
                  placeholder="Buscar disciplina..."
                  className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="border border-gray-300 p-3 rounded-lg bg-gray-50 max-h-52 overflow-y-auto grid grid-cols-1 sm:grid-cols-2 gap-2">
                {filteredSubjects.map(
                  subject => (
                    <label
                      key={subject.id}
                      className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer bg-white p-2 border border-gray-200 rounded hover:bg-gray-50"
                    >
                      <input
                        type="checkbox"
                        checked={newAllowedSubjects.includes(
                          subject.id,
                        )}
                        onChange={() =>
                          handleToggleSubject(
                            subject.id,
                          )
                        }
                        className="accent-indigo-600"
                      />

                      <span className="truncate">
                        {subject.name}
                      </span>
                    </label>
                  ),
                )}

                {filteredSubjects.length === 0 && (
                  <span className="text-xs text-gray-400 col-span-2">
                    Nenhuma disciplina encontrada.
                  </span>
                )}
              </div>
            </div>

            {/* DISPONIBILIDADE */}
            <div className="border border-gray-200 rounded-xl overflow-hidden">
              <button
                type="button"
                onClick={() =>
                  setAvailabilityExpanded(
                    current => !current,
                  )
                }
                className="w-full p-4 flex items-center justify-between gap-3 bg-gray-50 hover:bg-gray-100 text-left"
              >
                <span className="flex items-center gap-2">
                  <Clock3 className="w-5 h-5 text-indigo-500" />

                  <span>
                    <strong className="text-sm text-gray-700 block">
                      Disponibilidade de Horário
                    </strong>

                    <span className="text-xs text-gray-500">
                      {availablePeriodCount}/80
                      períodos disponíveis
                    </span>
                  </span>
                </span>

                {availabilityExpanded ? (
                  <ChevronUp className="w-5 h-5 text-gray-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-gray-500" />
                )}
              </button>

              {availabilityExpanded && (
                <div className="p-4">
                  <p className="text-xs text-gray-500 mb-3">
                    Desmarque quando o professor
                    não puder trabalhar aqui,
                    inclusive por estar em outra
                    escola. Clique no nome de um
                    dia para liberar/bloquear o
                    dia inteiro; clique no nome
                    de um turno para aplicar o
                    turno à semana inteira.
                  </p>

                  <div className="flex flex-wrap gap-2 mb-3">
                    <button
                      type="button"
                      onClick={() =>
                        setAllAvailability(true)
                      }
                      className="text-xs px-3 py-1.5 rounded border border-green-200 bg-green-50 text-green-700 hover:bg-green-100"
                    >
                      Tudo disponível
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setAllAvailability(false)
                      }
                      className="text-xs px-3 py-1.5 rounded border border-red-200 bg-red-50 text-red-700 hover:bg-red-100"
                    >
                      Bloquear tudo
                    </button>
                  </div>

                  <div className="border border-gray-300 rounded-lg overflow-hidden max-h-[430px] overflow-y-auto">
                    <table className="w-full text-sm text-center bg-white relative">
                      <thead className="bg-gray-100 text-gray-600 font-medium sticky top-0 z-10">
                        <tr>
                          <th className="p-2 border-r border-b">
                            Horário
                          </th>

                          {DAYS.map(
                            (day, dayIndex) => (
                              <th
                                key={day}
                                className="p-0 border-b"
                              >
                                <button
                                  type="button"
                                  onClick={() =>
                                    toggleWholeDay(
                                      dayIndex,
                                    )
                                  }
                                  title="Liberar ou bloquear o dia inteiro"
                                  className="w-full p-2 hover:bg-gray-200"
                                >
                                  {day.substring(
                                    0,
                                    3,
                                  )}
                                </button>
                              </th>
                            ),
                          )}
                        </tr>
                      </thead>

                      <tbody>
                        {SHIFTS.map(
                          shift => (
                            <React.Fragment
                              key={shift.name}
                            >
                              <tr className="bg-indigo-50">
                                <td
                                  colSpan={6}
                                  className="p-0 border-y"
                                >
                                  <button
                                    type="button"
                                    onClick={() =>
                                      toggleWholeShift(
                                        shift.startIndex,
                                        shift.count,
                                      )
                                    }
                                    className="w-full p-1.5 font-bold text-indigo-800 text-left pl-3 text-xs hover:bg-indigo-100"
                                    title="Liberar ou bloquear este turno na semana inteira"
                                  >
                                    TURNO:{" "}
                                    {shift.name.toUpperCase()}
                                  </button>
                                </td>
                              </tr>

                              {Array.from({
                                length:
                                  shift.count,
                              }).map(
                                (_, index) => {
                                  const periodIndex =
                                    shift.startIndex
                                    + index;

                                  return (
                                    <tr
                                      key={
                                        periodIndex
                                      }
                                      className="border-b last:border-0 hover:bg-gray-50"
                                    >
                                      <td className="p-1 border-r text-left font-medium text-gray-700 text-xs pl-3 whitespace-nowrap">
                                        {
                                          PERIOD_NAMES[
                                            periodIndex
                                          ]
                                        }
                                      </td>

                                      {DAYS.map(
                                        (
                                          _,
                                          dayIndex,
                                        ) => {
                                          const dayAvailability =
                                            newAvailability[
                                              dayIndex.toString()
                                            ];
                                          const isAvailable =
                                            dayAvailability
                                              ? dayAvailability[
                                                  periodIndex
                                                ]
                                              : false;

                                          return (
                                            <td
                                              key={
                                                dayIndex
                                              }
                                              className={`p-1 cursor-pointer ${
                                                isAvailable
                                                  ? "bg-green-50 hover:bg-green-100"
                                                  : "bg-red-50 hover:bg-red-100"
                                              }`}
                                              onClick={() =>
                                                handleToggleAvailability(
                                                  dayIndex,
                                                  periodIndex,
                                                )
                                              }
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
                                        },
                                      )}
                                    </tr>
                                  );
                                },
                              )}
                            </React.Fragment>
                          ),
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            {formError && (
              <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
                {formError}
              </div>
            )}

            <div className="flex gap-2 mt-auto pt-2">
              <button
                type="submit"
                className="flex-1 bg-indigo-600 text-white p-3 rounded-lg hover:bg-indigo-700 flex items-center justify-center gap-2 font-medium"
              >
                <Plus className="w-5 h-5" />
                {editingTeacherId
                  ? "Salvar Alterações"
                  : "Adicionar Professor"}
              </button>

              {editingTeacherId && (
                <button
                  type="button"
                  onClick={resetForm}
                  className="secondary-action-button p-3 rounded-lg flex items-center justify-center gap-2 font-medium"
                >
                  <X className="w-5 h-5" />
                  Cancelar
                </button>
              )}
            </div>
          </form>
        </div>

        {/* LISTA DE PROFESSORES */}
        <div className="app-panel app-panel-list bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 text-gray-700 flex items-center justify-between">
            Professores Cadastrados

            <span className="bg-indigo-100 text-indigo-700 text-sm py-1 px-3 rounded-full font-bold">
              {teachers.length}
            </span>
          </h3>

          <ul className="app-record-list">
            {teachers.map(teacher => (
              <li
                key={teacher.id}
                className="p-4 bg-gray-50 border border-gray-200 rounded-lg flex flex-col gap-3"
              >
                <div className="flex justify-between items-start border-b border-gray-200 pb-2">
                  <div>
                    <strong className="text-gray-800 text-lg block">
                      {teacher.name}
                    </strong>

                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="text-xs text-yellow-700 bg-yellow-100 px-2 py-1 rounded-full inline-flex items-center gap-1 font-bold">
                        <Star className="w-3 h-3" />
                        {teacher.score || 0} pts
                      </span>

                      <span className="text-xs text-indigo-700 bg-indigo-100 px-2 py-1 rounded-full">
                        {availabilitySummary(
                          teacher,
                        )}
                        /80 períodos
                      </span>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <button
                      onClick={() =>
                        handleEdit(teacher)
                      }
                      className="p-2 text-indigo-600 hover:bg-indigo-100 rounded-lg"
                      title="Editar"
                    >
                      <Edit className="w-4 h-4" />
                    </button>

                    <button
                      onClick={() =>
                        handleDelete(
                          teacher.id,
                        )
                      }
                      className="p-2 text-red-600 hover:bg-red-100 rounded-lg"
                      title="Remover"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                <div>
                  <strong className="text-xs text-gray-500 uppercase mb-1 block">
                    Disciplinas Permitidas
                  </strong>

                  <div className="flex flex-wrap gap-1">
                    {teacher.allowed_subjects.map(
                      subjectId => (
                        <span
                          key={subjectId}
                          className="bg-indigo-100 text-indigo-700 text-xs px-2 py-1 rounded"
                        >
                          {subjects.find(
                            subject =>
                              subject.id
                              === subjectId,
                          )?.name
                            || `ID ${subjectId}`}
                        </span>
                      ),
                    )}

                    {teacher.allowed_subjects
                      .length === 0 && (
                      <span className="text-xs text-gray-400">
                        Nenhuma
                      </span>
                    )}
                  </div>
                </div>

                <div>
                  <strong className="text-xs text-gray-500 uppercase mb-1 block">
                    Dias Disponíveis
                  </strong>

                  <div className="flex gap-2">
                    {DAYS.map(
                      (day, dayIndex) => {
                        const dayAvailability =
                          normalizeAvailabilityDay(
                            teacher.availability[
                              dayIndex.toString()
                            ],
                          );

                        const availableCount =
                          dayAvailability.filter(
                            Boolean,
                          ).length;

                        return (
                          <span
                            key={day}
                            title={`${day}: ${availableCount}/16 períodos disponíveis`}
                            className={`text-xs font-bold px-2 py-1 rounded-full min-w-10 text-center ${
                              availableCount > 0
                                ? "bg-green-100 text-green-700"
                                : "bg-gray-200 text-gray-400"
                            }`}
                          >
                            {day.substring(
                              0,
                              3,
                            )}
                            {" "}
                            {availableCount}
                          </span>
                        );
                      },
                    )}
                  </div>
                </div>
              </li>
            ))}

            {teachers.length === 0 && (
              <div className="flex flex-col items-center justify-center h-40 text-gray-400">
                <Users className="w-12 h-12 mb-2 opacity-50" />
                <p>
                  Nenhum professor cadastrado ainda.
                </p>
              </div>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
