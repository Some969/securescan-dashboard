import unittest
from unittest.mock import MagicMock, patch

from app.scanner.cookies import inspect_cookies_from_response
from app.scanner.ssl_check import check_ssl


class DummyResponse:
    def __init__(self, header_values):
        self.headers = {"Set-Cookie": header_values}


class CookieScannerTests(unittest.TestCase):
    def test_inspect_cookies_from_response_collects_cookie_summary(self):
        response = DummyResponse(
            "sessionid=abc123; Secure; HttpOnly; SameSite=Lax; Expires=Wed, 21 Oct 2035 07:28:00 GMT; Path=/"
        )

        result = inspect_cookies_from_response(response)

        self.assertEqual(result["cookies_found"], 1)
        self.assertTrue(result["results"][0]["secure"])
        self.assertTrue(result["results"][0]["httponly"])
        self.assertEqual(result["results"][0]["samesite"], "Lax")
        self.assertEqual(result["summary"]["missing_secure"], 0)
        self.assertEqual(result["summary"]["missing_httponly"], 0)
        self.assertEqual(result["summary"]["missing_samesite"], 0)
        self.assertEqual(result["status"], "1 cookie(s) detected.")

    def test_inspect_cookies_from_response_supports_multiple_headers_and_case_variants(self):
        response = DummyResponse([
            "theme=dark; samesite=strict; path=/; domain=example.com",
            "csrf=token; secure; httponly; SameSite=None",
        ])

        result = inspect_cookies_from_response(response)

        self.assertEqual(result["cookies_found"], 2)
        self.assertEqual(result["results"][0]["samesite"], "strict")
        self.assertEqual(result["results"][1]["samesite"], "None")
        self.assertEqual(result["summary"]["missing_secure"], 1)
        self.assertEqual(result["summary"]["missing_httponly"], 1)
        self.assertEqual(result["summary"]["missing_samesite"], 0)

    @patch("app.scanner.ssl_check.socket.create_connection")
    @patch("app.scanner.ssl_check.ssl.create_default_context")
    def test_check_ssl_uses_the_url_port_when_present(self, mock_context_factory, mock_create_connection):
        mock_context = MagicMock()
        mock_secure_sock = MagicMock()
        mock_secure_sock.getpeercert.return_value = {
            "notAfter": "Jun  7 00:00:00 2035 GMT",
            "issuer": [[("commonName", "Example CA")]],
        }
        mock_context.wrap_socket.return_value.__enter__.return_value = mock_secure_sock
        mock_context_factory.return_value = mock_context

        socket_manager = MagicMock()
        socket_manager.__enter__.return_value = object()
        mock_create_connection.return_value = socket_manager

        result = check_ssl("https://example.com:8443")

        self.assertTrue(result["ok"])
        self.assertEqual(mock_create_connection.call_args[0][0][1], 8443)


if __name__ == "__main__":
    unittest.main()
