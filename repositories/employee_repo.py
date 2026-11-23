import sqlite3
from typing import Optional
from models import Employee


class EmployeeRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_table()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_table(self) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    emp_id TEXT PRIMARY KEY,
                    password_hash TEXT NOT NULL,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    location TEXT NOT NULL,
                    pto_balance INTEGER NOT NULL,
                    sick_leave_balance INTEGER NOT NULL,
                    manager TEXT NOT NULL
                )
            """)
            conn.commit()

    def _row_to_employee(self, row: sqlite3.Row) -> Employee:
        """Helper to convert a database row into an Employee object."""
        return Employee(
            emp_id=row["emp_id"],
            name=row["name"],
            role=row["role"],
            location=row["location"],
            pto_balance=row["pto_balance"],
            sick_leave_balance=row["sick_leave_balance"],
            manager=row["manager"],
        )

    def count_employees(self) -> int:
        with self._get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) as count FROM employees").fetchone()
            return row["count"]

    def create_employee(
        self,
        emp_id: str,
        password_hash: str,
        name: str,
        role: str,
        location: str,
        pto_balance: int = 24,
        sick_leave_balance: int = 10,
        manager: str = "HR Admin",
    ) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO employees (
                        emp_id, password_hash, name, role, location,
                        pto_balance, sick_leave_balance, manager
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        emp_id.strip().upper(),
                        password_hash,
                        name.strip(),
                        role.strip(),
                        location.strip(),
                        pto_balance,
                        sick_leave_balance,
                        manager,
                    ),
                )
                conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def find_by_credentials(self, emp_id: str, password_hash: str) -> Optional[Employee]:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE emp_id = ? AND password_hash = ?",
                (emp_id.strip().upper(), password_hash),
            ).fetchone()

        return self._row_to_employee(row) if row else None

    # --- NEW METHODS FOR YOUR AI AGENT ---

    def get_employee_by_id(self, emp_id: str) -> Optional[Employee]:
        """Fetch the latest employee details and leave balances."""
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM employees WHERE emp_id = ?",
                (emp_id.strip().upper(),),
            ).fetchone()

        return self._row_to_employee(row) if row else None

    def apply_leave(self, emp_id: str, leave_type: str, days: int) -> str:
        """Deduct PTO or Sick leave days and return a clear status message for the AI."""
        emp_id = emp_id.strip().upper()
        clean_type = leave_type.strip().lower()

        if clean_type == "pto":
            column = "pto_balance"
            label = "PTO"
        elif clean_type in ("sick", "sick leave"):
            column = "sick_leave_balance"
            label = "Sick Leave"
        else:
            return "Invalid leave type. Please choose either 'PTO' or 'Sick'."

        with self._get_connection() as conn:
            row = conn.execute(
                f"SELECT {column} FROM employees WHERE emp_id = ?", (emp_id,)
            ).fetchone()

            if not row:
                return "Employee record not found."

            current_balance = row[column]
            if days <= 0:
                return "Number of leave days must be at least 1."
            if days > current_balance:
                return f"Insufficient {label} balance. Available: {current_balance} days."

            new_balance = current_balance - days
            conn.execute(
                f"UPDATE employees SET {column} = ? WHERE emp_id = ?",
                (new_balance, emp_id),
            )
            conn.commit()

        return f"Approved! Deducted {days} day(s) from {label}. Remaining balance: {new_balance} days."
