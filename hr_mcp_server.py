from mcp.server.fastmcp import FastMCP
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

from config import POLICY_FILE, CHROMA_DB_FOLDER, SQL_DB_FILE, EMBEDDING_MODEL, TOP_K_RESULTS
from repositories.employee_repo import EmployeeRepository
from repositories.policy_repo import PolicyRepository

# 1. Initialize the MCP Server with a friendly name
mcp = FastMCP("ThoughtMinds-HR-Server")

# 2. Connect to your existing SQLite and ChromaDB repositories
employee_repo = EmployeeRepository(db_path=SQL_DB_FILE)
embeddings = FastEmbedEmbeddings(model_name=EMBEDDING_MODEL)
policy_repo = PolicyRepository(
    persist_dir=CHROMA_DB_FOLDER,
    embedding_function=embeddings,
    initial_policy_file=POLICY_FILE,
)


# 3. Expose your HR functions as MCP Tools using @mcp.tool()
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


if __name__ == "__main__":
    # Run the MCP server over standard input/output (stdio)
    mcp.run(transport="stdio")
