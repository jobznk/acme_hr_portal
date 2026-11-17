from typing import Iterator
from models import Employee
from repositories.policy_repo import PolicyRepository
from config import TOP_K_RESULTS


class HRChatService:
    def __init__(self, policy_repo: PolicyRepository, llm):
        self.policy_repo = policy_repo
        self.llm = llm

    def _build_prompt(self, question: str, policy_context: str, employee: Employee) -> str:
        personal_context = (
            f"Employee ID: {employee.emp_id}\n"
            f"Name: {employee.name}\n"
            f"Role: {employee.role}\n"
            f"Office Location: {employee.location}\n"
            f"Remaining PTO Balance: {employee.pto_balance} days\n"
            f"Remaining Sick Leave Balance: {employee.sick_leave_balance} days\n"
            f"Reporting Manager: {employee.manager}"
        )

        return f"""You are an internal HR assistant. Answer the employee's question accurately using ONLY the General Company Policy and the Logged-In Employee Profile provided below.
Address the employee by their first name when appropriate. Do not invent facts.

General Company Policy:
{policy_context}

Logged-In Employee Profile:
{personal_context}

Employee Question: {question}
Answer:"""

    def stream_response(self, question: str, employee: Employee) -> Iterator[str]:
        policy_context = self.policy_repo.search_relevant_policies(question, k=TOP_K_RESULTS)
        full_prompt = self._build_prompt(question, policy_context, employee)

        for chunk in self.llm.stream(full_prompt):
            yield chunk.content

    def upload_policy_document(self, file_name: str, file_bytes: bytes) -> int:
        return self.policy_repo.index_uploaded_file(file_name, file_bytes)
