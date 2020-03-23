from django.test import TestCase

import requests

url = "https://fuelfinderzim.com/api/view-updates-user/"

data = {'username': 'mchihota'}

msg = requests.post(url=url, data=data)
print(msg.status_code, msg.content)

