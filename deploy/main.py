import functions_framework

from google.cloud.firestore import Client
from google.cloud.firestore_bundle import FirestoreBundle

from openai import OpenAI

from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    TextMessage,
)

from secret import CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET
from secret import OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT_ID

# set up linebot
handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)

# set up OpenAI
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=OPENAI_PROJECT_ID,
)

# set up Firestore
db = Client()
bundle = FirestoreBundle("my-bundle")
bundle.add_named_query("all-users", db.collection("users")._query())
bundle.add_named_query(
    "top-ten-hamburgers",
    db.collection("hamburgers").limit(limit=10),
)
serialized: str = bundle.build()


@functions_framework.http
def hello_bot(request):

    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)

    except InvalidSignatureError:
        print("not request from LINE")

    print(request)
    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)

        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Use english."},
                {"role": "user", "content": event.message.text},
            ],
        )
        openai_response = completion.choices[0].message.content

        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=openai_response)],
            )
        )
