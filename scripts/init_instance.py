#!/usr/bin/env python3
"""Создание нового инстанса Кимби СУ (md-реализация).

Использование:
  python3 init_instance.py <путь-к-инстансу>

Создаёт директорию инстанса: структура системы, README, точки входа для
ИИ-агентов (CLAUDE.md, AGENTS.md), указатель на фреймворк и реализацию
в базе знаний, git-репозиторий с первым коммитом `init`. Остаётся
привязать удалённый репозиторий.
"""

import subprocess
import sys
from pathlib import Path

FRAMEWORK_URL = "https://github.com/cheburatino/kimbi-ms-framework"
MD_URL = "https://github.com/cheburatino/kimbi-ms-md"

README = """\
# {name} — инстанс Кимби СУ

Этот репозиторий — **{name}**: инстанс системы управления Кимби СУ
на md-реализации.

- Фреймворк и реализация — указатель:
  [1 knowledge/tech/kimbi-ms.md](1%20knowledge/tech/kimbi-ms.md)

## Информация для ИИ-агента

Начни с руководства агента в локальном клоне md-реализации
(по умолчанию `../kimbi-ms-md/ai_agent/guide.md`; см. указатель):
начальная загрузка, сборка контекста, сценарии работы.

Локальные договорённости этого инстанса:

- пока нет.
"""

AGENT_ENTRY = "Прочитай `README.md` и следуй его разделу «Информация для ИИ-агента».\n"

POINTER = f"""\
# Кимби СУ / kimbi-ms — указатель

Система управления, по которой устроен этот репозиторий: цели, задачи,
знания; статусы — директориями; вся информация — в md-файлах и git.

Устройство системы — в репозитории реализации **kimbi-ms-md**
({MD_URL}): текст реализуемой версии фреймворка
(`framework/framework.md`), устройство носителя
(`framework/implementation.md`), руководство агента
(`ai_agent/guide.md`), шаблоны и скрипты. Локальный клон — рядом
с директорией инстанса: `../kimbi-ms-md`.

Канонически фреймворк развивается отдельно — **kimbi-ms-framework**
({FRAMEWORK_URL}); реализация содержит его копию.
"""

SPACES = {
    "2 goal": ("1 formulating", "2 planning", "3 ready_to_start", "4 set", "5 ended"),
    "3 task": ("1 formulating", "2 planning", "3 ready_to_start", "4 in_progress", "5 ended"),
}


def fail(msg: str) -> None:
    print(f"Ошибка: {msg}", file=sys.stderr)
    sys.exit(1)


def git(dest: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=dest, check=True, capture_output=True)


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0 if len(sys.argv) == 2 else 1)

    dest = Path(sys.argv[1]).resolve()
    if dest.exists():
        fail(f"{dest} уже существует")

    name = dest.name
    (dest / "1 knowledge" / "tech").mkdir(parents=True)
    (dest / "README.md").write_text(README.format(name=name), encoding="utf-8")
    (dest / "CLAUDE.md").write_text(AGENT_ENTRY, encoding="utf-8")
    (dest / "AGENTS.md").write_text(AGENT_ENTRY, encoding="utf-8")
    (dest / "1 knowledge" / "tech" / "kimbi-ms.md").write_text(POINTER, encoding="utf-8")
    for space, status_dirs in SPACES.items():
        for status_dir in status_dirs:
            d = dest / space / status_dir
            d.mkdir(parents=True)
            (d / ".gitkeep").touch()

    git(dest, "init", "-b", "main")
    git(dest, "add", "-A")
    git(dest, "commit", "-m", "init")

    print(f"Инстанс создан: {dest}")
    print("Дальше: привязать удалённый репозиторий —")
    print("  git remote add origin <url> && git push -u origin main")


if __name__ == "__main__":
    main()