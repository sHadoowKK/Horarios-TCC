from sqlalchemy import Boolean, Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from .database import Base


class Course(Base):
    __tablename__ = "courses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    classes = relationship("Classroom", back_populates="course")


class Classroom(Base):
    __tablename__ = "classrooms"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    shift = Column(String, nullable=False)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    course = relationship("Course", back_populates="classes")


class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    workload = Column(Integer, nullable=False)
    complexity = Column(String, nullable=False)
    course_ids = Column(JSON, default=list)


class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    allowed_subjects = Column(JSON, default=list)
    availability = Column(JSON, default=dict)
    score = Column(Integer, default=0)


class Period(Base):
    __tablename__ = "periods"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    start_time = Column(String, nullable=False)
    end_time = Column(String, nullable=False)
    is_break = Column(Boolean, default=False)


class SystemConfig(Base):
    __tablename__ = "system_configs"
    id = Column(Integer, primary_key=True, index=True)
    max_classes_per_day = Column(Integer, default=9)
    max_consecutive_classes = Column(Integer, default=5)
    max_high_complexity_per_day = Column(Integer, default=2)
    student_gaps_hard = Column(Boolean, default=True)
    teacher_gaps_hard = Column(Boolean, default=False)
    min_classes_students = Column(Integer, default=2)
    min_classes_teachers = Column(Integer, default=2)
    avoid_edges = Column(Boolean, default=False)
    avoid_friday = Column(Boolean, default=False)
    max_consec_per_teacher = Column(Integer, default=2)
    max_consec_teacher_mode = Column(String, default="hard")


class TimetableItem(Base):
    __tablename__ = "timetable"
    id = Column(Integer, primary_key=True, index=True)
    classroom_id = Column(Integer, index=True, nullable=False)
    subject_id = Column(Integer, nullable=False)
    teacher_id = Column(Integer, index=True, nullable=False)
    day = Column(Integer, nullable=False)
    period = Column(Integer, nullable=False)
