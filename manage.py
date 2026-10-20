"""Управление проектом.

    python manage.py seed      — создать базу с демо-данными
    python manage.py run       — запустить сервер на http://127.0.0.1:5000
    python manage.py export    — собрать статическую демо-версию в папку demo/
"""
import os
import re
import shutil
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
DB = os.environ.get("SCHOOL_DB", str(BASE / "instance" / "school.db"))


def seed():
    from school.seed import seed as do_seed
    Path(DB).parent.mkdir(parents=True, exist_ok=True)
    do_seed(DB)
    print(f"Демо-база создана: {DB}")


def run():
    from school.app import create_app
    if not Path(DB).exists():
        seed()
    create_app(DB).run(debug=True)


def export(out=BASE / "demo"):
    """Обходит все страницы и сохраняет их как HTML-файлы с относительными ссылками."""
    from school.app import create_app
    if not Path(DB).exists():
        seed()
    app = create_app(DB)
    client = app.test_client()
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    seen, queue = set(), ["/kz/index.html", "/ru/index.html"]
    while queue:
        path = queue.pop()
        if path in seen:
            continue
        seen.add(path)
        resp = client.get(path)
        if resp.status_code != 200:
            raise SystemExit(f"{path}: {resp.status_code}")
        html = resp.get_data(as_text=True)
        for link in re.findall(r'href="(/(?:kz|ru)/[^"#?]*)"', html):
            if link.endswith("/"):
                link += "index.html"
            if link not in seen:
                queue.append(link)
        depth = path.count("/") - 1

        def rel(m):
            target = m.group(1)
            if target.endswith("/"):
                target += "index.html"
            return f'href="{"../" * depth}{target.lstrip("/")}"'
        html = re.sub(r'href="(/(?:kz|ru)/[^"]*)"', rel, html)
        dest = out / path.lstrip("/")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(html, encoding="utf-8")
    print(f"Сохранено страниц: {len(seen)} → {out}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    {"seed": seed, "run": run, "export": export}[cmd]()
