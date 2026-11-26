# test-mockall-mocking

> Use mockall for trait mocking

## Why It Matters

Hand-written fakes grow with every method and can't check how they were called. Mockall generates a mock from a trait. You set what each method returns and how often it must be called, and the mock fails the test if the expectations are not met.

For how to design the trait and its seams, see [test-mock-traits](test-mock-traits.md). This rule covers the mockall API.

## Bad

```rust
// Hand-rolled mock: counts calls by hand, and every new method adds more code
struct MockDb {
    calls: std::cell::Cell<u32>,
}
```

## Good

```toml
# Cargo.toml
[dev-dependencies]
mockall = "0.15"
```

```rust
use mockall::automock;
use mockall::predicate::eq;

#[automock]
trait Database {
    fn get_user(&self, id: u64) -> Option<String>;
    fn save_user(&self, name: &str) -> Result<(), String>;
}

fn find_user(db: &impl Database, id: u64) -> Option<String> {
    db.get_user(id)
}

#[test]
fn find_user_returns_stored_name() {
    let mut mock = MockDatabase::new();
    mock.expect_get_user()
        .with(eq(42))
        .times(1)
        .returning(|_| Some("Alice".to_string()));

    assert_eq!(find_user(&mock, 42).as_deref(), Some("Alice"));
    // Expectations are verified when `mock` is dropped
}
```

## Expectations and Predicates

```rust
use mockall::automock;
use mockall::predicate::*;

#[automock]
trait Search {
    fn validate(&self, input: &str) -> bool;
    fn search(&self, query: &str, limit: usize) -> Vec<String>;
    fn count(&self) -> u32;
}

#[test]
fn matchers() {
    let mut mock = MockSearch::new();

    // Custom predicate on one argument
    mock.expect_validate()
        .with(function(|s: &str| s.len() > 5))
        .returning(|_| true);

    // `withf` checks all arguments at once
    mock.expect_search()
        .withf(|query, limit| query.len() < 100 && *limit <= 1000)
        .returning(|_, _| vec![]);

    // Call counts: `.times(1)`, `.times(3..)`, `.never()`
    mock.expect_count().times(1..).returning(|| 42);

    assert!(mock.validate("long enough"));
    assert!(mock.search("rust", 10).is_empty());
    assert_eq!(mock.count(), 42);
}
```

A call that matches no expectation panics. For a different value on each call, add several expectations with `.times(1)`. They match in the order added. Use `return_const(value)` for a fixed value.

## Sequences

```rust
use mockall::{automock, Sequence};

#[automock]
trait Connection {
    fn connect(&self);
    fn disconnect(&self);
}

#[test]
fn connects_before_disconnecting() {
    let mut seq = Sequence::new();
    let mut mock = MockConnection::new();

    mock.expect_connect().times(1).in_sequence(&mut seq).return_const(());
    mock.expect_disconnect().times(1).in_sequence(&mut seq).return_const(());

    mock.connect();
    mock.disconnect();
}
```

## Async Traits

`#[automock]` handles native `async fn` in traits directly. You do not need `#[async_trait]`.

```rust
use mockall::automock;

#[automock]
trait AsyncDatabase {
    async fn fetch(&self, id: u64) -> Option<String>;
}

#[tokio::test]
async fn fetch_returns_value() {
    let mut mock = MockAsyncDatabase::new();
    mock.expect_fetch().returning(|_| Some("data".to_string()));

    assert!(mock.fetch(1).await.is_some());
}
```

## Traits You Don't Own

`#[automock]` needs the trait definition. For a trait from another crate, declare the mock with `mock!`, repeating the method signatures you use.

```rust
use mockall::mock;

trait Greeter {
    fn greet(&self, name: &str) -> String;
}

mock! {
    pub Greet {}
    impl Greeter for Greet {
        fn greet(&self, name: &str) -> String;
    }
}

#[test]
fn mocks_foreign_trait() {
    let mut mock = MockGreet::new();
    mock.expect_greet().returning(|n| format!("hi {n}"));
    assert_eq!(mock.greet("bo"), "hi bo");
}
```

Gate `#[automock]` on your own traits with `#[cfg_attr(test, mockall::automock)]` so release builds don't need mockall.

## See Also

- [test-mock-traits](test-mock-traits.md) - Design dependencies behind traits, and when a hand-written fake is enough
- [async-fn-in-trait](async-fn-in-trait.md) - Native async fn in traits
- [test-arrange-act-assert](test-arrange-act-assert.md) - Test structure
- [test-proptest-properties](test-proptest-properties.md) - Property testing
