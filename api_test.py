import requests

url = "http://127.0.0.1:8000/chat"
data = {"message": "suggest me 3 horro books"}
response = requests.post(url, json=data)

print(response.json())
