from django.test import TestCase

import requests

url = "http://192.168.137.53:8080/api/change-password/"

data = {'old': '7809ea', 'new1': 'marlvin123', 'new2': 'marlvin123', 'username': 'Marlvin'}

msg = requests.post(url=url, data=data)
print(msg.status_code, msg.content)

