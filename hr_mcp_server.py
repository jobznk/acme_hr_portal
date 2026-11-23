from mcp.server.fastmcp import FastMCP
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import POLICY_FILE, CHROMA_DB_FOLDER, SQL_DB_FILE, EMBEDDING_MODEL, TOP_K_RESULTS
from repositories.employee_repo import EmployeeRepository
from repositories.policy_repo import PolicyRepository

mcp = FastMCP("ThoughtMinds-HR-Server")

employee_repo = EmployeeRepository(db_path=SQL_DB_FILE)
embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
policy_repo = PolicyRepository(
    persist_dir=CHROMA_DB_FOLDER,
    embedding_function=embeddings,
    initial_policy_file=POLICY_FILE,
)


# ==========================================
# 1. MCP TOOLS (Actions the AI can execute)
# ==========================================
@mcp.tool()
def search_hr_policies(query: str) -> str:
    """Search the ThoughtMinds HR policy handbook for rules on leave, expenses, or benefits."""
    return policy_repo.search_relevant_policies(query, k=TOP_K_RESULTS)


@mcp.tool()
def check_leave_balance(emp_id: str) -> str:
    """Check an employee's live PTO and Sick leave balances using their Employee ID (e.g., EMP101)."""
    emp = employee_repo.get_employee_by_id(emp_id)
    if not emp:
        return f"Employee {emp_id} not found."
    return f"{emp.name} ({emp_id}) -> PTO: {emp.pto_balance} days | Sick Leave: {emp.sick_leave_balance} days"


@mcp.tool()
def submit_leave_request(emp_id: str, leave_type: str, days: int, reason: str) -> str:
    """Apply for PTO or Sick leave for an employee. leave_type must be 'PTO' or 'Sick'."""
    message = employee_repo.apply_leave(emp_id, leave_type, days)
    return f"{message} (Reason: {reason})"


# ==========================================
# 2. MCP RESOURCES (Readable Data via URI)
# ==========================================
@mcp.resource("policy://handbook")
def get_full_policy_handbook() -> str:
    """Read the complete ThoughtMinds HR Policy Handbook directly."""
    with open(POLICY_FILE, "r", encoding="utf-8") as file:
        return file.read()


# ==========================================
# 3. MCP PROMPTS (Reusable Slash Templates)
# ==========================================
@mcp.prompt()
def apply_leave_workflow(emp_id: str, leave_type: str, days: int, reason: str) -> str:
    """Standard workflow to check an employee's balance first and then submit their leave."""
    return (
        f"First check the current leave balance for employee {emp_id}. "
        f"If they have enough balance, submit a {leave_type} leave request for {days} day(s) "
        f"with the reason: '{reason}', and confirm the updated remaining balance."
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
