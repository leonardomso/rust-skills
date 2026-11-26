# test-mock-traits

> Use traits for dependencies to enable mocking in tests

## Why It Matters

Concrete dependencies make testing hard—you can't easily test error paths, timeouts, or edge cases without real external systems. Extracting dependencies behind traits lets you inject test doubles (mocks, fakes, stubs), enabling isolated unit tests that run fast and cover edge cases.

## Bad

```rust
struct UserService {
    db: PostgresConnection,  // Concrete type - hard to test
}

impl UserService {
    async fn get_user(&self, id: u64) -> Result<User, Error> {
        // Directly calls Postgres - needs real database to test
        self.db.query("SELECT * FROM users WHERE id = $1", &[&id]).await
    }
}

// Test requires real Postgres instance
#[tokio::test]
async fn test_get_user() {
    let db = PostgresConnection::connect("postgres://...").await?;
    let service = UserService { db };
    // Slow, flaky, can't test error paths
}
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
// `UserRepository` the same way the fake does below.

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

## mockall Crate

`#[automock]` works on traits with native `async fn`, so no `#[async_trait]` is needed.

```rust
use mockall::automock;
use mockall::predicate::eq;

#[automock]
trait Database {
    async fn query(&self, sql: &str) -> Result<Vec<String>, String>;
}

#[tokio::test]
async fn query_runs_once_with_expected_sql() {
    let mut mock = MockDatabase::new();

    mock.expect_query()
        .with(eq("SELECT 1"))
        .times(1)
        .returning(|_| Ok(vec!["1".to_string()]));

    let result = mock.query("SELECT 1").await;
    assert!(result.is_ok());
}
```

## Testing Error Paths

```rust
#[derive(Debug)]
enum HttpError {
    Timeout,
}

trait HttpClient {
    async fn get(&self, url: &str) -> Result<String, HttpError>;
}

struct FailingClient;

impl HttpClient for FailingClient {
    async fn get(&self, _url: &str) -> Result<String, HttpError> {
        Err(HttpError::Timeout) // always fails
    }
}

async fn fetch_data(client: &impl HttpClient) -> Result<String, HttpError> {
    client.get("https://example.invalid/data").await
}

#[tokio::test]
async fn fetch_data_reports_timeout() {
    let result = fetch_data(&FailingClient).await;
    assert!(matches!(result, Err(HttpError::Timeout)));
}
```

## Dynamic Dispatch Alternative

A trait with a native `async fn` is not dyn-compatible, so `Box<dyn UserRepository>` does not work with the repository above. Keep the generic parameter, or use a trait with synchronous methods (or methods returning boxed futures) behind `dyn`. If you need `dyn` with async methods, see [async-fn-in-trait](async-fn-in-trait.md).

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

## Cargo.toml

```toml
[dev-dependencies]
mockall = "0.13"
tokio = { version = "1", features = ["macros", "rt"] }
```

## See Also

- [async-fn-in-trait](async-fn-in-trait.md) - Native async fn in traits
- [test-mockall-mocking](test-mockall-mocking.md) - Mocking with mockall
- [api-sealed-trait](./api-sealed-trait.md) - Trait design
- [test-proptest-properties](./test-proptest-properties.md) - Property-based testing
- [proj-lib-main-split](./proj-lib-main-split.md) - Testable architecture
