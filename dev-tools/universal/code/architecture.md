# Architecture

We use Domain-Driven Design, Hexagonal Architecture (ports and adapters) and Clean Architecture, adapted to our stack and pace.

Goal: a stable core, with messy edges you can swap.

## Layers

- **Domain**: business rules only. Pure, deterministic, no frameworks or I/O.
- **Application**: use cases (functions, handlers, orchestrators). They call domain logic and repositories. They coordinate, they don't hold business rules. Keep them thin; they're the entry points for testing full workflows.
- **Infra**: DBs, APIs, frameworks. Implements ports with adapters (e.g. a chat tool, a database).
- **UI**: renders and wires events. No domain logic.

## Rules

- The core depends on interfaces (ports), not implementations. Add a port for every outbound or volatile dependency (e.g. `UserRepository`, `NotificationService`).
- Push side effects (network, filesystem, browser) to the edges, behind an adapter. Don't mix I/O with computation.
- Don't leak domain into UI, or UI into domain. Pull domain logic out of UI, functions and effects.
- Split files and modules by layer and responsibility.
- Avoid tight coupling and leaky abstractions.
- Painful tests mean a missing boundary. Fix it by extracting pure functions, adding ports, or splitting logic.
