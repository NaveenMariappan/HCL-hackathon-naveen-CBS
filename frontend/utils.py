import streamlit as st
from typing import Literal

ALLOWED_DOC_TYPES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}

def init_state():
    defaults = {
        "token": None,
        "role": None,        # "customer" or "admin"
        "email": None,
        "full_name": None,
        "active_tab": "Login",   # navbar selection
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

def navbar(options: list[str]) -> str:
    cols = st.columns(len(options))
    for i, name in enumerate(options):
        if cols[i].button(name, use_container_width=True):
            st.session_state["active_tab"] = name
    st.write("---")
    return st.session_state["active_tab"]

def require_auth(role: Literal["customer", "admin"] | None = None) -> bool:
    if not st.session_state["token"]:
        st.warning("Please login first.")
        return False
    if role and st.session_state.get("role") != role:
        st.error(f"Only {role} can access this page.")
        return False
    return True

def file_is_allowed(name: str) -> tuple[bool, str]:
    name = name.lower()
    for ext, mime in ALLOWED_DOC_TYPES.items():
        if name.endswith(ext):
            return True, mime
    return False, ""

def logout():
    st.session_state["token"] = None
    st.session_state["role"] = None
    st.session_state["email"] = None
    st.session_state["full_name"] = None
    st.session_state["active_tab"] = "Login"
