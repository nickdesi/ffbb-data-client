"""Tests for http_requests_helper and http_requests_utils."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, Mock, patch

from httpx import ReadTimeout

from ffbb_data_client.helpers.http_requests_helper import catch_result
from ffbb_data_client.helpers.http_requests_utils import (
    encode_params,
    http_get,
    http_get_json,
    http_post,
    http_post_json,
    to_json_from_response,
    url_with_params,
)


class Test045HttpHelpers(unittest.TestCase):
    # -- catch_result tests --

    def test_001_catch_result_success(self) -> None:
        result = catch_result(lambda: 42)
        self.assertEqual(result, 42)

    def test_002_catch_result_json_decode_expecting_value(self) -> None:
        def raise_json_error() -> None:
            raise json.decoder.JSONDecodeError("Expecting value", "", 0)

        result = catch_result(raise_json_error)
        self.assertIsNone(result)

    def test_003_catch_result_json_decode_other(self) -> None:
        def raise_json_error() -> None:
            raise json.decoder.JSONDecodeError("Some other error", "", 0)

        with self.assertRaises(json.decoder.JSONDecodeError):
            catch_result(raise_json_error)

    def test_004_catch_result_read_timeout_retry(self) -> None:
        call_count = 0

        def raise_then_succeed() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ReadTimeout("timeout")
            return "ok"

        result = catch_result(raise_then_succeed)
        self.assertEqual(result, "ok")
        self.assertEqual(call_count, 2)

    def test_005_catch_result_read_timeout_twice(self) -> None:
        def always_timeout() -> None:
            raise ReadTimeout("timeout")

        with self.assertRaises(ReadTimeout):
            catch_result(always_timeout)

    def test_006_catch_result_connection_error_retry(self) -> None:
        call_count = 0

        def raise_then_succeed() -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("connection failed")
            return "ok"

        result = catch_result(raise_then_succeed)
        self.assertEqual(result, "ok")

    def test_007_catch_result_connection_error_twice(self) -> None:
        def always_fail() -> None:
            raise ConnectionError("connection failed")

        with self.assertRaises(ConnectionError):
            catch_result(always_fail)

    # -- to_json_from_response tests --

    def test_008_to_json_from_response_valid(self) -> None:
        resp = Mock()
        resp.text = '{"key": "value"}'
        result = to_json_from_response(resp)
        self.assertEqual(result, {"key": "value"})

    def test_009_to_json_from_response_trailing_comma(self) -> None:
        resp = Mock()
        resp.text = '[{"a":1}],'
        result = to_json_from_response(resp)
        self.assertEqual(result, [{"a": 1}])

    def test_010_to_json_from_response_concat_arrays(self) -> None:
        resp = Mock()
        resp.text = "[1,2][3,4]"
        result = to_json_from_response(resp)
        self.assertEqual(result, [1, 2, 3, 4])

    def test_011_to_json_from_response_leading_quotes(self) -> None:
        resp = Mock()
        resp.text = '""[1,2]'
        result = to_json_from_response(resp)
        self.assertEqual(result, [1, 2])

    # -- http_get tests --

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.get")
    def test_012_http_get_no_cache(self, mock_get: MagicMock) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_get.return_value = mock_resp
        response = http_get("https://example.com", {"Authorization": "Bearer test"})
        self.assertEqual(response, mock_resp)
        mock_get.assert_called_once()

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.get")
    def test_013_http_get_debug_mode(self, mock_get: MagicMock) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_get.return_value = mock_resp
        response = http_get(
            "https://example.com", {"Authorization": "Bearer test"}, debug=True
        )
        self.assertEqual(response, mock_resp)

    # -- http_post tests --

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.post")
    def test_014_http_post_no_cache(self, mock_post: MagicMock) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_post.return_value = mock_resp
        response = http_post(
            "https://example.com",
            {"Authorization": "Bearer test"},
            data={"key": "value"},
        )
        self.assertEqual(response, mock_resp)
        mock_post.assert_called_once()

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.post")
    def test_015_http_post_debug_mode(self, mock_post: MagicMock) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_post.return_value = mock_resp
        response = http_post(
            "https://example.com",
            {"Authorization": "Bearer test"},
            data={"key": "value"},
            debug=True,
        )
        self.assertEqual(response, mock_resp)

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.get")
    def test_016_http_get_json_calls_raise_for_status(
        self, mock_get: MagicMock
    ) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_resp.raise_for_status = Mock()
        mock_get.return_value = mock_resp

        result = http_get_json("https://example.com", {"Authorization": "Bearer test"})

        self.assertEqual(result, {"ok": True})
        mock_resp.raise_for_status.assert_called_once()

    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.post")
    def test_017_http_post_json_calls_raise_for_status(
        self, mock_post: MagicMock
    ) -> None:
        mock_resp = Mock()
        mock_resp.text = '{"ok": true}'
        mock_resp.raise_for_status = Mock()
        mock_post.return_value = mock_resp

        result = http_post_json(
            "https://example.com",
            {"Authorization": "Bearer test"},
            data={"key": "value"},
        )

        self.assertEqual(result, {"ok": True})
        mock_resp.raise_for_status.assert_called_once()

    # -- encode_params / url_with_params --

    def test_018_encode_params_array(self) -> None:
        result = encode_params({"fields[]": ["id", "nom"], "limit": 10})
        self.assertIn("fields%5B%5D=id", result)
        self.assertIn("fields%5B%5D=nom", result)
        self.assertIn("limit=10", result)

    def test_019_url_with_params_empty(self) -> None:
        result = url_with_params("https://api.ffbb.app/items", {})
        self.assertEqual(result, "https://api.ffbb.app/items")

    def test_020_url_with_params_none_values(self) -> None:
        result = url_with_params("https://api.ffbb.app/items", {"key": None})
        self.assertEqual(result, "https://api.ffbb.app/items")

    @patch("ffbb_data_client.utils.token_manager.TokenManager.get_tokens")
    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.get")
    def test_021_http_get_token_auto_refresh_on_401(
        self, mock_get: MagicMock, mock_get_tokens: MagicMock
    ) -> None:
        mock_resp_401 = Mock()
        mock_resp_401.status_code = 401
        mock_resp_401.text = "Unauthorized"

        mock_resp_200 = Mock()
        mock_resp_200.status_code = 200
        mock_resp_200.text = '{"ok": true}'

        mock_get.side_effect = [mock_resp_401, mock_resp_200]

        mock_tokens = Mock()
        mock_tokens.api_token = "new_api_token"
        mock_tokens.meilisearch_token = "new_ms_token"
        mock_get_tokens.return_value = mock_tokens

        headers = {"Authorization": "Bearer old_token"}
        response = http_get("https://api.ffbb.app/items/test", headers)

        self.assertEqual(response, mock_resp_200)
        self.assertEqual(headers["Authorization"], "Bearer new_api_token")
        mock_get_tokens.assert_called_once_with(use_cache=False)
        self.assertEqual(mock_get.call_count, 2)

    @patch("ffbb_data_client.utils.token_manager.TokenManager.get_tokens")
    @patch("ffbb_data_client.helpers.http_requests_utils.httpx.Client.post")
    def test_022_http_post_token_auto_refresh_on_403(
        self, mock_post: MagicMock, mock_get_tokens: MagicMock
    ) -> None:
        mock_resp_403 = Mock()
        mock_resp_403.status_code = 403
        mock_resp_403.text = "Forbidden"

        mock_resp_200 = Mock()
        mock_resp_200.status_code = 200
        mock_resp_200.text = '{"ok": true}'

        mock_post.side_effect = [mock_resp_403, mock_resp_200]

        mock_tokens = Mock()
        mock_tokens.api_token = "new_api_token"
        mock_tokens.meilisearch_token = "new_ms_token"
        mock_get_tokens.return_value = mock_tokens

        headers = {"Authorization": "Bearer old_token"}
        response = http_post(
            "https://api.ffbb.app/items/test", headers, data={"foo": "bar"}
        )

        self.assertEqual(response, mock_resp_200)
        self.assertEqual(headers["Authorization"], "Bearer new_api_token")
        mock_get_tokens.assert_called_once_with(use_cache=False)
        self.assertEqual(mock_post.call_count, 2)


if __name__ == "__main__":
    unittest.main()
