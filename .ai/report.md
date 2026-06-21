# Отчет: TASK-2026-06-21-03

Статус: done

## Кратко

Добавлен первый backend domain scaffold: Pydantic-модели разрешенных MVP-сущностей, pure-функция выбора аналитического контакта сделки и focused unit tests для правил выбора. Добавлен план будущей синтетической интеграционной фикстуры. Документация обновлена без добавления Bitrix-интеграции, схем БД, analytics calculations или frontend.

## Измененные файлы

- `backend/app/domain/__init__.py`
- `backend/app/domain/models.py`
- `backend/app/domain/contact_selection.py`
- `backend/tests/test_contact_selection.py`
- `backend/pyproject.toml`
- `backend/README.md`
- `docs/data-model.md`
- `docs/testing.md`
- `docs/project-status.md`
- `docs/fixtures.md`
- `.ai/report.md`

## Запущенные проверки

- `cd backend && pip install -e ".[dev]"` — не выполнено: команда `pip` отсутствует (`/bin/bash: line 1: pip: command not found`).
- `cd backend && pytest` — не выполнено: команда `pytest` отсутствует (`/bin/bash: line 1: pytest: command not found`).
- `cd backend && python3 -m pip --version` — failed: `/usr/bin/python3: No module named pip`.
- `cd backend && python3 -m ensurepip --version` — failed: `/usr/bin/python3: No module named ensurepip`.
- `python3 -m py_compile backend/app/domain/*.py backend/tests/test_*.py` — passed.
- `docker compose config` — не выполнено: команда `docker` недоступна в текущем WSL 2 distro.
- `git status --short` — выполнялся.
- `git diff --stat HEAD` — выполнялся перед commit; показывает также незакоммиченные пользовательские изменения `.ai/task.md` и `AGENTS.md`, которые не относятся к этому task и не staged.

## Критерии приемки

- Domain model package exists and is importable — реализовано в `backend/app/domain/`; runtime import через pytest не проверен из-за отсутствия `pip`/dependencies.
- Pydantic models cover the allowed MVP entity shapes listed in scope — выполнено.
- Forbidden personal/contact fields are not introduced — выполнено.
- Analytical contact selection is implemented as pure backend domain logic — выполнено.
- Unit tests cover the required contact selection cases — выполнено в `backend/tests/test_contact_selection.py`; pytest не запущен из-за отсутствующего tooling.
- `docs/fixtures.md` documents the future integration fixture strategy from `SPEC.md` — выполнено.
- Relevant docs are updated and remain concise — выполнено.
- No real secrets, real Bitrix data, local databases, Parquet snapshots, or CSV exports are added — выполнено.
- `.ai/report.md` lists changed files, checks, acceptance status, remaining unknowns, and next step — выполнено.

## Факты

- Модели используют только allowlisted MVP-поля из `SPEC.md`.
- Выбор аналитического контакта возвращает `contact_id` или `None` для сделки без контактов.
- Unknown/missing contact type получает нейтральный fallback priority без hardcoded business-specific type values.
- `backend/pyproject.toml` теперь включает пакет `app.domain`.
- Frontend implementation остается заблокированным до утверждения design system.

## Предположения

- Меньшее числовое значение `ContactTypeRule.priority` означает более высокий приоритет выбора контакта.
- В нормальном dev-окружении с установленным `pip` команда `pip install -e ".[dev]"` установит backend runtime и test dependencies из `backend/pyproject.toml`.

## Неизвестное

- Пройдет ли `pytest` после установки dependencies в окружении с доступным `pip`.
- Пройдет ли `docker compose config` в окружении с доступным Docker.
- Реальные Bitrix field codes, contact type values, priorities, region mapping, pipelines, stages и currencies.

## Риски или следующий шаг

Следующий шаг: в окружении с `pip` выполнить `cd backend && pip install -e ".[dev]" && pytest`, затем спланировать storage schema и синтетическую интеграционную fixture data на базе `docs/fixtures.md`.
