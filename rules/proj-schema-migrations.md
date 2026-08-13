# proj-schema-migrations

> Treat database migrations as ordered source artifacts and prove they build the production schema from empty

## Why It Matters

The database schema is part of the application contract. Manual DDL leaves
developers, CI, and production with different histories; an untested migration
can make a rolling deployment impossible even when the Rust binary is correct.
Keep forward migrations in source control, apply them in order, and prove the
entire sequence against the same database engine used in production.

## Bad

```text
# A developer changes a shared database by hand.
ALTER TABLE subscriptions ADD COLUMN status TEXT NOT NULL;

# The repository has no artifact that recreates that state.
```

This also fails during rolling deployment: old instances do not know the new
column and the new binary cannot start until every row has a value.

## Good

```text
migrations/
  202608130001_add_subscription_status.sql
  202608130002_backfill_subscription_status.sql
  202608130003_require_subscription_status.sql
```

Use an expand/backfill/contract sequence:

1. Add the new column or table in a form both binary versions tolerate.
2. Deploy code that writes both representations and can read either.
3. Backfill existing rows with a restartable, bounded job.
4. Switch reads to the new representation.
5. Add the stricter constraint and remove the old representation only after
   old binaries can no longer run.

## Verification Contract

- A fresh production-engine database accepts every migration in order.
- The application starts and exercises its persistence path after migration.
- Migration application is idempotent at the orchestrator level: concurrent
  starters do not each run the sequence.
- Roll-forward is the default recovery. A destructive down migration is not a
  substitute for a restore or compensating migration.
- Integration tests receive an isolation boundary the application cannot
  escape: a fresh logical database or a transaction only when the test owns
  every connection.
- Database tooling is an explicit integration prerequisite, never a hidden
  requirement of the default `cargo build`.

## Failure Tests

Exercise at least these cases:

- an empty database;
- a database at each supported intermediate migration;
- a migration interrupted during a bounded backfill and resumed;
- two application versions operating during the expand phase;
- a constraint violation that must leave the previous schema usable.

## See Also

- [proj-works-out-of-box](proj-works-out-of-box.md) - database services are explicit integration prerequisites
- [test-fixture-raii](test-fixture-raii.md) - tear down isolated test resources reliably
- [test-integration-dir](test-integration-dir.md) - exercise schema and application through integration tests
- [err-context-chain](err-context-chain.md) - report the migration and statement that failed
- [api-typestate](api-typestate.md) - model in-process transaction state when it adds safety
