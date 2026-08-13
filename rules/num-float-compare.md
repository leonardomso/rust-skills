# num-float-compare

> Don't compare floats with `==`; use a tolerance, and `total_cmp` for ordering

## Why It Matters

Floating-point arithmetic rounds to a finite binary representation:
`0.1 + 0.2 == 0.3` evaluates to `false` for Rust `f64`. Additionally,
`NaN != NaN`, so `partial_cmp` returns `None` when either operand is NaN; an
example that unwraps that result panics. Choose a domain-specific absolute and
relative tolerance for approximate equality, and use `f64::total_cmp` when a
deterministic total order over every bit pattern is the contract.

## Bad

```rust
fn is_unit_length(x: f64, y: f64) -> bool {
    (x * x + y * y).sqrt() == 1.0  // almost always false due to rounding
}

fn sort_scores(scores: &mut Vec<f64>) {
    scores.sort_by(|a, b| a.partial_cmp(b).unwrap());
    // panics (unwrap on None) if any score is NaN
}
```

## Good

```rust
// approximate equality with an absolute epsilon
fn approx_eq(a: f64, b: f64, epsilon: f64) -> bool {
    assert!(epsilon >= 0.0);
    (a - b).abs() <= epsilon
}

fn is_unit_length(x: f64, y: f64) -> bool {
    approx_eq((x * x + y * y).sqrt(), 1.0, 1e-9)
}

// IEEE totalOrder-compatible ordering, including signed NaN values.
fn sort_scores(scores: &mut Vec<f64>) {
    scores.sort_by(|a, b| a.total_cmp(b));
}

// direct NaN check when needed
fn safe_reciprocal(x: f64) -> Option<f64> {
    if x == 0.0 || x.is_nan() {
        None
    } else {
        Some(1.0 / x)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn float_addition_is_not_exact() {
        assert_ne!(0.1_f64 + 0.2, 0.3);  // IEEE 754 rounding
        assert!(approx_eq(0.1 + 0.2, 0.3, 1e-10));
    }

    #[test]
    fn nan_is_not_equal_to_itself() {
        let nan = f64::NAN;
        assert_ne!(nan, nan);  // NaN != NaN by IEEE 754
    }

    #[test]
    fn total_cmp_handles_nan() {
        let mut v = vec![3.0_f64, f64::NAN, 1.0, f64::NAN, 2.0];
        sort_scores(&mut v);
        // NaN values sort to the end; finite values are in order
        assert_eq!(&v[..3], &[1.0, 2.0, 3.0]);
        assert!(v[3].is_nan());
        assert!(v[4].is_nan());
    }

    #[test]
    fn unit_length_uses_tolerance() {
        assert!(is_unit_length(1.0, 0.0));
        assert!(is_unit_length(0.6, 0.8));  // 3-4-5 right triangle scaled
    }
}
```

## Key Points

- **Tolerance choice**: an absolute tolerance alone is usually inappropriate
  across many magnitudes. A common finite-value test accepts
  `diff <= absolute_tolerance` or
  `diff <= relative_tolerance * max(abs(a), abs(b))`; define explicit behavior
  for zero, infinities, and NaNs.
- **`f64::total_cmp`** defines a strict total order: `-NaN < -∞ < … < -0.0 < +0.0 < … < +∞ < NaN`. It never panics and is available on `f32` and `f64`.
- **`is_nan` / `is_infinite` / `is_finite`**: use these predicates before arithmetic on untrusted floats.
- **Equality on `f32`/`f64` with `==`** follows IEEE numeric equality:
  signed zeros compare equal and every NaN compares unequal. For bit-pattern
  equality compare `to_bits()`; for domain equality define finite/NaN/zero
  policy explicitly.

## See Also

- [num-overflow-explicit](num-overflow-explicit.md) - handle integer overflow explicitly
- [trait-ord-consistent](trait-ord-consistent.md) - keep ordered collection keys on one total order
