# async-join-parallel

> Use `join!` or `try_join!` for concurrent independent futures

## Why It Matters

Awaiting futures sequentially takes the sum of their durations. `join!` runs futures concurrently, taking only as long as the slowest one. For independent operations like multiple API calls or parallel file reads, this can dramatically reduce latency.

## Bad

```rust
async fn fetch_data() -> (User, Posts, Comments) {
    // Sequential: 300ms total (100 + 100 + 100)
    let user = fetch_user().await;        // 100ms
    let posts = fetch_posts().await;      // 100ms  
    let comments = fetch_comments().await; // 100ms
    
    (user, posts, comments)
}

async fn read_configs() -> Result<(Config, Settings)> {
    // Sequential: 20ms + 20ms = 40ms
    let config = fs::read_to_string("config.toml").await?;
    let settings = fs::read_to_string("settings.json").await?;
    
    Ok((parse_config(&config)?, parse_settings(&settings)?))
}
```

## Good

```rust
use anyhow::Result;
use tokio::{fs, join, try_join};

async fn fetch_data() -> (User, Posts, Comments) {
    // Concurrent: ~100ms total (max of all three)
    let (user, posts, comments) = join!(
        fetch_user(),
        fetch_posts(),
        fetch_comments(),
    );

    (user, posts, comments)
}

async fn read_configs() -> Result<(Config, Settings)> {
    // Concurrent: ~20ms total
    let (config_str, settings_str) = try_join!(
        fs::read_to_string("config.toml"),
        fs::read_to_string("settings.json"),
    )?;

    Ok((parse_config(&config_str)?, parse_settings(&settings_str)?))
}

struct User;
struct Posts;
struct Comments;
struct Config;
struct Settings;
async fn fetch_user() -> User { User }
async fn fetch_posts() -> Posts { Posts }
async fn fetch_comments() -> Comments { Comments }
fn parse_config(_s: &str) -> Result<Config> { Ok(Config) }
fn parse_settings(_s: &str) -> Result<Settings> { Ok(Settings) }
```

## join! vs try_join!

```rust
use tokio::{join, try_join};

let future_a = async { 1 };
let future_b = async { 2 };
let future_c = async { 3 };
let fallible_a = async { Ok::<_, std::io::Error>(1) };
let fallible_b = async { Ok::<_, std::io::Error>(2) };
let fallible_c = async { Ok::<_, std::io::Error>(3) };

// join! - all futures run to completion, returns tuple
let (a, b, c) = join!(future_a, future_b, future_c);

// try_join! - short-circuits on first error
let (a, b, c) = try_join!(fallible_a, fallible_b, fallible_c)?;
// If fallible_b fails, returns Err immediately
// Other futures may still be running (cancellation is async)
```

## futures::join_all for Dynamic Collections

```rust
use anyhow::Result;
use futures::future::{join_all, try_join_all};

async fn fetch_all_users(ids: &[u64]) -> Vec<User> {
    let futures: Vec<_> = ids.iter()
        .map(|id| fetch_user(*id))
        .collect();

    join_all(futures).await
}

// With fallible futures
async fn try_fetch_all_users(ids: &[u64]) -> Result<Vec<User>> {
    let futures: Vec<_> = ids.iter()
        .map(|id| try_fetch_user(*id))
        .collect();

    try_join_all(futures).await
}

struct User { id: u64 }
async fn fetch_user(id: u64) -> User { User { id } }
async fn try_fetch_user(id: u64) -> Result<User> { Ok(User { id }) }
```

## Limiting Concurrency

```rust
use std::sync::Arc;
use anyhow::Result;
use futures::future::join_all;
use futures::stream::{self, StreamExt};
use tokio::sync::Semaphore;

async fn fetch_with_limit(ids: &[u64]) -> Vec<Result<User>> {
    stream::iter(ids)
        .map(|id| fetch_user(*id))
        .buffer_unordered(10)  // Max 10 concurrent requests
        .collect()
        .await
}

// Or with tokio::sync::Semaphore
async fn fetch_with_semaphore(ids: &[u64]) -> Vec<Result<User>> {
    let semaphore = Arc::new(Semaphore::new(10));

    let futures: Vec<_> = ids.iter().map(|id| {
        let semaphore = semaphore.clone();
        async move {
            let _permit = semaphore.acquire().await.unwrap();
            fetch_user(*id).await
        }
    }).collect();

    join_all(futures).await
}

struct User { id: u64 }
async fn fetch_user(id: u64) -> Result<User> { Ok(User { id }) }
```

## When NOT to Use join!

```rust
use std::sync::Arc;
use anyhow::Result;
use tokio::join;
use tokio::sync::Mutex;

// ❌ Dependent futures - must be sequential
async fn create_and_populate() -> Result<()> {
    let db = create_database().await?;   // Must complete first
    populate_tables(&db).await?;          // Depends on db
    Ok(())
}

// ❌ Short-circuiting logic
async fn find_first() -> Option<Data> {
    // Want to stop when one succeeds
    // Use select! instead
    None
}

// ❌ Shared mutable state
async fn bad_shared_state() {
    let counter = Arc::new(Mutex::new(0));
    // This might work but can cause contention
    join!(
        increment(counter.clone()),
        increment(counter.clone()),
    );
}

struct Db;
struct Data;
async fn create_database() -> Result<Db> { Ok(Db) }
async fn populate_tables(_db: &Db) -> Result<()> { Ok(()) }
async fn increment(counter: Arc<Mutex<u32>>) { *counter.lock().await += 1; }
```

## See Also

- [async-try-join](./async-try-join.md) - Error handling in concurrent futures
- [async-select-racing](./async-select-racing.md) - Racing futures
- [async-joinset-structured](./async-joinset-structured.md) - Dynamic task sets
