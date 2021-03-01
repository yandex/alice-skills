from __future__ import unicode_literals

import json
import logging

import pandas as pd
from datetime import date
from alisa import Alisa, Dialog

# -- LOCAL CHECK -- #
from flask import Flask, request

# -- LOCAL CHECK -- #

logging.basicConfig(level=logging.DEBUG)


class ShowDialog(Dialog):

    def handle_dialog(self, alisa):
        if alisa.is_show_request():
            return self.handle_morning_show(alisa)

        return self.greetings(alisa)

    def handle_morning_show(self, alisa):
        alisa.show_episode(text=get_data())

    def greetings(self, alisa):
        alisa.tts_with_text(get_data())
        alisa.end_session()


def get_data():
    data_by_date = get_data_by_date(date.today())
    if data_by_date is None:
        return get_random_data()
    else:
        return data_by_date


def get_data_by_date(date):
    if data[data.date == str(date)].empty:
        return None
    return data[data.date == str(date)].sample(n=1)['text'].iloc[0]


def get_random_data():
    return data.sample(n=1)['text'].iloc[0]


def read_data():
    return pd.read_csv('data/data.csv')


data = read_data()
dialog = ShowDialog()


def handle_dialog_yacloud(request, context):
    logging.info('Request: %r', request)

    response = {
        "version": request['version'],
        "response": {
            "end_session": True
        }
    }

    dialog.handle_dialog(Alisa(request, response))

    logging.info('Response: %r', response)

    return response


# -- LOCAL CHECK -- #

app = Flask(__name__)


@app.route("/", methods=['POST'])
def main():
    logging.info('Request: %r', request.json)

    response = {
        "version": request.json['version'],
        "response": {
            "end_session": True
        }
    }

    dialog.handle_dialog(Alisa(request.json, response))

    logging.info('Response: %r', response)

    return json.dumps(
        response,
        ensure_ascii=False,
        indent=2
    )


if __name__ == '__main__':
    app.run(threaded=True, port=5000)
# -- LOCAL CHECK -- #
