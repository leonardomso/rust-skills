# const-named-magic

> Give production magic numbers a named `const` and a comment that says why that value

## Why It Matters

Six hours is obviously half a day; it is not obvious why a worker must renew a lease that soon, or what breaks if someone halves it. Give the number a named constant plus a note covering the choice, the side effects of changing it, and any external system that shares the value. Inline literals hide that contract from rustdoc and from every other call site.

## Bad

```rust
use std::time::Duration;

fn hold_lease(window: Duration) -> Duration {
    window
}

fn main() {
    // Bare product: a reader cannot tell this is a lease, or who else
    // shares the number.
    let _ = hold_lease(Duration::from_secs(6 * 60 * 60));
}
```

## Good

```rust
use std::time::Duration;

/// How long a worker may keep a job lease before renewing.
///
/// Matches the queue broker's `lease-ttl` (six hours). A shorter window
/// makes healthy workers lose jobs mid-run; a longer one delays failover
/// after a crash.
const LEASE_RENEWAL_WINDOW: Duration = Duration::from_secs(6 * 60 * 60);

fn hold_lease(window: Duration) -> Duration {
    window
}

fn main() {
    let _ = hold_lease(LEASE_RENEWAL_WINDOW);
}
```

## See Also

- [const-vs-static](const-vs-static.md) - use `const` for an inlined number, `static` only when you need an address
- [name-consts-screaming](name-consts-screaming.md) - `SCREAMING_SNAKE_CASE` marks the value as a policy knob
- [doc-all-public](doc-all-public.md) - the comment belongs on the constant, not only at the use site
