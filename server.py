import asyncio
import random
import time
from asyncio import Queue, Task
from enum import Enum
from typing import Any

import websockets
from fastapi import (BackgroundTasks, FastAPI, Request, Response, WebSocket,
                     WebSocketDisconnect)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from utils import get_config, get_endpoints


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    CANCELLED = "CANCELLED"


class Stoks(str, Enum):
    EURO_TO_SEK = "EURSEK"
    DOLLAR_TO_SEK = "DOLSEK"
    POUND_TO_SEK = "POUSEK"
    SEK_TO_EURO = "SEKEUR"
    SEK_TO_DOLLAR = "SEKDOL"
    SEK_TO_POUND = "SEKPOU"


class Listener:
    host = get_config()['server']['host']
    port = get_config()['server']['port']

    def __init__(self):
        # Every incoming websocket conneciton adds it own Queue to this list
        #   called subscribers.
        self.subscribers: list[Queue] = []
        # This will hold a asyncio task which will receives messages and
        #   broadcasts them to all subscribers.
        self.listener_task: Task

    async def subscribe(self, q: Queue):
        # Every incoming websocket connection must create a Queue and subscribe
        #   itself to this class instance
        self.subscribers.append(q)

    async def start_listening(self):
        # Method that must be called on startup of application to start the
        #   listening process of external messages.
        self.listener_task = asyncio.create_task(self._listener())

    async def _listener(self) -> None:
        # The method with the infinite listener. In this example, it listens to
        #   a websocket as it was the fastest way for me to mimic the 'infinite
        #   generator' in issue 5015 but this can be anything. It is started
        #   (via start_listening()) on startup of app.
        async with websockets.connect(f"ws://{self.host}:{self.port}") as ws:
            async for message in ws:
                for q in self.subscribers:
                    # Important here: every websocket connection has its own
                    #   Queue added to the list of subscribers. Here, we
                    #   actually broadcast incoming messages to all open
                    #   websocket connections.
                    await q.put(message)

    async def stop_listening(self):
        # Closing off the asyncio task when stopping the app. This method is
        #   called on app shutdown
        if self.listener_task.done():
            self.listener_task.result()
        else:
            self.listener_task.cancel()

    async def receive_and_publish_message(self, msg: Any):
        # This was a method that was called when someone would make a request
        #   to /add_item endpoint as part of earlier solution to see if the msg
        #   would be broadcasted to all open websocket connections (it does)
        for q in self.subscribers:
            try:
                q.put_nowait(str(msg))
            except Exception as e:
                raise e

    # Note: missing here is any disconnect logic (e.g. removing the queue from
    # the list of subscribers when a websocket connection is ended or closed.)


app = FastAPI()
global_listener = Listener()
endpoints = get_endpoints()

required_params = ["stoks", "quantity"]
orders = []
mock_rates = {Stoks.EURO_TO_SEK: 11.0886, Stoks.SEK_TO_EURO: 0.0780,
              Stoks.DOLLAR_TO_SEK: 10.2773, Stoks.SEK_TO_DOLLAR: 0.0823,
              Stoks.POUND_TO_SEK: 12.4602, Stoks.SEK_TO_POUND: 0.0677}


async def mock_process_order(order_id):
    timeout = 1
    for order in orders:
        if order.get("id") == order_id:
            if order["status"] != OrderStatus.PENDING:
                break  # nothing to process if the order is not pending
            # assign a random duration for processing the order
            process_duration = [0.2, 0.4, 0.6, 0.7, 2.0][random.randint(0, 4)]
            # wait for mimicing order processing
            time.sleep(min(process_duration, timeout))
            # set new status to the order according to it's process duration
            if process_duration < timeout:
                order["status"] = OrderStatus.EXECUTED
            else:
                order["status"] = OrderStatus.CANCELLED
            # publish status update message once the new status is set
            msg = (f"Order status is updated -> id: {order['id']} status: "
                   f"{order['status']}")
            await global_listener.receive_and_publish_message(msg)
            # remove 20 % of executed orders randomly
            if (order["status"] == OrderStatus.EXECUTED and
               random.randint(0, 5) == 5):
                time.sleep(random.random())  # sleep n seconds where 0 < n < 1
                order["status"] = OrderStatus.CANCELLED
                # publish status update message once the order is cancelled
                await global_listener.receive_and_publish_message(msg)


def _fetch_mock_rate(stoks):
    try:
        return mock_rates[stoks]
    except KeyError:
        raise Exception(f"Failed fetching rates for stoks: {stoks}")


def _find_next_id():
    if not orders:
        return 1
    return max(order["id"] for order in orders) + 1


def _fetch_rate(stoks):
    # TODO: fetch real instant rates from a web service
    return _fetch_mock_rate(stoks)


def _verify_order(order):
    errors = []
    if not isinstance(order, dict):
        return ["Order must be dict!"]
    errors.append(_verify_order_stoks(order))
    errors.append(_verify_order_quantity(order))
    u_pars = (list(set(order.keys()) - set(required_params)))
    if u_pars:
        errors.append(f"Unexpected parameter(s): {u_pars} in order request!")
    return [err for err in errors if err]


def _verify_order_stoks(order):
    if 'stoks' not in order:
        return "Missing required data 'stoks' in order request!"
    elif order["stoks"] not in Stoks._value2member_map_:
        return (f"Unrecognized stoks: {order['stoks']} in order request!"
                f"Recognized values: {Stoks._value2member_map_.keys()}")
    return


def _verify_order_quantity(order):
    if 'quantity' not in order:
        return "Missing required data 'quantity' in order request!"
    try:
        if not float(order['quantity']) >= 0:
            return (f"Negative({order['quantity']}) value for quantity in "
                    "request! It should be a positive number!")
    except ValueError:
        return (f"Non-numeric({order['quantity']}) value for quantity in order"
                " request! It should be a positive number.")
    # TODO: maybe a max allowed quantity check for each stoks?
    return


async def get_orders_from_db():
    """
    This is a coroutine that mocks fetching orders from database since it is
      allowed to keep database in memory in this task.
    """
    time.sleep(random.random())  # sleep n seconds where 0 < n < 1
    return orders


async def get_order_from_db(order_id):
    """
    This is a coroutine that mocks fetching an order from database since it is
      allowed to keep database in memory in this task.
    """
    time.sleep(random.random())  # sleep n seconds where 0 < n < 1
    for order in orders:
        try:
            if order.get("id") == int(order_id):
                return order
        except ValueError:
            return {"code": 404, "message": "Order not found!"}
    return {"code": 404, "message": f"No order with id: {order_id}!"}


async def add_order_to_db(request):
    order = await request.json()
    time.sleep(random.random())  # sleep n seconds where 0 < n < 1
    verification_errors = _verify_order(order)
    if verification_errors:
        return {"code": 400, "message": verification_errors}
    order["id"] = _find_next_id()
    order["rate"] = _fetch_rate(order["stoks"])
    order["status"] = OrderStatus.PENDING
    orders.append(order)
    # publish 'added new order' message upon adding a new order
    msg = (f"A new order is added -> id: {order['id']} status: "
           f"{order['status']}")
    await global_listener.receive_and_publish_message(msg)
    return order


async def cancel_order_in_db(order_id):
    time.sleep(random.random())  # sleep n seconds where 0 < n < 1
    for order in orders:
        try:
            if order.get("id") == int(order_id):
                if order.get("status") != OrderStatus.CANCELLED:
                    order["status"] = OrderStatus.CANCELLED
                    # publish status update message upon cancelling an order
                    msg = (f"Order status is updated -> id: {order['id']} "
                           f"status: {order['status']}")
                    await global_listener.receive_and_publish_message(msg)
                return order
        except ValueError:
            return {"code": 404, "message": "Order not found!"}
    return {"code": 404, "message": f"No order with id: {order_id}!"}


@app.get(f"{endpoints['orders']['get_all']}", status_code=200)
async def get_orders(response: Response):
    data = await get_orders_from_db()
    return JSONResponse(content=jsonable_encoder(data))


@app.get(f"{endpoints['orders']['get_one']}", status_code=200)
async def get_order(id, response: Response):
    data = await get_order_from_db(id)
    if "code" not in data:
        return JSONResponse(content=jsonable_encoder(data))
    else:
        response.status_code = data["code"]
        return data


@app.post(f"{endpoints['orders']['post']}", status_code=201)
async def add_order(request: Request, response: Response,
                    background_tasks: BackgroundTasks):
    data = await add_order_to_db(request)
    if "code" not in data:
        # add task to perform mock order process
        background_tasks.add_task(mock_process_order, data["id"])
    else:
        response.status_code = data["code"]
    return data


@app.delete(f"{endpoints['orders']['delete']}", status_code=204)
async def cancel_order(id, response: Response):
    data = await cancel_order_in_db(id)
    if "code" in data:
        response.status_code = data["code"]
        return data


@app.websocket(f"{endpoints['websocket']['subscription']}")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    q: asyncio.Queue = asyncio.Queue()
    await global_listener.subscribe(q=q)
    try:
        while True:
            data = await q.get()
            await websocket.send_text(data)
    except WebSocketDisconnect:
        return


@app.on_event("startup")
async def startup_event():
    await global_listener.start_listening()
    return


@app.on_event("shutdown")
async def shutdown_event():
    await global_listener.stop_listening()
    return


if __name__ == "__main__":
    import uvicorn
    host = get_config()['server']['host']
    port = get_config()['server']['port']
    uvicorn.run(app, port=port, host=host)
