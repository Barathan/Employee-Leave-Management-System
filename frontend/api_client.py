"""
Thin wrapper around `requests` for talking to the FastAPI backend.
Keeping all HTTP calls in one place means the Streamlit pages never build
URLs or headers themselves -- they just call these functions.
"""
import requests
import streamlit as st

try:
    BASE_URL = st.secrets["API_BASE_URL"]
except Exception:
    BASE_URL = "http://localhost:8000"

TIMEOUT = 10


def _headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(username: str, password: str):
    return requests.post(
        f"{BASE_URL}/auth/login",
        data={"username": username, "password": password},
        timeout=TIMEOUT,
    )


def get_me():
    return requests.get(f"{BASE_URL}/users/me", headers=_headers(), timeout=TIMEOUT)


def list_employees(role: str = None):
    params = {"role": role} if role else {}
    return requests.get(f"{BASE_URL}/users", headers=_headers(), params=params, timeout=TIMEOUT)


def get_user(user_id: int):
    return requests.get(f"{BASE_URL}/users/{user_id}", headers=_headers(), timeout=TIMEOUT)


def register_employee(payload: dict):
    return requests.post(f"{BASE_URL}/users/register", headers=_headers(), json=payload, timeout=TIMEOUT)


def apply_leave(payload: dict):
    return requests.post(f"{BASE_URL}/leaves/apply", headers=_headers(), json=payload, timeout=TIMEOUT)


def my_leaves():
    return requests.get(f"{BASE_URL}/leaves/my", headers=_headers(), timeout=TIMEOUT)


def pending_leaves():
    return requests.get(f"{BASE_URL}/leaves/pending", headers=_headers(), timeout=TIMEOUT)


def all_leaves(status: str = None):
    params = {"status": status} if status else {}
    return requests.get(f"{BASE_URL}/leaves/all", headers=_headers(), params=params, timeout=TIMEOUT)


def review_leave(leave_id: int, payload: dict):
    return requests.put(f"{BASE_URL}/leaves/{leave_id}/review", headers=_headers(), json=payload, timeout=TIMEOUT)


def statistics():
    return requests.get(f"{BASE_URL}/leaves/statistics", headers=_headers(), timeout=TIMEOUT)
