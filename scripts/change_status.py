#!/usr/bin/env python3
"""Смена статуса цели или задачи (md-реализация Кимби СУ).

Использование:
  python3 change_status.py <путь-к-директории-объекта> <статус> [--outcome …]

  статусы цели:   formulating | planning | ready_to_start | set | ended
  статусы задачи: formulating | planning | ready_to_start | in_progress | ended
  --outcome: success | failed | canceled — обязателен при ended

Механическая часть атомарной процедуры из implementation.md:
  1. таблица `## Данные`: Статус, Исход, фактические даты (у задачи
     «Дата начала» при in_progress и «Дата завершения» при ended, у цели
     «Дата завершения» при ended при любом исходе — если пустые);
  2. перемещение директории объекта в статусную директорию;
  3. обновление входящих ссылок по всем md-файлам системы (включая
     %20-кодированные пути в markdown-ссылках).

При старте задачи (in_progress) — неблокирующее предупреждение о незакрытых
зависимостях из строки «Зависит от» (закрыта = «завершена» с исходом «успех»).

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
        "planning": "2 planning",
        "ready_to_start": "3 ready_to_start",
        "set": "4 set",
        "ended": "5 ended",
    },
    "task.md": {
        "formulating": "1 formulating",
        "planning": "2 planning",
        "ready_to_start": "3 ready_to_start",
        "in_progress": "4 in_progress",
        "ended": "5 ended",
    },
}
ALL_STATUSES = sorted({s for dirs in STATUS_DIRS.values() for s in dirs})
STATUS_RU = {
    "formulating": "формулируется",
    "planning": "планируется",
    "ready_to_start": "на старте",
    "set": "поставлена",
    "in_progress": "в работе",
    "ended": "завершена",
}
OUTCOMES = ("success", "failed", "canceled")
OUTCOME_RU = {"success": "успех", "failed": "провал", "canceled": "отмена"}


def fail(msg: str) -> None:
    print(f"Ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def find_root(path: Path) -> Path:
    """Корень системы — ближайший предок с .git."""
    for p in (path, *path.parents):
        if (p / ".git").exists():
            return p
    fail("не найден корень системы (директория с .git) выше объекта")


def row_pat(label: str) -> re.Pattern:
    return re.compile(rf"^\|\s*{re.escape(label)}\s*\|(.*)\|\s*$")


def get_row(lines: list, label: str) -> str:
    """Значение ячейки строки таблицы `## Данные` по метке поля."""
    pat = row_pat(label)
    for line in lines:
        m = pat.match(line)
        if m:
            return m.group(1).strip()
    return ""


def set_row(lines: list, label: str, value: str, only_if_empty: bool = False) -> bool:
    """Записать значение в ячейку строки таблицы по метке поля."""
    pat = row_pat(label)
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        if only_if_empty and m.group(1).strip():
            return False
        lines[i] = f"| {label} | {value} |"
        return True
    return False


def link_paths(cell: str) -> list:
    """Пути из markdown-ссылок в ячейке: [Название](путь) → путь."""
    return [p.strip() for p in re.findall(r"\]\(([^)]+)\)", cell)]


def read_lines(path: Path) -> list:
    return path.read_text(encoding="utf-8").split("\n")


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

    # 1. таблица `## Данные`
    lines = read_lines(obj_file)
    if not set_row(lines, "Статус", STATUS_RU[args.status]):
        fail("в объекте нет строки «Статус» в таблице «## Данные»")
    today = datetime.date.today().isoformat()
    if args.outcome:
        set_row(lines, "Исход", OUTCOME_RU[args.outcome])
    if obj_file.name == "task.md":
        if args.status == "in_progress":
            set_row(lines, "Дата начала", today, only_if_empty=True)
        if args.status == "ended":
            set_row(lines, "Дата завершения", today, only_if_empty=True)
    else:
        if args.status == "ended":
            set_row(lines, "Дата завершения", today, only_if_empty=True)
    obj_file.write_text("\n".join(lines), encoding="utf-8")

    # предупреждение о незакрытых зависимостях при старте задачи
    open_deps = []
    if obj_file.name == "task.md" and args.status == "in_progress":
        for dep in link_paths(get_row(lines, "Зависит от")):
            dep_path = root / dep
            dep_file = dep_path if dep_path.is_file() else dep_path / "task.md"
            if not dep_file.is_file():
                open_deps.append(f"{dep} — не найдена")
                continue
            dep_lines = read_lines(dep_file)
            dep_status = get_row(dep_lines, "Статус")
            dep_outcome = get_row(dep_lines, "Исход")
            if not (dep_status == STATUS_RU["ended"] and dep_outcome == OUTCOME_RU["success"]):
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
    print("данные: Статус=" + STATUS_RU[args.status] + (f", Исход={OUTCOME_RU[args.outcome]}" if args.outcome else ""))
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