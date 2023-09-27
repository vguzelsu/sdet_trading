import json
import requests
import pytest

from utils import get_config


config = get_config()


@pytest.fixture()
def generate_order():
    # prepare order
    base_url = f"http://{config['server']['host']}:{config['server']['port']}"
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    data = json.dumps({'stoks': 'EURSEK', 'quantity': 125})
    resp = requests.post(f"{base_url}/orders", data=data, headers=headers)
    assert resp.status_code == 201, "Problem in adding a test order!"
    order = resp.json()
    yield order
    # clean up order
    resp = requests.delete(f"{base_url}/orders/{order['id']}")
    assert resp.status_code == 204, "Problem in removing the test order!"
