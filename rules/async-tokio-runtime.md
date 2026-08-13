# async-tokio-runtime

> Own one observable Tokio runtime and isolate blocking or CPU work behind bounded admission

## Why It Matters

A Tokio runtime owns executor workers, I/O/time drivers, a blocking pool, and shutdown behavior. Worker count is not a throughput knob to raise speculatively: async I/O should spend little time blocking workers, while sustained CPU work can starve timers and sockets regardless of worker count. Use one long-lived runtime per process unless isolation evidence justifies more. Put blocking calls and CPU work behind explicit admission, deadlines, and supervised shutdown.

## Bad

```rust
#[tokio::main]
async fn main() {
    for input in untrusted_inputs().await {
        tokio::task::spawn_blocking(move || cpu_transform(input));
    }
}
```

`spawn_blocking` has a large configurable thread ceiling and queues work after it is reached. Submitting one job per unbounded input moves overload into a hidden queue and those jobs cannot generally be cancelled once running.

## Good

```rust
use std::{num::NonZeroUsize, sync::Arc};
use tokio::{runtime::{Builder, Runtime}, sync::Semaphore};

struct BlockingAdmission {
    permits: Arc<Semaphore>,
}

impl BlockingAdmission {
    fn new(limit: NonZeroUsize) -> Self {
        Self {
            permits: Arc::new(Semaphore::new(limit.get())),
        }
    }

    async fn run<F, T>(&self, work: F) -> Result<T, WorkError>
    where
        F: FnOnce() -> Result<T, WorkError> + Send + 'static,
        T: Send + 'static,
    {
        let permit = Arc::clone(&self.permits)
            .acquire_owned()
            .await
            .map_err(|_| WorkError::ShuttingDown)?;
        tokio::task::spawn_blocking(move || {
            let _permit = permit;
            work()
        })
        .await
        .map_err(WorkError::Join)?
    }
}

fn service_runtime(worker_threads: NonZeroUsize) -> std::io::Result<Runtime> {
    Builder::new_multi_thread()
        .worker_threads(worker_threads.get())
        .thread_name("service-worker")
        .enable_all()
        .build()
}
```

The semaphore limits queued-plus-running work admitted through this adapter. Every production caller must use the adapter; direct `spawn_blocking` calls bypass the limit and should be denied by architecture or review. For sustained parallel CPU computation, prefer a fixed compute pool with equivalent bounded admission instead of consuming Tokio's general blocking pool.

## Runtime Construction

```rust
use std::num::NonZeroUsize;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let workers = std::thread::available_parallelism()?
        .max(NonZeroUsize::new(2).expect("literal is non-zero"));
    let runtime = service_runtime(workers)?;
    runtime.block_on(async_main())?;
    runtime.shutdown_timeout(std::time::Duration::from_secs(5));
    Ok(())
}
```

`available_parallelism` is an estimate of available parallelism for a sustained workload and may be stale, limited, or affected by platform/container behavior. It is a starting value, not proof of an optimal worker count. Use checked/capped configuration, benchmark under the deployment CPU quota, and observe worker busy time and scheduling latency.

`#[tokio::main]` is concise when default runtime policy and implicit shutdown are acceptable. A builder makes enabled drivers, thread naming, sizing, construction failure, and shutdown ownership explicit. Do not create a runtime per request or call `Runtime::block_on` from asynchronous code.

## Current-Thread Runtime

A current-thread runtime is useful for thread-affine `!Send` futures, deterministic small tools, and selected tests. It does not make blocking calls cheaper: one blocking operation stops every task on that runtime. Spawned tasks execute concurrently but not in CPU parallel. A `LocalSet` supplies local task scheduling when required; document the thread-affinity boundary.

## Worker And Blocking Limits

- Keep async executor workers near the measured CPU/quota baseline. Oversubscribing workers can increase scheduling and cache contention and does not turn blocking APIs non-blocking.
- `max_blocking_threads` is a ceiling, not an admission queue bound. Use a semaphore/queue before scheduling work.
- Tokio's blocking queue can grow; constrain input count and bytes before acquiring admission.
- Avoid setting a small global blocking ceiling as the only protection: filesystem/DNS/runtime internals and unrelated adapters may share the pool and deadlock or starve each other.
- Record runtime configuration with the artifact and re-measure after Tokio, target, quota, or workload changes.

## Multiple Runtimes

Multiple runtimes add thread pools, timers, I/O drivers, blocking pools, cross-runtime handle lifetimes, and shutdown order. Prefer one runtime plus isolated compute/blocking components. If a separately owned runtime is necessary, prevent resources and futures from outliving their originating runtime, avoid blocking one runtime while waiting on another, and integration-test startup, cross-boundary cancellation, and reverse-order shutdown.

## Supervision And Shutdown

Runtime drop can wait indefinitely for blocking work; `shutdown_timeout` stops waiting after the grace period but does not terminate already running threads/work. A production shutdown sequence should:

1. stop external admission;
2. cancel owned async tasks;
3. close bounded queues and wait for a defined drain period;
4. stop compute/worker components;
5. call bounded runtime shutdown;
6. exit/restart the process if a hostile blocking operation exceeds policy.

Use `JoinSet` or another owner for spawned tasks. Do not detach results silently. Preserve panics and typed failures at the supervision boundary.

## Runtime Tests

```rust
#[tokio::test(flavor = "multi_thread", worker_threads = 2)]
async fn cancellation_releases_admission() {
    let admission = BlockingAdmission::new(
        NonZeroUsize::new(1).expect("literal is non-zero"),
    );
    // Exercise queue saturation, cancellation before admission, worker error,
    // and bounded shutdown with a controllable fake work function.
    drop(admission);
}
```

Use paused Tokio time for timer logic where supported, Loom for small instrumented synchronization models, and real multi-thread/load tests for scheduler behavior. A one-task happy-path test does not verify runtime sizing or overload policy.

## Observability

Track admitted/queued blocking work, permit wait, execution latency, cancellations, panics, worker busy duration, scheduler latency, task counts, and shutdown drain time with bounded-cardinality labels. Alert on the product SLO and saturation signals, not on a generic thread-count threshold.

## See Also

- [async-spawn-blocking](./async-spawn-blocking.md) - bound blocking and CPU admission
- [async-bounded-channel](async-bounded-channel.md) - explicit queue backpressure
- [async-joinset-structured](./async-joinset-structured.md) - supervise spawned tasks
- [async-no-lock-await](./async-no-lock-await.md) - keep lock scope explicit
