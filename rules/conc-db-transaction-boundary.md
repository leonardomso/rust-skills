# conc-db-transaction-boundary

> Keep one atomic business change inside one short database transaction

## Why It Matters

Two successful statements separated by a crash can leave a half-completed
business operation. Conversely, holding a transaction open across remote
network I/O pins a connection and lock while waiting on an unrelated system.
Define the atomic state transition, execute its database work on the same
transaction handle, and commit only after every required statement succeeds.

## Bad

```text
INSERT subscriber
COMMIT
INSERT confirmation_token
# crash: subscriber can never confirm
```

## Good

```rust
pub trait SubscriptionTx {
    type Error;

    fn insert_subscriber(&mut self) -> Result<(), Self::Error>;
    fn insert_token(&mut self) -> Result<(), Self::Error>;
    fn commit(self) -> Result<(), Self::Error>;
}

pub fn persist_subscription<T: SubscriptionTx>(mut tx: T) -> Result<(), T::Error> {
    tx.insert_subscriber()?;
    tx.insert_token()?;
    tx.commit()
}

fn main() {}
```

Dropping or rolling back the uncommitted transaction restores the prior
database state.

## Contract

- Pass the transaction through every repository call participating in the
  invariant; a pool lookup inside one of those calls silently escapes it.
- Keep transactions short and never wait on email, HTTP, or other remote I/O
  while holding locks.
- Choose an isolation level from the anomaly the operation must prevent.
- Treat serialization/deadlock failures as bounded retry candidates for the
  whole transaction, not for one statement.
- Use an outbox or durable queue when database state and an external side
  effect must eventually agree.
- Test a failure between each statement and verify no partial state is visible.

## See Also

- [proj-schema-migrations](proj-schema-migrations.md) - keep schema transitions deployable
- [async-no-lock-await](async-no-lock-await.md) - do not hold unrelated in-memory locks across I/O
- [err-context-chain](err-context-chain.md) - retain the failed statement's business context
- [test-observable-coverage](test-observable-coverage.md) - assert the atomic outcome, not helper calls
- [api-typestate](api-typestate.md) - model transaction state only when it improves the API
