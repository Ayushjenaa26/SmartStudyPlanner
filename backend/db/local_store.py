import json
import os
from threading import Lock
from datetime import datetime

_STORE_PATH = os.path.join(os.path.dirname(__file__), 'local_links.json')
_lock = Lock()


def _read_store():
    if not os.path.exists(_STORE_PATH):
        return {}
    try:
        with open(_STORE_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _write_store(data):
    tmp = _STORE_PATH + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, _STORE_PATH)


def get_guest_links(guestSessionId: str):
    with _lock:
        store = _read_store()
        user = store.get(guestSessionId)
        if not user:
            return []
        return user.get('links', [])


def save_guest_link(guestSessionId: str, link: dict):
    with _lock:
        store = _read_store()
        user = store.get(guestSessionId) or {
            'guestSessionId': guestSessionId,
            'auth0UserId': None,
            'is_guest': True,
            'created_at': datetime.utcnow().isoformat(),
            'links': []
        }
        user.setdefault('links', []).append(link)
        user['updated_at'] = datetime.utcnow().isoformat()
        store[guestSessionId] = user
        _write_store(store)


def delete_guest_link(guestSessionId: str, link_id: int):
    with _lock:
        store = _read_store()
        user = store.get(guestSessionId)
        if not user or 'links' not in user:
            return False
        before = len(user['links'])
        user['links'] = [l for l in user['links'] if int(l.get('id')) != int(link_id)]
        after = len(user['links'])
        user['updated_at'] = datetime.utcnow().isoformat()
        store[guestSessionId] = user
        _write_store(store)
        return before != after
