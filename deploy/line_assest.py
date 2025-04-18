from typing import List, Dict


def build_project_flex(project_name: str) -> dict:
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


def build_project_list_flex(title: str, project_flex_list: List[Dict]) -> dict:
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "lg",
                }
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": project_flex_list,
            "flex": 0,
        },
    }


RICHMENU_ID = "richmenu-98647900e802ac8a90d800d12e10e65b"
