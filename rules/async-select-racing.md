# async-select-racing

> Use `select!` to race futures and handle the first to complete

## Why It Matters

Sometimes you need the first result from multiple futures—timeout vs operation, cancellation vs work, or competing alternatives. `tokio::select!` lets you race futures and handle whichever completes first, while properly cancelling the others.

## Bad

```rust
// Can't express "whichever finishes first"
async fn fetch_with_fallback() -> Data {
    match fetch_primary().await {
        Ok(data) => data,
        Err(_) => fetch_fallback().await.unwrap(),  // Sequential, not racing
    }
}

// Manual timeout is error-prone
async fn fetch_with_timeout() -> Option<Data> {
    let start = Instant::now();
    loop {
        if start.elapsed() > Duration::from_secs(5) {
            return None;
        }
        // How do we check timeout while awaiting?
    }
}
```

## Good

```rust
use std::time::Duration;
use tokio::select;

async fn fetch_with_timeout() -> Result<Data, Error> {
    select! {
        result = fetch_data() => result,
        _ = tokio::time::sleep(Duration::from_secs(5)) => {
            Err(Error::Timeout)
        }
    }
}

async fn fetch_with_fallback() -> Data {
    select! {
        result = fetch_primary() => {
            match result {
                Ok(data) => data,
                Err(_) => fetch_fallback().await.unwrap()
            }
        }
        _ = tokio::time::sleep(Duration::from_secs(1)) => {
            // Primary too slow, use fallback
            fetch_fallback().await.unwrap()
        }
    }
}

struct Data;
#[derive(Debug)]
enum Error { Timeout, Failed }
async fn fetch_data() -> Result<Data, Error> { Ok(Data) }
async fn fetch_primary() -> Result<Data, Error> { Ok(Data) }
async fn fetch_fallback() -> Result<Data, Error> { Ok(Data) }
```

## select! Syntax

```rust
use tokio::select;
use tokio::sync::mpsc;

async fn syntax(mut channel: mpsc::Receiver<u32>, should_receive: bool) {
    select! {
        // Pattern = future => handler
        result = async_operation() => {
            // Handle result
            println!("Got: {:?}", result);
        }

        // Can bind with pattern matching
        Ok(data) = fallible_operation() => {
            process(data);
        }

        // Conditional branches with if guards
        msg = channel.recv(), if should_receive => {
            handle_message(msg);
        }

        // else branch for when all futures are disabled
        else => {
            println!("All branches disabled");
        }
    }
}

async fn async_operation() -> u32 { 1 }
async fn fallible_operation() -> Result<String, String> { Ok(String::new()) }
fn process(_data: String) {}
fn handle_message(_msg: Option<u32>) {}
```

## Cancellation Behavior

```rust
use tokio::select;

async fn select_example() {
    select! {
        _ = operation_a() => {
            println!("A completed first");
            // operation_b() is dropped/cancelled
        }
        _ = operation_b() => {
            println!("B completed first");
            // operation_a() is dropped/cancelled
        }
    }
}

// Futures are cancelled at their next .await point
// For immediate cancellation, futures must be cancel-safe

async fn operation_a() {}
async fn operation_b() {}
```

## Biased Selection

```rust
use tokio::select;
use tokio::sync::mpsc;

async fn prioritized(
    mut high_priority: mpsc::Receiver<u32>,
    mut low_priority: mpsc::Receiver<u32>,
) {
    // By default, select! randomly picks when multiple are ready
    // Use biased mode for deterministic priority
    select! {
        biased;  // Check branches in order

        msg = high_priority.recv() => handle_high(msg),
        msg = low_priority.recv() => handle_low(msg),
    }
    // Without biased, both channels have equal chance
    // when both have messages ready
}

fn handle_high(_msg: Option<u32>) {}
fn handle_low(_msg: Option<u32>) {}
```

## Loop with select!

```rust
use tokio::select;
use tokio::sync::mpsc;
use tokio_util::sync::CancellationToken;

async fn event_loop(
    mut commands: mpsc::Receiver<Command>,
    shutdown: CancellationToken,
) {
    loop {
        select! {
            _ = shutdown.cancelled() => {
                println!("Shutting down");
                break;
            }
            Some(cmd) = commands.recv() => {
                process_command(cmd).await;
            }
            else => {
                // commands channel closed
                break;
            }
        }
    }
}

struct Command;
async fn process_command(_cmd: Command) {}
```

## Racing Multiple of Same Type

```rust
use anyhow::Result;

// Race multiple servers for fastest response
async fn fastest_response(servers: &[String]) -> Result<Response> {
    let futures = servers.iter()
        .map(|s| Box::pin(fetch_from(s)))  // select_all requires Unpin futures
        .collect::<Vec<_>>();

    // select! requires static branches, use select_all for dynamic
    let (result, _index, _remaining) =
        futures::future::select_all(futures).await;

    result
}

struct Response;
async fn fetch_from(_server: &str) -> Result<Response> { Ok(Response) }
```

## Common Patterns

```rust
use std::time::Duration;
use tokio::select;
use tokio::time::sleep;
use tokio_util::sync::CancellationToken;

use Error::{Cancelled, Timeout};

async fn patterns(
    cancel_token: CancellationToken,
    shutdown: CancellationToken,
) -> Result<(), Error> {
    // Timeout
    let timed: Result<(), Error> = select! {
        result = operation() => result,
        _ = sleep(Duration::from_secs(5)) => Err(Timeout),
    };

    // Cancellation
    let cancelled: Result<(), Error> = select! {
        result = operation() => result,
        _ = cancel_token.cancelled() => Err(Cancelled),
    };

    // Interval with cancellation
    let mut interval = tokio::time::interval(Duration::from_secs(1));
    loop {
        select! {
            _ = shutdown.cancelled() => break,
            _ = interval.tick() => {
                do_periodic_work().await;
            }
        }
    }

    timed.and(cancelled)
}

#[derive(Debug)]
enum Error { Timeout, Cancelled }
async fn operation() -> Result<(), Error> { Ok(()) }
async fn do_periodic_work() {}
```

## See Also

- [async-cancellation-token](./async-cancellation-token.md) - Cancellation patterns
- [async-join-parallel](./async-join-parallel.md) - All futures, not racing
- [async-bounded-channel](./async-bounded-channel.md) - Channel operations in select
