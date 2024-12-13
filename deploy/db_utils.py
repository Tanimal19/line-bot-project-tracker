import os
import firebase_admin
from firebase_admin import firestore, credentials
from google.cloud.firestore_v1.base_query import FieldFilter


MODE = os.environ.get("MODE", "development")

if MODE == "production":
    firebase_admin.initialize_app()
else:
    cred = credentials.Certificate("../firebase-key.json")
    firebase_admin.initialize_app(cred)


class Database:
    def __init__(self):
        self.client = firestore.client()

    # USER
    def if_user_exist(self, line_id: str):
        user_ref = self.client.collection("users").document(line_id)
        user = user_ref.get()
        return user.exists

    def add_new_user(self, line_id: str):
        user_ref = self.client.collection("users").document(line_id)
        user_ref.set(
            {
                "line_id": line_id,
                "create_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )

        return

    # PROJECT
    def add_new_project(
        self, line_id: str, project_name: str, project_description: str
    ):
        project_ref = (
            self.client.collection("users")
            .document(line_id)
            .collection("projects")
            .document()
        )
        project_ref.set(
            {
                "name": project_name,
                "description": project_description,
                "is_active": False,
                "last_used": firestore.SERVER_TIMESTAMP,
                "create_at": firestore.SERVER_TIMESTAMP,
            }
        )
        return

    def remove_project(self, line_id: str, project_name: str):
        project_ref = self.get_project_ref(line_id, project_name)
        if project_ref is None:
            return
        project_ref.delete()
        return

    def update_project(
        self, line_id: str, project_name: str, project_description: str, is_active: bool
    ):
        project_ref = self.get_project_ref(line_id, project_name)
        if project_ref is None:
            return

        if project_name is not None:
            project_ref.set(
                {
                    "name": project_name,
                },
                merge=True,
            )

        if project_description is not None:
            project_ref.set(
                {
                    "description": project_description,
                },
                merge=True,
            )

        if is_active is not None:
            project_ref.set(
                {
                    "is_active": is_active,
                },
                merge=True,
            )

        project_ref.set(
            {
                "last_used": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        return

    def get_all_projects(self, line_id: str):
        projects = (
            self.client.collection("users")
            .document(line_id)
            .collection("projects")
            .order_by("last_used", direction="DESCENDING")
            .stream()
        )
        projects = list(projects)
        if len(projects) == 0:
            return None

        projects = [project.to_dict() for project in projects]

        return projects

    def get_project_ref(self, line_id: str, project_name: str):
        project_list = (
            self.client.collection("users")
            .document(line_id)
            .collection("projects")
            .where(filter=FieldFilter("name", "==", project_name))
            .stream()
        )

        project_list = list(project_list)
        if len(project_list) == 0:
            return None

        return project_list[0].reference

    # DIALOGUE
    def generate_dialogue_cache(
        self, line_id: str, user_ask: str, bot_response: str, project_name: str
    ):
        project_ref = self.get_project_ref(line_id, project_name)
        if project_ref is None:
            return

        return {
            "user_ask": user_ask,
            "bot_response": bot_response,
            "project": project_ref,
            "create_at": firestore.SERVER_TIMESTAMP,
        }

    def store_dialogues(self, line_id: str, dialogue_cache_list: list):
        dialogue_ref = (
            self.client.collection("users")
            .document(line_id)
            .collection("dialogues")
            .document()
        )
        for dialogue_cache in dialogue_cache_list:
            dialogue_ref.set(dialogue_cache)

        return

    def get_project_dialogues(self, line_id: str, project_name: str):
        project_ref = self.get_project_ref(line_id, project_name)
        if project_ref is None:
            return

        dialogues = (
            self.client.collection("users")
            .document(line_id)
            .collection("dialogues")
            .where(filter=FieldFilter("project", "==", project_ref))
            .order_by("create_at", direction="DESCENDING")
            .stream()
        )
        dialogues = list(dialogues)
        if len(dialogues) == 0:
            return None

        dialogues = [dialogue.to_dict() for dialogue in dialogues]

        return dialogues
