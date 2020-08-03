import requests
import time
from datetime import datetime

timeout=10

while True:
    try:
        response = requests.get("http://localhost:8080/update", timeout=timeout)
        if(response is not None and response.status_code == 200):
            time.sleep(3)
        else:
            print(str(datetime.now().time()) + " Warning: response code != 200")
            time.sleep(5)
    except requests.exceptions.ReadTimeout:
        print(str(datetime.now().time()) + " Critical: Server didn't respond for " + str(timeout) + " sec, retrying in 5 sec")
        time.sleep(5)
    except requests.exceptions.ConnectionError:
        print(str(datetime.now().time()) + " Critical: Connection error, retrying in 5 sec")
        time.sleep(5)
