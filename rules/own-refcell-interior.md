# own-refcell-interior

> Use `RefCell<T>` only for deliberate single-threaded interior mutability

## Why It Matters

`RefCell<T>` enforces Rust's shared/exclusive borrowing rules at runtime and permits mutation through `&self` on one thread. A conflicting `borrow`/`borrow_mut` panics; `try_borrow` reports the conflict. Choose it only when interior mutability is the actual API contract. Prefer ordinary `&mut self`, `Cell`, `OnceCell`, or an ownership redesign when they express the invariant statically.

## Bad

```rust
use std::cell::RefCell;

fn notify(cell: &RefCell<State>, callback: impl FnOnce()) {
    let mut state = cell.borrow_mut();
    state.started = true;
    callback(); // Reentrant code can borrow cell again and panic.
    state.finished = true;
}
```

The dynamic borrow crosses an arbitrary callback. Nothing in the type prevents the callback from reaching the same cell.

## Good

```rust
use std::cell::{BorrowError, BorrowMutError, RefCell};
use std::collections::HashMap;

#[derive(Debug)]
enum CacheError {
    ReadConflict(BorrowError),
    WriteConflict(BorrowMutError),
    Compute(ComputeError),
}

struct Cache {
    data: RefCell<HashMap<String, String>>,
}

impl Cache {
    fn new() -> Self {
        Self {
            data: RefCell::new(HashMap::new()),
        }
    }

    fn get_or_compute(&self, key: &str) -> Result<String, CacheError> {
        if let Some(value) = self
            .data
            .try_borrow()
            .map_err(CacheError::ReadConflict)?
            .get(key)
            .cloned()
        {
            return Ok(value);
        }

        // Do potentially reentrant or fallible work without a RefCell borrow.
        // Duplicate computation is an explicit acceptable policy here.
        let computed = expensive_compute(key).map_err(CacheError::Compute)?;
        self.data
            .try_borrow_mut()
            .map_err(CacheError::WriteConflict)?
            .entry(key.to_owned())
            .or_insert_with(|| computed.clone());
        Ok(computed)
    }
}
```

Returning an owned value keeps the dynamic borrow out of the caller. If the API returns `Ref<'_, T>`, document that callers cannot mutably borrow the cell until the guard is dropped.

## Shared Single-Threaded Ownership

```rust
use std::cell::RefCell;
use std::rc::Rc;

type SharedState = Rc<RefCell<AppState>>;

fn increment(state: &SharedState) -> Result<(), BorrowMutError> {
    let mut state = state.try_borrow_mut()?;
    state.count = state.count.saturating_add(1);
    Ok(())
}
```

`Rc<RefCell<T>>` remains `!Send` and `!Sync`; cloning the `Rc` does not make it safe to move across threads. Keep the ownership graph acyclic with `Weak` back-references, and avoid long-lived borrows across event-loop callbacks.

## Panic Versus Typed Conflict

```rust
let cell = RefCell::new(5);
let read = cell.borrow();
assert!(cell.try_borrow_mut().is_err());
drop(read);
assert!(cell.try_borrow_mut().is_ok());
```

A conflict indicates a design or reentrancy condition, not resource contention: waiting cannot make progress while the current call stack holds the guard. Use `borrow` only when a local invariant proves no conflict; use `try_borrow` across callbacks, plugins, or other reentrant boundaries.

## `Cell` For Copy State

```rust
use std::cell::Cell;

struct Counter {
    count: Cell<u32>,
}

impl Counter {
    fn bump(&self) {
        self.count.set(self.count.get().saturating_add(1));
    }
}
```

`Cell` exposes value replacement rather than references and has no dynamic borrow flag. It is still single-threaded (`!Sync`). Choose an explicit overflow policy instead of relying on debug/release arithmetic differences.

## See Also

- [own-rc-single-thread](./own-rc-single-thread.md) - shared ownership that cannot cross threads
- [own-mutex-interior](./own-mutex-interior.md) - synchronized mutation across threads
- [conc-thread-local](./conc-thread-local.md) - per-thread state and reentrancy
- [own-cow-conditional](own-cow-conditional.md) - ownership without interior mutation
