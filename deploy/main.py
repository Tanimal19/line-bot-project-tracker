import os
from enum import Enum

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

from db_utils import Database
from context import UserContextManager, UserContext, Status


MODE = os.environ.get("MODE", "development")

if MODE == "production":
    CHANNEL_ACCESS_TOKEN = os.environ["CHANNEL_ACCESS_TOKEN"]
    CHANNEL_SECRET = os.environ["CHANNEL_SECRET"]
    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    OPENAI_ORG_ID = os.environ["OPENAI_ORG_ID"]
    OPENAI_PROJECT_ID = os.environ["OPENAI_PROJECT_ID"]
else:
    from secret import CHANNEL_ACCESS_TOKEN, CHANNEL_SECRET
    from secret import OPENAI_API_KEY, OPENAI_ORG_ID, OPENAI_PROJECT_ID
    import functions_framework


handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=OPENAI_PROJECT_ID,
)
db = Database()


# @functions_framework.http
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

        user_message = event.message.text
        user_id = event.source.user_id

        # if first time user
        if not db.if_user_exist(user_id):
            db.add_new_user(user_id)

        # get user context
        user_context = UserContextManager().get_or_create_context(user_id)

        if user_context.current_state == Status.HANDLE_REQUEST:

            # change state to ADD_PROJECT
            if user_message == RequestType.ADD_PROJECT:
                user_context.update_state(Status.ADD_PROJECT)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="Please tell me about your idea!")],
                    )
                )
                return

            # change state to IN_DIALOG
            elif user_message.startswith(RequestType.SET_PROJECT):
                user_context.update_state(Status.IN_DIALOG)
                project_name = user_message.split(" ")[1]
                user_context.update_project(project_name)
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            TextMessage(text="Okay, let's talk about " + project_name)
                        ],
                    )
                )
                return

            # return project list
            elif user_message == RequestType.GET_PROJECTS:
                projects = db.get_all_projects(user_id)
                # format flex message
                project_list = []
                for project in projects:
                    project_list.append(
                        {
                            "type": "button",
                            "style": "secondary",
                            "height": "sm",
                            "action": {
                                "type": "postback",
                                "label": RequestType.SET_PROJECT
                                + " "
                                + project["name"],
                                "data": RequestType.SET_PROJECT + " " + project["name"],
                            },
                        }
                    )

                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[
                            {
                                "type": "bubble",
                                "body": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "Your ideas:",
                                            "weight": "bold",
                                            "size": "lg",
                                        }
                                    ],
                                },
                                "footer": {
                                    "type": "box",
                                    "layout": "vertical",
                                    "spacing": "sm",
                                    "contents": project_list,
                                    "flex": 0,
                                },
                            }
                        ],
                    )
                )
                return

            # return prject idea based on user's previous idea
            elif user_message == RequestType.GET_IDEA:
                projects = db.get_all_projects(user_id)
                idea_context = ""
                completion = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Use english." + idea_context},
                        {"role": "user", "content": "Please give me one project idea in the format of name: short description:"},
                    ],
                )
                openai_response = completion.choices[0].message.content

            else:
                line_bot_api.reply_message_with_http_info(
                    ReplyMessageRequest(
                        reply_token=event.reply_token,
                        messages=[TextMessage(text="Please specify a valid option.")],
                    )
                )
                return

        elif user_context.current_state == Status.ADD_PROJECT:

            if user_message == 


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
            return



class RequestType(Enum):
    ADD_PROJECT = 0
    SET_PROJECT = 1
    GET_PROJECTS = 2
    GET_IDEA = 3

def parse_request_type(message: str):
    if message.startswith("[ADD_PROJECT]"):
        return RequestType.ADD_PROJECT

    elif message.startswith("[SET_PROJECT]"):
        return RequestType.SET_PROJECT

    elif message.startswith("[GET_PROJECTS]"):
        return RequestType.GET_PROJECTS

    elif message.startswith("[GET_IDEA]"):
        return RequestType.GET_IDEA

