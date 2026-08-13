# err-catch-unwind-boundary

> Use `catch_unwind` only at a task, FFI, or process isolation edge, and pair it with a restart policy

## Why It Matters

A panic means "this program should stop," not "throw to the caller." Catching it in the middle of a library leaves mutexes poisoned, thread-locals half-updated, and invariants that safe code assumed were impossible. `catch_unwind` belongs at the rim of a request worker or an FFI callback so *other* work can finish — then the process or task is recycled. The calling application may compile with `panic = "abort"`, in which case no unwind occurs and `catch_unwind` cannot run; isolation and restart must still work at the process boundary. `clippy::exit` does not cover this; the review check is: if you catch, you must say what restarts.

## Bad

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};

pub fn parse_or_keep_going(input: &str) -> i32 {
    catch_unwind(AssertUnwindSafe(|| input.parse::<i32>().expect("digits")))
        .unwrap_or(0)
}
```

## Good

```rust
use std::panic::{catch_unwind, AssertUnwindSafe};

pub struct RequestOutcome {
    pub ok: bool,
    pub restart_worker: bool,
}

pub fn handle_one_request(work: impl FnOnce() + std::panic::UnwindSafe) -> RequestOutcome {
    match catch_unwind(AssertUnwindSafe(work)) {
        Ok(()) => RequestOutcome {
            ok: true,
            restart_worker: false,
        },
        Err(_) => RequestOutcome {
            ok: false,
            restart_worker: true,
        },
    }
}

fn main() {
    let clean = handle_one_request(|| {});
    assert!(clean.ok && !clean.restart_worker);
    let panicked = handle_one_request(|| panic!("handler failed"));
    assert!(!panicked.ok && panicked.restart_worker);
}
```

## See Also

- [err-result-over-panic](err-result-over-panic.md) - recoverable failures are `Result`, not a caught panic
- [err-expect-bugs-only](err-expect-bugs-only.md) - a panic still means a bug; catching it does not make it expected
- [anti-panic-expected](anti-panic-expected.md) - do not design APIs that require the caller to unwind
