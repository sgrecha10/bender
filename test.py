import json
import requests


# url = "http://localhost:32769"
url = "http://172.17.0.1:32769"

payload = {
    "jsonrpc": "2.0",
    "method": "web3_clientVersion",
    "params": [],
    "id": 1
}

headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print("Status code:", response.status_code)
print("Response:", response.text)
