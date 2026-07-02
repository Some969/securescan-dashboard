import unittest

from app.scanner.cookies import inspect_cookies_from_response


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


if __name__ == "__main__":
    unittest.main()
