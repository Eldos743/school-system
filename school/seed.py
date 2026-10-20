"""Генератор демо-данных за 2025–2026 учебный год.

Данные вымышленные, но правдоподобные: у каждого учителя есть скрытый
«уровень», у каждого ученика — «способности», и от них зависят оценки,
прирост знаний, посещаемость и жалобы. Так панели показывают живую картину.
"""
import random
from datetime import date, timedelta

from .db import init_db

YEAR_START = date(2025, 9, 1)
YEAR_END = date(2026, 5, 25)
HOLIDAYS = [
    (date(2025, 11, 1), date(2025, 11, 9)),
    (date(2025, 12, 29), date(2026, 1, 11)),
    (date(2026, 3, 21), date(2026, 3, 29)),
]
PUBLIC_DAYS = {date(2025, 10, 27), date(2025, 12, 16), date(2026, 3, 9), date(2026, 5, 1), date(2026, 5, 7)}
QUARTER_ENDS = [date(2025, 10, 31), date(2025, 12, 28), date(2026, 3, 20), date(2026, 5, 25)]

SUBJECTS = [
    ("Математика", "Математика"),
    ("Қазақ тілі", "Казахский язык"),
    ("Орыс тілі", "Русский язык"),
    ("Ағылшын тілі", "Английский язык"),
    ("Физика", "Физика"),
    ("Химия", "Химия"),
    ("Биология", "Биология"),
    ("Қазақстан тарихы", "История Казахстана"),
    ("Информатика", "Информатика"),
    ("География", "География"),
]
DIAG_SUBJECTS = set(range(1, 11))  # диагностика по всем предметам

# ФИО, предмет, категория, дата приёма, уровень (-1..1), склонность опаздывать
TEACHERS = [
    ("Сапарова Гүлнар Ерланқызы", 1, "зерттеуші", "2015-08-20", 0.8, 0.02),
    ("Жақсылықов Нұрлан Серікұлы", 1, "модератор", "2023-08-25", -0.7, 0.05),
    ("Тұрсынова Мәдина Бақытқызы", 2, "сарапшы", "2012-08-15", 0.6, 0.02),
    ("Әбенова Сәуле Маратқызы", 2, "модератор", "2021-08-20", 0.1, 0.04),
    ("Ким Елена Викторовна", 3, "сарапшы", "2010-08-18", 0.5, 0.01),
    ("Петрова Ольга Николаевна", 3, "педагог", "2024-08-26", -0.1, 0.06),
    ("Омарова Айгерім Қайратқызы", 4, "зерттеуші", "2018-08-21", 0.7, 0.02),
    ("Смағұлов Дәурен Асқарұлы", 4, "педагог", "2025-08-25", -0.5, 0.20),
    ("Бекмұханов Ерлан Жұмабайұлы", 5, "шебер", "2008-08-14", 0.9, 0.01),
    ("Исаева Динара Талғатқызы", 5, "модератор", "2022-08-22", 0.2, 0.03),
    ("Нұрпейісова Жанар Әділқызы", 6, "сарапшы", "2016-08-19", 0.4, 0.02),
    ("Қасымов Арман Болатұлы", 6, "педагог", "2025-08-25", -0.2, 0.08),
    ("Сейітова Ләззат Нұрланқызы", 7, "сарапшы", "2014-08-20", 0.3, 0.03),
    ("Ержанова Ақмарал Сәкенқызы", 7, "модератор", "2020-08-24", 0.0, 0.04),
    ("Мұқанов Талғат Ерболұлы", 8, "зерттеуші", "2011-08-16", 0.5, 0.02),
    ("Оспанова Гүлмира Әскерқызы", 8, "педагог", "2023-08-23", -0.3, 0.10),
    ("Ли Андрей Сергеевич", 9, "сарапшы", "2019-08-21", 0.6, 0.03),
    ("Төлеуов Бауыржан Мұратұлы", 9, "педагог", "2024-08-26", 0.1, 0.05),
    ("Кенжебаева Роза Ахметқызы", 10, "сарапшы", "2013-08-19", 0.2, 0.02),
    ("Әбдірахманов Серік Қанатұлы", 10, "модератор", "2022-08-22", -0.1, 0.04),
]
FORMER_TEACHERS = [
    ("Ахметова Жұлдыз Сабитқызы", 4, "модератор", "2021-08-20", "2025-12-26", "relocation"),
    ("Сұлтанов Ержан Маратұлы", 1, "педагог", "2024-08-25", "2025-10-31", "salary"),
]

CLASSES = [("5А", 5), ("6А", 6), ("7А", 7), ("7Б", 7), ("8А", 8), ("9А", 9), ("10А", 10), ("11А", 11)]

SURNAMES = ["Ахметов", "Серікбаев", "Нұрланов", "Жұмабаев", "Қасымов", "Төлеуов", "Оспанов", "Сейітов",
            "Мұқанов", "Ержанов", "Исаев", "Кенжебаев", "Сұлтанов", "Омаров", "Байжанов", "Тәжібаев",
            "Әлиев", "Бейсенов", "Дүйсенов", "Есенов", "Жанұзақов", "Құдайбергенов", "Рахымов", "Шәкенов"]
MALE = ["Алихан", "Нұрсұлтан", "Ерасыл", "Әлинұр", "Арсен", "Данияр", "Ислам", "Темірлан", "Айбек",
        "Бекзат", "Мирас", "Димаш", "Рахат", "Ансар", "Жәнібек", "Нұрислам", "Санжар", "Әлішер"]
FEMALE = ["Аружан", "Айым", "Томирис", "Інжу", "Медина", "Әйгерім", "Дана", "Аяулым", "Сабина",
          "Камила", "Жансая", "Айша", "Мадина", "Нұрай", "Ақбота", "Амина", "Зарина", "Әсел"]
PARENT_M = ["Ерлан", "Серік", "Бауыржан", "Асқар", "Марат", "Қайрат", "Нұрлан", "Ғалым", "Дастан"]
PARENT_F = ["Гүлнар", "Сәуле", "Динара", "Жанар", "Айгүл", "Ләйлә", "Назгүл", "Ботагөз", "Салтанат"]

TASKS = [
    ("Күнтізбелік-тақырыптық жоспар (КТЖ) тапсыру", "Сдать календарно-тематический план (КТП)", date(2025, 9, 10)),
    ("Электронды журналды толтыру (1-тоқсан)", "Заполнить электронный журнал (1 четверть)", date(2025, 10, 31)),
    ("Бөлім бойынша жиынтық бағалау талдауы", "Анализ суммативного оценивания за раздел", date(2025, 11, 20)),
    ("Ашық сабақ өткізу", "Провести открытый урок", date(2025, 12, 12)),
    ("Электронды журналды толтыру (2-тоқсан)", "Заполнить электронный журнал (2 четверть)", date(2025, 12, 26)),
    ("Үлгерімі төмен оқушылармен жұмыс жоспары", "План работы с неуспевающими учениками", date(2026, 1, 23)),
    ("Тоқсандық есеп (3-тоқсан)", "Отчёт за 3 четверть", date(2026, 3, 20)),
    ("Біліктілікті арттыру курсы бойынша есеп", "Отчёт о курсах повышения квалификации", date(2026, 4, 17)),
    ("Жылдық есеп", "Годовой отчёт", date(2026, 5, 22)),
]
OBSERVERS = ["Директор", "Оқу ісі жөніндегі орынбасар", "Әдістемелік бірлестік жетекшісі"]
CONTACT_TOPICS = ["grades", "attendance", "behavior", "olympiad", "ent", "general"]
COMPLAINT_CATS = ["teaching", "communication", "homework", "food", "transport", "safety"]
LEAVE_REASONS = ["relocation", "finance", "other_school", "dissatisfied", "academic"]
ADM_SOURCES = ["recommend", "instagram", "site", "event"]


def school_days():
    d, out = YEAR_START, []
    while d <= YEAR_END:
        if d.weekday() < 5 and d not in PUBLIC_DAYS and not any(a <= d <= b for a, b in HOLIDAYS):
            out.append(d)
        d += timedelta(days=1)
    return out


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def rand_date(rng, a, b):
    return a + timedelta(days=rng.randint(0, (b - a).days))


def seed(path, rng_seed=2026):
    rng = random.Random(rng_seed)
    conn = init_db(path)
    ex = conn.execute
    days = school_days()

    for kz, ru in SUBJECTS:
        ex("INSERT INTO subjects(name_kz, name_ru) VALUES (?,?)", (kz, ru))

    teacher_level, teacher_late = {}, {}
    for i, (name, subj, cat, hired, level, late) in enumerate(TEACHERS, start=1):
        ex("INSERT INTO teachers(id, full_name, subject_id, category, hire_date) VALUES (?,?,?,?,?)",
           (i, name, subj, cat, hired))
        teacher_level[i], teacher_late[i] = level, late
    former = []
    for name, subj, cat, hired, left, reason in FORMER_TEACHERS:
        cur = ex("INSERT INTO teachers(full_name, subject_id, category, hire_date, left_date, left_reason) "
                 "VALUES (?,?,?,?,?,?)", (name, subj, cat, hired, left, reason))
        former.append(cur.lastrowid)

    # Классы и нагрузка: первый учитель предмета ведёт 5–8 классы, второй — 9–11
    class_ids = {}
    for idx, (cname, grade) in enumerate(CLASSES, start=1):
        homeroom = [1, 3, 7, 13, 5, 9, 15, 11][idx - 1]
        ex("INSERT INTO classes(id, name, grade, homeroom_teacher_id) VALUES (?,?,?,?)", (idx, cname, grade, homeroom))
        class_ids[idx] = grade
    teacher_of = {}
    for cid, grade in class_ids.items():
        for sid in range(1, len(SUBJECTS) + 1):
            if sid == 5 and grade < 7:      # физика с 7 класса
                continue
            if sid == 6 and grade < 8:      # химия с 8 класса
                continue
            tid = (sid - 1) * 2 + (1 if grade <= 8 else 2)
            ex("INSERT INTO teaching VALUES (?,?,?)", (tid, cid, sid))
            teacher_of[(cid, sid)] = tid

    # Ученики
    students = []
    sid_counter = 0
    for cid, grade in class_ids.items():
        n = rng.randint(15, 19)
        for _ in range(n):
            sid_counter += 1
            female = rng.random() < 0.5
            sur = rng.choice(SURNAMES) + ("а" if female else "")
            first = rng.choice(FEMALE if female else MALE)
            ability = clamp(rng.gauss(0, 1), -2.2, 2.2)
            enrolled = date(2025, 9, 1) - timedelta(days=365 * rng.randint(0, grade - 4))
            if rng.random() < 0.07:
                enrolled = rand_date(rng, date(2025, 9, 15), date(2026, 2, 20))
            left, reason = None, None
            if rng.random() < 0.06 and enrolled < date(2025, 10, 1):
                left = rand_date(rng, date(2025, 10, 15), date(2026, 4, 30))
                reason = rng.choice(LEAVE_REASONS)
                if ability < -0.8:
                    reason = rng.choice(["academic", "dissatisfied", "other_school"])
            parent = f"{rng.choice(PARENT_F + PARENT_M)} {sur.rstrip('а') + ('а' if rng.random() < 0.6 else '')}"
            phone = f"+7 70{rng.randint(1, 8)} {rng.randint(100, 999)} {rng.randint(10, 99)} {rng.randint(10, 99)}"
            ex("INSERT INTO students(id, full_name, class_id, enrolled_date, left_date, left_reason, parent_name, parent_phone) "
               "VALUES (?,?,?,?,?,?,?,?)",
               (sid_counter, f"{sur} {first}", cid, enrolled.isoformat(), left and left.isoformat(), reason, parent, phone))
            students.append(dict(id=sid_counter, cid=cid, grade=grade, a=ability, enrolled=enrolled, left=left))

    # Посещаемость учеников
    for s in students:
        p_abs = clamp(0.025 + 0.03 * max(0, -s["a"]) + rng.random() * 0.03, 0, 0.2)
        p_late = 0.02 + rng.random() * 0.04
        rows = []
        for d in days:
            if d < max(s["enrolled"], YEAR_START) or (s["left"] and d > s["left"]):
                continue
            r = rng.random()
            st = "present"
            if r < p_abs * 0.6:
                st = "absent"
            elif r < p_abs:
                st = "excused"
            elif r < p_abs + p_late:
                st = "late"
            rows.append((s["id"], d.isoformat(), st))
        conn.executemany("INSERT INTO student_attendance VALUES (?,?,?)", rows)

    # Приход учителей
    for tid in range(1, len(TEACHERS) + 1):
        rows = []
        for d in days:
            r = rng.random()
            if r < 0.008:
                rows.append((tid, d.isoformat(), "absent", None, 0))
            elif r < 0.025:
                rows.append((tid, d.isoformat(), "excused", None, 0))
            elif r < 0.025 + teacher_late[tid]:
                m = rng.randint(3, 35)
                rows.append((tid, d.isoformat(), "late", f"08:{m:02d}", m))
            else:
                rows.append((tid, d.isoformat(), "on_time", f"07:{rng.randint(30, 59):02d}", 0))
        conn.executemany("INSERT INTO teacher_arrivals VALUES (?,?,?,?,?)", rows)
    for tid, (_n, _s, _c, hired, left, _r) in zip(former, FORMER_TEACHERS):
        rows = []
        for d in days:
            if d.isoformat() > left:
                break
            late = rng.random() < 0.12
            rows.append((tid, d.isoformat(), "late" if late else "on_time",
                         "08:12" if late else "07:50", 12 if late else 0))
        conn.executemany("INSERT INTO teacher_arrivals VALUES (?,?,?,?,?)", rows)

    # Контроль уроков
    for tid in range(1, len(TEACHERS) + 1):
        lv = teacher_level[tid]
        classes_t = [c for (c, s), t in teacher_of.items() if t == tid]
        for k in range(rng.randint(3, 5)):
            d = rand_date(rng, date(2025, 9, 20) + timedelta(days=55 * k), date(2025, 10, 30) + timedelta(days=55 * k))
            d = min(d, date(2026, 5, 15))
            while d.weekday() >= 5:
                d -= timedelta(days=1)
            parts = [clamp(round(rng.gauss(18 + 5 * lv + k * 0.4, 2.2)), 6, 25) for _ in range(4)]
            if lv < -0.4:
                comment = rng.choice(["Сабақ мақсаты анық емес", "Кері байланыс жеткіліксіз", "Сыныпты басқару әлсіз"])
            elif lv > 0.5:
                comment = rng.choice(["Сабақ жоғары деңгейде өтті", "Оқушылар белсенді", "Саралап оқыту жақсы қолданылды"])
            else:
                comment = rng.choice(["Сабақ жоспарға сай өтті", "Уақытты тиімді пайдалану керек", "Бағалау критерийлерін нақтылау керек"])
            ex("INSERT INTO lesson_observations(teacher_id, class_id, date, observer, planning, methods, engagement, assessment, comment) "
               "VALUES (?,?,?,?,?,?,?,?,?)", (tid, rng.choice(classes_t), d.isoformat(), rng.choice(OBSERVERS), *parts, comment))

    # Задания учителям
    for tid in range(1, len(TEACHERS) + 1):
        lv = teacher_level[tid]
        for kz, ru, due in TASKS:
            r = rng.random()
            if r < 0.78 + 0.15 * lv:
                done = due - timedelta(days=rng.randint(0, 5))
            elif r < 0.95:
                done = due + timedelta(days=rng.randint(2, 14))
            else:
                done = None
            ex("INSERT INTO teacher_tasks(teacher_id, title_kz, title_ru, due_date, done_date) VALUES (?,?,?,?,?)",
               (tid, kz, ru, due.isoformat(), done and done.isoformat()))

    # Оценки и диагностики
    for s in students:
        for (cid, subj), tid in teacher_of.items():
            if cid != s["cid"]:
                continue
            lv = teacher_level[tid]
            for qn in range(1, 5):
                if s["left"] and s["left"] < QUARTER_ENDS[qn - 1]:
                    continue
                if s["enrolled"] > QUARTER_ENDS[qn - 1] - timedelta(days=20):
                    continue
                v = 3.75 + 0.62 * s["a"] + 0.12 * lv + 0.09 * lv * (qn - 1) + rng.gauss(0, 0.38)
                ex("INSERT INTO grades VALUES (?,?,?,?)", (s["id"], subj, qn, int(clamp(round(v), 2, 5))))
            if subj in DIAG_SUBJECTS and s["enrolled"] < date(2025, 9, 10):
                start = clamp(round(56 + 13 * s["a"] + rng.gauss(0, 6)), 8, 98)
                growth_end = 9 + 8 * lv + rng.gauss(0, 4)
                pts = [("start", date(2025, 9, 16), start),
                       ("mid", date(2026, 1, 21), clamp(round(start + growth_end * 0.45 + rng.gauss(0, 3)), 5, 100)),
                       ("end", date(2026, 5, 12), clamp(round(start + growth_end), 5, 100))]
                for kind, d, sc in pts:
                    if s["left"] and s["left"] < d:
                        continue
                    ex("INSERT INTO diagnostics VALUES (?,?,?,?,?)", (s["id"], subj, kind, d.isoformat(), sc))

    # Пробные ЕНТ и олимпиады
    for s in students:
        if s["grade"] == 11:
            mocks = [date(2025, m, 18) for m in (10, 11, 12)] + [date(2026, m, 18) for m in (1, 2, 3, 4)]
        elif s["grade"] == 10:
            mocks = [date(2026, 2, 18), date(2026, 4, 18)]
        else:
            mocks = []
        for i, d in enumerate(mocks):
            if s["left"] and s["left"] < d:
                continue
            sc = clamp(round(68 + 19 * s["a"] + 2.6 * i + rng.gauss(0, 5)), 20, 138)
            ex("INSERT INTO ent_mocks VALUES (?,?,?)", (s["id"], d.isoformat(), sc))
        if s["a"] > 0.7 and s["grade"] >= 6 and not s["left"]:
            subj = rng.choice([1, 4, 5, 6, 7, 8, 9, 10] if s["grade"] >= 8 else [1, 2, 4, 8, 9])
            ex("INSERT INTO olympiads(student_id, subject_id, level, result, date) VALUES (?,?,?,?,?)",
               (s["id"], subj, "school", "prize1" if s["a"] > 1.2 else "prize2", "2025-10-22"))
            if s["a"] > 1.0:
                res = "prize2" if s["a"] > 1.6 else rng.choice(["participant", "prize3"])
                ex("INSERT INTO olympiads(student_id, subject_id, level, result, date) VALUES (?,?,?,?,?)",
                   (s["id"], subj, "city", res, "2025-12-10"))
                if s["a"] > 1.5:
                    ex("INSERT INTO olympiads(student_id, subject_id, level, result, date) VALUES (?,?,?,?,?)",
                       (s["id"], subj, "region", rng.choice(["participant", "prize3"]), "2026-02-05"))

    # Связь с родителями
    for s in students:
        homeroom = conn.execute("SELECT homeroom_teacher_id FROM classes WHERE id=?", (s["cid"],)).fetchone()[0]
        n = rng.randint(1, 3) + (3 if s["a"] < -0.8 else 0)
        end = s["left"] or YEAR_END
        for _ in range(n):
            if s["a"] < -0.8:
                topic = rng.choice(["grades", "grades", "attendance", "behavior", "general"])
            elif s["a"] > 1.0:
                topic = rng.choice(["olympiad", "ent" if s["grade"] >= 10 else "olympiad", "general"])
            else:
                topic = rng.choice(CONTACT_TOPICS[:3] + ["general", "general"])
            ex("INSERT INTO parent_contacts(student_id, teacher_id, date, channel, topic) VALUES (?,?,?,?,?)",
               (s["id"], homeroom, rand_date(rng, max(s["enrolled"], YEAR_START), end).isoformat(),
                rng.choice(["call", "meeting", "message", "message"]), topic))

    # Опросы и жалобы родителей
    for s in students:
        for d in (date(2025, 12, 15), date(2026, 5, 15)):
            if (s["left"] and s["left"] < d) or s["enrolled"] > d or rng.random() < 0.18:
                continue
            base = 4.3 + 0.2 * s["a"] + (0.3 if d.year == 2026 else 0)
            ex("INSERT INTO parent_feedback(student_id, date, kind, rating) VALUES (?,?,?,?)",
               (s["id"], d.isoformat(), "survey", int(clamp(round(rng.gauss(base, 0.6)), 1, 5))))
    weak = [t for t, lv in teacher_level.items() if lv < -0.2]
    for _ in range(26):
        s = rng.choice(students)
        cat = rng.choice(COMPLAINT_CATS)
        tid = None
        if cat in ("teaching", "communication", "homework"):
            pool = [t for (c, _sj), t in teacher_of.items() if c == s["cid"]]
            tid = rng.choice([t for t in pool if t in weak] or pool) if rng.random() < 0.7 else rng.choice(pool)
        d = rand_date(rng, date(2025, 9, 10), date(2026, 5, 20))
        st = "open" if d > date(2026, 5, 1) and rng.random() < 0.6 else "resolved"
        ex("INSERT INTO parent_feedback(student_id, teacher_id, date, kind, category, status) VALUES (?,?,?,?,?,?)",
           (s["id"], tid, d.isoformat(), "complaint", cat, st))

    # Заявки на поступление
    for _ in range(96):
        d = rand_date(rng, date(2025, 6, 1), date(2026, 5, 25))
        if d < date(2025, 9, 1) and rng.random() < 0.5:
            d = rand_date(rng, date(2026, 3, 1), date(2026, 5, 25))
        r = rng.random()
        st = "enrolled" if r < 0.34 else "declined" if r < 0.52 else "tested" if r < 0.75 else "applied"
        ex("INSERT INTO admissions(date, grade, source, status) VALUES (?,?,?,?)",
           (d.isoformat(), rng.randint(5, 11), rng.choices(ADM_SOURCES, [5, 3, 2, 2])[0], st))

    conn.commit()
    conn.close()
