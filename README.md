# kimbi-ms-md — реализация Кимби СУ на markdown и git

Реализация фреймворка системы управления Кимби СУ в виде директорий
с md-файлами и git. Самодостаточна: текст реализуемой версии фреймворка —
внутри.

- Фреймворк (понятия, статусы, связи) —
  [framework/framework.md](framework/framework.md)
- Устройство реализации —
  [framework/implementation.md](framework/implementation.md)
- Руководство для ИИ-агента — [ai_agent/guide.md](ai_agent/guide.md)
- Шаблоны объектов — [templates/](templates/)
- Скрипты — [scripts/](scripts/)

## Создание инстанса

Требования: git, python3.

```
git clone https://github.com/cheburatino/kimbi-ms-md.git
python3 kimbi-ms-md/scripts/init_instance.py romashka-ms
```

Рядом с клоном появится директория инстанса: структура системы, README,
точки входа для ИИ-агентов, указатель на реализацию и git-репозиторий
(первый коммит — `init`). Останется привязать удалённый репозиторий.

## Фреймворк

`framework/framework.md` — копия текста фреймворка той версии, которую
реализует этот репозиторий (сейчас — kimbi-ms-framework, коммит `04686a4`).
Канонически фреймворк развивается в
[kimbi-ms-framework](https://github.com/cheburatino/kimbi-ms-framework);
копия не редактируется на месте, а обновляется оттуда вместе с приведением
реализации в соответствие — одной операцией.

Кастомизация фреймворка под себя — форк этого репозитория: копия
фреймворка и реализация меняются вместе.