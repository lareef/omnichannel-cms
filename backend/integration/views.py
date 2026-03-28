from django.shortcuts import render

# Create your views here.
from twilio.rest import Client
import os
account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
auth_token = os.environ.get('TWILIO_AUTH_TOKEN')

client = Client(account_sid, auth_token)

print(message.sid)
