from datetime import datetime, timedelta
from enum import Enum

TIMEOUT = 30


class Status(Enum):
    HANDLE_REQUEST = 0
    ADD_PROJECT = 1
    IN_DIALOG = 1


class UserContext:
    def __init__(self, user_id):
        self.user_id = user_id
        self.current_state = Status.HANDLE_REQUEST
        self.current_project = None
        self.dialogue_cache_list = []
        self.last_updated = datetime.now()

    def update_state(self, state):
        self.current_state = state
        self.last_updated = datetime.now()

    def update_project(self, project_name):
        self.current_project = project_name
        self.last_updated = datetime.now()

    def add_dialog_cache(self, dialogue_cache):
        self.dialogue_cache_list.append(dialogue_cache)
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

    def remove_expired_contexts(self):
        expired_users = [
            user_id
            for user_id, context in self.contexts.items()
            if context.is_expired()
        ]
        for user_id in expired_users:
            del self.contexts[user_id]
            print(f"removed expired context for user: {user_id}")
