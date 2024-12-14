from datetime import datetime, timedelta
from enum import Enum

TIMEOUT = 30


class Status(Enum):
    HANDLE_REQUEST = 0
    ADD_PROJECT = 1
    IN_DIALOGUE = 2


class UserContext:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_state = Status.HANDLE_REQUEST
        self.current_project_name = None
        self.current_project_context = None
        self.new_dialogue_list = []
        self.last_updated = datetime.now()

    def update_state(self, state):
        self.current_state = state
        self.last_updated = datetime.now()

    def update_project(self, project_name, project_context):
        self.current_project_name = project_name
        self.current_project_context = project_context
        self.new_dialogue_list = []
        self.last_updated = datetime.now()

    def add_new_dialog(self, dialogue):
        self.new_dialogue_list.append(dialogue)
        self.current_project_context += (
            f"User: {dialogue['user_ask']}\nBot: {dialogue['bot_response']}\n"
        )
        self.last_updated = datetime.now()

    def is_expired(self):
        return datetime.now() - self.last_updated > timedelta(minutes=TIMEOUT)


class UserContextManager:
    def __init__(self):
        self.contexts = {}

    def get_or_create_context(self, user_id):
        if user_id not in self.contexts.keys():
            print(f"created new context for user: {user_id}")
            self.contexts[user_id] = UserContext(user_id)
        return self.contexts[user_id]

    def remove_expired_contexts(self, db):
        expired_users = [
            user_id
            for user_id, context in self.contexts.items()
            if context.is_expired()
        ]
        for user_id in expired_users:
            db.store_dialogues(user_id, self.contexts[user_id].new_dialogue_list)
            del self.contexts[user_id]
            print(f"removed expired context for user: {user_id}")
