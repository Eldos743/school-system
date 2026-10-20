"""Расчёт показателей для панелей.

Формула KPI учителя (0–100 баллов) — предложение для согласования с заказчиком:

    Сабаққа бақылау (контроль уроков)        30%  средний балл посещённых уроков (из 100)
    Білім өсімі (прирост знаний)             25%  средний прирост диагностики, п.п.: 0 → 0, 15+ → 100
    Тапсырмалар (выполнение заданий)         15%  доля заданий, сданных вовремя
    Уақытылы келу (приход на работу)         15%  доля дней без опоздания: 80% → 0, 100% → 100
    Білім сапасы (качество знаний)           10%  доля оценок «4» и «5» в последней четверти
    Ата-ана шағымдары (жалобы родителей)      5%  100 − 25 за каждую жалобу

Учителю нужна поддержка, если KPI < 65 или любой компонент < 50.
"""
from collections import defaultdict

from .db import q, q1

KPI_WEIGHTS = {
    "observation": 30,
    "growth": 25,
    "tasks": 15,
    "punctuality": 15,
    "quality": 10,
    "complaints": 5,
}
SUPPORT_KPI = 65
SUPPORT_COMPONENT = 50
ENT_MAX = 140
ENT_THRESHOLD = 50      # пороговый балл для поступления на бакалавриат
ENT_GRANT = 100         # ориентир для гранта (условно)


def clamp(x, lo=0.0, hi=100.0):
    return max(lo, min(hi, x))


def pct(a, b):
    return 100.0 * a / b if b else 0.0


def last_quarter():
    return q1("SELECT MAX(quarter) m FROM grades")["m"] or 1


# ---------------------------------------------------------------- учителя

def teacher_components():
    """Сырые показатели и баллы компонентов KPI для всех работающих учителей."""
    teachers = q("""SELECT t.*, s.name_kz subj_kz, s.name_ru subj_ru FROM teachers t
                    JOIN subjects s ON s.id = t.subject_id WHERE t.left_date IS NULL ORDER BY t.id""")
    lq = last_quarter()

    obs = {r["teacher_id"]: r for r in q("""
        SELECT teacher_id, AVG(planning+methods+engagement+assessment) avg, COUNT(*) n
        FROM lesson_observations GROUP BY teacher_id""")}
    growth = {r["teacher_id"]: r for r in q("""
        SELECT tg.teacher_id, AVG(e.score - st.score) g, COUNT(*) n
        FROM teaching tg
        JOIN students s ON s.class_id = tg.class_id
        JOIN diagnostics st ON st.student_id = s.id AND st.subject_id = tg.subject_id AND st.kind = 'start'
        JOIN diagnostics e  ON e.student_id = s.id AND e.subject_id = tg.subject_id AND e.kind = 'end'
        GROUP BY tg.teacher_id""")}
    tasks = {r["teacher_id"]: r for r in q("""
        SELECT teacher_id, COUNT(*) n,
               SUM(done_date IS NOT NULL AND done_date <= due_date) ontime,
               SUM(done_date IS NOT NULL AND done_date > due_date) late,
               SUM(done_date IS NULL) missed
        FROM teacher_tasks GROUP BY teacher_id""")}
    arr = {r["teacher_id"]: r for r in q("""
        SELECT teacher_id, COUNT(*) n, SUM(status='on_time') ontime, SUM(status='late') late,
               SUM(status='absent') absent, SUM(status='excused') excused, SUM(late_minutes) late_min
        FROM teacher_arrivals GROUP BY teacher_id""")}
    quality = {r["teacher_id"]: r for r in q("""
        SELECT tg.teacher_id, AVG(g.value >= 4) * 100 qual, AVG(g.value) avg
        FROM teaching tg JOIN students s ON s.class_id = tg.class_id
        JOIN grades g ON g.student_id = s.id AND g.subject_id = tg.subject_id AND g.quarter = ?
        GROUP BY tg.teacher_id""", lq)}
    compl = {r["teacher_id"]: r["n"] for r in q("""
        SELECT teacher_id, COUNT(*) n FROM parent_feedback
        WHERE kind='complaint' AND teacher_id IS NOT NULL GROUP BY teacher_id""")}

    out = []
    for t in teachers:
        tid = t["id"]
        o, gr, tk, a, ql = obs.get(tid), growth.get(tid), tasks.get(tid), arr.get(tid), quality.get(tid)
        worked = (a["n"] - a["excused"]) if a else 0
        punct = pct(a["ontime"], worked) if a else 0
        raw = {
            "observation": o["avg"] if o else 0,
            "growth": gr["g"] if gr else 0,
            "tasks": pct(tk["ontime"], tk["n"]) if tk else 0,
            "punctuality": punct,
            "quality": ql["qual"] if ql else 0,
            "complaints": compl.get(tid, 0),
        }
        score = {
            "observation": clamp(raw["observation"]),
            "growth": clamp(raw["growth"] / 15 * 100),
            "tasks": clamp(raw["tasks"]),
            "punctuality": clamp((raw["punctuality"] - 80) / 20 * 100),
            "quality": clamp(raw["quality"]),
            "complaints": clamp(100 - 25 * raw["complaints"]),
        }
        kpi = sum(score[k] * w for k, w in KPI_WEIGHTS.items()) / 100
        weak = [k for k, v in score.items() if v < SUPPORT_COMPONENT]
        out.append(dict(
            t=t, raw=raw, score=score, kpi=kpi, weak=weak,
            needs_support=kpi < SUPPORT_KPI or bool(weak),
            obs_n=o["n"] if o else 0,
            arrivals=a, tasks=tk,
            avg_grade=ql["avg"] if ql else None,
            years=2026 - int(t["hire_date"][:4]),
        ))
    out.sort(key=lambda r: -r["kpi"])
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


def teacher_detail(tid):
    comp = next((r for r in teacher_components() if r["t"]["id"] == tid), None)
    if comp is None:
        return None
    monthly = q("""SELECT substr(date,1,7) m, COUNT(*) n, SUM(status='late') late,
                          SUM(status='absent') absent, SUM(late_minutes) mins
                   FROM teacher_arrivals WHERE teacher_id=? GROUP BY m ORDER BY m""", tid)
    late_days = q("""SELECT date, arrival_time, late_minutes FROM teacher_arrivals
                     WHERE teacher_id=? AND status='late' ORDER BY date DESC LIMIT 8""", tid)
    observations = q("""SELECT o.*, c.name cname FROM lesson_observations o LEFT JOIN classes c ON c.id=o.class_id
                        WHERE teacher_id=? ORDER BY date""", tid)
    tasks = q("SELECT * FROM teacher_tasks WHERE teacher_id=? ORDER BY due_date", tid)
    by_class = q("""
        SELECT c.id, c.name, tg.subject_id,
               AVG(st.score) start, AVG(md.score) mid, AVG(e.score) end_, COUNT(e.score) n
        FROM teaching tg JOIN classes c ON c.id = tg.class_id
        JOIN students s ON s.class_id = c.id
        JOIN diagnostics st ON st.student_id=s.id AND st.subject_id=tg.subject_id AND st.kind='start'
        LEFT JOIN diagnostics md ON md.student_id=s.id AND md.subject_id=tg.subject_id AND md.kind='mid'
        LEFT JOIN diagnostics e ON e.student_id=s.id AND e.subject_id=tg.subject_id AND e.kind='end'
        WHERE tg.teacher_id=? GROUP BY c.id ORDER BY c.grade, c.name""", tid)
    quarters = q("""
        SELECT g.quarter, AVG(g.value) avg, AVG(g.value>=4)*100 qual
        FROM teaching tg JOIN students s ON s.class_id=tg.class_id
        JOIN grades g ON g.student_id=s.id AND g.subject_id=tg.subject_id
        WHERE tg.teacher_id=? GROUP BY g.quarter ORDER BY g.quarter""", tid)
    complaints = q("""SELECT f.date, f.category, f.status, c.name cname FROM parent_feedback f
                      JOIN students s ON s.id=f.student_id JOIN classes c ON c.id=s.class_id
                      WHERE f.teacher_id=? AND f.kind='complaint' ORDER BY f.date DESC""", tid)
    return dict(c=comp, monthly=monthly, late_days=late_days, observations=observations,
                tasks=tasks, by_class=by_class, quarters=quarters, complaints=complaints)


def support_recommendations(comp):
    """Что предложить учителю по слабым компонентам."""
    recs = {
        "observation": "rec_observation",
        "growth": "rec_growth",
        "tasks": "rec_tasks",
        "punctuality": "rec_punctuality",
        "quality": "rec_quality",
        "complaints": "rec_complaints",
    }
    return [recs[k] for k in comp["weak"]]


# ---------------------------------------------------------------- ученики

def students_overview(class_id=None):
    lq = last_quarter()
    where = "WHERE s.left_date IS NULL" + (" AND s.class_id = ?" if class_id else "")
    args = (lq, class_id) if class_id else (lq,)
    rows = q(f"""
        SELECT s.id, s.full_name, c.name cname, c.grade, s.class_id,
          (SELECT AVG(status IN ('present','late'))*100 FROM student_attendance a WHERE a.student_id=s.id) att,
          (SELECT AVG(value) FROM grades g WHERE g.student_id=s.id AND g.quarter=?) avg,
          (SELECT MIN(value) FROM grades g WHERE g.student_id=s.id AND g.quarter=(SELECT MAX(quarter) FROM grades g2 WHERE g2.student_id=s.id)) minv,
          (SELECT AVG(e.score - st.score) FROM diagnostics st JOIN diagnostics e
             ON e.student_id=st.student_id AND e.subject_id=st.subject_id AND e.kind='end'
             WHERE st.student_id=s.id AND st.kind='start') growth,
          (SELECT score FROM ent_mocks m WHERE m.student_id=s.id ORDER BY date DESC LIMIT 1) ent,
          (SELECT COUNT(*) FROM olympiads o WHERE o.student_id=s.id) olymp
        FROM students s JOIN classes c ON c.id=s.class_id {where}
        ORDER BY c.grade, c.name, s.full_name""", *args)
    out = []
    for r in rows:
        need = extra_lessons_need(r["id"])
        out.append(dict(r=r, need=need, flag=status_flag(r, need)))
    return out


def status_flag(r, need):
    if (r["minv"] is not None and r["minv"] <= 2) or (r["att"] or 100) < 85:
        return "risk"
    if need:
        return "watch"
    if (r["avg"] or 0) >= 4.6:
        return "strong"
    return "ok"


def extra_lessons_need(sid):
    """Предметы, по которым ученику нужны дополнительные занятия."""
    rows = q("""
        SELECT sb.id, sb.name_kz, sb.name_ru,
          (SELECT value FROM grades g WHERE g.student_id=? AND g.subject_id=sb.id ORDER BY quarter DESC LIMIT 1) last_grade,
          (SELECT score FROM diagnostics d WHERE d.student_id=? AND d.subject_id=sb.id ORDER BY date DESC LIMIT 1) last_diag
        FROM subjects sb ORDER BY sb.id""", sid, sid)
    out = []
    for r in rows:
        if r["last_grade"] is None and r["last_diag"] is None:
            continue
        # правило: «2» за четверть, или диагностика ниже 40%, или «3» вместе с диагностикой ниже 55%
        g, dg = r["last_grade"], r["last_diag"]
        weak_grade = g is not None and (g <= 2 or (g == 3 and dg is not None and dg < 55))
        weak_diag = dg is not None and (dg < 40 or (dg < 55 and g == 3))
        reasons = []
        if weak_grade:
            reasons.append(("grade", g))
        if weak_diag:
            reasons.append(("diag", dg))
        if reasons:
            out.append(dict(subject=r, reasons=reasons))
    return out


def student_detail(sid):
    s = q1("""SELECT s.*, c.name cname, c.grade, t.full_name homeroom FROM students s
              JOIN classes c ON c.id=s.class_id LEFT JOIN teachers t ON t.id=c.homeroom_teacher_id
              WHERE s.id=?""", sid)
    if s is None:
        return None
    att = q1("""SELECT COUNT(*) n, SUM(status='present') present, SUM(status='late') late,
                       SUM(status='absent') absent, SUM(status='excused') excused
                FROM student_attendance WHERE student_id=?""", sid)
    att_monthly = q("""SELECT substr(date,1,7) m, AVG(status IN ('present','late'))*100 rate,
                              SUM(status='late') late
                       FROM student_attendance WHERE student_id=? GROUP BY m ORDER BY m""", sid)
    grades = q("""SELECT sb.id sid, sb.name_kz, sb.name_ru, g.quarter, g.value FROM grades g
                  JOIN subjects sb ON sb.id=g.subject_id WHERE g.student_id=? ORDER BY sb.id, g.quarter""", sid)
    table = defaultdict(dict)
    names = {}
    for g in grades:
        table[g["sid"]][g["quarter"]] = g["value"]
        names[g["sid"]] = (g["name_kz"], g["name_ru"])
    quarter_avg = q("""SELECT quarter, AVG(value) avg FROM grades WHERE student_id=?
                       GROUP BY quarter ORDER BY quarter""", sid)
    class_avg = q("""SELECT g.quarter, AVG(g.value) avg FROM grades g JOIN students s ON s.id=g.student_id
                     WHERE s.class_id=? GROUP BY g.quarter ORDER BY g.quarter""", s["class_id"])
    diags = q("""SELECT sb.id sid, sb.name_kz, sb.name_ru,
                   MAX(CASE WHEN kind='start' THEN score END) start,
                   MAX(CASE WHEN kind='mid' THEN score END) mid,
                   MAX(CASE WHEN kind='end' THEN score END) end_
                 FROM diagnostics d JOIN subjects sb ON sb.id=d.subject_id
                 WHERE d.student_id=? GROUP BY sb.id ORDER BY sb.id""", sid)
    ent = q("SELECT date, score FROM ent_mocks WHERE student_id=? ORDER BY date", sid)
    olymp = q("""SELECT o.*, sb.name_kz, sb.name_ru FROM olympiads o JOIN subjects sb ON sb.id=o.subject_id
                 WHERE student_id=? ORDER BY date""", sid)
    contacts = q("""SELECT p.*, t.full_name teacher FROM parent_contacts p LEFT JOIN teachers t ON t.id=p.teacher_id
                    WHERE student_id=? ORDER BY date DESC""", sid)
    feedback = q("SELECT * FROM parent_feedback WHERE student_id=? ORDER BY date DESC", sid)
    rank = None
    if s["grade"] >= 9:
        # готовность к олимпиаде: сильные предметы по последней диагностике
        rank = [d for d in diags if (d["end_"] or d["mid"] or 0) >= 80]
    return dict(s=s, att=att, att_monthly=att_monthly, table=dict(table), names=names,
                quarter_avg=quarter_avg, class_avg=class_avg, diags=diags, ent=ent, olymp=olymp,
                contacts=contacts, feedback=feedback, need=extra_lessons_need(sid), olymp_ready=rank)


# ---------------------------------------------------------------- учредитель

def founder_overview():
    lq = last_quarter()
    per_student = q("""SELECT g.student_id, g.quarter, MIN(g.value) minv FROM grades g
                       JOIN students s ON s.id=g.student_id
                       GROUP BY g.student_id, g.quarter""")
    by_q = defaultdict(lambda: [0, 0, 0])   # n, quality (все 4-5), success (без 2)
    for r in per_student:
        b = by_q[r["quarter"]]
        b[0] += 1
        b[1] += r["minv"] >= 4
        b[2] += r["minv"] >= 3
    quality = [dict(q=k, quality=pct(v[1], v[0]), success=pct(v[2], v[0])) for k, v in sorted(by_q.items())]

    growth = q1("""SELECT AVG(e.score - st.score) g, AVG(st.score) s, AVG(e.score) e FROM diagnostics st
                   JOIN diagnostics e ON e.student_id=st.student_id AND e.subject_id=st.subject_id AND e.kind='end'
                   WHERE st.kind='start'""")
    att = q1("SELECT AVG(status IN ('present','late'))*100 r FROM student_attendance")["r"]

    classes = q("SELECT * FROM classes ORDER BY grade, name")
    class_rows = []
    for c in classes:
        qs = q("""SELECT g.quarter, AVG(g.value) avg FROM grades g JOIN students s ON s.id=g.student_id
                  WHERE s.class_id=? GROUP BY g.quarter ORDER BY g.quarter""", c["id"])
        qual = q("""SELECT quarter, AVG(minv>=4)*100 qual FROM (
                      SELECT g.student_id, g.quarter, MIN(g.value) minv FROM grades g
                      JOIN students s ON s.id=g.student_id WHERE s.class_id=?
                      GROUP BY g.student_id, g.quarter) GROUP BY quarter ORDER BY quarter""", c["id"])
        gr = q1("""SELECT AVG(e.score - st.score) g FROM diagnostics st
                   JOIN diagnostics e ON e.student_id=st.student_id AND e.subject_id=st.subject_id AND e.kind='end'
                   JOIN students s ON s.id=st.student_id WHERE st.kind='start' AND s.class_id=?""", c["id"])
        n = q1("SELECT COUNT(*) n FROM students WHERE class_id=? AND left_date IS NULL", c["id"])["n"]
        class_rows.append(dict(c=c, avg=[r["avg"] for r in qs], qual=[r["qual"] for r in qual], growth=gr["g"], n=n))

    kpis = teacher_components()

    surveys = q("""SELECT date, AVG(rating) avg, COUNT(*) n, AVG(rating>=4)*100 sat FROM parent_feedback
                   WHERE kind='survey' GROUP BY date ORDER BY date""")
    complaints = q("""SELECT category, COUNT(*) n, SUM(status='open') open FROM parent_feedback
                      WHERE kind='complaint' GROUP BY category ORDER BY n DESC""")
    complaints_monthly = q("""SELECT substr(date,1,7) m, COUNT(*) n FROM parent_feedback
                              WHERE kind='complaint' GROUP BY m ORDER BY m""")

    staff_now = q1("SELECT COUNT(*) n FROM teachers WHERE left_date IS NULL")["n"]
    leavers = q("""SELECT t.*, s.name_kz, s.name_ru FROM teachers t JOIN subjects s ON s.id=t.subject_id
                   WHERE left_date IS NOT NULL ORDER BY left_date""")
    new_hires = q1("SELECT COUNT(*) n FROM teachers WHERE hire_date >= '2025-06-01'")["n"]
    tenure = q("SELECT hire_date FROM teachers WHERE left_date IS NULL")
    years = [2026 - int(r["hire_date"][:4]) for r in tenure]
    tenure_buckets = [sum(y <= 1 for y in years), sum(2 <= y <= 4 for y in years),
                      sum(5 <= y <= 9 for y in years), sum(y >= 10 for y in years)]
    avg_staff = staff_now + len(leavers) / 2
    turnover = pct(len(leavers), avg_staff)

    adm = q("SELECT status, COUNT(*) n FROM admissions GROUP BY status")
    adm_d = {r["status"]: r["n"] for r in adm}
    total_app = sum(adm_d.values())
    funnel = [("applied", total_app),
              ("tested", adm_d.get("tested", 0) + adm_d.get("enrolled", 0) + adm_d.get("declined", 0)),
              ("enrolled", adm_d.get("enrolled", 0))]
    adm_sources = q("SELECT source, COUNT(*) n, SUM(status='enrolled') e FROM admissions GROUP BY source ORDER BY n DESC")
    left_students = q("""SELECT left_reason, COUNT(*) n FROM students WHERE left_date IS NOT NULL
                         GROUP BY left_reason ORDER BY n DESC""")
    students_now = q1("SELECT COUNT(*) n FROM students WHERE left_date IS NULL")["n"]
    joined_midyear = q1("SELECT COUNT(*) n FROM students WHERE enrolled_date > '2025-09-01'")["n"]

    punct_monthly = q("""SELECT substr(a.date,1,7) m,
                           SUM(status='on_time')*100.0/SUM(status IN ('on_time','late')) ontime,
                           SUM(status='late') late, SUM(late_minutes) mins
                         FROM teacher_arrivals a JOIN teachers t ON t.id=a.teacher_id
                         GROUP BY m ORDER BY m""")
    punct_teachers = sorted(kpis, key=lambda r: r["raw"]["punctuality"])[:5]

    return dict(lq=lq, quality=quality, growth=growth, att=att, class_rows=class_rows,
                kpis=kpis, surveys=surveys, complaints=complaints, complaints_monthly=complaints_monthly,
                staff_now=staff_now, leavers=leavers, new_hires=new_hires, tenure_buckets=tenure_buckets,
                turnover=turnover, funnel=funnel, adm_sources=adm_sources, left_students=left_students,
                students_now=students_now, joined_midyear=joined_midyear,
                punct_monthly=punct_monthly, punct_teachers=punct_teachers,
                complaints_total=sum(r["n"] for r in complaints),
                complaints_open=sum(r["open"] for r in complaints))
