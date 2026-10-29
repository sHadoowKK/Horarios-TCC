"""Inicializador desktop do Anatinus para Windows."""

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

from app.main import app

HOST = "127.0.0.1"
PORT = 8765
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
    _configure_logging()
    logging.info("Inicializando Anatinus desktop.")

    server = None
    server_thread = None
    owns_server = False

    if _is_port_open():
        if _is_anatinus_running():
            _show_error(
                "O Anatinus já está aberto. Verifique as janelas em execução."
            )
        else:
            _show_error(
                "A porta local necessária pelo Anatinus já está ocupada. "
                "Feche o programa que está usando essa porta e tente novamente."
            )
        return
    else:
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

        if not _wait_for_server(server_thread):
            logging.error("A API não iniciou dentro do tempo esperado.")
            server.should_exit = True
            _show_error(
                "O Anatinus não conseguiu iniciar o serviço local. "
                "Consulte o log em %LOCALAPPDATA%\\Anatinus\\logs\\desktop.log."
            )
            return

    try:
        window = webview.create_window(
            "Anatinus",
            BASE_URL,
            width=1360,
            height=900,
            min_size=(980, 680),
            background_color="#08090a",
        )

        if owns_server and server is not None:
            def stop_local_server(*_args) -> None:
                logging.info("Janela fechada; encerrando a API local.")
                server.should_exit = True

            window.events.closed += stop_local_server

        webview.start(debug=False)
    except Exception:
        logging.exception("Falha ao abrir a janela do Anatinus.")
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