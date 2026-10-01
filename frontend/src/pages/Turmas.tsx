import { useEffect, useState } from "react";
import { api } from "../api";
import {
  BookOpen,
  ChevronDown,
  ChevronUp,
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
  split: boolean;
}

interface Classroom {
  id: number;
  name: string;
  shift: string;
  course_id: number;
  has_groups: boolean;
  subject_settings: ClassroomSubjectSetting[];
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

export default function Turmas() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [expandedClassrooms, setExpandedClassrooms] =
    useState<Set<number>>(new Set());
  const [copySourceByClassroom, setCopySourceByClassroom] =
    useState<Record<number, string>>({});

  const [newCourseName, setNewCourseName] = useState("");
  const [editingCourseId, setEditingCourseId] =
    useState<number | null>(null);
  const [editingCourseName, setEditingCourseName] =
    useState("");

  const [editingClassroomId, setEditingClassroomId] =
    useState<number | null>(null);
  const [classroomDraft, setClassroomDraft] = useState({
    name: "",
    shift: "Manhã",
    course_id: 0,
  });

  const [editingSubjectId, setEditingSubjectId] =
    useState<number | null>(null);
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
  const [newClassHasGroups, setNewClassHasGroups] =
    useState(false);

  const [newSubName, setNewSubName] = useState("");
  const [newSubWorkload, setNewSubWorkload] = useState(4);
  const [newSubComplexity, setNewSubComplexity] =
    useState("Media");
  const [newSubCourseIds, setNewSubCourseIds] =
    useState<number[]>([]);

  const fetchData = async () => {
    try {
      const [courseRes, classroomRes, subjectRes] =
        await Promise.all([
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

  const handleAddCourse = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();

    if (!newCourseName.trim()) return;

    await api.post("/courses/", {
      name: newCourseName,
    });

    setNewCourseName("");
    fetchData();
  };

  const startCourseEdit = (
    course: Course,
  ) => {
    setEditingCourseId(course.id);
    setEditingCourseName(course.name);
  };

  const saveCourseEdit = async (
    course: Course,
  ) => {
    const name = editingCourseName.trim();
    if (!name) return;

    await api.put(
      `/courses/${course.id}`,
      { name },
    );

    setEditingCourseId(null);
    setEditingCourseName("");
    fetchData();
  };

  const startClassroomEdit = (
    classroom: Classroom,
  ) => {
    setEditingClassroomId(classroom.id);
    setClassroomDraft({
      name: classroom.name,
      shift: classroom.shift,
      course_id: classroom.course_id,
    });
  };

  const saveClassroomEdit = async (
    classroom: Classroom,
  ) => {
    const name = classroomDraft.name.trim();
    if (!name || !classroomDraft.course_id) {
      return;
    }

    const validSubjectIds = new Set(
      subjects
        .filter(subject =>
          subject.course_ids?.includes(
            classroomDraft.course_id,
          ),
        )
        .map(subject => subject.id),
    );

    await saveClassroom(classroom, {
      name,
      shift: classroomDraft.shift,
      course_id: classroomDraft.course_id,
      subject_settings: (
        classroom.subject_settings || []
      ).filter(setting =>
        validSubjectIds.has(
          setting.subject_id,
        ),
      ),
    });

    setEditingClassroomId(null);
  };

  const startSubjectEdit = (
    subject: Subject,
  ) => {
    setEditingSubjectId(subject.id);
    setSubjectDraft({
      name: subject.name,
      workload: subject.workload,
      complexity: subject.complexity,
      course_ids: [
        ...(subject.course_ids || []),
      ],
    });
  };

  const saveSubjectEdit = async (
    subject: Subject,
  ) => {
    const name = subjectDraft.name.trim();

    if (
      !name
      || subjectDraft.course_ids.length === 0
    ) {
      alert(
        "Informe o nome e mantenha pelo menos um curso associado.",
      );
      return;
    }

    await api.put(
      `/subjects/${subject.id}`,
      {
        name,
        workload: Math.max(
          1,
          Math.round(
            Number(subjectDraft.workload),
          ),
        ),
        complexity:
          subjectDraft.complexity,
        // Campo legado mantido apenas para compatibilidade do backend.
        category: subject.category || "Ensino Médio",
        course_ids:
          subjectDraft.course_ids,
      },
    );

    setEditingSubjectId(null);
    fetchData();
  };

  const handleDeleteCourse = async (
    course: Course,
  ) => {
    if (
      !confirm(
        `Remover o curso "${course.name}"?`,
      )
    ) {
      return;
    }

    try {
      await api.delete(
        `/courses/${course.id}`,
      );
      fetchData();
    } catch (error: any) {
      alert(
        error.response?.data?.detail
        || "Não foi possível remover o curso.",
      );
    }
  };

  const handleDeleteClassroom = async (
    classroom: Classroom,
  ) => {
    if (
      !confirm(
        `Remover a turma "${classroom.name}" e os horários salvos dela?`,
      )
    ) {
      return;
    }

    try {
      await api.delete(
        `/classrooms/${classroom.id}`,
      );

      setExpandedClassrooms(current => {
        const next = new Set(current);
        next.delete(classroom.id);
        return next;
      });

      fetchData();
    } catch (error: any) {
      alert(
        error.response?.data?.detail
        || "Não foi possível remover a turma.",
      );
    }
  };

  const handleDeleteSubject = async (
    subject: Subject,
  ) => {
    if (
      !confirm(
        `Remover a disciplina "${subject.name}"? Ela será retirada das turmas e dos professores que a utilizam.`,
      )
    ) {
      return;
    }

    try {
      await api.delete(
        `/subjects/${subject.id}`,
      );
      fetchData();
    } catch (error: any) {
      alert(
        error.response?.data?.detail
        || "Não foi possível remover a disciplina.",
      );
    }
  };

  const handleAddClassroom = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();

    if (!newClassName.trim() || !newClassCourseId) {
      return;
    }

    await api.post("/classrooms/", {
      name: newClassName,
      shift: newClassShift,
      course_id: Number(newClassCourseId),
      has_groups: newClassHasGroups,
      subject_settings: [],
      split_subject_ids: [],
    });

    setNewClassName("");
    setNewClassHasGroups(false);
    fetchData();
  };

  const saveClassroom = async (
    classroom: Classroom,
    changes: Partial<Classroom>,
  ) => {
    await api.put(
      `/classrooms/${classroom.id}`,
      {
        name: changes.name ?? classroom.name,
        shift: changes.shift ?? classroom.shift,
        course_id:
          changes.course_id ?? classroom.course_id,
        has_groups:
          changes.has_groups ?? classroom.has_groups,
        subject_settings:
          changes.subject_settings
          ?? classroom.subject_settings
          ?? [],
        split_subject_ids:
          changes.split_subject_ids
          ?? classroom.split_subject_ids
          ?? [],
      },
    );

    fetchData();
  };

  const toggleClassroomDetails = (
    classroomId: number,
  ) => {
    setExpandedClassrooms(current => {
      const next = new Set(current);

      if (next.has(classroomId)) {
        next.delete(classroomId);
      } else {
        next.add(classroomId);
      }

      return next;
    });
  };

  const handleToggleClassGroups = async (
    classroom: Classroom,
  ) => {
    await saveClassroom(classroom, {
      has_groups: !classroom.has_groups,
    });
  };

  const subjectsForClassroom = (
    classroom: Classroom,
  ) =>
    subjects.filter(subject =>
      subject.course_ids?.includes(classroom.course_id),
    );

  const settingFor = (
    classroom: Classroom,
    subjectId: number,
  ) =>
    (classroom.subject_settings || []).find(
      setting => setting.subject_id === subjectId,
    );

  const handleToggleClassSubject = async (
    classroom: Classroom,
    subject: Subject,
  ) => {
    const current = classroom.subject_settings || [];
    const existing = settingFor(
      classroom,
      subject.id,
    );

    const next = existing
      ? current.filter(
          setting =>
            setting.subject_id !== subject.id,
        )
      : [
          ...current,
          {
            subject_id: subject.id,
            workload: subject.workload,
            split: false,
          },
        ];

    await saveClassroom(classroom, {
      subject_settings: next,
    });
  };

  const handleSubjectWorkload = async (
    classroom: Classroom,
    subjectId: number,
    workload: number,
  ) => {
    if (!Number.isFinite(workload)) return;

    const safeWorkload = Math.min(
      Math.max(Math.round(workload), 1),
      25,
    );

    const next = (
      classroom.subject_settings || []
    ).map(setting =>
      setting.subject_id === subjectId
        ? {
            ...setting,
            workload: safeWorkload,
          }
        : setting,
    );

    await saveClassroom(classroom, {
      subject_settings: next,
    });
  };

  const handleSubjectSplit = async (
    classroom: Classroom,
    subjectId: number,
    split: boolean,
  ) => {
    const next = (
      classroom.subject_settings || []
    ).map(setting =>
      setting.subject_id === subjectId
        ? {
            ...setting,
            split,
          }
        : setting,
    );

    await saveClassroom(classroom, {
      subject_settings: next,
    });
  };

  const handleUseAllSubjects = async (
    classroom: Classroom,
  ) => {
    const candidates = subjectsForClassroom(
      classroom,
    );
    const current = classroom.subject_settings || [];

    const next = candidates.map(subject => {
      const existing = current.find(
        setting =>
          setting.subject_id === subject.id,
      );

      return (
        existing || {
          subject_id: subject.id,
          workload: subject.workload,
          split: false,
        }
      );
    });

    await saveClassroom(classroom, {
      subject_settings: next,
    });
  };

  const handleClearSubjects = async (
    classroom: Classroom,
  ) => {
    await saveClassroom(classroom, {
      subject_settings: [],
    });
  };

  const handleCopySubjects = async (
    targetClassroom: Classroom,
  ) => {
    const sourceId = Number(
      copySourceByClassroom[targetClassroom.id],
    );

    const sourceClassroom = classrooms.find(
      item => item.id === sourceId,
    );

    if (!sourceClassroom) return;

    if (
      (targetClassroom.subject_settings || []).length > 0
      && !confirm(
        `Substituir as matérias de ${targetClassroom.name} pelas configurações de ${sourceClassroom.name}?`,
      )
    ) {
      return;
    }

    const validSubjectIds = new Set(
      subjectsForClassroom(targetClassroom).map(
        subject => subject.id,
      ),
    );

    const copiedSettings = (
      sourceClassroom.subject_settings || []
    )
      .filter(setting =>
        validSubjectIds.has(setting.subject_id),
      )
      .map(setting => ({
        ...setting,
        split:
          targetClassroom.has_groups
            ? setting.split
            : false,
      }));

    await saveClassroom(targetClassroom, {
      subject_settings: copiedSettings,
    });

    setCopySourceByClassroom(current => ({
      ...current,
      [targetClassroom.id]: "",
    }));
  };

  const handleAddSubject = async (
    event: React.FormEvent,
  ) => {
    event.preventDefault();

    if (
      !newSubName.trim()
      || newSubCourseIds.length === 0
    ) {
      return;
    }

    await api.post("/subjects/", {
      name: newSubName,
      workload: Number(newSubWorkload),
      complexity: newSubComplexity,
      // Categoria não participa mais das regras; fica apenas como legado.
      category: "Ensino Médio",
      course_ids: newSubCourseIds,
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
            <School className="w-5 h-5 text-blue-500" />
            Cursos
          </h3>

          <form
            onSubmit={handleAddCourse}
            className="mb-6 flex gap-2"
          >
            <input
              type="text"
              required
              placeholder="Nome do Curso"
              className="flex-1 border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={newCourseName}
              onChange={event =>
                setNewCourseName(event.target.value)
              }
            />

            <button
              type="submit"
              className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-5 h-5" />
            </button>
          </form>

          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[520px] pr-2">
            {courses.map(course => (
              <li
                key={course.id}
                className="p-3 bg-gray-50 border border-gray-100 rounded-lg"
              >
                {editingCourseId === course.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      value={editingCourseName}
                      onChange={event =>
                        setEditingCourseName(
                          event.target.value,
                        )
                      }
                      className="min-w-0 flex-1 border border-gray-300 rounded p-1.5"
                      autoFocus
                    />

                    <button
                      type="button"
                      onClick={() =>
                        saveCourseEdit(course)
                      }
                      className="p-1.5 text-emerald-600 hover:bg-emerald-100 rounded"
                      title="Salvar"
                    >
                      <Save className="w-4 h-4" />
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        setEditingCourseId(null)
                      }
                      className="p-1.5 text-gray-500 hover:bg-gray-200 rounded"
                      title="Cancelar"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>
                ) : (
                  <div className="flex justify-between items-center gap-2">
                    <span className="font-medium text-gray-800 flex-1 min-w-0 truncate">
                      {course.name}
                    </span>

                    <span className="text-xs text-gray-400 bg-gray-200 px-2 py-1 rounded-full">
                      ID: {course.id}
                    </span>

                    <button
                      type="button"
                      onClick={() =>
                        startCourseEdit(course)
                      }
                      className="p-1.5 text-indigo-600 hover:bg-indigo-100 rounded"
                      title="Editar curso"
                    >
                      <Edit className="w-4 h-4" />
                    </button>

                    <button
                      type="button"
                      onClick={() =>
                        handleDeleteCourse(course)
                      }
                      className="p-1.5 text-red-600 hover:bg-red-100 rounded"
                      title="Remover curso"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </li>
            ))}

            {courses.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                Nenhum curso cadastrado.
              </p>
            )}
          </ul>
        </div>

        {/* TURMAS */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <Layers className="w-5 h-5 text-emerald-500" />
            Turmas
          </h3>

          <form
            onSubmit={handleAddClassroom}
            className="mb-6 flex flex-col gap-3"
          >
            <input
              type="text"
              required
              placeholder="Nome da Turma (ex: 3º INFO)"
              className="border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              value={newClassName}
              onChange={event =>
                setNewClassName(event.target.value)
              }
            />

            <div className="flex gap-2">
              <select
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={newClassShift}
                onChange={event =>
                  setNewClassShift(event.target.value)
                }
              >
                <option value="Manhã">
                  Manhã
                </option>
                <option value="Integral">
                  Integral
                </option>
                <option value="Noite">
                  Noite
                </option>
              </select>

              <select
                required
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={newClassCourseId}
                onChange={event =>
                  setNewClassCourseId(
                    event.target.value,
                  )
                }
              >
                <option value="" disabled>
                  Selecione o Curso
                </option>

                {courses.map(course => (
                  <option
                    key={course.id}
                    value={course.id}
                  >
                    {course.name}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-3 cursor-pointer">
              <input
                type="checkbox"
                checked={newClassHasGroups}
                onChange={event =>
                  setNewClassHasGroups(
                    event.target.checked,
                  )
                }
                className="accent-emerald-600"
              />
              Esta turma utiliza Grupos A/B
            </label>

            <button
              type="submit"
              className="bg-emerald-600 text-white p-2 rounded-lg hover:bg-emerald-700 flex items-center justify-center gap-1 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Adicionar Turma
            </button>
          </form>

          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[600px] pr-2">
            {classrooms.map(classroom => {
              const candidates =
                subjectsForClassroom(classroom);
              const selectedCount =
                classroom.subject_settings?.length || 0;
              const copySources = classrooms.filter(
                other =>
                  other.id !== classroom.id
                  && other.course_id === classroom.course_id
                  && (other.subject_settings || []).length > 0,
              );

              return (
                <li
                  key={classroom.id}
                  className="p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm flex flex-col gap-2"
                >
                  {editingClassroomId === classroom.id ? (
                    <div className="space-y-2 rounded-lg border border-emerald-200 bg-white p-2">
                      <input
                        value={classroomDraft.name}
                        onChange={event =>
                          setClassroomDraft(current => ({
                            ...current,
                            name: event.target.value,
                          }))
                        }
                        className="w-full border border-gray-300 rounded p-1.5"
                        placeholder="Nome da turma"
                      />

                      <div className="flex gap-2">
                        <select
                          value={classroomDraft.shift}
                          onChange={event =>
                            setClassroomDraft(current => ({
                              ...current,
                              shift: event.target.value,
                            }))
                          }
                          className="min-w-0 flex-1 border border-gray-300 rounded p-1.5 bg-white"
                        >
                          <option value="Manhã">Manhã</option>
                          <option value="Integral">Integral</option>
                          <option value="Noite">Noite</option>
                        </select>

                        <select
                          value={classroomDraft.course_id}
                          onChange={event =>
                            setClassroomDraft(current => ({
                              ...current,
                              course_id: Number(
                                event.target.value,
                              ),
                            }))
                          }
                          className="min-w-0 flex-1 border border-gray-300 rounded p-1.5 bg-white"
                        >
                          {courses.map(course => (
                            <option
                              key={course.id}
                              value={course.id}
                            >
                              {course.name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() =>
                            saveClassroomEdit(
                              classroom,
                            )
                          }
                          className="text-xs px-2 py-1 rounded bg-emerald-600 text-white hover:bg-emerald-700"
                        >
                          Salvar
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            setEditingClassroomId(
                              null,
                            )
                          }
                          className="text-xs px-2 py-1 rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-100"
                        >
                          Cancelar
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex justify-between gap-2 items-start">
                      <strong className="text-gray-800 text-base flex-1 min-w-0 truncate">
                        {classroom.name}
                      </strong>

                      <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">
                        {classroom.shift}
                      </span>

                      <button
                        type="button"
                        onClick={() =>
                          startClassroomEdit(
                            classroom,
                          )
                        }
                        className="p-1 text-indigo-600 hover:bg-indigo-100 rounded"
                        title="Editar turma"
                      >
                        <Edit className="w-4 h-4" />
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          handleDeleteClassroom(
                            classroom,
                          )
                        }
                        className="p-1 text-red-600 hover:bg-red-100 rounded"
                        title="Remover turma"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  )}

                  <div className="text-xs text-emerald-600 font-medium">
                    Curso:{" "}
                    {courses.find(
                      course =>
                        course.id
                        === classroom.course_id,
                    )?.name || classroom.course_id}
                  </div>

                  <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={classroom.has_groups}
                      onChange={() =>
                        handleToggleClassGroups(
                          classroom,
                        )
                      }
                      className="accent-emerald-600"
                    />
                    Turma possui Grupos A/B
                  </label>

                  <div className="mt-1 border-t border-gray-200 pt-2">
                    <button
                      type="button"
                      onClick={() =>
                        toggleClassroomDetails(
                          classroom.id,
                        )
                      }
                      className="w-full flex items-center justify-between gap-2 text-left text-[11px] font-bold uppercase tracking-wide text-gray-500 hover:text-gray-700 transition-colors"
                    >
                      <span>
                        Matérias da turma
                        {" "}
                        ({selectedCount}/{candidates.length})
                      </span>

                      {expandedClassrooms.has(
                        classroom.id,
                      ) ? (
                        <ChevronUp className="w-4 h-4 shrink-0" />
                      ) : (
                        <ChevronDown className="w-4 h-4 shrink-0" />
                      )}
                    </button>

                    {expandedClassrooms.has(
                      classroom.id,
                    ) && (
                      <div className="mt-3 space-y-3">
                        {copySources.length > 0 && (
                          <div className="flex gap-2">
                            <select
                              value={
                                copySourceByClassroom[
                                  classroom.id
                                ] || ""
                              }
                              onChange={event =>
                                setCopySourceByClassroom(
                                  current => ({
                                    ...current,
                                    [classroom.id]:
                                      event.target.value,
                                  }),
                                )
                              }
                              className="min-w-0 flex-1 text-[11px] border border-gray-300 rounded p-1.5 bg-white"
                            >
                              <option value="">
                                Copiar matérias de...
                              </option>

                              {copySources.map(source => (
                                <option
                                  key={source.id}
                                  value={source.id}
                                >
                                  {source.name}
                                </option>
                              ))}
                            </select>

                            <button
                              type="button"
                              disabled={
                                !copySourceByClassroom[
                                  classroom.id
                                ]
                              }
                              onClick={() =>
                                handleCopySubjects(
                                  classroom,
                                )
                              }
                              className="text-[11px] px-2 py-1 rounded border border-blue-200 bg-blue-50 text-blue-700 hover:bg-blue-100 disabled:opacity-40 disabled:cursor-not-allowed"
                            >
                              Copiar
                            </button>
                          </div>
                        )}

                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() =>
                              handleUseAllSubjects(
                                classroom,
                              )
                            }
                            className="text-[11px] px-2 py-1 rounded border border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
                          >
                            Usar todas
                          </button>

                          <button
                            type="button"
                            onClick={() =>
                              handleClearSubjects(
                                classroom,
                              )
                            }
                            className="text-[11px] px-2 py-1 rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-100"
                          >
                            Limpar
                          </button>
                        </div>

                        {candidates.map(subject => {
                          const setting = settingFor(
                            classroom,
                            subject.id,
                          );
                          const selected = Boolean(
                            setting,
                          );

                          return (
                            <div
                              key={subject.id}
                              className={`rounded-lg border p-2 ${
                                selected
                                  ? "bg-white border-emerald-200"
                                  : "bg-gray-100 border-gray-200"
                              }`}
                            >
                              <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                  type="checkbox"
                                  checked={selected}
                                  onChange={() =>
                                    handleToggleClassSubject(
                                      classroom,
                                      subject,
                                    )
                                  }
                                  className="accent-emerald-600"
                                />

                                <span className="text-xs font-medium text-gray-700 flex-1">
                                  {subject.name}
                                </span>

                                <span className="text-[10px] text-gray-400">
                                  {subject.category}
                                </span>
                              </label>

                              {setting && (
                                <div className="grid grid-cols-1 gap-2 mt-2 pl-5">
                                  <label className="flex items-center justify-between gap-2 text-[11px] text-gray-500">
                                    <span>
                                      Aulas por semana
                                    </span>

                                    <input
                                      key={`${classroom.id}-${subject.id}-${setting.workload}`}
                                      type="number"
                                      min="1"
                                      max="25"
                                      defaultValue={
                                        setting.workload
                                      }
                                      onBlur={event =>
                                        handleSubjectWorkload(
                                          classroom,
                                          subject.id,
                                          Number(
                                            event.target.value,
                                          ),
                                        )
                                      }
                                      className="w-16 border border-gray-300 rounded p-1 text-center bg-white"
                                    />
                                  </label>

                                  {classroom.has_groups && (
                                    <label className="flex items-center justify-between gap-2 text-[11px] text-gray-500">
                                      <span>
                                        Organização
                                      </span>

                                      <select
                                        value={
                                          setting.split
                                            ? "split"
                                            : "all"
                                        }
                                        onChange={event =>
                                          handleSubjectSplit(
                                            classroom,
                                            subject.id,
                                            event.target.value
                                              === "split",
                                          )
                                        }
                                        className="border border-gray-300 rounded p-1 bg-white"
                                      >
                                        <option value="all">
                                          Turma inteira
                                        </option>
                                        <option value="split">
                                          Separada A/B
                                        </option>
                                      </select>
                                    </label>
                                  )}
                                </div>
                              )}
                            </div>
                          );
                        })}

                        {candidates.length === 0 && (
                          <p className="text-xs text-gray-400">
                            Nenhuma disciplina foi associada
                            a este curso ainda.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                </li>
              );
            })}

            {classrooms.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                Nenhuma turma cadastrada.
              </p>
            )}
          </ul>
        </div>

        {/* DISCIPLINAS */}
        <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm flex flex-col h-full">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-gray-700">
            <BookOpen className="w-5 h-5 text-purple-500" />
            Disciplinas
          </h3>

          <form
            onSubmit={handleAddSubject}
            className="mb-6 flex flex-col gap-3"
          >
            <input
              type="text"
              required
              placeholder="Nome (ex: Matemática)"
              className="border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500"
              value={newSubName}
              onChange={event =>
                setNewSubName(event.target.value)
              }
            />

            <div className="flex gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase">
                  Aulas/Sem padrão
                </label>

                <input
                  type="number"
                  min="1"
                  required
                  className="border border-gray-300 p-2 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={newSubWorkload}
                  onChange={event =>
                    setNewSubWorkload(
                      Number(event.target.value),
                    )
                  }
                />
              </div>

              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase">
                  Complexidade
                </label>

                <select
                  className="border border-gray-300 p-2 rounded-lg w-full bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={newSubComplexity}
                  onChange={event =>
                    setNewSubComplexity(
                      event.target.value,
                    )
                  }
                >
                  <option value="Alta">
                    Alta
                  </option>
                  <option value="Media">
                    Média
                  </option>
                  <option value="Baixa">
                    Baixa
                  </option>
                </select>
              </div>
            </div>

            <div className="border border-gray-300 p-2 rounded-lg bg-white max-h-32 overflow-y-auto flex flex-col gap-1">
              <label className="text-xs font-semibold text-gray-500 uppercase mb-1">
                Cursos Associados
              </label>

              {courses.map(course => (
                <label
                  key={course.id}
                  className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={newSubCourseIds.includes(
                      course.id,
                    )}
                    onChange={event => {
                      if (event.target.checked) {
                        setNewSubCourseIds([
                          ...newSubCourseIds,
                          course.id,
                        ]);
                      } else {
                        setNewSubCourseIds(
                          newSubCourseIds.filter(
                            id => id !== course.id,
                          ),
                        );
                      }
                    }}
                  />
                  {course.name}
                </label>
              ))}

              {courses.length === 0 && (
                <span className="text-xs text-gray-400">
                  Cadastre cursos primeiro
                </span>
              )}
            </div>

            <button
              type="submit"
              className="bg-purple-600 text-white p-2 rounded-lg hover:bg-purple-700 flex items-center justify-center gap-1 transition-colors mt-2"
            >
              <Plus className="w-4 h-4" />
              Adicionar Disciplina
            </button>
          </form>

          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[520px] pr-2">
            {subjects.map(subject => (
              <li
                key={subject.id}
                className="p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm flex flex-col gap-2"
              >
                {editingSubjectId === subject.id ? (
                  <div className="space-y-2">
                    <input
                      value={subjectDraft.name}
                      onChange={event =>
                        setSubjectDraft(current => ({
                          ...current,
                          name: event.target.value,
                        }))
                      }
                      className="w-full border border-gray-300 rounded p-1.5"
                      placeholder="Nome da disciplina"
                    />

                    <div className="flex gap-2">
                      <input
                        type="number"
                        min="1"
                        value={subjectDraft.workload}
                        onChange={event =>
                          setSubjectDraft(current => ({
                            ...current,
                            workload: Number(
                              event.target.value,
                            ),
                          }))
                        }
                        className="w-20 border border-gray-300 rounded p-1.5"
                        title="Carga padrão"
                      />

                      <select
                        value={subjectDraft.complexity}
                        onChange={event =>
                          setSubjectDraft(current => ({
                            ...current,
                            complexity:
                              event.target.value,
                          }))
                        }
                        className="min-w-0 flex-1 border border-gray-300 rounded p-1.5 bg-white"
                      >
                        <option value="Alta">Alta</option>
                        <option value="Media">Média</option>
                        <option value="Baixa">Baixa</option>
                      </select>
                    </div>

                    <div className="border border-gray-200 rounded p-2 space-y-1">
                      <span className="text-[10px] uppercase font-bold text-gray-500">
                        Cursos associados
                      </span>

                      {courses.map(course => (
                        <label
                          key={course.id}
                          className="flex items-center gap-2 text-xs text-gray-700"
                        >
                          <input
                            type="checkbox"
                            checked={subjectDraft.course_ids.includes(
                              course.id,
                            )}
                            onChange={event =>
                              setSubjectDraft(current => ({
                                ...current,
                                course_ids:
                                  event.target.checked
                                    ? Array.from(
                                        new Set([
                                          ...current.course_ids,
                                          course.id,
                                        ]),
                                      )
                                    : current.course_ids.filter(
                                        id =>
                                          id !== course.id,
                                      ),
                              }))
                            }
                          />
                          {course.name}
                        </label>
                      ))}
                    </div>

                    <div className="flex justify-end gap-2">
                      <button
                        type="button"
                        onClick={() =>
                          saveSubjectEdit(subject)
                        }
                        className="text-xs px-2 py-1 rounded bg-purple-600 text-white hover:bg-purple-700"
                      >
                        Salvar
                      </button>

                      <button
                        type="button"
                        onClick={() =>
                          setEditingSubjectId(null)
                        }
                        className="text-xs px-2 py-1 rounded border border-gray-200 bg-white text-gray-600 hover:bg-gray-100"
                      >
                        Cancelar
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="flex justify-between items-start gap-2">
                      <div className="flex-1 min-w-0">
                        <strong className="text-gray-800 text-base block truncate">
                          {subject.name}
                        </strong>

                        <span className="text-xs text-gray-500">
                          Padrão: {subject.workload} aulas
                          semanais
                        </span>
                      </div>

                      <div className="flex items-center gap-1">
                        <span
                          className={`text-[10px] uppercase font-bold px-2 py-1 rounded-full ${
                            subject.complexity === "Alta"
                              ? "bg-red-100 text-red-700"
                              : subject.complexity === "Media"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-green-100 text-green-700"
                          }`}
                        >
                          {subject.complexity}
                        </span>

                        <button
                          type="button"
                          onClick={() =>
                            startSubjectEdit(
                              subject,
                            )
                          }
                          className="p-1.5 text-indigo-600 hover:bg-indigo-100 rounded"
                          title="Editar disciplina"
                        >
                          <Edit className="w-4 h-4" />
                        </button>

                        <button
                          type="button"
                          onClick={() =>
                            handleDeleteSubject(
                              subject,
                            )
                          }
                          className="p-1.5 text-red-600 hover:bg-red-100 rounded"
                          title="Remover disciplina"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="text-xs text-purple-600 font-medium">
                      Cursos:{" "}
                      {subject.course_ids
                        ?.map(
                          id =>
                            courses.find(
                              course =>
                                course.id === id,
                            )?.name || id,
                        )
                        .join(", ")
                        || "Nenhum"}
                    </div>
                  </>
                )}
              </li>
            ))}

            {subjects.length === 0 && (
              <p className="text-sm text-gray-500 text-center py-4">
                Nenhuma disciplina cadastrada.
              </p>
            )}
          </ul>
        </div>
      </div>
    </div>
  );
}
