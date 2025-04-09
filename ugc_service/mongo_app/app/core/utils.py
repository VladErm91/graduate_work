from contextvars import ContextVar

ctx_request_id: ContextVar[str] = ContextVar("request_id")


def convert_objectid(data):
    if isinstance(data, list):
        for item in data:
            item["_id"] = str(item["_id"])
    else:
        data["_id"] = str(data["_id"])
    return data
