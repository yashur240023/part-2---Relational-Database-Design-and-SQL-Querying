from abc import ABC, abstractmethod
from typing import List, Optional

# ============================================================================
# Task 2.3b — Interface Definition (Dependency Inversion Principle)
# ============================================================================

class EnrollmentRepository(ABC):
    """
    Abstract interface for enrollment data operations.
    High-level modules do not depend on concrete database drivers;
    they depend strictly on this abstraction.
    """
    @abstractmethod
    def save(self, enrollment: 'Enrollment') -> bool:
        pass

    @abstractmethod
    def find_by_student_id(self, student_id: int) -> List['Enrollment']:
        pass


# ============================================================================
# Task 2.3a — Structural Domain Classes (SOLID Compliance)
# ============================================================================

class Student:
    """
    Represents a student entity.
    
    DESIGN DECISION (Single Responsibility Principle - SRP):
    This class is strictly responsible for representing and modifying student state.
    It deliberately does NOT contain notification logic (e.g., send_email()), 
    as changes to notification infrastructure should not force changes to the Student model.
    """
    def __init__(self, student_id: int, student_name: str, department: str):
        self.student_id: int = student_id
        self.student_name: str = student_name
        self.department: str = department

    def update_profile(self, new_name: str, new_dept: str) -> None:
        self.student_name = new_name
        self.department = new_dept


class Enrollment:
    """
    Represents a standard base core course enrollment.
    
    DESIGN DECISION (Open/Closed Principle - OCP):
    This class captures core enrollment attributes and exposes a calculation method 
    (calculate_fees) that can be extended via polymorphism by subclasses 
    (e.g., WaitlistedEnrollment, InternationalEnrollment) without modifying this file.
    """
    def __init__(self, student_id: int, course_code: str, base_fee: float):
        self.student_id: int = student_id
        self.course_code: str = course_code
        self.base_fee: float = base_fee
        self.status: str = "Active"

    def calculate_fees(self) -> float:
        return self.base_fee


class WaitlistedEnrollment(Enrollment):
    """
    Extension of Enrollment demonstrating OCP.
    Modifies behavior without changing code in the parent Enrollment class.
    """
    def __init__(self, student_id: int, course_code: str, base_fee: float, position: int):
        super().__init__(student_id, course_code, base_fee)
        self.status = "Waitlisted"
        self.waitlist_position: int = position

    # Overriding fee calculation behavior for waitlisted tracks dynamically
    def calculate_fees(self) -> float:
        return super().calculate_fees() * 0.10  # Only hold-fee applies
