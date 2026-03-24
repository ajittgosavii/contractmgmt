"""Multi-user authentication using streamlit-authenticator."""

import os
import yaml
import bcrypt
import streamlit as st
import streamlit_authenticator as stauth

AUTH_CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "auth.yaml")


def _hash_password(password: str) -> str:
    """Hash a password using bcrypt directly."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _ensure_auth_config():
    """Create default auth config if it doesn't exist."""
    config_dir = os.path.dirname(AUTH_CONFIG_PATH)
    os.makedirs(config_dir, exist_ok=True)

    if not os.path.exists(AUTH_CONFIG_PATH):
        default_config = {
            "credentials": {
                "usernames": {
                    "admin": {
                        "email": "admin@company.com",
                        "name": "Admin User",
                        "password": _hash_password("admin123"),
                        "role": "admin",
                    },
                    "analyst": {
                        "email": "analyst@company.com",
                        "name": "Contract Analyst",
                        "password": _hash_password("analyst123"),
                        "role": "analyst",
                    },
                    "viewer": {
                        "email": "viewer@company.com",
                        "name": "Viewer",
                        "password": _hash_password("viewer123"),
                        "role": "viewer",
                    },
                }
            },
            "cookie": {
                "expiry_days": 30,
                "key": "cobalt_contract_mgmt_secret_key",
                "name": "cobalt_clm_auth",
            },
        }
        with open(AUTH_CONFIG_PATH, "w") as f:
            yaml.dump(default_config, f, default_flow_style=False)


def load_auth_config() -> dict:
    """Load authentication configuration."""
    _ensure_auth_config()
    with open(AUTH_CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def save_auth_config(config: dict):
    """Save authentication configuration."""
    with open(AUTH_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_user_role(username: str) -> str:
    """Get the role for a given username."""
    config = load_auth_config()
    user = config["credentials"]["usernames"].get(username, {})
    return user.get("role", "viewer")


def setup_authentication():
    """
    Set up authentication. Returns (authenticator, config).
    After calling authenticator.login(), check st.session_state for:
      - st.session_state["authentication_status"]
      - st.session_state["name"]
      - st.session_state["username"]
    """
    config = load_auth_config()

    authenticator = stauth.Authenticate(
        config["credentials"],
        config["cookie"]["name"],
        config["cookie"]["key"],
        config["cookie"]["expiry_days"],
        auto_hash=False,  # passwords are already bcrypt-hashed
    )

    return authenticator, config


def check_permission(username: str, required_role: str) -> bool:
    """
    Check if a user has the required role.
    Role hierarchy: admin > analyst > viewer
    """
    role_hierarchy = {"admin": 3, "analyst": 2, "viewer": 1}
    user_role = get_user_role(username)
    return role_hierarchy.get(user_role, 0) >= role_hierarchy.get(required_role, 0)


def render_user_management():
    """Render user management UI for admins."""
    config = load_auth_config()
    users = config["credentials"]["usernames"]

    st.subheader("Current Users")
    for uname, udata in users.items():
        col1, col2, col3, col4 = st.columns([2, 3, 2, 1])
        with col1:
            st.write(f"**{uname}**")
        with col2:
            st.write(udata.get("email", ""))
        with col3:
            st.write(f"Role: {udata.get('role', 'viewer')}")
        with col4:
            if uname != "admin":
                if st.button("Remove", key=f"rm_{uname}"):
                    del config["credentials"]["usernames"][uname]
                    save_auth_config(config)
                    st.success(f"Removed {uname}")
                    st.rerun()

    st.divider()
    st.subheader("Add New User")
    with st.form("add_user_form"):
        new_username = st.text_input("Username")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        new_role = st.selectbox("Role", ["viewer", "analyst", "admin"])
        submitted = st.form_submit_button("Add User")

        if submitted and new_username and new_password:
            if new_username in users:
                st.error("Username already exists!")
            else:
                config["credentials"]["usernames"][new_username] = {
                    "email": new_email,
                    "name": new_name,
                    "password": _hash_password(new_password),
                    "role": new_role,
                }
                save_auth_config(config)
                st.success(f"User '{new_username}' added with role '{new_role}'!")
                st.rerun()
