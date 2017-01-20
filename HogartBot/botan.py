# -*- coding: utf-8 -*-
# Modified for pyTelegramBotAPI (https://github.com/eternnoir/pyTelegramBotAPI/)

import requests
import json

TRACK_URL = 'https://api.botan.io/track'


# Эту функцию можно модифицировать, чтобы собирать...
# ...именно то, что нужно (или вообще ничего)
def make_json(message, answer = '',text = ''):
    data = [{'"{}"'.format(message.text if text == '' else text): 
        {message.from_user.username: ['id:{}'.format(message.from_user.id),
            'chat_id:{}'.format(message.chat.id),'message_id:{}'.format(message.message_id)
        ]}
    }]
    if answer != '':
        data.append({answer: message.text if text == '' else text})
    return json.dumps(data)


def track(token, uid, message, name='Message', answer = '', text = ''):
    try:
        if name.find('Inline') > -1:
            r = requests.post(
                TRACK_URL,
                params={"token": token, "uid": uid, "name": name},
                #data=make_json(message, answer),
                data=json.dumps([uid]),
                headers={'Content-type': 'application/json'},
            )
        else:
            r = requests.post(
                TRACK_URL,
                params={"token": token, "uid": uid, "name": name},
                data=make_json(message, answer, text),
                #data=json.dumps(message),
                headers={'Content-type': 'application/json'},
            )
        
        return r.json()
    except requests.exceptions.Timeout:
        # set up for a retry, or continue in a retry loop
        return False
    except (requests.exceptions.RequestException, ValueError) as e:
        # catastrophic error
        print(e)
        return False
