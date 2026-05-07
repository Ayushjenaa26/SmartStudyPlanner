from backend.db.mongo import get_db


def users_collection():
    """Users collection - Auth0 user references and app preferences"""
    return get_db()["users"]


def study_plans_collection():
    """Study plans collection - AI-generated study schedules"""
    return get_db()["study_plans"]


def study_sessions_collection():
    """Study sessions collection - Actual study time tracking and session logs"""
    return get_db()["study_sessions"]


def calendar_sync_collection():
    """Calendar sync collection - Google Calendar integration metadata"""
    return get_db()["calendar_sync"]


def tasks_collection():
    """Tasks collection - User's study tasks and assignments"""
    return get_db()["tasks"]


def progress_collection():
    """Progress collection - User progress tracking and analytics (deprecated - use study_sessions)"""
    return get_db()["progress"]


def integrations_collection():
    """Integrations collection - Third-party service integration metadata"""
    return get_db()["integrations"]
