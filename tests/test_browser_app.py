import json
import threading
import unittest
import urllib.error
import urllib.request

from src.browser_app import BrowserApp


class BrowserAppInteractionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = BrowserApp(["apple"], host="127.0.0.1", port=0)
        cls.server = cls.app.create_server()
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base_url = f"http://{cls.app.host}:{cls.app.port}"

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(
        self,
        path: str,
        *,
        method: str = "GET",
        payload: dict | None = None,
        session_id: str | None = None,
    ):
        request = urllib.request.Request(f"{self.base_url}{path}", method=method)
        if session_id:
            request.add_header("X-Wordies-Session", session_id)
        if payload is not None:
            request.add_header("Content-Type", "application/json")
            data = json.dumps(payload).encode("utf-8")
        else:
            data = None

        with urllib.request.urlopen(request, data=data, timeout=5) as response:
            content_type = response.headers.get("Content-Type", "")
            body = response.read().decode("utf-8")
            if "application/json" in content_type:
                return response.status, json.loads(body)
            return response.status, body

    def test_browser_html_contains_error_boundary_hooks(self) -> None:
        status, body = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn('window.addEventListener("error"', body)
        self.assertIn("Something went wrong in the browser UI.", body)
        self.assertIn('id="stats-modal"', body)
        self.assertIn('id="confetti-layer"', body)
        self.assertIn("wordies_results", body)
        self.assertIn("triggerCelebration()", body)

    def test_browser_session_persists_across_interactions(self) -> None:
        status, initial = self.request("/api/state")
        self.assertEqual(status, 200)
        session_id = initial["session_id"]
        self.assertEqual(initial["guesses_left"], 6)

        status, invalid = self.request(
            "/api/guess",
            method="POST",
            payload={"guess": "ab1de"},
            session_id=session_id,
        )
        self.assertEqual(status, 200)
        self.assertEqual(invalid["status"], "Word must only contain letters A-Z.")
        self.assertEqual(invalid["guesses_left"], 6)
        self.assertEqual(invalid["session_id"], session_id)

        status, win = self.request(
            "/api/guess",
            method="POST",
            payload={"guess": "apple"},
            session_id=session_id,
        )
        self.assertEqual(status, 200)
        self.assertTrue(win["finished"])
        self.assertTrue(win["won"])
        self.assertEqual(win["session_id"], session_id)

        status, persisted = self.request("/api/state", session_id=session_id)
        self.assertEqual(status, 200)
        self.assertTrue(persisted["finished"])
        self.assertTrue(persisted["won"])
        self.assertEqual(persisted["session_id"], session_id)

        status, reset = self.request(
            "/api/reset",
            method="POST",
            payload={},
            session_id=session_id,
        )
        self.assertEqual(status, 200)
        self.assertFalse(reset["finished"])
        self.assertEqual(reset["guesses_left"], 6)
        self.assertEqual(reset["session_id"], session_id)

    def test_unknown_route_returns_404(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as exc_info:
            self.request("/api/missing")
        self.assertEqual(exc_info.exception.code, 404)
        exc_info.exception.close()
