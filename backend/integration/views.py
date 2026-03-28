from django.shortcuts import render

# Create your views here.
from twilio.rest import Client

account_sid = 'AC2d9aa458165b9fdf89e06fc5ac29cd4d'
auth_token = '[AuthToken]'
client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  content_sid='HXb5b62575e6e4ff6129ad7c8efe1f983e',
  content_variables='{"1":"12/1","2":"3pm"}',
  to='whatsapp:+94773584585'
)

print(message.sid)