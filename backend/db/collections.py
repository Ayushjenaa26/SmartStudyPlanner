from db.mongo import get_db


def users_collection():
    return get_db()["users"]


def study_plans_collection():
    return get_db()["study_plans"]


def tasks_collection():
    return get_db()["tasks"]


def progress_collection():
    return get_db()["progress"]


def integrations_collection():
    return get_db()["integrations"]
