---
name: dev-migration
description: Use for database migration
---

# Writing migrations

- omnea-app uses Atlas for schema migrations. We write a migration in SQL and then generate a checksum for Atlas.
- For non-schema migrations, such as data moves, another option is for the developer to run the SQL directly against the databases.
