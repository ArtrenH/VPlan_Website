import requests

r = requests.post('http://localhost:5010/preferences/10001329?course=JG12',
    json=["734", "729", "101"])

print(r.status_code)
print(r.text)