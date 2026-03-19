---
name: write-code
description: Guides on writing code. Use when the user asks "write this code" or "implement this functionality".
---

<!-- Reference Content -->

# Principles

## Designing for testability: architectural insights

The architecture of a system _dictates_ how testable it is. Well-structured systems aren’t just easier to test - they’re easier to evolve, scale, and trust. We aim to build **testable systems by design**, not by accident or cleanup.

This means designing **with boundaries**, **for clarity**, and **against entanglement**.

We apply principles from **Domain-Driven Design**, **Hexagonal Architecture**, **Ports and Adapters**, and **Clean Architecture**, adapted to our stack and pace of change. Here’s how they translate into practice:

### 1. **Domain as center of gravity**

> “Isolate domain logic from frameworks and I/O.” — DDD

- Keep domain logic **pure**, **deterministic**, and **free of tech-specific concerns**.
- Domain models and services should express business rules, not infrastructure.

### 2. **Separate core from edges (hexagonal shape)**

> “Application and domain at the center. External systems plug in via ports.” — Hexagonal Architecture

- Push frameworks, DBs, APIs, and UIs to the outer edges.
- Create **ports (interfaces)** for all outbound dependencies (e.g. `NotificationService`, `SupplierRepository`).
- Implement these ports via **adapters** in the infra layer.

### 3. **Use application layer to orchestrate, not compute**

> “Use cases coordinate flows; they don’t contain business rules.” — Clean Architecture

- Application services (e.g. Lambdas, `handlers/`, orchestrators) call into domain logic and repositories.
- Keep them thin and focused - they expose meaningful entry points for testing full workflows.

### 4. **Keep UI, app, and domain decoupled**

> “Avoid leaking domain into UI, and UI into domain.” — DDD + Hexagonal

- React components should render props and wire events - not contain logic.
- Side effects and data fetching go in custom hooks or services.
- Domain logic lives in domain layer — not in `useEffect`, handlers, or nested conditions.

### 5. **Push side effects to the edges**

> “Separate pure logic from impure actions.” — Functional Core, Imperative Shell

- Hitting the network, filesystem, or browser? Push that logic behind an adapter or boundary.
- Treat I/O as pluggable and avoid mixing it with core computation.

### 6. **Design for replaceability via ports**

> “Core depends on abstractions, not implementations.” — Ports & Adapters

- Define clear interfaces for core dependencies - e.g. `NotificationHandler`, `UserRepository`.
- Infra provides the implementation (e.g Slack, Postgres).

### 7. **Let tests drive the architecture**

> “Painful tests reveal poor design.” — TDD, GOOS

- When testing feels slow, brittle, or hard — take that as a signal.
- Refactor by **extracting pure functions**, **introducing ports**, or **splitting logic**.
- Use tests as a lens into where **boundaries** are missing.

**🧱 What does “adding boundaries” mean?**

> Adding boundaries = separating logic, responsibilities, and dependencies — so you can test, reason about, and evolve them independently.

In practice:

- Pull domain logic out of UI, Lambdas, or effects.
- Create ports (interfaces) for infrastructure or volatile dependencies.
- Split files/modules by responsibility (domain, application, infra, UI).
- Move toward a hexagonal shape: a stable core, messy edges you can swap.

