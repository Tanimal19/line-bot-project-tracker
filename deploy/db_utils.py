import os
import firebase_admin
from firebase_admin import firestore, credentials
from google.cloud.firestore import (
    CollectionReference,
    DocumentReference,
    DocumentSnapshot,
)
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import List, Dict


MODE = os.environ.get("MODE", "development")

if MODE == "production":
    firebase_admin.initialize_app()
else:
    cred = credentials.Certificate("../firebase-key.json")
    firebase_admin.initialize_app(cred)


class Database:
    def __init__(self):
        self.client = firestore.client()

    def delete_collection(
        self, collection_ref: CollectionReference, batch_size=50
    ) -> None:
        if batch_size <= 0:
            return

        docs = collection_ref.limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            print(f"deleting doc {doc.id} from {collection_ref.id}")
            doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return self.delete_collection(collection_ref, batch_size)

    # USER
    def is_user_exist(self, user_id: str) -> bool:
        user: DocumentSnapshot = self.client.collection("users").document(user_id).get()
        return user.exists

    def add_user(self, user_id: str) -> None:
        self.client.collection("users").document(user_id).set(
            {
                "create_at": firestore.SERVER_TIMESTAMP,
            },
            merge=True,
        )
        return

    def get_user_list(self) -> List[str]:
        query_stream = self.client.collection("users").stream()
        user_list = [doc.id for doc in query_stream]
        return user_list

    # PROJECT
    def add_project(
        self, user_id: str, project_name: str, project_description: str
    ) -> None:
        if self.is_user_exist(user_id) is False:
            return

        project_ref: DocumentReference = (
            self.client.collection("users")
            .document(user_id)
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

    def get_project_ref(self, user_id: str, project_name: str) -> DocumentReference:
        if self.is_user_exist(user_id) is False:
            return None

        query_stream = (
            self.client.collection("users")
            .document(user_id)
            .collection("projects")
            .where(filter=FieldFilter("name", "==", project_name))
            .stream()
        )

        project_list = list(query_stream)
        if len(project_list) == 0:
            return None

        return project_list[0].reference

    def get_project_dict(self, user_id: str, project_name: str) -> dict:
        project_ref: DocumentReference = self.get_project_ref(user_id, project_name)
        if project_ref is None:
            return None

        return project_ref.get().to_dict()

    def get_project_list(self, user_id: str) -> List[Dict]:
        if self.is_user_exist(user_id) is False:
            return None

        query_stream = (
            self.client.collection("users")
            .document(user_id)
            .collection("projects")
            .order_by("last_used", direction="DESCENDING")
            .stream()
        )

        project_list = list(query_stream)
        if len(project_list) == 0:
            return None

        project_list = [p.to_dict() for p in project_list]

        return project_list

    def remove_project(self, user_id: str, project_name: str) -> None:
        project_ref = self.get_project_ref(user_id, project_name)
        if project_ref is None:
            return

        dialogues_ref = project_ref.collection("dialogues")
        self.delete_collection(dialogues_ref)
        project_ref.delete()

        return

    def update_project(
        self, user_id: str, project_name: str, project_description: str, is_active: bool
    ) -> None:
        project_ref = self.get_project_ref(user_id, project_name)
        if project_ref is None:
            return

        if project_name is not None:
            project_ref.set(
                {"name": project_name},
                merge=True,
            )

        if project_description is not None:
            project_ref.set(
                {"description": project_description},
                merge=True,
            )

        if is_active is not None:
            project_ref.set(
                {"is_active": is_active},
                merge=True,
            )

        project_ref.set(
            {"last_used": firestore.SERVER_TIMESTAMP},
            merge=True,
        )
        return

    # DIALOGUE
    def generate_dialogue_dict(self, user_ask: str, bot_response: str) -> dict:
        return {
            "user_ask": user_ask,
            "bot_response": bot_response,
            "create_at": firestore.SERVER_TIMESTAMP,
        }

    def add_project_dialogues(
        self, user_id: str, project_name: str, dialogue_list: List[Dict]
    ) -> None:
        project_ref = self.get_project_ref(user_id, project_name)
        if project_ref is None:
            return

        batch = self.client.batch()
        dialogue_collection_ref: CollectionReference = project_ref.collection(
            "dialogues"
        )
        for dialogue in dialogue_list:
            batch.set(dialogue_collection_ref.document(), dialogue)
        batch.commit()
        return

    def get_project_dialogue_list(self, user_id: str, project_name: str) -> List[Dict]:
        project_ref = self.get_project_ref(user_id, project_name)
        if project_ref is None:
            return

        query_stream = (
            project_ref.collection("dialogues")
            .order_by("create_at", direction="ASCENDING")
            .limit(10)
            .stream()
        )
        dialogue_list = list(query_stream)
        if len(dialogue_list) == 0:
            return None

        dialogue_list = [d.to_dict() for d in dialogue_list]

        return dialogue_list
