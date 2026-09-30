from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Shift = Literal["Manhã", "Integral", "Noite"]
Complexity = Literal["Alta", "Media", "Baixa"]
SubjectCategory = Literal["Ensino Médio", "Técnica"]
StudentGroup = Literal["Todos", "A", "B"]
RuleMode = Literal["ignore", "soft", "hard"]


class CourseBase(BaseModel):
    name: str = Field(min_length=1)


class CourseCreate(CourseBase):
    pass


class Course(CourseBase):
    id: int

    class Config:
        from_attributes = True


class ClassroomSubjectSetting(BaseModel):
    subject_id: int = Field(gt=0)
    workload: int = Field(ge=1, le=25)
    split: bool = False


class ClassroomBase(BaseModel):
    name: str = Field(min_length=1)
    shift: Shift
    course_id: int = Field(gt=0)
    has_groups: bool = False
    subject_settings: List[ClassroomSubjectSetting] = Field(
        default_factory=list
    )

    # Compatibilidade com versões anteriores.
    split_subject_ids: List[int] = Field(default_factory=list)


class ClassroomCreate(ClassroomBase):
    pass


class Classroom(ClassroomBase):
    id: int

    class Config:
        from_attributes = True


class SubjectBase(BaseModel):
    name: str = Field(min_length=1)
    workload: int = Field(ge=1, le=25)
    complexity: Complexity
    category: SubjectCategory = "Ensino Médio"
    course_ids: List[int]


class SubjectCreate(SubjectBase):
    pass


class Subject(SubjectBase):
    id: int

    class Config:
        from_attributes = True


class TeacherBase(BaseModel):
    name: str = Field(min_length=1)
    allowed_subjects: List[int]
    availability: Dict[str, List[bool]]
    score: int = Field(default=0, ge=0, le=100)


class TeacherCreate(TeacherBase):
    pass


class Teacher(TeacherBase):
    id: int

    class Config:
        from_attributes = True


class PeriodBase(BaseModel):
    name: str
    start_time: str
    end_time: str
    is_break: bool = False


class PeriodCreate(PeriodBase):
    pass


class Period(PeriodBase):
    id: int

    class Config:
        from_attributes = True


class SystemConfigBase(BaseModel):
    # Pode ser reduzido pela escola, mas nunca ultrapassa o teto de 9.
    max_classes_per_day: int = Field(default=9, ge=1, le=9)

    # Campo legado: a regra real de 6 aulas + 1h de descanso é fixa.
    max_consecutive_classes: int = Field(default=6, ge=1, le=6)

    max_high_complexity_per_day: int = Field(default=2, ge=0, le=15)

    # Alunos sem janelas é regra fixa. O campo permanece por compatibilidade.
    student_gaps_hard: bool = True

    teacher_gaps_hard: bool = False
    min_classes_students: int = Field(default=2, ge=0, le=15)
    min_classes_teachers: int = Field(default=2, ge=0, le=15)
    avoid_first_period: bool = False
    avoid_last_period: bool = False
    avoid_friday: bool = False
    max_consec_per_teacher: int = Field(default=2, ge=1, le=15)
    max_consec_teacher_mode: RuleMode = "ignore"


class SystemConfigUpdate(SystemConfigBase):
    pass


class SystemConfig(SystemConfigBase):
    id: int

    class Config:
        from_attributes = True


class TimetableItemBase(BaseModel):
    classroom_id: int
    subject_id: int
    teacher_id: Optional[int] = None
    day: int = Field(ge=0, le=4)
    period: int = Field(ge=0, le=15)
    student_group: StudentGroup = "Todos"


class TimetableItemCreate(TimetableItemBase):
    pass


class TimetableItem(TimetableItemBase):
    id: int

    class Config:
        from_attributes = True
