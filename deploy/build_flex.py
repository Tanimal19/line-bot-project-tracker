# for flex message building
def build_project_flex(project_name):
    return {
        "type": "button",
        "style": "secondary",
        "height": "sm",
        "action": {
            "type": "message",
            "label": project_name,
            "text": f"[SET_PROJECT]{project_name}",
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
