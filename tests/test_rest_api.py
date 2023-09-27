import json

import pytest
import requests

from utils import get_config, get_endpoints

config = get_config()
endpoints = get_endpoints()


class TestOrdersEndPoint:
    base_url = (f"http://{config['server']['host']}:"
                f"{config['server']['port']}")
    input_order_req_params = ["stoks", "quantity"]
    error_req_params = ["code", "message"]

    def test_get_without_order_id(self):

        resp = requests.get(f"{self.base_url}{endpoints['orders']['get_all']}")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        for resp_item in resp.json():
            self._verify_order_input(resp_item)

    @pytest.mark.parametrize(
        "test_input, test_expected_status_code",
        [(1, 200),
         (9999, 404),
         (-1, 404),
         ("5dc", 404)],
        ids=["positive case scenario(with existing order id)",
             "negative case scenario(with nonexisting order id)",
             "negative case scenario(with negative order id)",
             "negative case scenario(with non-numeric order id)",])
    def test_get_with_order_id(self, test_input, test_expected_status_code,
                               generate_order):
        resp = requests.get(f"{self.base_url}/orders/{test_input}")
        assert resp.status_code == test_expected_status_code, \
            f"Scenario failed for test input: {test_input}"
        if resp.status_code == 200:
            self._verify_order_input(resp.json())
            assert test_input == resp.json()['id'], \
                (f"Response order id: {resp.json()['id']} doesn't match with "
                 f"{test_input=}")
        elif resp.status_code == 404:
            self._verify_error(resp.json())
            assert test_expected_status_code == resp.json()['code'], \
                (f"Response error code: {resp.json()['code']} doesn't match "
                 f"with {test_expected_status_code=}")
        else:
            self.fail("Unexpected {resp.status_code=} for {test_input=}")

    @pytest.mark.parametrize(
        "test_input, test_expected_status_code",
        [({"stoks": "EURSEK", "quantity": 125}, 201),
         ({"quantity": 125}, 400),
         ({"stoks": "EURSEK"}, 400),
         ({"stoks": "FOOBAZ", "quantity": 125}, 400),
         ({"stoks": "EURSEK", "quantity": -50}, 400),
         ({"stoks": "EURSEK", "quantity": "50k0c"}, 400),
         ({"stoks": "FOOBAZ", "quantity": 125, "foobar": 3}, 400)],
        ids=["positive case scenario(with a valid order example)",
             "negative case scenario(with a missing required property[I])",
             "negative case scenario(with a missing required property[II])",
             "negative case scenario(with an unexpected property)",
             "negative case scenario(with an unacceptable input value[I])",
             "negative case scenario(with an unacceptable input value[II])",
             "negative case scenario(with an unacceptable input value[III])"])
    def test_post(self, test_input, test_expected_status_code):
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        data = json.dumps(test_input)
        rsp = requests.post(f"{self.base_url}{endpoints['orders']['get_all']}",
                            data=data, headers=headers)
        assert rsp.status_code == test_expected_status_code, \
            f"Scenario failed for test input: {test_input}"
        if rsp.status_code == 201:
            self._verify_order_input(rsp.json())
            assert set(test_input.items()).issubset(set(rsp.json().items())), \
                (f"Response order: {rsp.json()} doesn't match with the items "
                 f"in {test_input=}")
        elif rsp.status_code == 400:
            self._verify_error(rsp.json())
            assert test_expected_status_code == rsp.json()['code'], \
                (f"Response error code: {rsp.json()['code']} doesn't match "
                 f"with {test_expected_status_code=}")
        else:
            self.fail("Unexpected {rsp.status_code=} for {test_input=}")

    @pytest.mark.parametrize(
        "test_input, test_expected_status_code",
        [(1, 204),
         (9999, 404),
         (-1, 404),
         ("f8k", 404)],
        ids=["positive case scenario(with existing order id)",
             "negative case scenario(with nonexisting order id)",
             "negative case scenario(with negative order id)",
             "negative case scenario(with non-numeric order id)",])
    def test_delete(self, test_input, test_expected_status_code,
                    generate_order):
        resp = requests.delete(f"{self.base_url}/orders/{test_input}")
        assert resp.status_code == test_expected_status_code, \
            f"Scenario failed for test input: {test_input}"
        if resp.status_code == 204:
            pass  # no content, nothing to check
        elif resp.status_code == 404:
            self._verify_error(resp.json())
            assert test_expected_status_code == resp.json()['code'], \
                (f"Response error code: {resp.json()['code']} doesn't match "
                 f"with {test_expected_status_code=}")
        else:
            self.fail("Unexpected {resp.status_code=} for {test_input=}")

    def _verify_order_input(self, item):
        assert isinstance(item, dict), "Order input must be dict!"
        mis_pars = list(set(self.input_order_req_params) - set(item.keys()))
        assert not mis_pars, \
            f"Missing property(s): {mis_pars} in response order item!"

    def _verify_error(self, item):
        assert isinstance(item, dict), "Error must be a dict!"
        mis_pars = list(set(self.error_req_params) - set(item.keys()))
        assert not mis_pars, \
            f"Missing property(s): {mis_pars} in response error item!"
