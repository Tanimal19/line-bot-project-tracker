# for flex message building
def build_project_flex(project_name):
    return {
        "type": "button",
        "style": "secondary",
        "height": "sm",
        "action": {
            "type": "postback",
            "label": project_name,
            "data": f"[SET_PROJECT]{project_name}",
        },
    }


def build_project_list_flex(project_list):
    return {
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


# for openai prompt message
def build_get_idea_prompt(project_list):
    """
    prompt for generating project idea based on user's previous projects
    """

    system_prompt = "You are an expert project idea generator. Based on the user's past projects, recommend exactly one new project idea that is creative, feasible, and aligns with their previous interests and skills. Make sure the recommendation includes a clear project name and a concise description.\nHere are the user's past projects:\n"

    if project_list == None:
        system_prompt += "The user has no past projects.\n"
    else:
        for i, project in enumerate(project_list):
            system_prompt += f"{i+1}. {project['name']}: {project['description']}\n"

    system_prompt += "Your response should be structured as follow json format:\n"
    system_prompt += '{\n"name": "the name of the project",\n"description": "a brief description of the project"\n}\n'
    system_prompt += "The project name should be catchy and descriptive, with no more than 30 characters. The description should be short and clear description of the project, explaining what it does, with no more than 50 words.\n"
    system_prompt += "Focus on making the new project idea relevant to the user's previous projects while adding a fresh perspective."

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": "Please give me one project idea.",
        },
    ]


def build_parse_project_info_prompt(project_info):
    """
    prompt for parsing project name and description from user input
    """

    system_prompt = "You are helping the user add a new project to their list.\n"
    system_prompt += "Please parse the project name and description base on the info given by the user\n"
    system_prompt += "Your response should be structured as follow json format:\n"
    system_prompt += '{\n"name": "the name of the project",\n"description": "a brief description of the project"\n}\n'
    system_prompt += "The project name should be catchy and descriptive, with no more than 30 characters. The description should be short and clear description of the project, explaining what it does, with no more than 50 words.\n"

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": project_info,
        },
    ]


def build_project_context(dialogue_list):
    """
    build project context based on dialogues
    """

    context = (
        "You are discussing a project with the user.\nHere's your previous dialogues:\n"
    )
    for dialogue in dialogue_list:
        context += f"User: {dialogue['user_ask']}\nBot: {dialogue['bot_response']}\n"

    context += "Based on the dialogues, provide a response that is relevant to the user's project and continues the conversation.\n"

    return context
