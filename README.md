# kimbi-ms-md — реализация Кимби СУ на markdown и git

Реализация фреймворка системы управления
[Кимби СУ / kimbi-ms-framework](https://github.com/cheburatino/kimbi-ms-framework)
в виде директорий с md-файлами и git.

- Устройство реализации — [md_implementation.md](md_implementation.md)
- Руководство для ИИ-агента — [agent_guide.md](agent_guide.md)
- Шаблоны объектов — [templates/](templates/)
- Скрипты — [scripts/](scripts/)

## Создание инстанса

Требования: git, python3.

```
git clone git@github.com:cheburatino/kimbi-ms-md.git
python3 kimbi-ms-md/scripts/init_instance.py romashka-ms
```

Рядом с клоном появится директория инстанса: структура системы, README,
точки входа для ИИ-агентов, указатель на фреймворк и git-репозиторий
(первый коммит — `init`). Останется привязать удалённый репозиторий.
Для локального чтения фреймворка рядом клонируется и kimbi-ms-framework.

## Соответствие фреймворку

Реализация соответствует kimbi-ms-framework, коммит `5fa010a` (2026-07-11).
При изменении фреймворка реализация приводится в соответствие следующей
операцией, отметка обновляется.