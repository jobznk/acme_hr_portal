import streamlit as st
from config import COMPANY_NAME
from services.api_client import HRBackendClient

st.set_page_config(page_title=f"{COMPANY_NAME} HR Assistant", page_icon="🏢", layout="centered")
api_client = HRBackendClient()


def render_login_page() -> None:
    st.title(f"🏢 {COMPANY_NAME} Employee Portal")
    st.caption("Sign in to access your personalized HR & Operations AI Assistant.")
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register New Employee"])

    with tab_login:
        with st.form("login_form"):
            emp_id = st.text_input("Employee ID", placeholder="e.g., EMP101")
            password = st.text_input("Password", type="password", placeholder="e.g., pass123")
            if st.form_submit_button("Login", use_container_width=True):
                employee, error_msg = api_client.login(emp_id, password)
                if employee:
                    st.session_state.update({"user": employee, "messages": []})
                    st.rerun()
                else:
                    st.error(error_msg)
        st.info("**Test Accounts:** `EMP101` / `pass123`  |  `EMP102` / `secure456`")

    with tab_register:
        with st.form("register_form"):
            new_id = st.text_input("Choose Employee ID", placeholder="e.g., EMP103")
            new_name = st.text_input("Full Name")
            new_role = st.text_input("Job Role")
            new_loc = st.selectbox("Office Location", ["Kochi", "Bengaluru", "Remote"])
            new_pass = st.text_input("Create Password", type="password")

            if st.form_submit_button("Create Account", use_container_width=True):
                success, message = api_client.register(new_id, new_name, new_role, new_loc, new_pass)
                if success:
                    st.success(message)
                else:
                    st.error(message)


def render_chat_portal() -> None:
    session_user = st.session_state["user"]
    if latest_user := api_client.get_employee(session_user["emp_id"]):
        session_user = latest_user
        st.session_state["user"] = session_user

    with st.sidebar:
        st.header(f"👤 {session_user['name']}")
        st.write(
            f"**ID:** {session_user['emp_id']}\n"
            f"**Role:** {session_user['role']}\n"
            f"**Location:** {session_user['location']}\n"
            f"**Manager:** {session_user['manager']}"
        )
        st.divider()

        st.subheader("Leave Balances")
        col1, col2 = st.columns(2)
        col1.metric("PTO", f"{session_user['pto_balance']}d")
        col2.metric("Sick", f"{session_user['sick_leave_balance']}d")
        st.divider()

        st.subheader("📂 Upload Policy Docs (OCR)")
        uploaded_file = st.file_uploader(
            "Upload PDF, TXT, or Scanned Image",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
        )
        if uploaded_file and st.button("Scan & Index Document", use_container_width=True):
            with st.spinner(f"Scanning {uploaded_file.name} via FastAPI..."):
                chunks, err = api_client.upload_document(uploaded_file.name, uploaded_file.getvalue())
            if chunks > 0:
                st.success(f"Added {chunks} chunks from '{uploaded_file.name}'!")
            else:
                st.warning(err)
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.update({"user": None, "messages": []})
            st.rerun()

    st.title(f"💬 {COMPANY_NAME} HR Assistant")
    st.caption(f"Logged in as **{session_user['name']}** ({session_user['location']} Office)")

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt_text := st.chat_input("Ask about company policies, leave balances, or apply for leave..."):
        st.session_state["messages"].append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = api_client.ask_agent(session_user["emp_id"], prompt_text)
            st.markdown(response)

        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.rerun()


def main() -> None:
    st.session_state.setdefault("user", None)
    st.session_state.setdefault("messages", [])

    if not api_client.is_online():
        st.warning("🔌 **HR Backend Service (`FastAPI`) is currently offline.** Some actions may not work until it is started.")
        if st.button("🔄 Retry Connection"):
            st.rerun()

    if st.session_state["user"] is None:
        render_login_page()
    else:
        render_chat_portal()


if __name__ == "__main__":
    main()
