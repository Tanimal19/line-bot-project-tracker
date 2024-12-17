import os
import json
from typing import Tuple

from openai import OpenAI
from linebot.exceptions import InvalidSignatureError
from linebot.v3 import WebhookHandler
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)
from linebot.v3.messaging import (
    Configuration,
    ApiClient,
    MessagingApi,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage,
    FlexContainer,
    ShowLoadingAnimationRequest,
)


from db_utils import Database
from user_context import *
from request_type import *
from line_assest import *
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
    print(request)

    # chech if is refresh request (by google cloud scheduler)
    if request.args.get("refresh") == "true":
        # send notification to all users
        users = db.get_user_list()
        for user_id in users:
            if user_id == "test-user":
                continue
            push_project_notification(user_id)

        user_context_manager.cleanup_all(db)

        return "refreshed"

    try:
        signature = request.headers["X-Line-Signature"]
        body = request.get_data(as_text=True)
        handler.handle(body, signature)

    except InvalidSignatureError:
        print("Not Line request")

    return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def message_text(event):
    try:
        handle_message(event)

    except Exception as e:
        print("error:\n", e)
        send_line_text_message(event, "error occurred.")


def handle_message(event):
    send_line_loading_animation(event)

    user_id = event.source.user_id

    # if first time user
    if not db.is_user_exist(user_id):
        db.add_user(user_id)

    # get user context
    user_context: UserContext = user_context_manager.get_or_create_context(user_id)

    (request_type, user_message) = parse_request(event.message.text)

    if user_context.current_state == Status.HANDLE_REQUEST:

        # generate project idea (by openai)
        if request_type == RequestType.GET_IDEA:
            if MODE == "development":
                print("HANDLE_REQUEST > GET_IDEA")

            project_list = db.get_project_list(user_id)
            prompt = prompt_for_generate_idea(project_list)
            openai_response = get_openai_response(prompt)
            project_name, project_description = parse_project_info(openai_response)

            send_line_text_message(
                event,
                f"專案發想: {project_name}\n{project_description}",
            )
            return

        # return list of projects with name and description
        elif request_type == RequestType.GET_PROJECTS:
            if MODE == "development":
                print("HANDLE_REQUEST > GET_PROJECTS")

            project_list = db.get_project_list(user_id)
            if project_list == None:
                send_line_text_message(
                    event, "看起來你還沒有任何專案，趕快新增一個吧！"
                )
                return

            project_flex_list = [
                build_project_flex(project["name"]) for project in project_list
            ]

            send_line_flex_message(
                event, build_project_list_flex("你目前的專案:", project_flex_list)
            )
            return

        elif request_type == RequestType.GET_DIALOGUES:
            if MODE == "development":
                print("HANDLE_REQUEST > GET_DIALOGUES")

            send_line_text_message(event, "抱歉，此功能還未開放 :(")
            return

        # add new project
        elif request_type == RequestType.ADD_PROJECT:
            if MODE == "development":
                print("HANDLE_REQUEST > ADD_PROJECT")

            user_context.update_state(Status.ADD_PROJECT)
            send_line_text_message(
                event, "請說明欲新增的專案內容\n說多一點可以讓 bot 更容易理解喔~"
            )
            return

        # remove project
        elif request_type == RequestType.REMOVE_PROJECT:
            if MODE == "development":
                print("HANDLE_REQUEST > REMOVE_PROJECT")

            # show list of projects
            project_list = db.get_project_list(user_id)
            if project_list == None:
                send_line_text_message(
                    event, "喔喔，看起來你還沒有任何專案，趕快新增一個吧！"
                )
                return

            user_context.update_state(Status.REMOVE_PROJECT)
            project_flex_list = [
                build_project_flex(project["name"]) for project in project_list
            ]

            send_line_flex_message(
                event, build_project_list_flex("請選擇欲移除的專案:", project_flex_list)
            )
            return

        # set project context
        elif request_type == RequestType.SET_PROJECT:
            if MODE == "development":
                print("HANDLE_REQUEST > SET_PROJECT")

            user_context.update_state(Status.IN_DIALOGUE)

            # initialize project context
            project = db.get_project_dict(user_id, user_message)
            history_dialogue_list = db.get_project_dialogue_list(user_id, user_message)
            project_context = build_project_context(
                project["name"], project["description"], history_dialogue_list
            )
            user_context.update_project(project["name"], project_context)

            prompt = prompt_for_project_discuss(project_context, type="summary")
            openai_response = get_openai_response(prompt)

            send_line_text_message(event, openai_response)
            return

        elif request_type == RequestType.CANCEL:
            if MODE == "development":
                print("HANDLE_REQUEST > CANCEL")

            send_line_text_message(event, "沒有可以取消的動作 :(")
            return

    elif user_context.current_state == Status.ADD_PROJECT:

        # add new project into database
        if request_type == None:
            if MODE == "development":
                print("ADD_PROJECT > ADD_PROJECT")

            # parse project name and description
            prompt = prompt_for_parse_project_info(user_message)
            openai_response = get_openai_response(prompt)
            project_name, project_description = parse_project_info(openai_response)

            db.add_project(user_id, project_name, project_description)

            # switch to dialogue state, so user can directly discuss about the project
            user_context.update_state(Status.IN_DIALOGUE)
            project_context = build_project_context(
                project_name, project_description, []
            )
            user_context.update_project(project_name, project_context)

            send_line_text_message(
                event,
                f"成功新增專案: {project_name}\n馬上開始討論{project_name}吧！",
            )
            return

        # cancel adding project
        elif request_type == RequestType.CANCEL:
            if MODE == "development":
                print("ADD_PROJECT > CANCEL_ADD_PROJECT")

            user_context.update_state(Status.HANDLE_REQUEST)
            send_line_text_message(event, "取消新增專案")
            return

    elif user_context.current_state == Status.REMOVE_PROJECT:

        # remove select project into database
        if request_type == RequestType.SET_PROJECT:
            if MODE == "development":
                print("REMOVE_PROJECT > REMOVE_PROJECT")

            user_context.update_state(Status.HANDLE_REQUEST)

            db.remove_project(user_id, user_message)

            send_line_text_message(event, f"成功移除專案: {user_message}")
            return

        # cancel adding project
        elif request_type == RequestType.CANCEL:
            if MODE == "development":
                print("REMOVE_PROJECT > CANCEL_REMOVE_PROJECT")

            user_context.update_state(Status.HANDLE_REQUEST)
            send_line_text_message(event, "取消移除專案")
            return

    elif user_context.current_state == Status.IN_DIALOGUE:

        # continue dialogue
        if request_type == None:
            if MODE == "development":
                print("IN_DIALOGUE > CONTINUE_DIALOGUE")

            prompt = prompt_for_project_discuss(
                user_context.current_project_context, user_message, type="response"
            )
            openai_response = get_openai_response(prompt)
            dialogue = db.generate_dialogue_dict(user_message, openai_response)
            user_context.add_new_dialog(dialogue)

            send_line_text_message(event, openai_response)
            return

        # leave dialogue state, store dialogues, and update project description
        elif request_type == RequestType.CANCEL:
            if MODE == "development":
                print("IN_DIALOGUE > LEAVE_DIALOGUE")

            user_context.update_state(Status.HANDLE_REQUEST)
            db.add_project_dialogues(
                user_id,
                user_context.current_project_name,
                user_context.new_dialogue_list,
            )

            # gerenate new project description
            prompt = prompt_for_parse_project_info(user_context.current_project_context)
            openai_response = get_openai_response(prompt)
            project_name, project_description = parse_project_info(openai_response)
            db.update_project(
                user_id, user_context.current_project_name, project_description, False
            )

            send_line_text_message(event, "結束討論專案，專案簡介已更新！")
            return

    send_line_text_message(event, "無效的指令 :(")
    return


def get_openai_response(prompt) -> str:
    completion = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=prompt,
        max_tokens=400,
    )

    # if MODE == "development":
    #     print("\nprompt:\n", prompt)
    #     print("\nopenai response:\n", completion.choices[0].message.content)

    return completion.choices[0].message.content


def parse_project_info(openai_response: str) -> Tuple[str, str]:
    obj = json.loads(openai_response)
    return obj["name"], obj["description"]


def push_project_notification(user_id: str) -> None:
    project_list = db.get_project_list(user_id)

    notification = "嗨，今天有新點子嗎？\n"
    if project_list is None:
        notification += "你還沒有任何專案，趕快新增一個吧！"
    elif len(project_list) == 1:
        notification += f'快來討論 {project_list[-1]["name"]} 吧！'
    else:
        notification += f"你目前已經累積了 {len(project_list)} 個專案想法！\n"
        notification += f'最近討論的專案: {project_list[-1]["name"]}\n'
        notification += f'最久沒動的專案: {project_list[0]["name"]}'

    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.push_message_with_http_info(
            PushMessageRequest(
                to=user_id,
                messages=[TextMessage(text=notification)],
            )
        )


def send_line_text_message(event, text_message: str) -> None:
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.reply_message_with_http_info(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=text_message)],
            )
        )


def send_line_flex_message(event, flex: dict) -> None:
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


def send_line_loading_animation(event) -> None:
    with ApiClient(configuration) as api_client:
        line_bot_api = MessagingApi(api_client)
        line_bot_api.show_loading_animation_with_http_info(
            ShowLoadingAnimationRequest(chatId=event.source.user_id, loadingSeconds=10)
        )
