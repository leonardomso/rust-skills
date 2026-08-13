# const-generics

> Parameterize over values with const generics `<const N: usize>`

## Why It Matters

Const generics let one source definition work with arrays or inline buffers of
different compile-time sizes without a trait object or a separate runtime
capacity field. Each used value participates in monomorphization, which can
remove runtime indirection but can also increase compile time and code size.
Use them when the value is part of the type-level contract, not merely to move
a runtime configuration knob into the type system.

## Bad

```rust
// works only for one fixed size — must be copy-pasted per size
fn sum_4(arr: [i32; 4]) -> i32 {
    arr.iter().sum()
}

fn sum_8(arr: [i32; 8]) -> i32 {
    arr.iter().sum()
}

// Carries a redundant runtime capacity and uses separately allocated storage.
struct Buffer {
    data: Vec<u8>,
    capacity: usize,
}
```

## Good

```rust
// one generic function works for any array size; N is inferred from the argument
fn sum<const N: usize>(arr: [i32; N]) -> i32 {
    arr.iter().sum()
}

let total = sum([1, 2, 3, 4]);       // N = 4, inferred
let total8 = sum([0i32; 8]);         // N = 8, inferred

// Inline buffer parameterized by capacity; len remains runtime state.
struct Buffer<const N: usize> {
    data: [u8; N],
    len: usize,
}

impl<const N: usize> Buffer<N> {
    const fn new() -> Self {
        Self { data: [0u8; N], len: 0 }
    }

    fn push(&mut self, byte: u8) -> bool {
        if self.len < N {
            self.data[self.len] = byte;
            self.len += 1;
            true
        } else {
            false
        }
    }

    fn as_slice(&self) -> &[u8] {
        &self.data[..self.len]
    }
}

// capacity is part of the type — mismatches caught at compile time
let mut small: Buffer<8> = Buffer::new();
let mut large: Buffer<1024> = Buffer::new();
small.push(42);
large.push(99);

// const generic used as an array length computed from another const
const BLOCK: usize = 16;
fn xor_block<const N: usize>(a: [u8; N], b: [u8; N]) -> [u8; N] {
    let mut out = [0u8; N];
    for i in 0..N {
        out[i] = a[i] ^ b[i];
    }
    out
}
let result = xor_block([0u8; BLOCK], [0xFF; BLOCK]);
```

## Notes

Rust 1.65+ stabilized const generic defaults
(`struct Buf<const N: usize = 64>`). Const generic parameter types currently
include integers, `bool`, and `char`; floating-point and user-defined parameter
types are not stable. Inference often supplies `N` from an argument, but public
types with different values remain different, non-interchangeable types.

## See Also

- [const-fn](const-fn.md) - mark functions `const fn` so they can be called in const contexts
- [mem-assert-type-size](mem-assert-type-size.md) - assert type sizes to catch layout regressions
