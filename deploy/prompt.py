# generate prompt for different tasks
from typing import List, Dict

BASE_PROMPT = "除非用戶明確指定語言，否則請使用繁體中文回應。以純文字回應，請勿加入任何Markdown語法。你的回應限制在300字內，不要讓回答被截斷。\n"


def prompt_for_generate_idea(project_list: List[Dict]):
    system_prompt = BASE_PROMPT
    system_prompt += "你是一位有創意的專案發想專家。根據使用者的過去專案，推薦一個創意、有可行性且符合他們興趣與技能的新專案點子。請確保推薦包含清晰的專案名稱和簡介。\n"
    system_prompt += "以下是使用者的過去專案：\n"

    if project_list == None:
        system_prompt += "無\n"
    else:
        for i, project in enumerate(project_list):
            system_prompt += f"{i+1}. {project['name']}: {project['description']}\n"

    system_prompt += "你的回應應以下列JSON格式呈現：\n"
    system_prompt += '{\n"name": "專案名稱",\n"description": "專案簡介"\n}\n'
    system_prompt += "名稱應簡潔且描述性，且字數不超過30字。簡介應清楚簡短，說明專案的用途，且字數不超過50字。\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "請給我一個專案點子。"},
    ]


def prompt_for_parse_project_info(project_info: str):
    system_prompt = BASE_PROMPT
    system_prompt += "你正在協助使用者新增一個專案到資料庫中。\n"
    system_prompt += "請根據使用者提供的資訊解析專案名稱與簡介。\n"
    system_prompt += "你的回應應以下列JSON格式呈現：\n"
    system_prompt += '{\n"name": "專案名稱",\n"description": "專案簡介"\n}\n'
    system_prompt += "名稱應簡潔且描述性，且字數不超過30字。簡介應清楚簡短，說明專案的用途，且字數不超過50字。\n"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": project_info},
    ]


def prompt_for_project_discuss(context: str, user_input="", type="response"):
    system_prompt = BASE_PROMPT
    system_prompt += context

    if type == "summary":
        system_prompt += "請提供簡潔的50字討論摘要，幫助使用者回憶先前討論進度。\n"
    elif type == "response":
        system_prompt += (
            "根據先前對話內容，提供一個與使用者專案相關並延續對話的回應。\n"
        )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_input},
    ]


def build_project_context(
    project_name: str, project_description: str, dialogue_list: List[Dict]
) -> str:
    context = "你正在與使用者討論一個專案。以下是專案資訊：\n"
    context += f"專案名稱: {project_name}\n"
    context += f"專案簡介: {project_description}\n"

    context += "以下是先前的對話：\n"
    if dialogue_list != None:
        for dialogue in dialogue_list:
            context += (
                f"User: {dialogue['user_ask']}\nBot: {dialogue['bot_response']}\n"
            )

    return context
