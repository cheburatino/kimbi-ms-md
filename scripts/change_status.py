#!/usr/bin/env python3
"""Смена статуса цели или задачи (md-реализация Кимби СУ).

Использование:
  python3 change_status.py <путь-к-директории-объекта> <статус> [--outcome …]

  статусы цели:   formulating | formulated | set | ended
  статусы задачи: planning | ready | in_progress | ended
  --outcome: success | failed | canceled — обязателен при ended

Механическая часть атомарной процедуры из implementation.md:
  1. front matter: status, outcome, фактические даты (у задачи start_date
     при in_progress и end_date при ended, у цели achieve_date при ended
     с исходом success — если пустые);
  2. перемещение директории объекта в статусную директорию;
  3. обновление входящих ссылок по всем md-файлам системы (включая
     %20-кодированные пути в markdown-ссылках).

При старте задачи (in_progress) — неблокирующее предупреждение о незакрытых
зависимостях из depends_on (закрыта = ended с исходом success).

Смысловая часть — заполнить результат и сделать коммит — за агентом
или человеком.
"""

import argparse
import datetime
import re
import sys
from pathlib import Path

STATUS_DIRS = {
    "goal.md": {
        "formulating": "1 formulating",
        "formulated": "2 formulated",
        "set": "3 set",
        "ended": "4 ended",
    },
    "task.md": {
        "planning": "1 planning",
        "ready": "2 ready",
        "in_progress": "3 in_progress",
        "ended": "4 ended",
    },
}
ALL_STATUSES = sorted({s for dirs in STATUS_DIRS.values() for s in dirs})
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


def get_scalar(fm_lines: list, key: str) -> str:
    """Значение скалярного поля front matter (без комментария)."""
    pat = re.compile(rf"^{re.escape(key)}:\s*([^#]*?)\s*(#.*)?$")
    for line in fm_lines:
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return ""


def get_list_field(fm_lines: list, key: str) -> list:
    """Значения YAML-списка: инлайн `[a, b]` или блок строк `- item`."""
    for i, line in enumerate(fm_lines):
        m = re.match(rf"^{re.escape(key)}:\s*(.*)$", line)
        if not m:
            continue
        inline = m.group(1).strip()
        if inline:
            return [v.strip().strip("'\"") for v in inline.strip("[]").split(",") if v.strip()]
        vals = []
        for nxt in fm_lines[i + 1:]:
            lm = re.match(r"^\s+-\s*(.+?)\s*$", nxt)
            if lm:
                vals.append(lm.group(1).strip("'\""))
            elif nxt.strip() == "":
                continue
            else:  # следующее поле front matter
                break
        return vals
    return []


def read_fm_lines(path: Path) -> list:
    """Строки front matter файла объекта; пустой список, если его нет."""
    m = re.match(r"^---\n(.*?)\n---\n", path.read_text(encoding="utf-8"), re.DOTALL)
    return m.group(1).split("\n") if m else []


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Смена статуса цели или задачи",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    ap.add_argument("object_dir", help="директория цели или задачи")
    ap.add_argument("status", choices=ALL_STATUSES, help="новый статус")
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
    status_dirs = STATUS_DIRS[obj_file.name]
    if args.status not in status_dirs:
        kind = "цели" if obj_file.name == "goal.md" else "задачи"
        fail(
            f"статус «{args.status}» не применим к объекту типа {obj_file.name}; "
            f"статусы {kind}: {', '.join(status_dirs)}"
        )
    if args.status == "ended" and not args.outcome:
        fail("для статуса ended обязателен --outcome")
    if args.outcome and args.status != "ended":
        fail("--outcome имеет смысл только со статусом ended")
    if obj_dir.parent.name not in status_dirs.values():
        fail(f"объект лежит не в статусной директории: «{obj_dir.parent.name}»")

    root = find_root(obj_dir)
    new_dir = obj_dir.parent.parent / status_dirs[args.status] / obj_dir.name
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
    if obj_file.name == "task.md":
        if args.status == "in_progress":
            set_field(fm_lines, "start_date", today, only_if_empty=True)
        if args.status == "ended":
            set_field(fm_lines, "end_date", today, only_if_empty=True)
    else:
        if args.status == "ended" and args.outcome == "success":
            set_field(fm_lines, "achieve_date", today, only_if_empty=True)
    obj_file.write_text(
        "---\n" + "\n".join(fm_lines) + "\n---\n" + text[m.end():], encoding="utf-8"
    )

    # предупреждение о незакрытых зависимостях при старте задачи
    open_deps = []
    if obj_file.name == "task.md" and args.status == "in_progress":
        for dep in get_list_field(fm_lines, "depends_on"):
            dep_path = root / dep
            dep_file = dep_path / "task.md" if dep_path.is_dir() else dep_path
            if not dep_file.is_file():
                open_deps.append(f"{dep} — не найдена")
                continue
            dep_fm = read_fm_lines(dep_file)
            dep_status = get_scalar(dep_fm, "status")
            dep_outcome = get_scalar(dep_fm, "outcome")
            if not (dep_status == "ended" and dep_outcome == "success"):
                state = dep_status or "?"
                if dep_outcome:
                    state += f"/{dep_outcome}"
                open_deps.append(f"{dep} — {state}")

    # 2. перемещение
    old_rel = obj_dir.relative_to(root).as_posix()
    new_rel = new_dir.relative_to(root).as_posix()
    obj_dir.rename(new_dir)

    # 3. входящие ссылки. Путь заменяется только на границе сегмента: следом
    # должен идти разделитель, закрытие ссылки/списка или конец строки — иначе
    # путь-префикс затронул бы «соседа» с более длинным слагом (foo → foo-bar).
    boundary = r"""(?=[/\s"')\]>,}]|$)"""
    pairs = [
        (old_rel, new_rel),
        (old_rel.replace(" ", "%20"), new_rel.replace(" ", "%20")),
    ]
    subs = [(re.compile(re.escape(old) + boundary), new) for old, new in pairs]
    changed = []
    for p in sorted(root.rglob("*.md")):
        if ".git" in p.parts:
            continue
        t = p.read_text(encoding="utf-8")
        t2 = t
        for pat, new in subs:
            t2 = pat.sub(lambda _m, r=new: r, t2)
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
    if open_deps:
        print("Предупреждение: при старте есть незакрытые зависимости:", file=sys.stderr)
        for d in open_deps:
            print(f"  {d}", file=sys.stderr)
    print("Дальше: заполнить результат (при завершении) и закоммитить.")


if __name__ == "__main__":
    main()