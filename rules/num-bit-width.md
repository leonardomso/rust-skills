# num-bit-width

> Use integer `bit_width` / `highest_one` / `isolate_*_one` instead of hand-rolled bit math

## Why It Matters

Counting bits with `leading_zeros` and isolating a set bit with `n & n.wrapping_neg()` are easy to get slightly wrong — especially at zero, where `leading_zeros` is the full width and a mask must not invent a bit. Rust 1.97 added named methods on every integer primitive (and `NonZero`) that return the bit width, the index of the highest or lowest set bit, or a value with only that bit kept. The standard library documents the zero cases; call the method instead of re-deriving it.

## Bad

```rust
fn needed_bits(n: u32) -> u32 {
    if n == 0 {
        0
    } else {
        32 - n.leading_zeros()  // width minus leading zeros; wrong the moment you forget the n == 0 arm
    }
}

fn highest_set_bit(n: u32) -> Option<u32> {
    if n == 0 {
        None
    } else {
        Some(31 - n.leading_zeros())  // 31 is width-1 — off-by-one bait
    }
}

fn lowest_power_of_two(n: u32) -> u32 {
    n & n.wrapping_neg()  // classic lowest-set-bit mask; yields 0 for 0 by accident, not by contract
}
```

## Good

```rust
fn needed_bits(n: u32) -> u32 {
    n.bit_width()  // 0 for 0, documented — no manual zero arm
}

fn highest_set_bit(n: u32) -> Option<u32> {
    n.highest_one()  // Option: the zero case is in the type
}

fn lowest_set_bit(n: u32) -> Option<u32> {
    n.lowest_one()
}

fn lowest_power_of_two(n: u32) -> u32 {
    n.isolate_lowest_one()  // 0 for 0, by contract
}

fn highest_power_of_two(n: u32) -> u32 {
    n.isolate_highest_one()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bit_width_is_zero_for_zero() {
        assert_eq!(needed_bits(0), 0);
        assert_eq!(needed_bits(0b111), 3);
        assert_eq!(needed_bits(0b1110), 4);
    }

    #[test]
    fn highest_one_is_none_for_zero() {
        assert_eq!(highest_set_bit(0), None);
        assert_eq!(highest_set_bit(0b1_0000), Some(4));
        assert_eq!(lowest_set_bit(0b1_0000), Some(4));
        assert_eq!(lowest_set_bit(0b1_1111), Some(0));
    }

    #[test]
    fn isolate_keeps_a_single_bit() {
        let n = 0b_01100100u32;
        assert_eq!(lowest_power_of_two(n), 0b_00000100);
        assert_eq!(highest_power_of_two(n), 0b_01000000);
        assert_eq!(lowest_power_of_two(0), 0);
    }
}
```

## Key Points

- `bit_width` is the minimum number of bits needed to represent the value, and is `0` when the value is `0`.
- `highest_one` / `lowest_one` return `Option<u32>` indexes (or a bare `u32` on `NonZero`, where zero is impossible).
- `isolate_highest_one` / `isolate_lowest_one` return a value with only that bit set, or `0` when the input is `0`.
- Prefer these over `32 - leading_zeros()` or `n & n.wrapping_neg()` even when the hand-rolled form is correct — the named methods make the zero case obvious to the next reader.

## See Also

- [num-overflow-explicit](num-overflow-explicit.md) - name overflow intent with `checked_`/`saturating_`/`wrapping_`
- [num-cast-try-from](num-cast-try-from.md) - avoid `as` for narrowing integer conversions
- [mem-smaller-integers](mem-smaller-integers.md) - pick the smallest integer type that fits
