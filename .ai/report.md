# Отчет: TASK-2026-06-21-04

Статус: done

## Кратко

Провел диагностику verification tooling. Системный Python есть, но системные `pip`/`ensurepip`/`pytest` отсутствуют, а `sudo` без пароля недоступен. Без root удалось временно bootstrap-нуть `pip` из официальных Ubuntu `.deb` пакетов в `/tmp`, установить backend dev dependencies во временный target и запустить pytest. Domain tests проходят, но health-тест через `fastapi.testclient.TestClient` зависает на `client.get("/health")`; точка зависания зафиксирована через `faulthandler`. Docker CLI виден через Windows path, но Docker Desktop WSL integration для текущего distro не подключена, поэтому `docker compose config` недоступен.

## Измененные файлы

- `docs/development.md`
- `.ai/report.md`

## Запущенные проверки

- `pwd` — `/mnt/e/Projects/bitrix`.
- `uname -a` — WSL2 Linux `6.6.87.2-microsoft-standard-WSL2`.
- `cat /etc/os-release` — Ubuntu 24.04.3 LTS.
- `python3 --version` — Python 3.12.3.
- `which python3` — `/usr/bin/python3`.
- `which pip` — не найден.
- `python3 -m pip --version` — failed: `No module named pip`.
- `python3 -m ensurepip --version` — failed: `No module named ensurepip`.
- `which pytest` — не найден.
- `which apt` — `/usr/bin/apt`.
- `which sudo` — `/usr/bin/sudo`.
- `sudo -n true` — failed: `sudo: a password is required`.
- `apt-cache policy python3-pip python3-venv` — пакеты доступны, но не установлены.
- `which uv` / `which pipx` — не найдены.
- `which docker` — `/mnt/c/Program Files/Docker/Docker/resources/bin/docker`.
- `docker --version` и `docker compose version` — failed: Docker сообщает, что команда недоступна в этом WSL 2 distro и нужно включить Docker Desktop WSL integration.
- `apt download python3-pip python3-wheel` в `/tmp` — passed.
- `dpkg-deb -x ... /tmp/pip-bootstrap` — passed.
- `PYTHONPATH=/tmp/pip-bootstrap/usr/lib/python3/dist-packages python3 -m pip --version` — passed: pip 24.0.
- `TMPDIR=/tmp PYTHONPATH=/tmp/pip-bootstrap/usr/lib/python3/dist-packages python3 -m pip install --no-cache-dir --no-compile --target /tmp/bitrix-python-deps ".[dev]"` — passed after setting `TMPDIR=/tmp`.
- `PYTHONPATH=/tmp/bitrix-python-deps:/tmp/pip-bootstrap/usr/lib/python3/dist-packages python3 -m pytest` — started, collected 6 tests, `tests/test_contact_selection.py` passed 5 tests, then hung on `tests/test_health.py`.
- `faulthandler.dump_traceback_later(...)` around `TestClient(app).get("/health")` — confirmed hang inside Starlette/FastAPI TestClient request handling.
- Temporary dependency check with FastAPI 0.128.0 and `httpx2` — did not fix the `TestClient` hang; no dependency pin was kept.
- `python3 -m py_compile backend/app/domain/*.py backend/tests/test_*.py` — passed.
- Generated artifacts (`egg-info`, `.pytest_cache`, `__pycache__`, temporary dependency target) were removed from the repository.

## Критерии приемки

- Environment diagnostics are captured — выполнено.
- Python package tooling is installed or blocker documented — выполнено: system tooling still requires host/admin action; temporary `/tmp` bootstrap works only for this session.
- Backend dependencies are installed and `pytest` is run, or blocker documented — выполнено: dependencies installed in `/tmp`, pytest run; health test hang documented.
- Docker Compose validation is run, or Docker/host blocker documented — выполнено: Docker Desktop WSL integration is missing for this distro.
- No product functionality is added — выполнено.
- No secrets, raw Bitrix data, databases, Parquet, CSV, dependency folders, or virtual environments are committed — выполнено.

## Факты

- Current distro: Ubuntu 24.04.3 LTS under WSL2.
- Python exists at `/usr/bin/python3`, but system `pip` and `ensurepip` are absent.
- `sudo` requires an interactive password, so Codex cannot install `python3-pip` or `python3-venv` system-wide.
- Official Ubuntu `.deb` packages can be downloaded and extracted to `/tmp` without root.
- Setting `TMPDIR=/tmp` is required for the temporary pip install to finish cleanly; otherwise pip used Windows temp paths and hung/left partial installs.
- Docker CLI is exposed from Docker Desktop on Windows, but WSL integration is not active for this distro.

## Предположения

- Host/admin setup should install `python3-pip` and `python3-venv` with apt for a durable local dev setup.
- Host/admin setup should enable Docker Desktop WSL integration for this Ubuntu distro before Docker Compose checks can pass.
- The `TestClient` hang is a test/dependency runtime issue separate from missing Python package tooling.

## Неизвестное

- Whether `tests/test_health.py` passes in a normal venv created by system `python3-venv`.
- Whether the `TestClient` hang is specific to the temporary `/tmp` target install, current FastAPI/Starlette/httpx versions, WSL filesystem behavior, or another runtime interaction.
- Whether Docker Compose config passes after Docker Desktop WSL integration is enabled.

## Риски или следующий шаг

Host/admin action still required for durable tooling:

```bash
sudo apt update
sudo apt install python3-pip python3-venv
```

Then run:

```bash
cd backend
python3 -m pip install -e ".[dev]"
python3 -m pytest
```

For Docker, enable Docker Desktop WSL integration for this Ubuntu distro or connect/install a Linux Docker daemon, then run `docker compose config` from the repository root.
