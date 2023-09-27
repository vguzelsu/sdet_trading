import rel
import websocket


def on_message(ws, message):
    print(f"Websocket says: {message}")


def on_error(ws, error):
    print(f"An error occured: {error}")


def on_close(ws, close_status_code, close_msg):
    print("### Closed connection ###")


def on_open(ws):
    print("Opened connection")


if __name__ == "__main__":
    websocket.enableTrace(True)
    ws = websocket.WebSocketApp("ws://localhost:5000/ws",
                                on_open=on_open,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    # Set dispatcher to automatic reconnection, 5 second reconnect delay if
    #   connection closed unexpectedly
    ws.run_forever(dispatcher=rel, reconnect=5)
    rel.signal(2, rel.abort)  # Keyboard Interrupt
    rel.dispatch()
