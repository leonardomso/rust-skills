# test-no-tautological

> Test properties and independently known values, not a restatement of the code under test

## Why It Matters

A test that computes its expected value with the same logic as the implementation, or that asserts a constant equals its own literal, passes by construction. It catches no bugs, but it fails whenever the code is legitimately changed, which adds noise to every later edit. Assert something that could be wrong: a hand-computed example, a relationship between values, or an invariant that must always hold.

## Bad

```rust
const CHECKPOINTS: [u32; 4] = [0, 90, 180, 270];

pub fn discounted(cents: u64) -> u64 {
    cents - cents * 10 / 100
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn checkpoints_are_correct() {
        // Repeats the definition
        assert_eq!(CHECKPOINTS, [0, 90, 180, 270]);
    }

    #[test]
    fn discount_applied() {
        // Mirrors the implementation; a wrong formula passes too
        assert_eq!(discounted(1000), 1000 - 1000 * 10 / 100);
    }
}
```

## Good

```rust
const CHECKPOINTS: [u32; 4] = [0, 90, 180, 270];

pub fn discounted(cents: u64) -> u64 {
    cents - cents * 10 / 100
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn checkpoints_are_evenly_spaced_and_within_a_turn() {
        let steps: Vec<u32> = CHECKPOINTS.windows(2).map(|w| w[1] - w[0]).collect();
        assert!(steps.windows(2).all(|pair| pair[0] == pair[1]));
        assert!(CHECKPOINTS.iter().all(|&degrees| degrees < 360));
    }

    #[test]
    fn ten_percent_off_a_ten_dollar_item() {
        // A value worked out by hand, independent of the code
        assert_eq!(discounted(1000), 900);
    }

    #[test]
    fn discount_never_increases_the_price() {
        for cents in [0, 1, 99, 1000, u32::MAX as u64] {
            assert!(discounted(cents) <= cents);
        }
    }
}
```

## See Also

- [test-descriptive-names](test-descriptive-names.md) - Name the behavior being checked
- [test-proptest-properties](test-proptest-properties.md) - Generate inputs to check properties
- [test-arrange-act-assert](test-arrange-act-assert.md) - Keep tests structured
- Source: Microsoft Pragmatic Rust Guidelines, M-TAUTOLOGICAL-TESTS
