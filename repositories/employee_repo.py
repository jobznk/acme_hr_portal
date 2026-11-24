from psycopg_pool import ConnectionPool
from models import Employee


class EmployeeRepository:
    def __init__(self, db_url: str):
        clean_url = db_url.replace("postgresql+psycopg://", "postgresql://")
        self.pool = ConnectionPool(clean_url, min_size=1, max_size=10)
        self._init_db()

    def _get_conn(self):
        return self.pool.connection()

    def _init_db(self):
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS employees (
                        emp_id TEXT PRIMARY KEY,
                        password TEXT NOT NULL,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        location TEXT NOT NULL,
                        pto_balance INTEGER NOT NULL,
                        sick_leave_balance INTEGER NOT NULL,
                        manager TEXT NOT NULL
                    )
                """)
            conn.commit()

    def count_employees(self) -> int:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM employees")
                row = cur.fetchone()
                return row[0] if row else 0

    def _row_to_employee(self, row) -> Employee:
        emp_id, _password, name, role, location, pto_balance, sick_leave_balance, manager = row
        return Employee(
            emp_id=emp_id,
            name=name,
            role=role,
            location=location,
            pto_balance=pto_balance,
            sick_leave_balance=sick_leave_balance,
            manager=manager,
        )

    def get_employee_by_id(self, emp_id: str) -> Employee | None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT emp_id, password, name, role, location, pto_balance, sick_leave_balance, manager
                    FROM employees WHERE emp_id = %s
                    """,
                    (emp_id.upper(),),
                )
                row = cur.fetchone()
                return self._row_to_employee(row) if row else None

    def find_by_credentials(self, emp_id: str, hashed_password: str) -> Employee | None:
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT emp_id, password, name, role, location, pto_balance, sick_leave_balance, manager
                    FROM employees WHERE emp_id = %s AND password = %s
                    """,
                    (emp_id.upper(), hashed_password),
                )
                row = cur.fetchone()
                return self._row_to_employee(row) if row else None

    def create_employee(
        self,
        emp_id: str,
        password: str,
        name: str,
        role: str,
        location: str,
        pto_balance: int = 20,
        sick_leave_balance: int = 10,
        manager: str = "HR Operations",
    ) -> Employee:
        clean_id = emp_id.upper()
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO employees VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        clean_id,
                        password,
                        name,
                        role,
                        location,
                        pto_balance,
                        sick_leave_balance,
                        manager,
                    ),
                )
            conn.commit()
        return Employee(
            emp_id=clean_id,
            name=name,
            role=role,
            location=location,
            pto_balance=pto_balance,
            sick_leave_balance=sick_leave_balance,
            manager=manager,
        )


    def apply_leave(self, emp_id: str, leave_type: str, days: int) -> str:
        emp = self.get_employee_by_id(emp_id)
        if not emp:
            return f"Employee {emp_id} not found."

        col = "pto_balance" if leave_type.lower() == "pto" else "sick_leave_balance"
        current = emp.pto_balance if col == "pto_balance" else emp.sick_leave_balance

        if days <= 0:
            return "Leave days must be at least 1."
        if current < days:
            return f"Insufficient {leave_type} balance. Available: {current} days, Requested: {days} days."

        new_balance = current - days
        with self._get_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    f"UPDATE employees SET {col} = %s WHERE emp_id = %s",
                    (new_balance, emp.emp_id),
                )
            conn.commit()
        return f"Approved! {days} day(s) of {leave_type} deducted. Remaining {leave_type} balance: {new_balance} days."
