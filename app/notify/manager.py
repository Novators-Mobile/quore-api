import firebase_admin
from firebase_admin import credentials
import firebase_admin.messaging

cred = credentials.Certificate('app/notify/firebase.json')
firebase_admin.initialize_app(cred)

def sendNotification(title: str, msg: str, tokens, obj=None):
    message = firebase_admin.messaging.MulticastMessage(
        notification=firebase_admin.messaging.Notification(
            title=title,
            body=msg
        ),
        data=obj,
        tokens=tokens
    )
    firebase_admin.messaging.send_multicast(message)

def sendMessage(tokens, obj=None):
    message = firebase_admin.messaging.MulticastMessage(
        data=obj,
        tokens=tokens
    )
    firebase_admin.messaging.send_multicast(message)