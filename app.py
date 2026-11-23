import os
import streamlit as st
#from langchain_ollama import OllamaEmbeddings, ChatOllama

from langchain_groq import ChatGroq
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

#from langchain_ollama import ChatOllama

from config import (
    COMPANY_NAME,
    POLICY_FILE,
    CHROMA_DB_FOLDER,
    SQL_DB_FILE,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    OLLAMA_BASE_URL,
    GROQ_API_KEY,
    GROQ_MODEL,
)


from config import (
    COMPANY_NAME,
    POLICY_FILE,
    CHROMA_DB_FOLDER,
    SQL_DB_FILE,
    EMBEDDING_MODEL,
    CHAT_MODEL,
    OLLAMA_BASE_URL,
)
from models import Employee
from repositories.employee_repo import EmployeeRepository
from repositories.policy_repo import PolicyRepository
from services.auth_service import AuthService
from services.rag_service import HRChatService

st.set_page_config(page_title=f"{COMPANY_NAME} HR Assistant", page_icon="🏢", layout="centered")


@st.cache_resource
def get_auth_service() -> AuthService:
    return AuthService(employee_repo=EmployeeRepository(db_path=SQL_DB_FILE))



@st.cache_resource(show_spinner=False)
def get_chat_service() -> HRChatService:
    embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
    llm = ChatGroq(model=GROQ_MODEL, api_key=GROQ_API_KEY, temperature=0)

    employee_repo = EmployeeRepository(db_path=SQL_DB_FILE)
    policy_repo = PolicyRepository(
        persist_dir=CHROMA_DB_FOLDER,
        embedding_function=embeddings,
        initial_policy_file=POLICY_FILE,
    )
    return HRChatService(
        policy_repo=policy_repo,
        employee_repo=employee_repo,
        llm=llm,
    )




def render_login_page(auth_service: AuthService) -> None:
    st.title(f"🏢 {COMPANY_NAME} Employee Portal")
    st.caption("Sign in to access your personalized HR & Operations AI Assistant.")
    tab_login, tab_register = st.tabs(["🔐 Login", "📝 Register New Employee"])

    with tab_login:
        with st.form("login_form"):
            emp_id = st.text_input("Employee ID", placeholder="e.g., EMP101")
            password = st.text_input("Password", type="password", placeholder="e.g., pass123")
            if st.form_submit_button("Login", use_container_width=True):
                if employee := auth_service.login(emp_id, password):
                    st.session_state.update({"user": employee, "messages": []})
                    st.rerun()
                else:
                    st.error("Invalid Employee ID or Password.")
        st.info("**Test Accounts:** `EMP101` / `pass123`  |  `EMP102` / `secure456`")

    with tab_register:
        with st.form("register_form"):
            new_id = st.text_input("Choose Employee ID", placeholder="e.g., EMP103")
            new_name = st.text_input("Full Name")
            new_role = st.text_input("Job Role")
            new_loc = st.selectbox("Office Location", ["Kochi", "Bengaluru", "Remote"])
            new_pass = st.text_input("Create Password", type="password")

            if st.form_submit_button("Create Account", use_container_width=True):
                success, message = auth_service.register(
                    new_id, new_name, new_role, new_loc, new_pass
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)


def render_chat_portal(auth_service: AuthService, chat_service: HRChatService) -> None:
    # Always fetch the latest employee data so sidebar leave balances stay up to date
    session_user: Employee = st.session_state["user"]
    user = auth_service.employee_repo.get_employee_by_id(session_user.emp_id) or session_user
    st.session_state["user"] = user

    with st.sidebar:
        st.header(f"👤 {user.name}")
        st.write(
            f"**ID:** {user.emp_id}\n"
            f"**Role:** {user.role}\n"
            f"**Location:** {user.location}\n"
            f"**Manager:** {user.manager}"
        )
        st.divider()

        st.subheader("Leave Balances")
        col1, col2 = st.columns(2)
        col1.metric("PTO", f"{user.pto_balance}d")
        col2.metric("Sick", f"{user.sick_leave_balance}d")
        st.divider()

        st.subheader("📂 Upload Policy Docs (OCR)")
        uploaded_file = st.file_uploader(
            "Upload PDF, TXT, or Scanned Image",
            type=["pdf", "txt", "png", "jpg", "jpeg"],
        )
        if uploaded_file and st.button("Scan & Index Document", use_container_width=True):
            with st.spinner(f"Scanning {uploaded_file.name}..."):
                chunks = chat_service.upload_policy_document(
                    uploaded_file.name, uploaded_file.getvalue()
                )
            if chunks > 0:
                st.success(f"Added {chunks} chunks from '{uploaded_file.name}'!")
            else:
                st.warning("Could not read any text from that file.")
        st.divider()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.update({"user": None, "messages": []})
            st.rerun()

    st.title(f"💬 {COMPANY_NAME} HR Assistant")
    st.caption(f"Logged in as **{user.name}** ({user.location} Office)")

    # Display chat history
    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Handle new user message
    if prompt_text := st.chat_input("Ask about company policies, leave balances, or apply for leave..."):
        st.session_state["messages"].append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = chat_service.ask_agent(prompt_text, user)
            st.markdown(response)

        st.session_state["messages"].append({"role": "assistant", "content": response})
        st.rerun()



def main() -> None:
    if not os.path.exists(POLICY_FILE):
        st.error(f"Missing `{POLICY_FILE}`. Please create it inside the project folder first.")
        st.stop()

    st.session_state.setdefault("user", None)
    st.session_state.setdefault("messages", [])

    auth_service = get_auth_service()
    if st.session_state["user"] is None:
        render_login_page(auth_service)
    else:
        render_chat_portal(auth_service, get_chat_service())


if __name__ == "__main__":
    main()
