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


RICHMENU_ID = "richmenu-d093eb83684baf5943d16b92bfb6e721"

RICHMENU_JSON = {
    "size": {"width": 1200, "height": 405},
    "selected": False,
    "name": "richmenu-1",
    "chatBarText": "選單",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 400, "height": 200},
            "action": {"type": "message", "label": "新增專案", "text": "[ADD_PROJECT]"},
        },
        {
            "bounds": {"x": 0, "y": 200, "width": 400, "height": 200},
            "action": {
                "type": "message",
                "label": "移除專案",
                "text": "[REMOVE_PROJECT]",
            },
        },
        {
            "bounds": {"x": 400, "y": 0, "width": 400, "height": 400},
            "action": {
                "type": "message",
                "label": "討論專案",
                "text": "[GET_PROJECTS]",
            },
        },
        {
            "bounds": {"x": 800, "y": 0, "width": 400, "height": 400},
            "action": {"type": "message", "label": "獲取靈感", "text": "[GET_IDEA]"},
        },
    ],
}
