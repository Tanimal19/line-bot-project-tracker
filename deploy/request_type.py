from enum import Enum


class RequestType(Enum):
    ADD_PROJECT = 0
    REMOVE_PROJECT = 1
    GET_PROJECTS = 2
    GET_IDEA = 3
    SET_PROJECT = 4
    CANCEL = 5


def parse_request(message: str):
    """
    return (RequestType, param)
    """

    if message.startswith("[ADD_PROJECT]"):
        return (RequestType.ADD_PROJECT, None)

    elif message.startswith("[REMOVE_PROJECT]"):
        project_name = message.split("]")[1]
        return (RequestType.REMOVE_PROJECT, project_name)

    elif message.startswith("[GET_PROJECTS]"):
        return (RequestType.GET_PROJECTS, None)

    elif message.startswith("[GET_IDEA]"):
        return (RequestType.GET_IDEA, None)

    elif message.startswith("[SET_PROJECT]"):
        project_name = message.split("]")[1]
        return (RequestType.SET_PROJECT, project_name)

    elif message.startswith("cancel"):
        return (RequestType.CANCEL, None)

    else:
        return (None, message)
