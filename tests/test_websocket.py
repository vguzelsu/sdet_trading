import pytest

from utils import get_config, get_endpoints


config = get_config()
endpoints = get_endpoints()


class TestWebsocket:
    base_url = (f"ws://{config['server']['host']}:"
                f"{config['server']['port']}")

    def test_order_status_update_messages_received_properly(self):
        pass

    def test_pending_is_always_the_first_order_status_message(self):
        pass

    def test_no_order_status_update_message_after_cancelled(self):
        pass
