import os
import json
import pprint

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
    FlexMessage,
    FlexContainer,
)


from db_utils import Database
from user_context import *
from request_type import *
from build_flex import *
from prompt import *


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


handler = WebhookHandler(CHANNEL_SECRET)
configuration = Configuration(access_token=CHANNEL_ACCESS_TOKEN)
openai_client = OpenAI(
    api_key=OPENAI_API_KEY,
    organization=OPENAI_ORG_ID,
    project=OPENAI_PROJECT_ID,
)
db = Database()
user_context_manager = UserContextManager()


def hello_bot(request):
    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)

    except InvalidSignatureError:
        print("not request from LINE")

    user_context_manager.remove_expired_contexts(db)

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    try:
        handle_message(event)

    except Exception as e:
        print("error:\n", e)
        send_line_text_message(event, "error occurred.")


def handle_message(event):
    uid = event.source.user_id

    # if first time user
    if not db.if_user_exist(uid):
        db.add_new_user(uid)

    # get user context
    user_context: UserContext = user_context_manager.get_or_create_context(uid)

    (request_type, user_message) = parse_request(event.message.text)

    if user_context.current_state == Status.HANDLE_REQUEST:

        # generate project idea (by openai)
        if request_type == RequestType.GET_IDEA:
            if MODE == "development":
                print("HANDLE_REQUEST > GET_IDEA")

            projects = db.get_all_projects(uid)
            prompt = build_get_idea_prompt(projects)
            openai_response = get_openai_response(prompt)
            project_name, project_description = get_project_info(openai_response)
            send_line_text_message(
                event,
                f"Here is your new project idea: {project_name}\n{project_description}",
            )
            return

        # return list of projects with name and description
        elif request_type == RequestType.GET_PROJECTS:
            if MODE == "development":
                print("HANDLE_REQUEST > GET_PROJECTS")

            projects = db.get_all_projects(uid)
            if projects == None:
                send_line_text_message(event, "seems like you don't have any projects")
                return

            project_list = []
            for project in projects:
                project_list.append(build_project_flex(project["name"]))
            project_flex_list = build_project_list_flex(project_list)
            send_line_flex_message(event, project_flex_list)
            return

        # add new project
        elif request_type == RequestType.ADD_PROJECT:
            if MODE == "development":
                print("HANDLE_REQUEST > ADD_PROJECT")

            user_context.update_state(Status.ADD_PROJECT)
            send_line_text_message(event, "tell me about you idea")
            return

        # set project context
        elif request_type == RequestType.SET_PROJECT:
            if MODE == "development":
                print("HANDLE_REQUEST > SET_PROJECT")

            user_context.update_state(Status.IN_DIALOGUE)

            # initialize project context
            project = db.get_project(uid, user_message)
            old_dialogue_list = db.get_project_dialogues(uid, user_message)
            context = build_project_context(
                project["name"], project["description"], old_dialogue_list
            )
            user_context.update_project(project["name"], context)

            prompt = build_context_prompt(context, type="summary")
            openai_response = get_openai_response(prompt)

            send_line_text_message(event, openai_response)
            return

        # act like a normal chatbot
        else:
            openai_response = get_openai_response(
                [{"role": "user", "content": user_message}]
            )
            send_line_text_message(event, openai_response)
            return

    elif user_context.current_state == Status.ADD_PROJECT:

        # add new project into database
        if request_type == None:
            if MODE == "development":
                print("ADD_PROJECT > ADD_PROJECT")

            # parse project name and description
            prompt = build_parse_project_info_prompt(user_message)
            openai_response = get_openai_response(prompt)
            project_name, project_description = get_project_info(openai_response)

            db.add_new_project(uid, project_name, project_description)

            # switch to dialogue state, so user can directly discuss about the project
            user_context.update_state(Status.IN_DIALOGUE)
            context = build_project_context(project_name, project_description, [])
            user_context.update_project(project_name, context)
            send_line_text_message(
                event,
                f"project [{project_name}] added successfully.\nnow we can discuss about {project["name"]}!",
            )
            return

        # cancel adding project
        else:
            if MODE == "development":
                print("ADD_PROJECT > CANCEL_ADD_PROJECT")

            user_context.update_state(Status.HANDLE_REQUEST)
            send_line_text_message(event, "do nothing.")
            return

    elif user_context.current_state == Status.IN_DIALOGUE:

        # continue dialogue
        if request_type == None:
            if MODE == "development":
                print("IN_DIALOGUE > CONTINUE_DIALOGUE")

            prompt = build_context_prompt(
                user_context.current_project_context, user_message, type="response"
            )
            openai_response = get_openai_response(prompt)
            dialogue = db.generate_dialogue_dict(
                uid, user_message, openai_response, user_context.current_project_name
            )
            user_context.add_new_dialog(dialogue)
            send_line_text_message(event, openai_response)
            return

        # leave dialogue state, store dialogues, and update project description
        else:
            if MODE == "development":
                print("IN_DIALOGUE > LEAVE_DIALOGUE")

            user_context.update_state(Status.HANDLE_REQUEST)
            db.store_dialogues(uid, user_context.new_dialogue_list)

            # gerenate new project description
            prompt = build_parse_project_info_prompt(
                user_context.current_project_context
            )
            openai_response = get_openai_response(prompt)
            project_name, project_description = get_project_info(openai_response)
            db.update_project(
                uid, user_context.current_project_name, project_description, False
            )
            send_line_text_message(event, "discuss end.\nproject description updated.")
            return


def get_openai_response(prompt):
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=prompt,
        max_tokens=150,
    )

    # if MODE == "development":
    #     print("\nprompt:\n", prompt)
    #     print("\nopenai response:\n", completion.choices[0].message.content)

    return completion.choices[0].message.content


def get_project_info(openai_response):
    obj = json.loads(openai_response)
    return obj["name"], obj["description"]


def send_line_text_message(event, text_message):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text_message)],
            )
        )


def send_line_flex_message(event, flex):
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[
                    FlexMessage(
                        altText="flex message",
                        contents=FlexContainer.from_dict(flex),
                    )
                ],
            )
        )
