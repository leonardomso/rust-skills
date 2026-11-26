# test-mock-traits

> Use traits for dependencies to enable mocking in tests

## Why It Matters

Concrete dependencies make testing hard. You can't test error paths, timeouts, or edge cases without the real external system. Put each dependency behind a small trait and inject a test double (a fake or stub). Tests then run fast and can force any failure.

## Bad

```rust
struct UserService {
    db: PostgresConnection,  // Concrete type - hard to test
}

impl UserService {
    async fn get_user(&self, id: u64) -> Result<User, Error> {
        self.db.query("SELECT * FROM users WHERE id = $1", &[&id]).await
    }
}

// A test needs a real Postgres instance: slow, flaky, no error paths
```

## Good

```rust
use std::collections::HashMap;

#[derive(Clone, Debug, PartialEq)]
struct User {
    id: u64,
    name: String,
}

#[derive(Debug)]
enum DbError {
    Unavailable,
}

#[derive(Debug)]
enum Error {
    NotFound,
    Db(DbError),
}

impl From<DbError> for Error {
    fn from(e: DbError) -> Self {
        Error::Db(e)
    }
}

// Define a trait for the dependency. Native `async fn` in traits needs no macro.
trait UserRepository {
    async fn find_by_id(&self, id: u64) -> Result<Option<User>, DbError>;
}

// Service depends on the trait, not a concrete type
struct UserService<R: UserRepository> {
    repo: R,
}

impl<R: UserRepository> UserService<R> {
    async fn get_user(&self, id: u64) -> Result<User, Error> {
        self.repo.find_by_id(id).await?.ok_or(Error::NotFound)
    }
}

// The production implementation (for example a database pool) implements
// `UserRepository` the same way the fakes below do.

#[cfg(test)]
mod tests {
    use super::*;

    struct FakeUserRepo {
        users: HashMap<u64, User>,
    }

    impl UserRepository for FakeUserRepo {
        async fn find_by_id(&self, id: u64) -> Result<Option<User>, DbError> {
            Ok(self.users.get(&id).cloned())
        }
    }

    struct DownRepo;

    impl UserRepository for DownRepo {
        async fn find_by_id(&self, _id: u64) -> Result<Option<User>, DbError> {
            Err(DbError::Unavailable)
        }
    }

    #[tokio::test]
    async fn get_user_returns_user_when_present() {
        let mut users = HashMap::new();
        users.insert(1, User { id: 1, name: "Alice".into() });
        let service = UserService { repo: FakeUserRepo { users } };

        let user = service.get_user(1).await.unwrap();

        assert_eq!(user.name, "Alice");
    }

    #[tokio::test]
    async fn get_user_returns_not_found_for_unknown_id() {
        let service = UserService { repo: FakeUserRepo { users: HashMap::new() } };

        let result = service.get_user(999).await;

        assert!(matches!(result, Err(Error::NotFound)));
    }

    #[tokio::test]
    async fn get_user_propagates_database_errors() {
        let service = UserService { repo: DownRepo };

        let result = service.get_user(1).await;

        assert!(matches!(result, Err(Error::Db(DbError::Unavailable))));
    }
}
```

## Generics vs `dyn`

A trait with a native `async fn` is not dyn-compatible, so `Box<dyn UserRepository>` does not work above. Keep the generic parameter. For synchronous dependencies, `dyn` keeps the service type simple. For `dyn` with async methods, see [async-fn-in-trait](async-fn-in-trait.md).

```rust
// Synchronous dependency: `dyn` works and keeps the service type simple
trait Clock {
    fn now_secs(&self) -> u64;
}

struct Service {
    clock: Box<dyn Clock>,
}

impl Service {
    fn new(clock: impl Clock + 'static) -> Self {
        Self { clock: Box::new(clock) }
    }

    fn is_after(&self, deadline: u64) -> bool {
        self.clock.now_secs() > deadline
    }
}
```

## See Also

- [test-mockall-mocking](test-mockall-mocking.md) - Generate mocks with mockall instead of writing fakes by hand
- [async-fn-in-trait](async-fn-in-trait.md) - Native async fn in traits, and `dyn` with async methods
- [trait-dyn-vs-generic](trait-dyn-vs-generic.md) - Choosing generics or `dyn`
- [api-sans-io](api-sans-io.md) - Take `impl Read`/`Write` instead of paths
- [test-utils-feature-gated](test-utils-feature-gated.md) - Gate test utilities behind a feature
- [proj-lib-main-split](proj-lib-main-split.md) - Testable architecture
