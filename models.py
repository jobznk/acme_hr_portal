from dataclasses import dataclass

@dataclass
class Employee:
    emp_id: str
    name: str
    role: str
    location: str
    pto_balance: int
    sick_leave_balance: int
    manager: str
