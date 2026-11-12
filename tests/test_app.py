import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app import ReportStore, create_handler


class ReportApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = ReportStore(Path(self.temp_dir.name) / "reports.sqlite3")
        self.server = ThreadingHTTPServer(
            ("127.0.0.1", 0), create_handler(self.store)
        )
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()
        self.temp_dir.cleanup()

    def send(self, path: str, method: str = "GET", payload: object = None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {"Content-Type": "application/json"} if data else {}
        request = Request(
            self.base_url + path, data=data, headers=headers, method=method
        )
        try:
            response = urlopen(request)
        except HTTPError as error:
            response = error
        with response:
            return response.status, json.loads(response.read())

    def test_create_and_list_report(self) -> None:
        status, created = self.send(
            "/api/reports",
            "POST",
            {
                "category": "Alagamento",
                "location": "Rua Central",
                "description": "Água acumulada na via.",
            },
        )
        self.assertEqual(status, 201)
        self.assertEqual(created["location"], "Rua Central")

        status, reports = self.send("/api/reports")
        self.assertEqual(status, 200)
        self.assertEqual(reports, [created])

    def test_invalid_report_is_rejected(self) -> None:
        status, response = self.send(
            "/api/reports",
            "POST",
            {"category": "Inválida", "location": "", "description": ""},
        )
        self.assertEqual(status, 400)
        self.assertIn("error", response)

    def test_delete_report(self) -> None:
        report = self.store.create_report(
            "Trânsito", "Avenida Norte", "Via bloqueada."
        )

        status, response = self.send(
            f"/api/reports/{report['id']}", "DELETE"
        )
        self.assertEqual(status, 200)
        self.assertTrue(response["deleted"])
        self.assertEqual(self.store.list_reports(), [])

    def test_delete_missing_report_returns_not_found(self) -> None:
        status, response = self.send("/api/reports/999", "DELETE")
        self.assertEqual(status, 404)
        self.assertIn("error", response)

    def test_delete_invalid_or_too_large_id_is_rejected(self) -> None:
        for report_id in ("not-a-number", "9" * 5000):
            with self.subTest(report_id=report_id[:20]):
                status, response = self.send(
                    f"/api/reports/{report_id}", "DELETE"
                )
                self.assertEqual(status, 400)
                self.assertIn("error", response)


if __name__ == "__main__":
    unittest.main()
