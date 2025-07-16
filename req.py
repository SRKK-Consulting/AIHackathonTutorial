import requests

url = "http://localhost:8000/api/message"
payload = {
    "content": "Hi BankingKnowledge"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code, response.json())