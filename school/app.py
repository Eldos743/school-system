"""Веб-приложение: три панели (учредитель, учителя, ученики)."""
import os
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for

from . import charts, metrics
from .db import close_db, q, q1
from .i18n import LANGS, make_t

BASE = Path(__file__).resolve().parent.parent
QUARTERS = [1, 2, 3, 4]


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DATABASE"] = db_path or os.environ.get("SCHOOL_DB", str(BASE / "instance" / "school.db"))
    app.teardown_appcontext(close_db)
    app.jinja_env.filters["dt"] = lambda v: f"{v[8:10]}.{v[5:7]}.{v[:4]}" if v else ""
    app.jinja_env.globals.update(charts=charts, metrics=metrics, QUARTERS=QUARTERS)

    def ctx(lang, endpoint, **kw):
        if lang not in LANGS:
            abort(404)
        other = "ru" if lang == "kz" else "kz"
        t = make_t(lang)
        month = lambda m: t("months")[int(m[5:7]) - 1]
        return dict(lang=lang, t=t, endpoint=endpoint,
                    ql=lambda xs: [t("q_short", x) for x in xs],
                    ml=lambda xs: [month(x) for x in xs],
                    other_url=url_for(endpoint, lang=other, **kw),
                    month=month,
                    name=lambda row, base="name": row[f"{base}_{lang}"])

    @app.route("/")
    def root():
        return redirect(url_for("founder", lang="kz"))

    @app.route("/<lang>/")
    @app.route("/<lang>/index.html")
    def founder(lang):
        c = ctx(lang, "founder")
        return render_template("founder.html", d=metrics.founder_overview(), **c)

    @app.route("/<lang>/teachers.html")
    def teachers(lang):
        c = ctx(lang, "teachers")
        rows = metrics.teacher_components()
        return render_template("teachers.html", rows=rows, weights=metrics.KPI_WEIGHTS, **c)

    @app.route("/<lang>/teacher/<int:tid>.html")
    def teacher(lang, tid):
        c = ctx(lang, "teacher", tid=tid)
        d = metrics.teacher_detail(tid)
        if d is None:
            abort(404)
        classes = {r["id"]: r for r in q("SELECT * FROM classes")}
        return render_template("teacher.html", d=d, recs=metrics.support_recommendations(d["c"]),
                               weights=metrics.KPI_WEIGHTS, classes=classes, **c)

    @app.route("/<lang>/students.html")
    @app.route("/<lang>/students/<int:class_id>.html")
    def students(lang, class_id=None):
        c = ctx(lang, "students", **({"class_id": class_id} if class_id else {}))
        classes = q("SELECT * FROM classes ORDER BY grade, name")
        rows = metrics.students_overview(class_id)
        cur = q1("SELECT * FROM classes WHERE id=?", class_id) if class_id else None
        return render_template("students.html", rows=rows, classes=classes, cur=cur,
                               lq=metrics.last_quarter(), **c)

    @app.route("/<lang>/student/<int:sid>.html")
    def student(lang, sid):
        c = ctx(lang, "student", sid=sid)
        d = metrics.student_detail(sid)
        if d is None:
            abort(404)
        return render_template("student.html", d=d, ENT_THRESHOLD=metrics.ENT_THRESHOLD,
                               ENT_GRANT=metrics.ENT_GRANT, **c)

    return app
