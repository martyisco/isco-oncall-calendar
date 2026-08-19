import importlib.util
import json
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT = Path(__file__).resolve().parents[1]
MODULE_PATH = PROJECT / "scripts" / "publish_schedule.py"
spec = importlib.util.spec_from_file_location("publish_schedule", MODULE_PATH)
publish_schedule = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publish_schedule)


class FakeResponse:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return b'{"success":true}'


class PublishScheduleTests(unittest.TestCase):
    def test_publish_uses_kv_value_endpoint_and_json_body(self):
        schedule = {"service": "Test rotation", "blocks": [{"primary": "Operator A"}]}
        with patch.object(publish_schedule.urllib.request, "urlopen", return_value=FakeResponse()) as urlopen:
            result = publish_schedule.publish(
                schedule=schedule,
                account_id="account-123",
                namespace_id="namespace-456",
                api_token="test-token",
                key="schedule",
            )

        self.assertEqual(result, {"success": True, "status": 200})
        request = urlopen.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://api.cloudflare.com/client/v4/accounts/account-123/storage/kv/namespaces/namespace-456/values/schedule",
        )
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(request.get_header("Authorization"), "Bearer test-token")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(json.loads(request.data.decode()), schedule)


if __name__ == "__main__":
    unittest.main()
