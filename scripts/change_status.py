#!/usr/bin/env python3
"""Смена статуса цели или задачи (md-реализация Кимби СУ).

Использование:
  python3 change_status.py <путь-к-директории-объекта> <статус> [--outcome …]

  статус:    draft | in_progress | ended
  --outcome: success | failed | canceled — обязателен при ended

Механическая часть атомарной процедуры из md_implementation.md:
  1. front matter: status, outcome, фактические даты (start_date при
     in_progress, end_date при ended — если пустые);
  2. перемещение директории объекта в статусную директорию;
  3. обновление входящих ссылок по всем md-файлам системы (включая
     %20-кодированные пути в markdown-ссылках).

Смысловая часть — заполнить результат и сделать коммит — за агентом
или человеком.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

STATUS_DIRS = {"draft": "1 draft", "in_progress": "2 in_progress", "ended": "3 ended"}
OUTCOMES = ("success", "failed", "canceled")


def fail(msg: str) -> None:
    print(f"Ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def find_root(path: Path) -> Path:
    """Корень системы — ближайший предок с .git."""
    for p in (path, *path.parents):
        if (p / ".git").exists():
            return p
    fail("не найден корень системы (директория с .git) выше объекта")


def set_field(fm_lines: list, key: str, value: str, only_if_empty: bool = False) -> bool:
    """Заменить значение поля front matter, сохранив комментарий строки."""
    pat = re.compile(rf"^({re.escape(key)}:)\s*([^#]*?)\s*(#.*)?$")
    for i, line in enumerate(fm_lines):
        m = pat.match(line)
        if not m:
            continue
        if only_if_empty and m.group(2).strip():
            return False
        new = f"{m.group(1)} {value}".rstrip()
        if m.group(3):
            new += "  " + m.group(3)
        fm_lines[i] = new
        return True
    return False


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Смена статуса цели или задачи",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("object_dir", help="директория цели или задачи")
    ap.add_argument("status", choices=sorted(STATUS_DIRS), help="новый статус")
    ap.add_argument("--outcome", choices=OUTCOMES, help="исход — только при ended")
    args = ap.parse_args()

    obj_dir = Path(args.object_dir).resolve()
    if not obj_dir.is_dir():
        fail(f"{obj_dir} — не директория")
    obj_file = next(
        (obj_dir / n for n in ("goal.md", "task.md") if (obj_dir / n).is_file()), None
    )
    if obj_file is None:
        fail(f"в {obj_dir} нет goal.md или task.md")
    if args.status == "ended" and not args.outcome:
        fail("для статуса ended обязателен --outcome")
    if args.outcome and args.status != "ended":
        fail("--outcome имеет смысл только со статусом ended")
    if obj_dir.parent.name not in STATUS_DIRS.values():
        fail(f"объект лежит не в статусной директории: «{obj_dir.parent.name}»")

    root = find_root(obj_dir)
    new_dir = obj_dir.parent.parent / STATUS_DIRS[args.status] / obj_dir.name
    if new_dir == obj_dir:
        fail(f"объект уже в статусе {args.status}")
    if new_dir.exists():
        fail(f"{new_dir} уже существует")

    # 1. front matter
    text = obj_file.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        fail(f"в {obj_file.name} нет front matter")
    fm_lines = m.group(1).split("\n")
    if not set_field(fm_lines, "status", args.status):
        fail("во front matter нет поля status")
    today = datetime.date.today().isoformat()
    if args.outcome:
        set_field(fm_lines, "outcome", args.outcome)
    if args.status == "in_progress":
        set_field(fm_lines, "start_date", today, only_if_empty=True)
    if args.status == "ended":
        set_field(fm_lines, "end_date", today, only_if_empty=True)
    obj_file.write_text(
        "---\n" + "\n".join(fm_lines) + "\n---\n" + text[m.end():], encoding="utf-8"
    )

    # 2. перемещение
    old_rel = obj_dir.relative_to(root).as_posix()
    new_rel = new_dir.relative_to(root).as_posix()
    obj_dir.rename(new_dir)

    # 3. входящие ссылки
    pairs = [
        (old_rel, new_rel),
        (old_rel.replace(" ", "%20"), new_rel.replace(" ", "%20")),
    ]
    changed = []
    for p in sorted(root.rglob("*.md")):
        if ".git" in p.parts:
            continue
        t = p.read_text(encoding="utf-8")
        t2 = t
        for old, new in pairs:
            t2 = t2.replace(old, new)
        if t2 != t:
            p.write_text(t2, encoding="utf-8")
            changed.append(p.relative_to(root).as_posix())

    print(f"{old_rel} → {new_rel}")
    print("front matter: status=" + args.status + (f", outcome={args.outcome}" if args.outcome else ""))
    if changed:
        print("обновлены ссылки:")
        for c in changed:
            print(f"  {c}")
    else:
        print("входящих ссылок не найдено")
    print("Дальше: заполнить результат (при завершении) и закоммитить.")


if __name__ == "__main__":
    main()