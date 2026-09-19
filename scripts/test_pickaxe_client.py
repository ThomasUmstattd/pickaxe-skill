"""Offline client checks. No real credentials, network calls, or paid runs."""
import io
import http.client
import json
import os
import unittest
from unittest.mock import mock_open, patch

import pickaxe_client as client


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.http = patch.object(client.urllib.request, "urlopen").start()
        patch.object(client, "load_token", return_value="Bearer fake").start()
        self.addCleanup(patch.stopall)

    def respond(self, result):
        self.http.return_value = io.BytesIO(json.dumps({"result": result}).encode())
        self.http.return_value.headers = {"Content-Type": "application/json"}

    def complete(self):
        return client.run_completion("BOT_ID", message="hello")

    def test_success_shapes(self):
        for value in ({"success": True, "result": "hello"},
                      {"success": True, "data": {"success": True, "result": "hello"}},
                      {"success": True, "data": "hello"}):
            with self.subTest(value=value):
                self.respond({"structuredContent": value})
                self.assertEqual(self.complete(), "hello")

    def test_success_without_data(self):
        self.respond({"structuredContent": {"success": True}})
        self.assertEqual(client.call("document_connect", {}), {"success": True})

    def test_multiple_text_blocks(self):
        self.respond({"content": [
            {"type": "text", "text": "Provider diagnostic"},
            {"type": "text", "text": '{"success": false, "error": "failed"}'},
        ]})
        with self.assertRaises(client.PickaxeError):
            self.complete()
        self.respond({"content": [
            {"type": "text", "text": '{"success": true,'},
            {"type": "text", "text": '"result": "hello"}'},
        ]})
        self.assertEqual(self.complete(), "hello")

    def test_interrupted_read_is_an_ambiguous_failure(self):
        self.http.return_value.__enter__.return_value.headers = {"Content-Type": "application/json"}
        self.http.return_value.__enter__.return_value.read.side_effect = http.client.IncompleteRead(b"partial", 20)
        with self.assertRaises(client.PickaxeError) as caught:
            self.complete()
        self.assertIsInstance(caught.exception.__cause__, http.client.IncompleteRead)
        self.http.assert_called_once()

    def test_mcp_event_stream(self):
        body = (b': keepalive\r\n\r\nevent: message\r\n'
                b'data: {"jsonrpc":"2.0","method":"notifications/progress"}\r\n\r\n'
                b'data: {"jsonrpc":"2.0","id":99,"result":{}}\r\n\r\n'
                b'data: {"jsonrpc":"2.0","id":1,\r\n'
                b'data: "result":{"structuredContent":{"success":true,"result":"hello"}}}\r\n\r\n')
        self.http.return_value = io.BytesIO(body)
        self.http.return_value.headers = {"Content-Type": "text/event-stream; charset=utf-8"}
        self.assertEqual(self.complete(), "hello")
        self.assertTrue(self.http.return_value.closed)

    def test_mcp_stream_error_and_missing_result(self):
        for body in (b'data: {"jsonrpc":"2.0","id":1,"error":{"message":"failed"}}\n\n',
                     b': keepalive\n\n', b'data: invalid json\n\n'):
            with self.subTest(body=body):
                self.http.return_value = io.BytesIO(body)
                self.http.return_value.headers = {"Content-Type": "text/event-stream"}
                with self.assertRaises(client.PickaxeError):
                    self.complete()

    def test_text_envelopes_and_plain_answers(self):
        for text in ("{'success': True, 'result': 'hello'}",
                     '{"success": true, "result": "hello"}', "hello"):
            with self.subTest(text=text):
                self.respond({"content": [{"type": "text", "text": text}]})
                self.assertEqual(self.complete(), "hello")
        text = '{"result": "this is ordinary generated JSON"}'
        self.respond({"structuredContent": {"success": True, "data": text}})
        self.assertEqual(self.complete(), text)

    def test_errors_at_each_layer(self):
        for result in (
            {"isError": True, "structuredContent": {"data": "bad"}},
            {"structuredContent": {"success": False, "error": "bad"}},
            {"structuredContent": {"success": True, "data": {"success": False, "result": "bad"}}},
            {"content": [{"type": "text", "text": "{'success': False, 'result': 'bad'}"}]},
        ):
            with self.subTest(result=result):
                self.respond(result)
                with self.assertRaises(client.PickaxeError):
                    self.complete()

    def test_bad_transport_and_missing_payload(self):
        for body in (b"not json", b"[]", b'{"result": null}',
                     b'{"error": {"message": "bad"}}', b'{"result": {}}',
                     b'{"result": {"content": null}}'):
            with self.subTest(body=body):
                self.http.return_value = io.BytesIO(body)
                self.http.return_value.headers = {"Content-Type": "application/json"}
                with self.assertRaises(client.PickaxeError):
                    client.call("pickaxe_get", {})
        self.http.side_effect = TimeoutError("late")
        with self.assertRaises(client.PickaxeError):
            self.complete()
        self.assertEqual(self.http.call_count, 7)

    def test_input_validation_before_network(self):
        for args in ([], "not an object", 0):
            with self.assertRaises(ValueError):
                client.call("pickaxe_get", args)
        for kwargs in ({}, {"message": "hi", "inputs": {}},
                       {"message": []}, {"inputs": []},
                       {"message": "hi", "retries": -1}):
            with self.assertRaises(ValueError):
                client.run_completion("BOT_ID", **kwargs)
        self.http.assert_not_called()

    def test_form_conversation_and_explicit_token(self):
        self.respond({"structuredContent": {"success": True, "result": "ok"}})
        self.assertEqual(client.run_completion(
            "BOT_ID", inputs={"userinput:F": "value"}, server="testing",
            conversation_id="CONVERSATION_ID", token="Bearer explicit"), "ok")
        request = self.http.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer explicit")
        self.assertEqual(json.loads(request.data)["params"]["arguments"], {
            "pickaxeId": "BOT_ID", "inputs": {"userinput:F": "value"},
            "conversationId": "CONVERSATION_ID"})
        client.load_token.assert_not_called()

    def test_no_default_paid_retry(self):
        self.respond({"isError": True, "content": [
            {"type": "text", "text": "Could not reach the Completion API:"}]})
        with self.assertRaises(client.PickaxeError):
            self.complete()
        self.http.assert_called_once()

    def test_explicit_retry_remains_bounded(self):
        with patch.object(client, "call", side_effect=[
            client.PickaxeError("Could not reach the Completion API:"),
            {"success": True, "result": "ok"}]) as call, patch.object(client.time, "sleep") as sleep:
            self.assertEqual(client.run_completion("BOT_ID", message="hi", retries=1), "ok")
            self.assertEqual(call.call_count, 2)
            sleep.assert_called_once_with(10)


class CredentialTests(unittest.TestCase):
    def test_default_environment_key(self):
        for value in ("fake", "Bearer fake"):
            with patch.dict(os.environ, {"PICKAXE_API_KEY": value}, clear=True):
                self.assertEqual(client.load_token(), "Bearer fake")

    def test_named_server_uses_its_config(self):
        config = json.dumps({"mcpServers": {"testing": {"headers": {"Authorization": "Bearer test-key"}}}})
        with patch.dict(os.environ, {"PICKAXE_API_KEY": "production-key"}, clear=True), patch.object(client.os.path, "exists", return_value=True), patch("builtins.open", mock_open(read_data=config)):
            self.assertEqual(client.load_token("testing"), "Bearer test-key")

    def test_named_server_missing_fails_closed(self):
        with patch.dict(os.environ, {"PICKAXE_API_KEY": "production-key"}, clear=True), patch.object(client.os.path, "exists", return_value=False):
            with self.assertRaises(client.PickaxeError):
                client.load_token("testing")


if __name__ == "__main__":
    unittest.main()
