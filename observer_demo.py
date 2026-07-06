from abc import ABC, abstractmethod
from typing import List

# ============================================================================
# Observer Pattern Abstractions
# ============================================================================

class MarksObserver(ABC):
    """Abstract Observer Interface."""
    @abstractmethod
    def update(self, student_id: int, new_marks: float) -> None:
        pass


class MarksUpdateNotifier:
    """Subject (Observable) tracking system status changes."""
    def __init__(self):
        self._observers: List[MarksObserver] = []

    def register_observer(self, observer: MarksObserver) -> None:
        if observer not in self._observers:
            self._observers.append(observer)

    def remove_observer(self, observer: MarksObserver) -> None:
        if observer in self._observers:
            self._observers.remove(observer)

    def notify_observers(self, student_id: int, new_marks: float) -> None:
        for observer in self._observers:
            observer.update(student_id, new_marks)


# ============================================================================
# Concrete Observer Core Implementations
# ============================================================================

class EmailNotifier(MarksObserver):
    def update(self, student_id: int, new_marks: float) -> None:
        print(f"[Email Service] Dispatching Notification: Student {student_id} marks have been set to: {new_marks}%")


class AuditLogNotifier(MarksObserver):
    def update(self, student_id: int, new_marks: float) -> None:
        print(f"[Audit Log Service] Security Entry Written: Student ID {student_id} modified to {new_marks}. Immutable entry recorded.")


# --- Execution Demonstration Driver ---
if __name__ == "__main__":
    # Instantiate Subject
    notifier = MarksUpdateNotifier()

    # Instantiate Observers
    email_service = EmailNotifier()
    audit_service = AuditLogNotifier()

    # Register Observers
    notifier.register_observer(email_service)
    notifier.register_observer(audit_service)

    print("--- Execution Trigger 1: Faculty updates grades ---")
    # Simulate an update event inside the Admin Panel
    target_student = 99201
    updated_score = 89.50
    notifier.notify_observers(target_student, updated_score)

    print("\n--- Execution Trigger 2: Removing Email Listener, keeping Audit Track ---")
    notifier.remove_observer(email_service)
    notifier.notify_observers(target_student, 94.00)
