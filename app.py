from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


ROOT = Path(__file__).parent
DATABASE = ROOT / "data" / "reports.sqlite3"
CATEGORIES = {
    "Poluição do ar",
    "Trânsito",
    "Alagamento",
    "Desmatamento",
    "Área de manancial",
    "Outro",
}
MAX_BODY_SIZE = 16_384


class ReportStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path)) as connection:
            with connection:
                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS reports (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        location TEXT NOT NULL,
                        description TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                    """
                )

    def list_reports(self) -> list[dict[str, Any]]:
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                """
                SELECT id, category, location, description, created_at
                FROM reports
                ORDER BY created_at DESC, id DESC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def create_report(
        self, category: Any, location: Any, description: Any
    ) -> dict[str, Any]:
        if not isinstance(category, str) or category not in CATEGORIES:
            raise ValueError("Selecione uma categoria válida.")
        if not isinstance(location, str) or not location.strip():
            raise ValueError("Informe o local da ocorrência.")
        if len(location.strip()) > 120:
            raise ValueError("O local deve ter no máximo 120 caracteres.")
        if not isinstance(description, str) or not description.strip():
            raise ValueError("Descreva a ocorrência.")
        if len(description.strip()) > 500:
            raise ValueError("A descrição deve ter no máximo 500 caracteres.")

        created_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                cursor = connection.execute(
                    """
                    INSERT INTO reports (category, location, description, created_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (category, location.strip(), description.strip(), created_at),
                )
                row = connection.execute(
                    """
                    SELECT id, category, location, description, created_at
                    FROM reports
                    WHERE id = ?
                    """,
                    (cursor.lastrowid,),
                ).fetchone()
        if row is None:
            raise RuntimeError("Não foi possível ler o registro recém-criado.")
        return dict(row)

    def delete_report(self, report_id: int) -> bool:
        with closing(sqlite3.connect(self.path, timeout=5)) as connection:
            with connection:
                cursor = connection.execute(
                    "DELETE FROM reports WHERE id = ?", (report_id,)
                )
        return cursor.rowcount > 0


def create_handler(store: ReportStore) -> type[BaseHTTPRequestHandler]:
    class RequestHandler(BaseHTTPRequestHandler):
        def send_json(self, status: int, payload: Any) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def read_json(self) -> dict[str, Any]:
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("Tamanho da requisição inválido.") from error
            if content_length <= 0:
                raise ValueError("Envie os dados da ocorrência.")
            if content_length > MAX_BODY_SIZE:
                raise OverflowError("A requisição é grande demais.")
            try:
                payload = json.loads(self.rfile.read(content_length))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError("O conteúdo enviado não é um JSON válido.") from error
            if not isinstance(payload, dict):
                raise ValueError("O conteúdo enviado deve ser um objeto JSON.")
            return payload

        def do_GET(self) -> None:
            path = urlsplit(self.path).path
            if path == "/api/reports":
                try:
                    self.send_json(200, store.list_reports())
                except sqlite3.Error:
                    logging.exception("Não foi possível consultar os relatos")
                    self.send_json(500, {"error": "Erro ao consultar os relatos."})
                return

            asset = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
            }.get(path)
            if asset is None:
                self.send_json(404, {"error": "Página não encontrada."})
                return

            content = (ROOT / "static" / asset[0]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", asset[1])
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self) -> None:
            if urlsplit(self.path).path != "/api/reports":
                self.send_json(404, {"error": "Página não encontrada."})
                return
            try:
                payload = self.read_json()
                report = store.create_report(
                    payload.get("category"),
                    payload.get("location"),
                    payload.get("description"),
                )
            except OverflowError as error:
                self.send_json(413, {"error": str(error)})
                return
            except ValueError as error:
                self.send_json(400, {"error": str(error)})
                return
            except sqlite3.Error:
                logging.exception("Não foi possível salvar o relato")
                self.send_json(500, {"error": "Erro ao salvar o relato."})
                return
            self.send_json(201, report)

        def do_DELETE(self) -> None:
            path = urlsplit(self.path).path
            prefix = "/api/reports/"
            if not path.startswith(prefix):
                self.send_json(404, {"error": "Página não encontrada."})
                return
            report_id_text = path.removeprefix(prefix)
            if (
                not report_id_text.isascii()
                or not report_id_text.isdecimal()
                or len(report_id_text) > 19
            ):
                self.send_json(400, {"error": "Identificador de relato inválido."})
                return
            report_id = int(report_id_text)
            if report_id > 9_223_372_036_854_775_807:
                self.send_json(400, {"error": "Identificador de relato inválido."})
                return
            try:
                deleted = store.delete_report(report_id)
            except sqlite3.Error:
                logging.exception("Não foi possível excluir o relato")
                self.send_json(500, {"error": "Erro ao excluir o relato."})
                return
            if not deleted:
                self.send_json(404, {"error": "Relato não encontrado."})
                return
            self.send_json(200, {"deleted": True})

        def log_message(self, format: str, *args: Any) -> None:
            logging.info("%s - %s", self.address_string(), format % args)

    return RequestHandler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
    store = ReportStore(DATABASE)
    server = ThreadingHTTPServer(("0.0.0.0", 8000), create_handler(store))
    print("Aplicativo disponível em http://localhost:8000")
    print("Para acessar pelo celular, use o IP deste computador na mesma rede Wi-Fi.")
    print("Pressione Ctrl+C para encerrar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
