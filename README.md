# part-2---Relational-Database-Design-and-SQL-Querying
# Software Architecture & LLD Structural Manifest

## SOLID Principles Design Application Ledger

### 1. Single Responsibility Principle (SRP)
Applied directly within `lld_classes.py` inside the `Student` model. The data object is decoupled entirely from reporting, transmission, and output streaming concerns. It holds attributes representing state and basic modification logic. This guarantees that if the university switches from an SMTP email service to a platform notification system, the `Student` entity code remains untouched.

### 2. Open/Closed Principle (OCP)
Demonstrated by the polymorphic design of the `Enrollment` class. The base class handles standard registration fee processing rules. When specialized conditions arise (such as `WaitlistedEnrollment`), we extend the system by subclassing `Enrollment` and overriding runtime methods (`calculate_fees()`) instead of introducing complex conditional switch blocks directly inside the source file of the core class.

### 3. Dependency Inversion Principle (DIP)
Achieved by the declaration of the abstraction wrapper contract layer `EnrollmentRepository`. The system's domain orchestrations interact purely with this abstract class instead of coupling tightly to concrete infrastructure modules like `PostgreSQLRepository` or `MySQLRepository`. Concrete database logic is injected externally at runtime.

---

## Observer Design Pattern Architectural Rationale
The integration of `MarksUpdateNotifier` preserves loose coupling between the core administrative business components and ancillary notification operations. 

Without this pattern, the Admin Panel code would need to instantiate or import `EmailNotifier` and `AuditLogNotifier` directly, making it brittle and difficult to change. By using the Observer pattern, the Admin Panel broadcasts events to registered subscribers via an interface contract. New auxiliary services (such as a Mobile Push Notification Service or Student Analytics Engine) can be introduced at any time without modifying the core Admin Panel source code.

---

## Task 2.4 — Redundancy and Fault Tolerance Strategy

### a. Database Tier Redundancy Mechanics
To guarantee zero data loss and prevent single-point-of-failure vulnerabilities, a **Primary-Replica Database Cluster Architecture** is applied. Data is continuously copied from the primary node to one or more read replicas.

* **During Standard Runtime:** All transactional execution paths containing modification commands (`INSERT`, `UPDATE`, `DELETE`) are routed exclusively to the Primary Node. Read operations (`SELECT`) are balanced across the Read Replicas to optimize processing performance.
* **During Primary Node Failure:** The system's health monitoring software senses the primary node's failure, triggers automated failover logic, and coordinates a leader election to promote the most up-to-date Read Replica to become the new primary master node. Write requests are temporarily queued or rejected during the brief failover window, then resume normally on the newly promoted master.

---

### b. Fault Isolation & Microservices Execution Flow
The specific system property that enables independent application preservation is **Fault Isolation**. 

In a Monolithic deployment, all components execute within a shared memory space and runtime process boundary. If the email transmission module encounters a thread crash or memory leak, the single process aborts, taking down the Student Portal along with it. In a microservices architecture, the components run inside separate isolated OS containers, ensuring that an unhandled crash in the email service has no blast radius outside its container.

#### Programming Call-Site Resiliency Pattern
To prevent a slow or broken email dependency from blocking threads on the Student Portal, developers must implement the **Circuit Breaker Pattern** alongside an asynchronous fallback mechanism at the call site. Instead of executing direct blocking synchronous calls inside the primary transaction execution thread, the code uses a non-blocking pathway (such as an asynchronous task queue or an explicit try-catch wrapper paired with an immediate timeout configuration):

```python
# Programming pattern concept at the call site
try:
    # Wrap remote call with a strict low-threshold timeout value
    email_service_proxy.trigger_notification(student_id, payload, timeout=1.5)
except RemoteServiceTimeoutException:
    # Activate circuit breaker mechanism, log the failure, and gracefully proceed
    audit_logger.log_fallback("Email service unhealthy. Message buffered locally to disk.")
