"""Inicializador desktop do Anatinus para Windows."""

import argparse
import json
import logging
import os
import socket
import time
import urllib.error
import urllib.request
from pathlib import Path
from threading import Thread

import uvicorn
import webview

HOST = "127.0.0.1"
PORT = int(os.environ.get("ANATINUS_PORT", "8765"))
BASE_URL = f"http://{HOST}:{PORT}"


def _data_directory() -> Path:
    configured = os.environ.get("ANATINUS_DATA_DIR")
    if configured:
        return Path(configured).expanduser()

    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        return Path(local_app_data) / "Anatinus"

    return Path.home() / "AppData" / "Local" / "Anatinus"


def _configure_logging() -> None:
    log_directory = _data_directory() / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_directory / "desktop.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        encoding="utf-8",
    )


def _show_error(message: str) -> None:
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, message, "Anatinus", 0x10)
    except Exception:
        logging.exception("Não foi possível abrir a mensagem de erro.")


def _is_port_open() -> bool:
    try:
        with socket.create_connection((HOST, PORT), timeout=0.5):
            return True
    except OSError:
        return False


def _is_anatinus_running() -> bool:
    try:
        with urllib.request.urlopen(f"{BASE_URL}/health", timeout=1.5) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload.get("app") == "Anatinus" and payload.get("status") == "ok"
    except (OSError, ValueError, urllib.error.URLError):
        return False


def _wait_for_server(server_thread: Thread) -> bool:
    for _ in range(80):
        if not server_thread.is_alive():
            return False
        if _is_anatinus_running():
            return True
        time.sleep(0.25)
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializador desktop do Anatinus.")
    parser.add_argument(
        "--smoke-test",
        action="store_true",
        help="inicia a API local e verifica a grade demo sem abrir a janela gráfica.",
    )
    args = parser.parse_args()
    smoke_test = args.smoke_test or os.environ.get("ANATINUS_SMOKE_TEST") == "1"

    _configure_logging()
    logging.info("Inicializando Anatinus desktop.")

    try:
        from app.main import app
    except Exception:
        logging.exception("Falha ao carregar a aplicação e o banco de dados.")
        if smoke_test:
            raise
        _show_error(
            "Não foi possível carregar os dados do Anatinus. "
            "Detalhes no log em %LOCALAPPDATA%\\Anatinus\\logs\\desktop.log."
        )
        return

    server = None
    server_thread = None
    owns_server = False

    if _is_port_open():
        if _is_anatinus_running():
            message = "O Anatinus já está aberto. Verifique as janelas em execução."
        else:
            message = (
                "A porta local necessária pelo Anatinus já está ocupada. "
                "Feche o programa que está usando essa porta e tente novamente."
            )
        if smoke_test:
            raise RuntimeError(message)
        _show_error(message)
        return

    config = uvicorn.Config(
        app,
        host=HOST,
        port=PORT,
        log_level="warning",
        access_log=False,
        log_config=None,
    )
    server = uvicorn.Server(config)
    server_thread = Thread(
        target=server.run,
        name="AnatinusAPI",
        daemon=True,
    )
    server_thread.start()
    owns_server = True

    try:
        if not _wait_for_server(server_thread):
            raise RuntimeError(
                "A API local não iniciou dentro do tempo esperado. "
                "Consulte o log em %LOCALAPPDATA%\\Anatinus\\logs\\desktop.log."
            )

        if smoke_test:
            def get_json(path):
                with urllib.request.urlopen(f"{BASE_URL}{path}", timeout=10) as response:
                    return json.loads(response.read().decode("utf-8"))

            classrooms = get_json("/classrooms/")
            subjects = get_json("/subjects/")
            teachers = get_json("/teachers/")
            timetable = get_json("/timetable/")

            lesson_units = 0
            for classroom in classrooms:
                for setting in classroom.get("subject_settings", []):
                    if (
                        classroom.get("has_groups")
                        and classroom.get("shift") != "Noite"
                        and setting.get("split")
                    ):
                        lesson_units += int(setting.get("joint_workload") or 0)
                        lesson_units += int(setting.get("workload_a") or 0)
                        lesson_units += int(setting.get("workload_b") or 0)
                    else:
                        lesson_units += int(setting.get("workload") or 0)

            schedule_class_ids = {item["classroom_id"] for item in timetable}
            schedule_class = next(
                (
                    classroom
                    for classroom in classrooms
                    if classroom["id"] in schedule_class_ids
                ),
                None,
            )
            group_counts = {}
            for item in timetable:
                group = item.get("student_group") or "Todos"
                group_counts[group] = group_counts.get(group, 0) + 1

            if (
                len(classrooms) != 20
                or len(subjects) != 102
                or len(teachers) != 51
                or lesson_units != 695
                or len(timetable) != 50
                or len(schedule_class_ids) != 1
                or any(item.get("teacher_id") is None for item in timetable)
                or group_counts != {"Todos": 22, "A": 14, "B": 14}
                or schedule_class is None
                or "INFORM" not in schedule_class.get("name", "").upper()
            ):
                raise RuntimeError(
                    "A base da planilha não passou na conferência: "
                    f"{len(classrooms)} turmas, {len(subjects)} disciplinas, "
                    f"{len(teachers)} docentes, {lesson_units} aulas semanais "
                    f"configuradas e {len(timetable)} aulas demonstrativas."
                )

            message = (
                "SMOKE TEST OK: API local ativa, 20 turmas da planilha "
                "e grade demonstrativa de 50 aulas do 3º Informática carregadas."
            )
            print(message, flush=True)
            logging.info(message)
            (_data_directory() / "smoke-test.ok").write_text(
                message,
                encoding="utf-8",
            )
            return

        window = webview.create_window(
            "Anatinus",
            BASE_URL,
            width=1360,
            height=900,
            min_size=(980, 680),
            background_color="#08090a",
        )

        def stop_local_server(*_args) -> None:
            logging.info("Janela fechada; encerrando a API local.")
            server.should_exit = True

        window.events.closed += stop_local_server
        webview.start(debug=False)
    except Exception:
        logging.exception("Falha ao iniciar o Anatinus.")
        if smoke_test:
            raise
        _show_error(
            "Não foi possível abrir a janela do Anatinus. "
            "Verifique se o WebView2 do Microsoft Edge está instalado. "
            "Detalhes no log em %LOCALAPPDATA%\\Anatinus\\logs\\desktop.log."
        )
    finally:
        if owns_server and server is not None:
            server.should_exit = True
        if owns_server and server_thread is not None:
            server_thread.join(timeout=5)


if __name__ == "__main__":
    main()
