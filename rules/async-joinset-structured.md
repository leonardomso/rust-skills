# async-joinset-structured

> Use `JoinSet` for managing dynamic collections of spawned tasks

## Why It Matters

When spawning a variable number of tasks, collecting `JoinHandle`s in a `Vec` and using `join_all` works but lacks flexibility. `JoinSet` provides a better abstraction: add/remove tasks dynamically, get results as they complete, and abort all on drop. It's the idiomatic way to manage task collections.

## Bad

```rust
// Manual handle management
let mut handles: Vec<JoinHandle<Result<Data>>> = Vec::new();

for url in urls {
    handles.push(tokio::spawn(fetch(url)));
}

// Wait for all, in order (not as they complete)
let results = futures::future::join_all(handles).await;

// No easy way to cancel all, handle errors progressively, or add more tasks
```

## Good

```rust
use tokio::task::JoinSet;

let urls = vec!["https://example.com".to_string()];
let mut set = JoinSet::new();

for url in urls {
    set.spawn(fetch(url.clone()));
}

// Process results as they complete
while let Some(result) = set.join_next().await {
    match result {
        Ok(Ok(data)) => process(data),
        Ok(Err(e)) => log::error!("Task failed: {}", e),
        Err(e) => log::error!("Task panicked: {}", e),
    }
}
// All tasks done, set is empty

struct Data;
async fn fetch(_url: String) -> anyhow::Result<Data> { Ok(Data) }
fn process(_data: Data) {}
```

## Dynamic Task Addition

```rust
use tokio::sync::mpsc;
use tokio::task::{JoinError, JoinSet};

async fn worker_pool(mut rx: mpsc::Receiver<Task>) {
    let mut set = JoinSet::new();
    let max_concurrent = 10;

    loop {
        tokio::select! {
            // Accept new tasks if under limit
            Some(task) = rx.recv(), if set.len() < max_concurrent => {
                set.spawn(process_task(task));
            }

            // Process completed tasks
            Some(result) = set.join_next() => {
                handle_result(result);
            }

            // Exit when no tasks and channel closed
            else => break,
        }
    }
}

struct Task;
async fn process_task(_task: Task) -> u32 { 0 }
fn handle_result(_result: Result<u32, JoinError>) {}
```

## Abort on Drop

```rust
use tokio::task::JoinSet;

async fn early_exit() {
    let mut set = JoinSet::new();
    set.spawn(long_running_task());
    set.spawn(another_task());

    // Early exit
    return;
}  // JoinSet dropped here - all tasks are aborted!

// Explicit abort
async fn explicit_abort() {
    let mut set = JoinSet::new();
    set.spawn(task());
    set.abort_all();  // Cancel all tasks
}

async fn long_running_task() {}
async fn another_task() {}
async fn task() {}
```

## Error Handling Pattern

```rust
use tokio::task::JoinSet;

async fn fetch_all(urls: &[String]) -> Vec<Result<Data, Error>> {
    let mut set = JoinSet::new();
    let mut results = Vec::new();

    for url in urls {
        set.spawn(fetch(url.clone()));
    }

    while let Some(join_result) = set.join_next().await {
        let result = match join_result {
            Ok(task_result) => task_result,
            Err(join_error) => {
                if join_error.is_panic() {
                    Err(Error::TaskPanicked)
                } else {
                    Err(Error::TaskCancelled)
                }
            }
        };
        results.push(result);
    }

    results
}

struct Data;
enum Error { TaskPanicked, TaskCancelled }
async fn fetch(_url: String) -> Result<Data, Error> { Ok(Data) }
```

## With Cancellation

```rust
use tokio::task::JoinSet;
use tokio_util::sync::CancellationToken;

async fn run_workers(shutdown: CancellationToken) {
    let mut set = JoinSet::new();

    for i in 0..4 {
        let token = shutdown.child_token();
        set.spawn(async move {
            loop {
                tokio::select! {
                    _ = token.cancelled() => break,
                    _ = do_work(i) => {}
                }
            }
        });
    }

    // Wait for shutdown
    shutdown.cancelled().await;

    // Abort remaining tasks
    set.abort_all();

    // Wait for all to finish (drain aborted tasks)
    while set.join_next().await.is_some() {}
}

async fn do_work(_worker: u32) {}
```

## Spawning with Context

```rust
use tokio::task::JoinSet;

let urls = vec!["https://example.com".to_string()];
let mut results: Vec<Option<Result<Data, Error>>> = urls.iter().map(|_| None).collect();
let mut set: JoinSet<(usize, Result<Data, Error>)> = JoinSet::new();

for (index, url) in urls.iter().enumerate() {
    let url = url.clone();
    set.spawn(async move {
        (index, fetch(&url).await)
    });
}

// Results include their index
while let Some(result) = set.join_next().await {
    if let Ok((index, data)) = result {
        results[index] = Some(data);
    }
}

struct Data;
struct Error;
async fn fetch(_url: &str) -> Result<Data, Error> { Ok(Data) }
```

## JoinSet vs join_all

| Feature | JoinSet | join_all |
|---------|---------|----------|
| Add tasks dynamically | Yes | No |
| Results as-completed | Yes | No (all at once) |
| Abort all on drop | Yes | No |
| Cancel individual | Yes | No |
| Memory efficient | Yes | Pre-allocates |

## See Also

- [async-join-parallel](./async-join-parallel.md) - Static concurrent futures
- [async-cancellation-token](./async-cancellation-token.md) - Cancellation patterns
- [async-try-join](./async-try-join.md) - Error handling in joins
