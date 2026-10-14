import ipaddress
import socket
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import requests
from fastapi import HTTPException

from app.utils import (
    MAX_RESPONSE_BYTES,
    _PinnedHTTPSConnection,
    ensure_public_hostname,
    normalize_url,
    safe_get,
)
from app.scanner.redirects import check_https_redirect
from app.scanner.ports import check_open_ports


def _dns_answer(address):
    ip = ipaddress.ip_address(address)
    if ip.version == 4:
        sockaddr = (address, 0)
        family = socket.AF_INET
    else:
        sockaddr = (address, 0, 0, 0)
        family = socket.AF_INET6
    return family, socket.SOCK_STREAM, socket.IPPROTO_TCP, "", sockaddr


class NetworkSafetyTests(unittest.TestCase):
    @patch("app.utils.socket.getaddrinfo")
    def test_mixed_public_and_private_dns_answers_are_rejected(self, getaddrinfo):
        getaddrinfo.return_value = [
            _dns_answer("93.184.216.34"),
            _dns_answer("10.0.0.5"),
        ]

        with self.assertRaises(HTTPException):
            ensure_public_hostname("example.com")

    def test_ipv4_mapped_ipv6_private_address_is_rejected(self):
        with self.assertRaises(HTTPException):
            ensure_public_hostname("::ffff:127.0.0.1")

    def test_unique_local_ipv6_address_is_rejected(self):
        with self.assertRaises(HTTPException):
            ensure_public_hostname("fd00::1")

    @patch("app.utils._request_pinned")
    def test_direct_private_target_is_rejected_before_connect(self, request_pinned):
        with self.assertRaises(HTTPException):
            safe_get("http://10.0.0.1")

        request_pinned.assert_not_called()

    def test_hostname_is_pinned_without_a_second_dns_lookup(self):
        with patch("app.utils.create_connection") as create_connection:
            connection = _PinnedHTTPSConnection(
                "example.com",
                443,
                pinned_ip="93.184.216.34",
            )

            connection._new_conn()

        self.assertEqual(create_connection.call_args.args[0], ("93.184.216.34", 443))

    def test_http_request_connects_to_pinned_ip_and_preserves_host_header(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                self.server.received_host = self.headers.get("Host")
                body = (
                    b"x" * (MAX_RESPONSE_BYTES + 1)
                    if self.path == "/large"
                    else b"fixture response"
                )
                self.send_response(200)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, _format, *_args):
                pass

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def connect_fixture(address, timeout, source_address=None, socket_options=None):
            self.assertEqual(address, ("93.184.216.34", 8080))
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            if source_address:
                sock.bind(source_address)
            for level, option, value in socket_options or []:
                sock.setsockopt(level, option, value)
            sock.connect(("127.0.0.1", server.server_port))
            return sock

        try:
            with (
                patch(
                    "app.utils.socket.getaddrinfo",
                    return_value=[_dns_answer("93.184.216.34")],
                ),
                patch("app.utils.create_connection", side_effect=connect_fixture),
            ):
                response = safe_get("http://example.com:8080/")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, "fixture response")
            self.assertEqual(server.received_host, "example.com:8080")
            with self.assertRaises(requests.RequestException):
                safe_get("http://example.com:8080/large")
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    @patch("app.scanner.redirects.safe_get")
    def test_tls_custom_port_redirect_check_uses_standard_http_port(self, safe_get_mock):
        response = MagicMock()
        response.url = "http://example.com/"
        response.history = []
        response.status_code = 200
        safe_get_mock.return_value = response

        check_https_redirect("https://example.com:8443")

        self.assertEqual(safe_get_mock.call_args.args[0], "http://example.com/")

    @patch("app.scanner.ports.subprocess.run")
    @patch("app.scanner.ports.find_nmap_executable", return_value="nmap")
    @patch("app.scanner.ports.resolve_public_addresses", return_value=["93.184.216.34"])
    def test_nmap_receives_the_validated_ip_not_the_hostname(
        self, _resolve, _find_nmap, run
    ):
        run.return_value = SimpleNamespace(returncode=0, stdout="", stderr="")

        check_open_ports("https://example.com")

        command = run.call_args.args[0]
        self.assertEqual(command[-1], "93.184.216.34")

    @patch("app.utils._request_pinned")
    @patch("app.utils.socket.getaddrinfo")
    def test_dns_change_to_private_address_is_blocked_before_connect(
        self, getaddrinfo, request_pinned
    ):
        getaddrinfo.side_effect = [
            [_dns_answer("93.184.216.34")],
            [_dns_answer("10.0.0.5")],
        ]

        with self.assertRaises(requests.RequestException):
            safe_get("https://example.com")

        request_pinned.assert_not_called()

    @patch("app.utils.socket.getaddrinfo")
    @patch("app.utils._request_pinned")
    def test_private_redirect_is_rejected_before_a_second_connection(
        self, request_pinned, getaddrinfo
    ):
        getaddrinfo.return_value = [_dns_answer("93.184.216.34")]
        redirect = requests.Response()
        redirect.status_code = 302
        redirect.headers["Location"] = "http://127.0.0.1/"
        redirect.url = "https://example.com/"
        redirect.raw = MagicMock()
        request_pinned.return_value = redirect

        with self.assertRaises(requests.RequestException):
            safe_get("https://example.com")

        request_pinned.assert_called_once()

    def test_non_web_port_is_rejected(self):
        with self.assertRaises(HTTPException):
            normalize_url("https://example.com:22")


if __name__ == "__main__":
    unittest.main()
