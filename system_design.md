# System Design: Architecture and Scalability (SARS)

## Task 2.1 — Requirements and Architecture Choice

### a. System Requirements

#### Functional Requirements
1. **Authentication:** Users must be able to log into the system securely with distinct roles (Student, Admin, Faculty).
2. **Student Portal:** Students must be able to view their examination marks and enroll in available courses.
3. **Admin Panel:** Administrators must be able to manage records, assign faculty, and update course/student information.

#### Non-Functional Requirements
1. **Scalability:** The system must handle a peak load of 50,000 concurrent users during results publication without degradation in performance.
2. **Availability:** The system must achieve 99.9% uptime during the examination results week, ensuring the portal remains accessible.
3. **Security:** All user sessions must be encrypted using TLS, and access to student marks must be guarded by strict Role-Based Access Control (RBAC).

---

### b. Architectural Comparison & Recommendation

| Dimension | Monolithic Architecture | Microservices Architecture |
| :--- | :--- | :--- |
| **Independent Deployment** | Low; the entire application must be compiled and deployed as a single unit. | High; each service (Auth, Portal, Admin) can be deployed independently without affecting others. |
| **Fault Isolation** | Low; a memory leak or crash in the email service can bring down the entire application process. | High; a crash in the email or admin service does not impact the availability of the Student Portal. |
| **Management Complexity** | Low to Medium; single codebase, unified CI/CD pipeline, and simpler initial development. | High; requires container orchestration (Kubernetes), distributed tracing, and service mesh management. |

#### Recommendation & Justification
For SARS at a scale of 50,000 concurrent users during high-stakes event windows (like results day), a **Microservices Architecture** is strongly recommended. 

While a monolith is simpler to manage initially, its lack of fault isolation presents a massive operational risk during peak traffic: a bottleneck in the notification engine could completely take down results viewing. Microservices allow the university to horizontally scale the *Student Portal* independently to meet the 50,000 concurrent user demand, while keeping the *Admin Panel* and *Authentication* services scaled down, optimizing resource spend. This structural isolation guarantees that even if non-critical systems bottleneck under load, students can reliably access their marks.

---

## Task 2.2 — High-Level Design

### a. Main Components & Interface Contracts
1. **Authentication Service:** Responsible for verifying credentials, issuing JWT tokens, and enforcing RBAC.
   * *Interface Type:* REST API (`POST /api/v1/auth/login`)
2. **Student Portal Service:** Handles course viewing, enrollment requests, and grades retrieval.
   * *Interface Type:* REST API (`GET /api/v1/students/{id}/marks`)
3. **Admin Service:** Facilitates CRUD operations on student, faculty, and course catalogs.
   * *Interface Type:* REST API (`POST /api/v1/admin/records`)
4. **Notification Service:** Asynchronously processes and dispatches emails and SMS updates.
   * *Interface Type:* Asynchronous Message Queue / Event Broker Interface (e.g., consuming from an AMQP queue)

---

### b. Layered Architecture (Student Portal Module)



1. **Presentation Layer (Controllers/API Endpoints)**
   * *Responsibility:* Handles incoming HTTP requests, validates initial payload shapes, manages HTTP response headers, and routes requests to the business layer.
   * *Data In/Out:* Receives raw HTTP Request objects/JSON payloads from clients; passes clean DTOs (Data Transfer Objects) to the Business Layer; receives domain entities/response DTOs from the Business Layer and returns JSON responses to clients.
2. **Business Logic Layer (Services)**
   * *Responsibility:* Evaluates system business rules (e.g., checking if a student has prerequisites or if a course has open capacity before executing an enrollment).
   * *Data In/Out:* Receives DTOs and primitive parameters from the Presentation Layer; orchestrates operations by interacting with the Data Access Layer; returns validated domain entities or business response objects.
3. **Data Access Layer (Repositories/DAOs)**
   * *Responsibility:* Interfaces directly with the physical database engine, abstracting raw SQL queries, connections, and ORM operations.
   * *Data In/Out:* Receives entities or queries from the Business Layer; maps database rows to internal domain objects; returns mapped domain objects back up to the Business Layer.

---

### c. Scaling Strategy & Load Balancing
To handle 50,000 concurrent users, **Horizontal Scaling** (adding more web server instances) must be used rather than Vertical Scaling (upgrading a single machine's CPU/RAM). Vertical scaling hits a hard physical limit, incurs substantial cost penalties at high tiers, and creates a single point of failure (SPOF). Horizontal scaling allows for elastic expansion across commodity hardware.

Traffic will be distributed using an upstream **Load Balancer** running the **Least Connections Algorithm**. Unlike Round-Robin, which blindly sends requests sequentially, Least Connections routes traffic to the specific web server currently handling the fewest active connections. This is highly suitable for SARS during results day because user behavior varies wildly: some students check their marks instantly and close the tab (short-lived connection), while others linger to enroll in courses (long-lived stateful connection). Least Connections balances the actual processing load dynamically.

---

### d. Elasticity & Cost Optimization
Elasticity uses automated scaling policies driven by real-time infrastructure telemetry (such as CPU utilization, memory thresholds, or active connection rates). 

* **During Peak Load (Results Day):** As traffic surges, CPU metrics cross a set threshold (e.g., 70%), triggering the auto-scaling group to provision and boot up new web server containers automatically within minutes to match the 50,000 concurrent user demands.
* **During Off-Peak Periods (Semester Breaks):** When concurrent traffic drops to near zero, the telemetry drops below the minimum scale-down threshold. The system automatically tears down unnecessary web server instances, scaling down to a minimal base footprint (e.g., two small instances). This avoids paying for unutilized idle compute resources, drastically reducing operating costs.

---

### e. The Shared Session State Problem

#### Problem Definition
This phenomenon is known as the **Session Mismatch / Lost Session Problem** (or breaking session persistence). Because HTTP is stateless, if Server A authenticates a user and saves the session identifier locally in its own local RAM, Server B remains completely unaware of this session. When a subsequent request lands on Server B, it treats the authenticated user as an unauthenticated guest, forcing unexpected logouts.

#### Resolution Strategies

1. **Strategy 1: Sticky Sessions (Session Affinity at Load Balancer)**
   * *Description:* Modify the load balancer configuration to inject a tracking cookie or inspect the client IP, ensuring that all subsequent requests from that specific client are consistently routed to the exact same backend server instance.
   * *Trade-off:* **Damages Fault Tolerance and Load Distribution.** If a backend server crashes, all users pinned to that server lose their session state instantly. Furthermore, it can create highly unbalanced hot-spots across the server pool if a group of heavy users get stuck on the same instance.

2. **Strategy 2: Centralized Distributed Session Store**
   * *Description:* Extract the session storage mechanism completely away from the local web servers and decouple it into an external, fast, in-memory cache system like Redis or Memcached. Every web server looks up session tokens from this central cluster.
   * *Trade-off:* **Introduces Network Overhead and Capital Cost.** Every single HTTP request now requires an additional network round-trip from the web server to the Redis cluster to validate the session, adding marginal latency, and requires managing additional infrastructure assets.
