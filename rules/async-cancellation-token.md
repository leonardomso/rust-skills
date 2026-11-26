# async-cancellation-token

> Use `CancellationToken` for graceful shutdown and task cancellation

## Why It Matters

Dropping a `JoinHandle` doesn't cancel the task—it just detaches it. For graceful shutdown, you need explicit cancellation. `tokio_util::sync::CancellationToken` provides a cooperative cancellation mechanism that tasks can check and respond to, enabling clean resource cleanup.

## Bad

```rust
// Dropping the handle doesn't stop the task
let handle = tokio::spawn(async {
    loop {
        do_work().await;
    }
});

drop(handle);  // Task continues running in background!

// A bool flag is not async-aware
let running = Arc::new(AtomicBool::new(true));

tokio::spawn({
    let running = running.clone();
    async move {
        while running.load(Ordering::Relaxed) {
            do_work().await; // the flag is only checked between calls
        }
    }
});

running.store(false, Ordering::Relaxed); // waits for the current do_work()
```

## Good

```rust
use std::time::Duration;
use tokio_util::sync::CancellationToken;

async fn do_work() {
    tokio::time::sleep(Duration::from_millis(10)).await;
}

async fn cleanup() {}

#[tokio::main]
async fn main() -> Result<(), tokio::task::JoinError> {
    let token = CancellationToken::new();

    let handle = tokio::spawn({
        let token = token.clone(); // cheap, Arc-based clone
        async move {
            loop {
                tokio::select! {
                    _ = token.cancelled() => {
                        cleanup().await;
                        break;
                    }
                    _ = do_work() => {}
                }
            }
        }
    });

    token.cancel();
    handle.await // the task finishes cleanly
}
```

Other calls: `token.is_cancelled()` (non-blocking check), `token.cancelled().await` (wait), `token.child_token()`.

## Hierarchical Cancellation

A child token is cancelled when its parent is, but cancelling a child does not touch the parent. Give each connection or subtask a child token so one shutdown signal reaches all of them.

```rust
use tokio::io::{AsyncReadExt, BufReader};
use tokio::net::{TcpListener, TcpStream};
use tokio_util::sync::CancellationToken;

async fn run_server(shutdown: CancellationToken) -> std::io::Result<()> {
    let listener = TcpListener::bind("0.0.0.0:8080").await?;

    loop {
        tokio::select! {
            _ = shutdown.cancelled() => break,
            result = listener.accept() => {
                let (socket, _) = result?;
                tokio::spawn(handle_connection(socket, shutdown.child_token()));
            }
        }
    }
    Ok(())
}

async fn handle_connection(socket: TcpStream, token: CancellationToken) {
    let mut reader = BufReader::new(socket);
    let mut buf = [0u8; 1024];
    loop {
        tokio::select! {
            _ = token.cancelled() => break,
            n = reader.read(&mut buf) => match n {
                Ok(0) | Err(_) => break,
                Ok(_) => { /* handle data */ }
            },
        }
    }
}
```

## Graceful Shutdown

Trigger the token from a signal handler, then wait for tasks with a deadline.

```rust
use std::time::Duration;
use tokio::task::JoinSet;
use tokio_util::sync::CancellationToken;

async fn worker(token: CancellationToken) {
    token.cancelled().await;
}

#[tokio::main]
async fn main() {
    let shutdown = CancellationToken::new();

    let trigger = shutdown.clone();
    tokio::spawn(async move {
        tokio::signal::ctrl_c().await.expect("failed to listen for ctrl+c");
        trigger.cancel();
    });

    let mut tasks = JoinSet::new();
    tasks.spawn(worker(shutdown.child_token()));
    tasks.spawn(worker(shutdown.child_token()));

    shutdown.cancelled().await;

    // Give tasks 30 seconds to finish their cleanup
    let drain = async { while tasks.join_next().await.is_some() {} };
    let _ = tokio::time::timeout(Duration::from_secs(30), drain).await;
}
```

## DropGuard

`drop_guard()` cancels the token when the guard is dropped, so an early return or panic still stops the tasks.

```rust
use tokio_util::sync::CancellationToken;

#[tokio::main]
async fn main() {
    let token = CancellationToken::new();
    let guard = token.clone().drop_guard();

    let task = tokio::spawn({
        let token = token.clone();
        async move { token.cancelled().await }
    });

    drop(guard); // calls token.cancel()
    task.await.unwrap();
}
```

## See Also

- [async-joinset-structured](./async-joinset-structured.md) - Managing multiple tasks
- [async-select-racing](./async-select-racing.md) - select! for cancellation
- [async-tokio-runtime](./async-tokio-runtime.md) - Runtime setup and shutdown
