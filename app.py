import asyncio
import os

import slack
from sanic import Sanic


app = Sanic()


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
async def index():
    return "<h1>Welcome to server !!</h1>"


@app.websocket('/bot')
async def bot(request, ws):
    slack_token = os.environ["SLACK_API_TOKEN"]
    rtm_client = slack.RTMClient(token=slack_token)
    rtm_client.start()
    while True:
        await asyncio.sleep(1)


if __name__ == "__main__":
    app.run()
