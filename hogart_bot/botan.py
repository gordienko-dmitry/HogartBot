import requests
import logging
import json

from telebot.types import Message
from typing import Optional

TRACK_URL: str = 'https://api.botan.io/track'


def make_json(message: Message, answer: str = '', text: str = '') -> str:
    """Making json string."""
    data = [
        {
            f'{message.text if text == "" else text}':
                {
                    message.from_user.username: [
                        f'id:{message.from_user.id}',
                        f'chat_id:{message.chat.id}',
                        f'message_id:{message.message_id}'
                    ]
                }
        }
    ]

    if answer != '':
        data.append({answer: message.text if text == '' else text})

    return json.dumps(data)


def track(token: str, uid: str, message: Optional[Message], name: str = 'Message',
          answer: str = '', text: str = '') -> bool:
    """Fixing track to botan service."""
    try:
        if name.find('Inline') > -1:
            r = requests.post(
                TRACK_URL,
                params={"token": token, "uid": uid, "name": name},
                data=json.dumps([uid]),
                headers={'Content-type': 'application/json'},
            )
        else:
            r = requests.post(
                TRACK_URL,
                params={"token": token, "uid": uid, "name": name},
                data=make_json(message, answer, text),
                headers={'Content-type': 'application/json'},
            )
        
        return True
    except requests.exceptions.Timeout:
        return False
    except (requests.exceptions.RequestException, ValueError) as e:
        logging.exception(e)
        return False
