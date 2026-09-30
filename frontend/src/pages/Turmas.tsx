import { useEffect, useState } from "react";
import { api } from "../api";
import { BookOpen, ChevronDown, ChevronUp, School, Layers, Plus } from "lucide-react";

interface Course {
  id: number;
  name: string;
}

interface Classroom {
  id: number;
  name: string;
  shift: string;
  course_id: number;
  has_groups: boolean;
  split_subject_ids: number[];
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
  const [expandedClassrooms, setExpandedClassrooms] = useState<Set<number>>(
    new Set(),
  );

  const [newCourseName, setNewCourseName] = useState("");

  const [newClassName, setNewClassName] = useState("");
  const [newClassShift, setNewClassShift] = useState("Manhã");
  const [newClassCourseId, setNewClassCourseId] = useState("");
  const [newClassHasGroups, setNewClassHasGroups] = useState(false);

  const [newSubName, setNewSubName] = useState("");
  const [newSubWorkload, setNewSubWorkload] = useState(4);
  const [newSubComplexity, setNewSubComplexity] = useState("Media");
  const [newSubCategory, setNewSubCategory] =
    useState<"Ensino Médio" | "Técnica">("Ensino Médio");
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

    await api.post("/courses/", { name: newCourseName });
    setNewCourseName("");
    fetchData();
  };

  const handleAddClassroom = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newClassName.trim() || !newClassCourseId) return;

    await api.post("/classrooms/", {
      name: newClassName,
      shift: newClassShift,
      course_id: Number(newClassCourseId),
      has_groups: newClassHasGroups,
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
    await api.put(`/classrooms/${classroom.id}`, {
      name: changes.name ?? classroom.name,
      shift: changes.shift ?? classroom.shift,
      course_id: changes.course_id ?? classroom.course_id,
      has_groups: changes.has_groups ?? classroom.has_groups,
      split_subject_ids:
        changes.split_subject_ids ?? classroom.split_subject_ids ?? [],
    });

    fetchData();
  };

  const handleToggleClassGroups = async (classroom: Classroom) => {
    const nextHasGroups = !classroom.has_groups;

    await saveClassroom(classroom, {
      has_groups: nextHasGroups,
    });

    if (!nextHasGroups) {
      setExpandedClassrooms(current => {
        const next = new Set(current);
        next.delete(classroom.id);
        return next;
      });
    }
  };

  const toggleClassroomDetails = (classroomId: number) => {
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

  const handleSubjectMode = async (
    classroom: Classroom,
    subjectId: number,
    mode: "Todos" | "Grupos",
  ) => {
    const current = classroom.split_subject_ids || [];

    const next =
      mode === "Grupos"
        ? Array.from(new Set([...current, subjectId]))
        : current.filter(id => id !== subjectId);

    await saveClassroom(classroom, {
      split_subject_ids: next,
    });
  };

  const handleAddSubject = async (event: React.FormEvent) => {
    event.preventDefault();
    if (!newSubName.trim() || newSubCourseIds.length === 0) return;

    await api.post("/subjects/", {
      name: newSubName,
      workload: Number(newSubWorkload),
      complexity: newSubComplexity,
      category: newSubCategory,
      course_ids: newSubCourseIds,
    });

    setNewSubName("");
    setNewSubWorkload(4);
    setNewSubCategory("Ensino Médio");
    setNewSubCourseIds([]);
    fetchData();
  };

  const handleSubjectCategory = async (
    subject: Subject,
    category: "Ensino Médio" | "Técnica",
  ) => {
    await api.put(`/subjects/${subject.id}`, {
      name: subject.name,
      workload: subject.workload,
      complexity: subject.complexity,
      category,
      course_ids: subject.course_ids,
    });

    fetchData();
  };

  const subjectsForClassroom = (classroom: Classroom) =>
    subjects.filter(subject =>
      subject.course_ids?.includes(classroom.course_id),
    );

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

          <form onSubmit={handleAddCourse} className="mb-6 flex gap-2">
            <input
              type="text"
              required
              placeholder="Nome do Curso"
              className="flex-1 border border-gray-300 p-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={newCourseName}
              onChange={event => setNewCourseName(event.target.value)}
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
                className="p-3 bg-gray-50 border border-gray-100 rounded-lg flex justify-between items-center"
              >
                <span className="font-medium text-gray-800">
                  {course.name}
                </span>
                <span className="text-xs text-gray-400 bg-gray-200 px-2 py-1 rounded-full">
                  ID: {course.id}
                </span>
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
              onChange={event => setNewClassName(event.target.value)}
            />

            <div className="flex gap-2">
              <select
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={newClassShift}
                onChange={event => setNewClassShift(event.target.value)}
              >
                <option value="Manhã">Manhã</option>
                <option value="Integral">Integral</option>
                <option value="Noite">Noite</option>
              </select>

              <select
                required
                className="border border-gray-300 p-2 rounded-lg flex-1 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
                value={newClassCourseId}
                onChange={event => setNewClassCourseId(event.target.value)}
              >
                <option value="" disabled>
                  Selecione o Curso
                </option>
                {courses.map(course => (
                  <option key={course.id} value={course.id}>
                    {course.name}
                  </option>
                ))}
              </select>
            </div>

            <label className="flex items-center gap-2 text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg p-3 cursor-pointer">
              <input
                type="checkbox"
                checked={newClassHasGroups}
                onChange={event => setNewClassHasGroups(event.target.checked)}
                className="accent-emerald-600"
              />
              Esta turma utiliza Grupos A/B
            </label>

            {newClassHasGroups && (
              <p className="text-xs text-gray-500 -mt-1">
                Depois de criar a turma, você escolhe quais disciplinas
                ficam juntas e quais separam A/B.
              </p>
            )}

            <button
              type="submit"
              className="bg-emerald-600 text-white p-2 rounded-lg hover:bg-emerald-700 flex items-center justify-center gap-1 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Adicionar Turma
            </button>
          </form>

          <ul className="space-y-3 flex-1 overflow-y-auto max-h-[520px] pr-2">
            {classrooms.map(classroom => {
              const classSubjects = subjectsForClassroom(classroom);

              return (
                <li
                  key={classroom.id}
                  className="p-3 bg-gray-50 border border-gray-100 rounded-lg text-sm flex flex-col gap-2"
                >
                  <div className="flex justify-between">
                    <strong className="text-gray-800 text-base">
                      {classroom.name}
                    </strong>
                    <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">
                      {classroom.shift}
                    </span>
                  </div>

                  <div className="text-xs text-emerald-600 font-medium">
                    Curso:{" "}
                    {courses.find(
                      course => course.id === classroom.course_id,
                    )?.name || classroom.course_id}
                  </div>

                  <label className="flex items-center gap-2 text-xs text-gray-600 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={classroom.has_groups}
                      onChange={() => handleToggleClassGroups(classroom)}
                      className="accent-emerald-600"
                    />
                    Turma possui Grupos A/B
                  </label>

                  {classroom.has_groups && (
                    <div className="mt-1 border-t border-gray-200 pt-2">
                      <button
                        type="button"
                        onClick={() => toggleClassroomDetails(classroom.id)}
                        className="w-full flex items-center justify-between gap-2 text-left text-[11px] font-bold uppercase tracking-wide text-gray-500 hover:text-gray-700 transition-colors"
                      >
                        <span>Organização das disciplinas</span>
                        {expandedClassrooms.has(classroom.id) ? (
                          <ChevronUp className="w-4 h-4 shrink-0" />
                        ) : (
                          <ChevronDown className="w-4 h-4 shrink-0" />
                        )}
                      </button>

                      {expandedClassrooms.has(classroom.id) && (
                        <div className="space-y-2 mt-2">
                          {classSubjects.map(subject => {
                            const isSplit =
                              classroom.split_subject_ids?.includes(subject.id);

                            return (
                              <div
                                key={subject.id}
                                className="flex items-center gap-2"
                              >
                                <span
                                  className="text-xs text-gray-700 flex-1 truncate"
                                  title={subject.name}
                                >
                                  {subject.name}
                                </span>

                                <select
                                  value={isSplit ? "Grupos" : "Todos"}
                                  onChange={event =>
                                    handleSubjectMode(
                                      classroom,
                                      subject.id,
                                      event.target.value as "Todos" | "Grupos",
                                    )
                                  }
                                  className="text-[11px] border border-gray-300 rounded p-1 bg-white"
                                >
                                  <option value="Todos">
                                    Turma inteira
                                  </option>
                                  <option value="Grupos">
                                    Separada A/B
                                  </option>
                                </select>
                              </div>
                            );
                          })}

                          {classSubjects.length === 0 && (
                            <span className="text-xs text-gray-400">
                              Nenhuma disciplina associada ao curso.
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  )}
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
              onChange={event => setNewSubName(event.target.value)}
            />

            <div className="flex gap-2">
              <div className="flex-1 flex flex-col gap-1">
                <label className="text-xs font-semibold text-gray-500 uppercase">
                  Aulas/Sem
                </label>
                <input
                  type="number"
                  min="1"
                  required
                  className="border border-gray-300 p-2 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-purple-500"
                  value={newSubWorkload}
                  onChange={event =>
                    setNewSubWorkload(Number(event.target.value))
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
                    setNewSubComplexity(event.target.value)
                  }
                >
                  <option value="Alta">Alta</option>
                  <option value="Media">Média</option>
                  <option value="Baixa">Baixa</option>
                </select>
              </div>
            </div>

            <div className="flex flex-col gap-1">
              <label className="text-xs font-semibold text-gray-500 uppercase">
                Categoria
              </label>
              <select
                className="border border-gray-300 p-2 rounded-lg w-full bg-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                value={newSubCategory}
                onChange={event =>
                  setNewSubCategory(
                    event.target.value as "Ensino Médio" | "Técnica",
                  )
                }
              >
                <option value="Ensino Médio">Ensino Médio</option>
                <option value="Técnica">Técnica</option>
              </select>
              <span className="text-[11px] text-gray-400">
                A categoria não decide se a aula é conjunta ou separada.
              </span>
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
                    checked={newSubCourseIds.includes(course.id)}
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
                <div className="flex justify-between items-start">
                  <div>
                    <strong className="text-gray-800 text-base block">
                      {subject.name}
                    </strong>
                    <span className="text-xs text-gray-500">
                      {subject.workload} aulas semanais
                    </span>
                  </div>

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
                </div>

                <select
                  value={subject.category}
                  onChange={event =>
                    handleSubjectCategory(
                      subject,
                      event.target.value as "Ensino Médio" | "Técnica",
                    )
                  }
                  className="text-xs border border-gray-200 bg-white rounded p-1.5"
                >
                  <option value="Ensino Médio">Ensino Médio</option>
                  <option value="Técnica">Técnica</option>
                </select>

                <div className="text-xs text-purple-600 font-medium">
                  Cursos:{" "}
                  {subject.course_ids
                    ?.map(
                      id =>
                        courses.find(course => course.id === id)?.name ||
                        id,
                    )
                    .join(", ") || "Nenhum"}
                </div>
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
