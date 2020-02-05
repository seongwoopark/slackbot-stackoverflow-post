import os

import slack
from flask import Flask


app = Flask(__name__)


@slack.RTMClient.run_on(event='message')
def say_hello(**payload):
    data = payload['data']
    web_client = payload['web_client']
    rtm_client = payload['rtm_client']
    if 'Hello' in data.get('text', []):
        channel_id = data['channel']
        thread_ts = data['ts']
        user = data['user']

        web_client.chat_postMessage(
            channel=channel_id,
            text=f"Hi <@{user}>!",
            thread_ts=thread_ts
        )


@app.route('/')
def index():
    return "<h1>Welcome to our server !!</h1>"


@app.route('/bot')
def bot():
    slack_token = os.environ["SLACK_API_TOKEN"]
    rtm_client = slack.RTMClient(token=slack_token)
    rtm_client.start()


if __name__ == '__main__':
    app.run()
