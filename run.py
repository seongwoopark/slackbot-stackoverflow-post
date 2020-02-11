import asyncio
import os
import re
from pprint import pprint

import aiohttp
import slack
from yarl import URL


SLACK_BOT_TOKEN = os.environ["SLACK_API_TOKEN"]
# SLACK_LEGACY_TOKEN = os.environ["SLACK_API_LEGACY_TOKEN"]
STACKOVERFLOW_KEY = os.environ["STACKOVERFLOW_KEY"]
STACKOVERFLOW_ACCESS_TOKEN = os.environ["STACKOVERFLOW_ACCESS_TOKEN"]
STACKOVERFLOW_SITE = 'stackoverflow'
STACKOVERFLOW_TEAM_URL = os.environ["STACKOVERFLOW_TEAM_URL"]

QUESTION_PATTERN = re.compile(r"^[^\S\r\n]*Q\.[^\S\r\n]*")
ANSWER_PATTERN = re.compile(r"^[^\S\r\n]*A\.[^\S\r\n]*")


class StackOverFlowDispatcher:
    def __init__(self):
        self.headers = {
            'X-API-Access-Token': STACKOVERFLOW_ACCESS_TOKEN
        }
        self.query_params = {
            'site': STACKOVERFLOW_SITE,
            'team': STACKOVERFLOW_TEAM_URL,
            'key': STACKOVERFLOW_KEY
        }
        self.session = aiohttp.ClientSession(headers=self.headers)

    async def _get(self, url: URL):
        url = url.update_query(self.query_params)
        async with self.session.get(url) as response:
            return await response.json()

    async def _post(self, url):
        pass

    async def search(self, query: str, limit: int = 3):
        url = URL('https://api.stackexchange.com/2.2/search/advanced')
        url = url.update_query(q=query)
        response = await self._get(url)
        return response['items'][:limit]


dispatcher = StackOverFlowDispatcher()


@slack.RTMClient.run_on(event='message')
async def on_message(**payload):
    # print payload
    # pprint(payload)

    # unpack data
    data = payload['data']
    text = data.get('text')
    channel_id = data['channel']
    thread_ts = data['ts']
    user = data.get('user')
    web_client = payload['web_client']

    # handle text
    if text and QUESTION_PATTERN.match(text):
        # split text with QUESTION_PATTERN
        title_and_body = QUESTION_PATTERN.split(text)[-1] + '\n'
        chunks = [part for part in title_and_body.split('\n') if part]
        if len(chunks) == 0:
            pass
        elif len(chunks) == 1:
            await reply(client=web_client, channel_id=channel_id, thread_ts=thread_ts, title=chunks[0], body=chunks[0])
        else:
            await reply(client=web_client, channel_id=channel_id, thread_ts=thread_ts, title=chunks[0], body=chunks[1])


async def reply(client, channel_id: str, thread_ts: str, title: str, body: str = None):
    # search existing question or answer items by body
    results = await dispatcher.search(query=title)
    # post slack message to search results
    if results:
        text = f'Results for *_"{title}"_*:\n' + \
               '\n'.join([f"<{r['link']}|{i}. {r['title']}>" for i, r in enumerate(results, start=1)])
    else:
        text = f'No results found for *_"{title}"_*'
    client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": text},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Search on Stackoverflow"
                        },
                        "url": str(URL(f"{STACKOVERFLOW_TEAM_URL}/search").update_query(q=title, mixed=0))
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Ask on Stackoverflow"
                        },
                        "url": str(URL(f"{STACKOVERFLOW_TEAM_URL}/questions/ask").update_query(title=title, r='Slack'))
                    }
                ]
            }
        ]
    )

    # TO USE SLACK COMMAND TO USE STACK OVERFLOW APP COMMAND
    # web_client_legacy = slack.WebClient(token=SLACK_LEGACY_TOKEN, run_async=True)
    # web_client_legacy.api_call(
    #     api_method='chat.command',
    #     json=dict(
    #         token=SLACK_LEGACY_TOKEN,
    #         channel=channel_id,
    #         command="/stack",
    #         text=f"search {body}",
    #     )
    # )


if __name__ == '__main__':
    print("bot is running")
    loop = asyncio.get_event_loop()
    rtm_client = slack.RTMClient(token=SLACK_BOT_TOKEN, run_async=True, loop=loop)
    loop.run_until_complete(rtm_client.start())
    print("bot is closed")
