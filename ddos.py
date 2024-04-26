import requests
import threading

def send_request():
    response = requests.get('http://192.168.0.126:8091')
    print(response)
    print(response.headers)


# threading.Thread(target=send_request).start()

for i in range(300):  # Adjust this value based on your needs
    threading.Thread(target=send_request).start()
