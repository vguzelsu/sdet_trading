# Task Status
## Server 
### Basic requirements
- [x] Implement API enpoints
- [x] Make sure that server sends confirmation and orderId upon successfull POST requests
- [x] Adding random short delay between 0,1 and 1 second for each end point
### Advanced requirements
- [x] Make server asyncchronous
- [x] Implement WebSocket functionality into your server
- [x] Adding random short delay for each order status update
- [x] Make sure order status updates are published to subscribed client via Websocket connection
- [ ] Dockerize server and make it possible to run it in a separate container
## Test cases
### Basic requirements
- [x] Covering all endpoints and methods of the api
- [x] Organizing test cases into test suites abd test functions using a testing framework
- [x] Including both positive and negative scenarios including input validation
- [x] Verifying both correctness and the expected behavior of the api
- [ ] Dockerize test suite and make it possible to run it in a separate container
- [x] Enable to generate standalone html report for test suite runs
### Advanced requirements
- [ ] Ensure that real-time order status updates are properly received by connected WebSocket clients
- [ ] Ensure that the order of receiving order status updates are correct

# How to Run
## Running server
> uvicorn server:app --host 127.0.0.1 --port 5000 --reload
  or
> python server.py
## Running test suite
> pytest --verbose -s --html=test_report.html --self-contained-html  .\tests\test_rest_api.py
## Running simple websocket client demo
> python simple_websocket_client_example.py
