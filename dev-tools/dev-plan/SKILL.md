---
name: dev-plan
description: Guides on how to plan for development
---

Help me plan for developement. First check the Linear ticket with the ID given. Then investigate how to do the piece of work depending on whether this is a major or minor change.

Major changes include:

- New feature addition
- Cross-cutting refactor
- etc...

Minor changes include:

- Bug fixing
- Feature tweaks
- etc...

For minor changes, propose the most suitable change, which should be appropriately scoped to the ticket and lean towards lightweight implementations. However, if you spot any code smells, do raise it for discussion.

For major changes, investigate the codebase including any relevant repositories under ~/omnea/omnea-meta-repo. Understand the context surrounding the change. Then discusss:

- the product requirements (clearly mark [PRODUCT REQUIREMENT] in your response)
- the technical requirements (clearly mark [TECHNICAL REQUIREMENT] in your response)

For each technical requirement, propose architectural approaches to tackle it.
