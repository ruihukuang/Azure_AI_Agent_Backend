import requests

url = "http://127.0.0.1:8000/items/"
data = {
    "name": "Coffee",
    "price": 4.5,
    "is_offer": True
}

response = requests.post(url, json=data)
print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")