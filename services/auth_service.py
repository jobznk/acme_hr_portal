import hashlib
from typing import Optional, Tuple
from models import Employee
from repositories.employee_repo import EmployeeRepository


class AuthService:
    def __init__(self, employee_repo: EmployeeRepository):
        self.employee_repo = employee_repo
        self._seed_default_users()

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _seed_default_users(self) -> None:
        if self.employee_repo.count_employees() == 0:
            self.employee_repo.create_employee(
                "EMP101", self.hash_password("pass123"), "Arun Kumar",
                "Senior Software Engineer", "Kochi", 14, 8, "Priya Nair"
            )
            self.employee_repo.create_employee(
                "EMP102", self.hash_password("secure456"), "Meera Menon",
                "Product Manager", "Bengaluru", 5, 10, "Rahul Verma"
            )

    def login(self, emp_id: str, password: str) -> Optional[Employee]:
        if not emp_id or not password:
            return None
        hashed = self.hash_password(password)
        return self.employee_repo.find_by_credentials(emp_id, hashed)

    def register(
        self, emp_id: str, name: str, role: str, location: str, password: str
    ) -> Tuple[bool, str]:
        if not all([emp_id, name, role, location, password]):
            return False, "Please fill in all fields."

        hashed = self.hash_password(password)
        created = self.employee_repo.create_employee(emp_id, hashed, name, role, location)

        if created:
            return True, "Account created! Please switch to the Login tab."
        return False, f"Employee ID '{emp_id.upper()}' already exists."
