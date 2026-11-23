from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from config import TOP_K_RESULTS , COMPANY_NAME
from models import Employee


class HRChatService:
    def __init__(self, policy_repo, employee_repo, llm):
        self.policy_repo = policy_repo
        self.employee_repo = employee_repo
        self.llm = llm
        self.agent = self._create_hr_agent()

    def upload_policy_document(self, filename: str, file_bytes: bytes) -> int:
        return self.policy_repo.index_uploaded_file(filename, file_bytes)

    def _create_hr_agent(self):
        """Define all HR tools and build the agent once."""

        @tool
        def search_hr_policies(query: str) -> str:
            """Search the company HR policy handbook for rules on leave, expenses, or benefits."""
            return self.policy_repo.search_relevant_policies(query, k=TOP_K_RESULTS)

        @tool
        def check_leave_balance(config: RunnableConfig) -> str:
            """Check the logged-in employee's live PTO and Sick leave balances."""
            emp_id = config["configurable"]["emp_id"]
            emp = self.employee_repo.get_employee_by_id(emp_id)
            if not emp:
                return "Employee record not found."
            return f"PTO: {emp.pto_balance} days | Sick Leave: {emp.sick_leave_balance} days"

        @tool
        def submit_leave_request(leave_type: str, days: int, reason: str, config: RunnableConfig) -> str:
            """
            Apply for PTO or Sick leave.
            - leave_type must be strictly 'PTO' or 'Sick' (default to 'PTO' if unspecified).
            - days must match the exact number of days requested (e.g. 'one leave' = 1, even if scheduled for 'next week').
            """
            emp_id = config["configurable"]["emp_id"]
            message = self.employee_repo.apply_leave(emp_id, leave_type, days)
            return f"{message} (Reason: {reason})"


        return create_agent(
            model=self.llm,
            tools=[search_hr_policies, check_leave_balance, submit_leave_request],
            system_prompt=(
                f"You are {COMPANY_NAME}'s helpful HR Assistant. "
                "Always reply in clear, friendly, plain English sentences. "
                "NEVER output raw JSON, tool names, or function parameters in your response. "
                "When a user says 'one leave' or 'a leave' (even for 'next week' or 'next month'), always pass days=1 unless they explicitly state a higher number of days. "
                "Never invent or promise sending emails unless a tool actually sends one."
            ),
        )


    def ask_agent(self, prompt_text: str, user: Employee) -> str:
        """Run the pre-built agent for the currently logged-in employee."""
        config = {"configurable": {"emp_id": user.emp_id}}
        user_msg = f"[Employee: {user.name}, ID: {user.emp_id}] {prompt_text}"

        result = self.agent.invoke({"messages": [("user", user_msg)]}, config=config)
        reply = result["messages"][-1].content.strip()

        # Fallback: If Ollama ever outputs raw JSON text instead of invoking the tool properly,
        # re-prompt it once to answer in plain English.
        if reply.startswith("{") and '"name"' in reply:
            retry_msg = (
                f"{user_msg} (Please answer in plain English sentences only, do not output JSON.)"
            )
            result = self.agent.invoke({"messages": [("user", retry_msg)]}, config=config)
            reply = result["messages"][-1].content.strip()

        return reply
