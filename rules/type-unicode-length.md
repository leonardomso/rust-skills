# type-unicode-length

> Define whether text limits count bytes, scalar values, or grapheme clusters

## Why It Matters

`str::len()` counts UTF-8 bytes, `chars().count()` counts Unicode scalar
values, and user-perceived characters may span several scalar values. An
unspecified “256-character” limit behaves differently across languages,
scripts, storage layers, and clients. Choose the unit from the product
contract, name it, and enforce the same unit at every boundary.

## Bad

```rust
pub fn valid_display_name(value: &str) -> bool {
    value.len() <= 64
}
```

This implements a 64-byte limit while presenting it as a character limit.

## Good

```rust
pub const MAX_NAME_BYTES: usize = 256;

pub fn valid_storage_name(value: &str) -> bool {
    !value.trim().is_empty() && value.len() <= MAX_NAME_BYTES
}

fn main() {
    assert!(valid_storage_name("Zoë"));
    assert!(!valid_storage_name("   "));
}
```

If the interface promises user-perceived characters, use a maintained Unicode
segmentation implementation and call the limit `MAX_NAME_GRAPHEMES`. Do not
hand-roll grapheme boundaries.

## Contract

- State the unit in configuration, error messages, documentation, and tests.
- Apply a byte limit before expensive parsing or normalization to cap resource
  use.
- Use domain evidence rather than culturally narrow allowlists for names and
  other human text.
- Escaping is output-context-specific. Rejecting punctuation is not a
  substitute for parameterized SQL, HTML escaping, or safe header APIs.
- Test composed/decomposed text, emoji sequences, non-Latin scripts, leading
  and trailing whitespace, empty input, and exact boundaries.

## See Also

- [type-newtype-validated](type-newtype-validated.md) - preserve the validated text invariant
- [api-parse-dont-validate](api-parse-dont-validate.md) - parse once into the domain type
- [num-overflow-explicit](num-overflow-explicit.md) - make size arithmetic overflow behavior explicit
- [test-proptest-properties](test-proptest-properties.md) - generate Unicode boundary cases
- [api-extract-or-reject](api-extract-or-reject.md) - reject oversized input before effects
