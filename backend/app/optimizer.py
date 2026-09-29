from ortools.sat.python import cp_model
from typing import List, Dict, Any
import time

def generate_schedule(
    classrooms: List[Dict[str, Any]],
    subjects: List[Dict[str, Any]],
    teachers: List[Dict[str, Any]],
    sys_config: Dict[str, Any],
    num_days: int = 5,
    num_periods: int = 15 # 0-4 Manhã, 5-9 Tarde, 10-14 Noite
):
    model = cp_model.CpModel()
    penalties = []
    
    Y = {} # Y[c, s, t, d, p] = 1 se Turma c tem Matéria s com Prof t no dia d, período p
    A = {} # A[c, s, t] = 1 se Turma c tem Matéria s lecionada pelo Prof t
    
    # Helper limits per shift
    shift_limits = {
        "Manhã": (0, 4),
        "Tarde": (5, 9),
        "Noite": (10, 14)
    }

    for c in classrooms:
        c_shift = c.get("shift", "Manhã")
        min_p, max_p = shift_limits.get(c_shift, (0, 4))
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        
        for s in c_subjects:
            for t in teachers:
                can_teach = s["id"] in t.get("allowed_subjects", [])
                
                # A[c,s,t]
                A[(c["id"], s["id"], t["id"])] = model.NewBoolVar(f'A_c{c["id"]}_s{s["id"]}_t{t["id"]}')
                if not can_teach:
                    model.Add(A[(c["id"], s["id"], t["id"])] == 0)
                
                for d in range(num_days):
                    for p in range(num_periods):
                        Y[(c["id"], s["id"], t["id"], d, p)] = model.NewBoolVar(
                            f'Y_c{c["id"]}_s{s["id"]}_t{t["id"]}_d{d}_p{p}'
                        )
                        
                        # Only assign classes if teacher is assigned to subject
                        model.Add(Y[(c["id"], s["id"], t["id"], d, p)] <= A[(c["id"], s["id"], t["id"])])
                        
                        # Shift constraint for Classroom: Can only have classes in its own shift
                        if p < min_p or p > max_p:
                            model.Add(Y[(c["id"], s["id"], t["id"], d, p)] == 0)
                            
                        # Teacher Availability
                        day_str = str(d)
                        if day_str in t.get("availability", {}):
                            day_avail = t["availability"][day_str]
                            if p < len(day_avail) and not day_avail[p]:
                                model.Add(Y[(c["id"], s["id"], t["id"], d, p)] == 0)

    # 1. Exactly one teacher per subject per classroom
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        for s in c_subjects:
            if s["workload"] > 0:
                model.AddExactlyOne([A[(c["id"], s["id"], t["id"])] for t in teachers])

    # 2. Exact workload for each subject in classroom
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        for s in c_subjects:
            model.Add(
                sum(Y[(c["id"], s["id"], t["id"], d, p)] 
                    for t in teachers 
                    for d in range(num_days) 
                    for p in range(num_periods)) == s["workload"]
            )

    # 3. No classroom conflicts (max 1 class per period)
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        for d in range(num_days):
            for p in range(num_periods):
                model.AddAtMostOne([
                    Y[(c["id"], s["id"], t["id"], d, p)]
                    for s in c_subjects
                    for t in teachers
                ])

    # 4. No teacher conflicts (max 1 class per period)
    for t in teachers:
        for d in range(num_days):
            for p in range(num_periods):
                model.AddAtMostOne([
                    Y[(c["id"], s["id"], t["id"], d, p)]
                    for c in classrooms
                    for s in [sub for sub in subjects if c["course_id"] in sub.get("course_ids", [])]
                ])

    # --- REGRAS E LEIS ---
    
    # 5. Interjornada (11h rest): If teaches Night, cannot teach Morning next day
    for t in teachers:
        for d in range(num_days - 1): # Exclude last day as there's no next day
            teaches_night = []
            for p in range(10, 15):
                for c in classrooms:
                    c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
                    for s in c_subjects:
                        teaches_night.append(Y[(c["id"], s["id"], t["id"], d, p)])
            
            teaches_morning_next = []
            for p in range(0, 5):
                for c in classrooms:
                    c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
                    for s in c_subjects:
                        teaches_morning_next.append(Y[(c["id"], s["id"], t["id"], d+1, p)])
            
            if teaches_night and teaches_morning_next:
                # Se soma(noite) > 0, então soma(manha) = 0
                b_night = model.NewBoolVar(f"night_t{t['id']}_d{d}")
                model.Add(sum(teaches_night) > 0).OnlyEnforceIf(b_night)
                model.Add(sum(teaches_night) == 0).OnlyEnforceIf(b_night.Not())
                model.Add(sum(teaches_morning_next) == 0).OnlyEnforceIf(b_night)

    # 6. Intrajornada (Max Consecutive Classes)
    max_consec = sys_config.get("max_consecutive_classes", 5)
    for t in teachers:
        for d in range(num_days):
            for start_p in range(num_periods - max_consec):
                window = []
                for p in range(start_p, start_p + max_consec + 1):
                    for c in classrooms:
                        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
                        for s in c_subjects:
                            window.append(Y[(c["id"], s["id"], t["id"], d, p)])
                if window:
                    model.Add(sum(window) <= max_consec)

    # 7. Max Classes Per Day
    max_classes = sys_config.get("max_classes_per_day", 9)
    for t in teachers:
        for d in range(num_days):
            day_classes = []
            for p in range(num_periods):
                for c in classrooms:
                    c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
                    for s in c_subjects:
                        day_classes.append(Y[(c["id"], s["id"], t["id"], d, p)])
            if day_classes:
                model.Add(sum(day_classes) <= max_classes)

    # 8. Max High Complexity Per Day (Students)
    max_high = sys_config.get("max_high_complexity_per_day", 2)
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        high_comp_subjects = [s for s in c_subjects if s.get("complexity") == "Alta"]
        for d in range(num_days):
            day_high_classes = []
            for s in high_comp_subjects:
                for t in teachers:
                    for p in range(num_periods):
                        day_high_classes.append(Y[(c["id"], s["id"], t["id"], d, p)])
            if day_high_classes:
                model.Add(sum(day_high_classes) <= max_high)

    # 9. Aulas Geminadas (Max 2 consecutive of same subject)
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        for s in c_subjects:
            for d in range(num_days):
                for p in range(num_periods - 2):
                    model.Add(
                        sum(Y[(c["id"], s["id"], t["id"], d, p_offset)] 
                            for t in teachers for p_offset in range(p, p+3)) <= 2
                    )

    # 9b. Max Consecutive classes per teacher in the same classroom
    max_consec_teacher_class = sys_config.get("max_consec_per_teacher", 2)
    mode = sys_config.get("max_consec_teacher_mode", "hard")
    
    if mode != "ignore":
        for c in classrooms:
            c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
            for t in teachers:
                for d in range(num_days):
                    for p in range(num_periods - max_consec_teacher_class):
                        class_sum = sum(Y[(c["id"], s["id"], t["id"], d, p_offset)]
                                        for s in c_subjects
                                        for p_offset in range(p, p + max_consec_teacher_class + 1))
                        
                        if mode == "hard":
                            model.Add(class_sum <= max_consec_teacher_class)
                        elif mode == "soft":
                            pen_var = model.NewIntVar(0, num_periods, f"pen_consec_t{t['id']}_c{c['id']}_d{d}_p{p}")
                            model.Add(pen_var >= class_sum - max_consec_teacher_class)
                            penalties.append(pen_var * 40) # penalidade por cada aula excedente

    # 10. Student Gaps (Contiguous blocks per day)
    student_gaps_hard = sys_config.get("student_gaps_hard", True)
    
    for c in classrooms:
        min_p, max_p = shift_limits.get(c.get("shift", "Manhã"), (0, 4))
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        
        for d in range(num_days):
            day_has_class = []
            for p in range(min_p, max_p + 1):
                b_p = model.NewBoolVar(f"c_has_class_c{c['id']}_d{d}_p{p}")
                model.AddMaxEquality(b_p, [Y[(c["id"], s["id"], t["id"], d, p)] for s in c_subjects for t in teachers])
                day_has_class.append(b_p)
                
            for p1 in range(min_p, max_p - 1):
                for p2 in range(p1 + 1, max_p):
                    for p3 in range(p2 + 1, max_p + 1):
                        if student_gaps_hard:
                            model.Add(day_has_class[p1 - min_p] + (1 - day_has_class[p2 - min_p]) + day_has_class[p3 - min_p] <= 2)
                        else:
                            gap_penalty = model.NewBoolVar(f"gap_c{c['id']}_d{d}_p1{p1}_p2{p2}_p3{p3}")
                            model.Add(day_has_class[p1 - min_p] + (1 - day_has_class[p2 - min_p]) + day_has_class[p3 - min_p] - 2 <= gap_penalty)
                            penalties.append(gap_penalty * 100)

    # 11. Teacher Gaps (Janelas para professores)
    teacher_gaps_hard = sys_config.get("teacher_gaps_hard", False)
    shift_ranges = [(0, 5), (5, 10), (10, 15)] # Manhã, Tarde, Noite
    for t in teachers:
        for d in range(num_days):
            t_day_has_class = []
            for p in range(num_periods):
                b_p = model.NewBoolVar(f"t_has_class_t{t['id']}_d{d}_p{p}")
                # Teacher t has class in period p if they teach ANY subject to ANY classroom
                model.AddMaxEquality(b_p, [
                    Y[(c["id"], s["id"], t["id"], d, p)]
                    for c in classrooms
                    for s in [sub for sub in subjects if c["course_id"] in sub.get("course_ids", [])]
                ])
                t_day_has_class.append(b_p)
                
            for s_start, s_end in shift_ranges:
                for p1 in range(s_start, s_end - 2):
                    for p2 in range(p1 + 1, s_end - 1):
                        for p3 in range(p2 + 1, s_end):
                            if teacher_gaps_hard:
                                model.Add(t_day_has_class[p1] + (1 - t_day_has_class[p2]) + t_day_has_class[p3] <= 2)
                            else:
                                gap_penalty = model.NewBoolVar(f"gap_t{t['id']}_d{d}_p1{p1}_p2{p2}_p3{p3}")
                                model.Add(t_day_has_class[p1] + (1 - t_day_has_class[p2]) + t_day_has_class[p3] - 2 <= gap_penalty)
                                penalties.append(gap_penalty * 80) # Peso alto para juntar as aulas do professor

    # Objective Function
    objective_terms = []
    
    # 1. Pontuação de Professores (Maximizar)
    for c in classrooms:
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        for s in c_subjects:
            for t in teachers:
                score = t.get("score", 0)
                if score > 0:
                    for d in range(num_days):
                        for p in range(num_periods):
                            objective_terms.append(score * Y[(c["id"], s["id"], t["id"], d, p)])
                            
    # 2. Novas Preferências Soft (Penalidades)
    min_classes_students = sys_config.get("min_classes_students", 2)
    min_classes_teachers = sys_config.get("min_classes_teachers", 2)
    avoid_edges = sys_config.get("avoid_edges", False)
    avoid_friday = sys_config.get("avoid_friday", False)
    
    # A) Mínimo de aulas para professores
    for t in teachers:
        for d in range(num_days):
            day_classes = []
            for p in range(num_periods):
                for c in classrooms:
                    c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
                    for s in c_subjects:
                        day_classes.append(Y[(c["id"], s["id"], t["id"], d, p)])
            
            if day_classes:
                day_active = model.NewBoolVar(f"active_t{t['id']}_d{d}")
                model.Add(sum(day_classes) > 0).OnlyEnforceIf(day_active)
                model.Add(sum(day_classes) == 0).OnlyEnforceIf(day_active.Not())
                
                # Penalty variable
                pen_var = model.NewIntVar(0, num_periods, f"pen_min_t{t['id']}_d{d}")
                model.Add(pen_var >= min_classes_teachers - sum(day_classes)).OnlyEnforceIf(day_active)
                model.Add(pen_var == 0).OnlyEnforceIf(day_active.Not())
                penalties.append(pen_var * 100) # peso alto

    # B) Mínimo de aulas para alunos e Preferências de Bordas/Sexta
    for c in classrooms:
        c_shift = c.get("shift", "Manhã")
        min_p, max_p = shift_limits.get(c_shift, (0, 4))
        c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
        
        for d in range(num_days):
            day_classes = []
            for p in range(min_p, max_p + 1):
                p_classes = []
                for s in c_subjects:
                    for t in teachers:
                        p_classes.append(Y[(c["id"], s["id"], t["id"], d, p)])
                        
                        # Borda do dia (Primeira e Última Aula)
                        if avoid_edges and (p == min_p or p == max_p):
                            penalties.append(Y[(c["id"], s["id"], t["id"], d, p)] * 20) # penalidade leve
                        
                        # Evitar Sexta-feira
                        if avoid_friday and d == 4:
                            penalties.append(Y[(c["id"], s["id"], t["id"], d, p)] * 30) # penalidade moderada
                            
                day_classes.extend(p_classes)
                
            if day_classes:
                day_active = model.NewBoolVar(f"active_c{c['id']}_d{d}")
                model.Add(sum(day_classes) > 0).OnlyEnforceIf(day_active)
                model.Add(sum(day_classes) == 0).OnlyEnforceIf(day_active.Not())
                
                pen_var = model.NewIntVar(0, num_periods, f"pen_min_c{c['id']}_d{d}")
                model.Add(pen_var >= min_classes_students - sum(day_classes)).OnlyEnforceIf(day_active)
                model.Add(pen_var == 0).OnlyEnforceIf(day_active.Not())
                penalties.append(pen_var * 100)

    # Aplicação final das penalidades
    objective_expr = sum(objective_terms) - sum(penalties)
    
    model.Maximize(objective_expr)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 15.0 
    started = time.perf_counter()
    status = solver.Solve(model)
    elapsed = time.perf_counter() - started

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        schedule = []
        for c in classrooms:
            c_subjects = [s for s in subjects if c["course_id"] in s.get("course_ids", [])]
            for s in c_subjects:
                for t in teachers:
                    for d in range(num_days):
                        for p in range(num_periods):
                            if solver.Value(Y[(c["id"], s["id"], t["id"], d, p)]) == 1:
                                schedule.append({
                                    "classroom_id": c["id"],
                                    "subject_id": s["id"],
                                    "teacher_id": t["id"],
                                    "day": d,
                                    "period": p
                                })
        return {
            "status": "success",
            "solution_status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "solve_time_seconds": round(elapsed, 3),
            "schedule": schedule,
        }
    else:
        return {"status": "infeasible", "message": "Não foi possível gerar uma grade com as restrições informadas."}
