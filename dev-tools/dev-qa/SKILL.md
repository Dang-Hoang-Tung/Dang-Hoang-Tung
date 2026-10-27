---
name: dev-qa
description: Guides on how to QA, interactively test, and productionise code
---

# Context

Several things to confirm before starting the QA process:

- What is the functionality we're testing? (can be a Linear ticket or a PR)
- Are we testing the frontend, backend, or end-to-end?
- Do we have existing data or do we need to create it?
- What scenarios are we testing? Most of the time, we want to test all the happy paths, and the most prominent unhappy paths or edge cases.

# Modes

- Auto mode (default): run automatically, and I will only intervene if I need to. You can spin up the local server and run the frontend and backend tests, and check the database for records.
- Manual mode: I will tell you when to move to the next stage, and you will wait for my instructions.

# Steps

1. Classify the change (backend / frontend / data / e2e) to choose the approach.
2. Map topology: where each part runs, and which datastore/service it reads and writes.
3. Identify the exact prerequisite state the feature needs, including auth/ownership and transitive dependencies.
4. Create that state (reuse-and-tweak → product UI → direct seed), in the place the system reads from.
5. Obtain credentials; confirm the identity/role matches the path you intend to exercise.
6. Test deterministic/cheap paths first, then expensive/non-deterministic ones.
7. Use low-level access for setup and verification; assert via the real interface.
8. Note what the interface can't reveal (logs, internal state) and cover it another way.
9. Decide on cleanup.

# General approaches

For all QA, you can mint a a session JWT for my user and use it whether to test frontend or backend.

1. Test the frontend

- Run the full stack or just the frontend with a mock shell for the backend
- Identify the flow we want to test, and on which page we can find it
- Check UI/UX is working correctly (you can use Playwright chrome extension to launch a browser and test interactively)

2. Test the backend

- Run the backend
- Identify the endpoints and lambdas we want to test
- Create an example payload and send to the API (i.e. a cURL command)
- Check the DB table (if relevant) for records - can give a SQL query for the user to run

2. Test end-to-end

- Run the full stack
- Identify the flow we want to test, and on which page we can find it
- Trigger the flow through the UI/UX
- Check the DB table (if relevant) for records - can give a SQL query for the user to run

# Reference material

Use REFERENCE.md to understand exactly how the development stack works so you can navigate the QA process.
