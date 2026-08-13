# test-observable-coverage

> Cover observable behavior and failure modes so refactors can proceed without implementation-shaped tests

## Why It Matters

A coverage percentage says which lines ran, not whether the contract was checked. Refactoring stays safe when tests exercise outputs, state transitions, errors, and externally visible side effects through supported APIs. That evidence also lets coding agents change internals without inventing assumptions about private branches.

Treat uncovered observable behavior as a product gap. Do not inflate the number by calling getters, mirroring match arms, or asserting private representation details.

## Bad

```rust
pub struct Counter {
    value: u64,
}

impl Counter {
    pub fn increment(&mut self) {
        self.value += 1;
    }
}

#[test]
fn counter_starts_at_zero() {
    let counter = Counter { value: 0 };
    assert_eq!(counter.value, 0); // Repeats construction; no behavior ran.
}
```

## Good

```rust
#[derive(Debug, Default, PartialEq)]
pub struct Counter {
    value: u64,
}

#[derive(Debug, PartialEq)]
pub enum CounterError {
    Overflow,
}

impl Counter {
    pub fn increment(&mut self) -> Result<u64, CounterError> {
        self.value = self.value.checked_add(1).ok_or(CounterError::Overflow)?;
        Ok(self.value)
    }
}

#[test]
fn increment_reports_the_new_value() {
    let mut counter = Counter::default();
    assert_eq!(counter.increment(), Ok(1));
    assert_eq!(counter.increment(), Ok(2));
}

#[test]
fn increment_rejects_overflow_without_changing_state() {
    let mut counter = Counter { value: u64::MAX };
    assert_eq!(counter.increment(), Err(CounterError::Overflow));
    assert_eq!(counter.value, u64::MAX);
}
```

## Coverage Policy

- Inventory public operations, branch outcomes, invariants, and named failure modes before choosing a percentage target.
- Measure line or branch coverage to find omissions, then add a test only when the uncovered behavior has an independent oracle.
- Exercise the public surface in integration tests when private access is not required.
- Keep coverage and mutation reports as diagnostic evidence; neither justifies tautological tests.
- Compile and run repository examples because they are user-facing behavior, not decorative snippets.

## See Also

- [test-no-tautology](test-no-tautology.md) - an independent oracle matters more than a covered line
- [test-integration-dir](test-integration-dir.md) - test public behavior from a consumer crate
- [test-proptest-properties](test-proptest-properties.md) - cover invariants over generated inputs
- [doc-examples-section](doc-examples-section.md) - keep runnable workflows under `examples/`
