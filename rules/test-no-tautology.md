# test-no-tautology

> Assert a property or observable outcome, not a constant restated from the source

## Why It Matters

A test that copies `[1, 2, 4, 8]` into both the production item and the assertion cannot fail unless someone edits only one side. Those tests satisfy a coverage counter and then rot. Reject tautological tests: check a property the values must keep (spacing, monotonicity, a parse round-trip) or drop the test.

## Bad

```rust
const RETRY_BACKOFF_SECS: [u32; 4] = [1, 2, 4, 8];

#[test]
fn backoff_matches_the_literal() {
    assert_eq!(RETRY_BACKOFF_SECS, [1, 2, 4, 8]);
}
```

## Good

```rust
const RETRY_BACKOFF_SECS: [u32; 4] = [1, 2, 4, 8];

fn backoff_doubles(points: &[u32]) -> bool {
    points.windows(2).all(|pair| pair[1] == pair[0] * 2)
}

fn main() {
    assert!(backoff_doubles(&RETRY_BACKOFF_SECS));
    assert_eq!(RETRY_BACKOFF_SECS[0], 1);
    assert_eq!(*RETRY_BACKOFF_SECS.last().unwrap(), 8);
}
```

## Mutation Testing

A mutation tool may generate a mutant for a constant or definition whose
literal value has no independent behavioral oracle. Do not add a
copy-the-literal assertion merely to kill that mutant. Mark the mutant as
inapplicable in the mutation tool and keep a property test only when the
property matters to users.

## See Also

- [test-descriptive-names](test-descriptive-names.md) - a name that states the property makes a tautology obvious
- [test-proptest-properties](test-proptest-properties.md) - generate inputs instead of restating one fixture
- [test-arrange-act-assert](test-arrange-act-assert.md) - keep the expected value in Assert, not copied into Arrange
