# num-cast-try-from

> Avoid `as` for narrowing casts; use `From` for widening and `TryFrom` for narrowing

## Why It Matters

The `as` cast silently truncates or wraps on narrowing (`300u32 as u8 == 44`)
and produces surprising results on float-to-integer conversion (finite values
outside the destination range saturate, while `NaN` becomes `0`). These
behaviors are easy to miss during review. Standard-library `From`
implementations are infallible and follow the convention that conversions do
not lose information; Rust cannot enforce that semantic contract for a custom
implementation. `TryFrom`/`TryInto` make a representability failure explicit.

## Bad

```rust
fn narrow(x: u32) -> u8 {
    x as u8  // silently truncates: 300 becomes 44
}

fn to_index(f: f64) -> usize {
    f as usize  // NaN becomes 0, negatives become 0, may truncate
}

fn widen(x: u8) -> u32 {
    x as u32  // works, but hides that this is always safe
}
```

## Good

```rust
use std::convert::TryFrom;

// widening: From<u8> for u32 is always lossless — won't compile if lossy
fn widen(x: u8) -> u32 {
    u32::from(x)
    // or: x.into()
}

// narrowing: TryFrom makes the failure case explicit
fn narrow(x: u32) -> Result<u8, <u8 as TryFrom<u32>>::Error> {
    u8::try_from(x)
    // or: x.try_into()
}

// float → integer: this API accepts only finite, integral in-range indices
fn float_to_index(f: f64, len: usize) -> Option<usize> {
    if !f.is_finite() || f < 0.0 || f.fract() != 0.0 {
        return None;
    }
    let index = f as usize;
    (index < len).then_some(index)
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::convert::TryFrom;

    #[test]
    fn widen_is_lossless() {
        assert_eq!(widen(255), 255u32);
    }

    #[test]
    fn narrow_errors_on_overflow() {
        assert!(narrow(300).is_err());
        assert_eq!(narrow(200), Ok(200u8));
    }

    #[test]
    fn float_to_index_rejects_nan_and_negative() {
        assert_eq!(float_to_index(f64::NAN, 10), None);
        assert_eq!(float_to_index(-1.0, 10), None);
        assert_eq!(float_to_index(3.9, 10), None);
        assert_eq!(float_to_index(3.0, 10), Some(3));
    }

    #[test]
    fn as_cast_truncation_footgun() {
        // demonstrating why `as` is dangerous for narrowing:
        let x: u32 = 300;
        assert_eq!(x as u8, 44);  // 300 % 256 == 44 — silently wrong
    }
}
```

## Key Points

- The standard library implements `From<A> for B` only for infallible
  conversions that preserve the source value. A custom `From` implementation
  must uphold the same convention; the compiler does not prove it.
- `TryFrom` returns `Result<T, TryFromIntError>` from the standard library — no external crates needed.
- Reserve `as` for a representation change whose exact Rust semantics are the
  contract and whose preconditions are checked. Prefer raw-pointer `.cast()`
  methods and provenance-aware APIs over integer or mutability round trips.
- When using `.try_into()`, the turbofish or type annotation is often needed to help inference: `let n: u8 = x.try_into()?;`

## See Also

- [conv-tryfrom-fallible](conv-tryfrom-fallible.md) - implement `TryFrom` for your own fallible conversions
- [num-overflow-explicit](num-overflow-explicit.md) - handle integer overflow explicitly with `checked_`/`saturating_`/`wrapping_`
