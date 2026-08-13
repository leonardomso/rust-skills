# mem-take-replace

> Use `mem::take` / `mem::replace` to move a value out of a `&mut` without cloning

## Why It Matters

Rust prevents moving a field out through `&mut self` while leaving the
containing value partially uninitialized. `std::mem::take` replaces the field
with `T::default()` and returns the original; `std::mem::replace` installs an
explicit replacement. Both avoid requiring `T: Clone`. They may still move
inline bytes, and constructing the replacement may allocate or perform other
work according to `Default` or the supplied expression.

## Bad

```rust
struct Processor {
    items: Vec<String>,
}

impl Processor {
    // clones the entire Vec just to drain it — unnecessary allocation
    fn flush(&mut self) -> Vec<String> {
        let v = self.items.clone();
        self.items.clear();
        v
    }
}
```

## Good

```rust
use std::mem;

struct Processor {
    items: Vec<String>,
}

impl Processor {
    // moves the Vec out in one step, leaving an empty Vec behind
    fn flush(&mut self) -> Vec<String> {
        mem::take(&mut self.items)
    }
}
```

`mem::take` is equivalent to `mem::replace(&mut self.items, Vec::new())` but shorter when the replacement value is `Default::default()`.

## State-Machine Transition with `mem::replace`

A common pattern in state machines and `Future::poll` implementations is replacing a field with an explicit next state rather than the default:

```rust
use std::mem;

#[derive(Debug)]
enum State {
    Idle,
    Loading { url: String },
    Done { body: String },
}

impl Default for State {
    fn default() -> Self {
        State::Idle
    }
}

struct Machine {
    state: State,
}

impl Machine {
    fn start_load(&mut self, url: String) {
        // replace Idle with Loading, getting Idle back (discarded here)
        let _prev = mem::replace(&mut self.state, State::Loading { url });
    }

    fn complete(&mut self, body: String) {
        // replace Loading with Done; capture old state if needed for logging
        match mem::replace(&mut self.state, State::Done { body }) {
            State::Loading { url } => {
                println!("finished loading {url}");
            }
            other => {
                // unexpected transition — put it back or handle the error
                self.state = other;
            }
        }
    }
}
```

## Do Not Hide Fallible Flushes in `Drop`

`mem::take` can move a field out inside `Drop`, but a destructor cannot return
an I/O error and may run during unwinding. Provide an explicit `finish` or
`close` operation for required persistence; reserve `Drop` for best-effort,
non-blocking cleanup.

```rust
use std::mem;

struct FileWriter {
    buffer: Vec<u8>,
    // imagine a real file handle here
}

impl Drop for FileWriter {
    fn drop(&mut self) {
        let data = mem::take(&mut self.buffer);
        // Best-effort cleanup only. Required writes happen in finish().
        let _ = data;
    }
}
```

## Key Points

- `mem::take` requires `T: Default`. If `T` has no meaningful default, use `mem::replace` with an explicit sentinel value (e.g., an `Option<T>` field — `mem::take` an `Option<T>` yields `None`, which is often exactly right).
- Neither function clones the old value. Code generation and allocation
  behavior depend on `T` and on how the replacement is constructed.
- `Option<T>` is a natural pairing: keep expensive values in `Option<T>` and call `self.field.take()` (the `Option::take` method, same idea) to move ownership out cleanly.

## See Also

- [own-move-large](own-move-large.md) - move large data instead of cloning
- [mem-clone-from](mem-clone-from.md) - use `clone_from()` to reuse allocations
- [own-borrow-over-clone](own-borrow-over-clone.md) - prefer `&T` borrowing over `.clone()`
