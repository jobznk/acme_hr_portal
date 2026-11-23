import asyncio
import os
import sys
from langchain.agents import create_agent
from langchain_mcp_adapters.client import MultiServerMCPClient

from config import COMPANY_NAME
from models import Employee

# Build the exact path to hr_mcp_server.py in the project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_SERVER_PATH = os.path.join(PROJECT_ROOT, "hr_mcp_server.py")


class HRChatService:
    def __init__(self, policy_repo, employee_repo, llm):
        self.policy_repo = policy_repo
        self.employee_repo = employee_repo
        self.llm = llm

    def upload_policy_document(self, filename: str, file_bytes: bytes) -> int:
        """Index uploaded policy documents (including OCR) into ChromaDB."""
        return self.policy_repo.index_uploaded_file(filename, file_bytes)

    async def _ask_mcp_agent(self, prompt_text: str, user: Employee) -> str:
        """Connect to hr_mcp_server.py, discover tools dynamically, and run the Groq agent."""
        client = MultiServerMCPClient(
            {
                "thoughtminds_hr": {
                    "command": sys.executable,
                    "args": [MCP_SERVER_PATH],
                    "transport": "stdio",
                }
            }
        )

        # Dynamically fetch all tools exposed by hr_mcp_server.py
        mcp_tools = await client.get_tools()

        agent = create_agent(
            model=self.llm,
            tools=mcp_tools,
            system_prompt=(
                f"You are {COMPANY_NAME}'s helpful HR Assistant. "
                "Always reply in clear, friendly, plain English sentences. "
                "NEVER output raw JSON, tool names, or function parameters in your response. "
                "When calling tools that require emp_id, always use the logged-in employee's emp_id provided in the user message. "
                "When a user says 'one leave' or 'a leave' (even for 'next week' or 'next month'), always pass days=1 unless they explicitly state a higher number of days. "
                "Never invent or promise sending emails."
            ),
        )

        user_msg = f"[Logged-in Employee: {user.name}, emp_id: {user.emp_id}] {prompt_text}"
        result = await agent.ainvoke({"messages": [("user", user_msg)]})
        return result["messages"][-1].content

    def ask_agent(self, prompt_text: str, user: Employee) -> str:
        """Run the async MCP agent inside Streamlit."""
        return asyncio.run(self._ask_mcp_agent(prompt_text, user))
