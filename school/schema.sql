-- Схема базы данных учётной системы школы (SQLite; переносится на PostgreSQL).

PRAGMA foreign_keys = ON;

CREATE TABLE subjects (
    id        INTEGER PRIMARY KEY,
    name_kz   TEXT NOT NULL,
    name_ru   TEXT NOT NULL
);

CREATE TABLE teachers (
    id           INTEGER PRIMARY KEY,
    full_name    TEXT NOT NULL,
    subject_id   INTEGER REFERENCES subjects(id),
    category     TEXT,            -- педагог, модератор, сарапшы, зерттеуші, шебер
    hire_date    TEXT NOT NULL,
    left_date    TEXT,
    left_reason  TEXT
);

CREATE TABLE classes (
    id                  INTEGER PRIMARY KEY,
    name                TEXT NOT NULL,       -- 7А
    grade               INTEGER NOT NULL,
    homeroom_teacher_id INTEGER REFERENCES teachers(id)
);

-- Кто какой предмет ведёт в каком классе
CREATE TABLE teaching (
    teacher_id INTEGER NOT NULL REFERENCES teachers(id),
    class_id   INTEGER NOT NULL REFERENCES classes(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    PRIMARY KEY (class_id, subject_id)
);

CREATE TABLE students (
    id              INTEGER PRIMARY KEY,
    full_name       TEXT NOT NULL,
    class_id        INTEGER REFERENCES classes(id),
    enrolled_date   TEXT NOT NULL,
    left_date       TEXT,
    left_reason     TEXT,             -- код причины ухода
    parent_name     TEXT,
    parent_phone    TEXT
);

-- Посещаемость учеников по дням: present / late / absent / excused
CREATE TABLE student_attendance (
    student_id INTEGER NOT NULL REFERENCES students(id),
    date       TEXT NOT NULL,
    status     TEXT NOT NULL,
    PRIMARY KEY (student_id, date)
);

-- Приход учителей на работу
CREATE TABLE teacher_arrivals (
    teacher_id   INTEGER NOT NULL REFERENCES teachers(id),
    date         TEXT NOT NULL,
    status       TEXT NOT NULL,       -- on_time / late / absent / excused
    arrival_time TEXT,
    late_minutes INTEGER DEFAULT 0,
    PRIMARY KEY (teacher_id, date)
);

-- Контроль (посещение) уроков
CREATE TABLE lesson_observations (
    id          INTEGER PRIMARY KEY,
    teacher_id  INTEGER NOT NULL REFERENCES teachers(id),
    class_id    INTEGER REFERENCES classes(id),
    date        TEXT NOT NULL,
    observer    TEXT NOT NULL,
    planning    INTEGER NOT NULL,     -- каждая часть 0..25
    methods     INTEGER NOT NULL,
    engagement  INTEGER NOT NULL,
    assessment  INTEGER NOT NULL,
    comment     TEXT
);

-- Задания администрации учителю (КТП, отчёты, ведение журнала ...)
CREATE TABLE teacher_tasks (
    id          INTEGER PRIMARY KEY,
    teacher_id  INTEGER NOT NULL REFERENCES teachers(id),
    title_kz    TEXT NOT NULL,
    title_ru    TEXT NOT NULL,
    due_date    TEXT NOT NULL,
    done_date   TEXT
);

-- Четвертные оценки
CREATE TABLE grades (
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    quarter    INTEGER NOT NULL,      -- 1..4
    value      INTEGER NOT NULL,      -- 2..5
    PRIMARY KEY (student_id, subject_id, quarter)
);

-- Диагностические тесты: start / mid / end, результат в %
CREATE TABLE diagnostics (
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    kind       TEXT NOT NULL,
    date       TEXT NOT NULL,
    score      INTEGER NOT NULL,
    PRIMARY KEY (student_id, subject_id, kind)
);

-- Пробные ЕНТ (макс. 140 баллов)
CREATE TABLE ent_mocks (
    student_id INTEGER NOT NULL REFERENCES students(id),
    date       TEXT NOT NULL,
    score      INTEGER NOT NULL,
    PRIMARY KEY (student_id, date)
);

CREATE TABLE olympiads (
    id         INTEGER PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id),
    subject_id INTEGER NOT NULL REFERENCES subjects(id),
    level      TEXT NOT NULL,         -- school / city / region / republic
    result     TEXT NOT NULL,         -- participant / prize3 / prize2 / prize1
    date       TEXT NOT NULL
);

-- История связи с родителями
CREATE TABLE parent_contacts (
    id          INTEGER PRIMARY KEY,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    teacher_id  INTEGER REFERENCES teachers(id),
    date        TEXT NOT NULL,
    channel     TEXT NOT NULL,        -- call / meeting / message
    topic       TEXT NOT NULL         -- код темы
);

-- Отзывы и жалобы родителей
CREATE TABLE parent_feedback (
    id          INTEGER PRIMARY KEY,
    student_id  INTEGER REFERENCES students(id),
    teacher_id  INTEGER REFERENCES teachers(id),
    date        TEXT NOT NULL,
    kind        TEXT NOT NULL,        -- survey / complaint
    rating      INTEGER,              -- 1..5 для опроса
    category    TEXT,                 -- код категории жалобы
    status      TEXT                  -- open / resolved
);

-- Заявки на поступление
CREATE TABLE admissions (
    id          INTEGER PRIMARY KEY,
    date        TEXT NOT NULL,
    grade       INTEGER NOT NULL,
    source      TEXT NOT NULL,        -- recommend / instagram / site / event
    status      TEXT NOT NULL         -- applied / tested / enrolled / declined
);
