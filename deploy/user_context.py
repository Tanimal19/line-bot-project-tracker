from datetime import datetime
from enum import Enum
from db_utils import Database

TIMEOUT = 30


class Status(Enum):
    HANDLE_REQUEST = 0
    ADD_PROJECT = 1
    REMOVE_PROJECT = 2
    IN_DIALOGUE = 3


class UserContext:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_state = Status.HANDLE_REQUEST
        self.current_project_name = None
        self.current_project_context = None
        self.new_dialogue_list = []
        self.last_updated = datetime.now()

    def update_state(self, state: Status):
        self.current_state = state
        self.last_updated = datetime.now()

    def update_project(self, project_name: str, project_context: str):
        self.current_project_name = project_name
        self.current_project_context = project_context
        self.new_dialogue_list = []
        self.last_updated = datetime.now()

    def add_new_dialog(self, dialogue: dict):
        self.new_dialogue_list.append(dialogue)
        self.current_project_context += (
            f"User: {dialogue['user_ask']}\nBot: {dialogue['bot_response']}\n"
        )
        self.last_updated = datetime.now()


class UserContextManager:
    def __init__(self):
        self.contexts = {}

    def get_or_create_context(self, user_id) -> UserContext:
        if user_id not in self.contexts.keys():
            print(f"created new context for user: {user_id}")
            self.contexts[user_id] = UserContext(user_id)
        return self.contexts[user_id]

    def cleanup_all(self, db: Database) -> None:
        for user_id, context in self.contexts.items():
            db.add_project_dialogues(
                user_id, context.current_project_name, context.new_dialogue_list
            )
            del self.contexts[user_id]

        self.contexts = {}
        print("user contexts refreshed")
