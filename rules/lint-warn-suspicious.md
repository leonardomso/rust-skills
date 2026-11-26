# lint-warn-suspicious

> Enable clippy::suspicious for likely bugs

## Why It Matters

The `clippy::suspicious` lint group catches code patterns that are syntactically valid but almost always wrong. These are potential bugs that deserve investigation. Enabling this group as a warning helps catch mistakes early.

## Configuration

```rust
// In lib.rs or main.rs
#![warn(clippy::suspicious)]
```

Or in `Cargo.toml`:

```toml
[lints.clippy]
suspicious = "warn"
```

Or in `clippy.toml`:

```toml
warn = ["clippy::suspicious"]
```

## What It Catches

### Suspicious Operators

```rust
// suspicious_arithmetic_impl: `-` inside an `Add` impl
impl Add for P {
    type Output = P;
    fn add(self, rhs: P) -> P { P(self.0 - rhs.0) }  // WARN
}

// suspicious_assignment_formatting: `=-` looks like `-=`
a =- b;  // WARN: this is `a = -b`
```

### Suspicious Control Flow and Locks

```rust
// await_holding_lock: a MutexGuard lives across an await
async fn work(m: &Mutex<i32>) {
    let g = m.lock().unwrap();  // WARN: held across an await point
    other().await;
    drop(g);
}
```

### Suspicious Types and Bindings

```rust
// mutable_key_type: key with interior mutability in a hash set or map
let s: HashSet<KeyWithCell> = HashSet::new();  // WARN

// redundant_locals: rebinding a variable to itself
let x = x;  // WARN

// suspicious_map: map used only for its side effects
let n = items.iter().map(|v| { println!("{v}"); v }).count();  // WARN, use inspect
```

## Notable Lints in This Group

| Lint | Description |
|------|-------------|
| `suspicious_arithmetic_impl` | Unusual operator in arithmetic trait |
| `suspicious_assignment_formatting` | Looks like typo in assignment |
| `suspicious_else_formatting` | Else on wrong line |
| `suspicious_map` | Map with side effects |
| `suspicious_op_assign_impl` | Unusual op-assign implementation |
| `suspicious_unary_op_formatting` | Confusing unary operator spacing |
| `await_holding_lock` | Lock guard held across `.await` |
| `mutable_key_type` | Hash key with interior mutability |

`suspicious_splitn`, `modulo_one`, and `almost_swapped` look like they belong here but are in `clippy::correctness`.

## When to Allow

Rarely. If you need to suppress, document why:

```rust
#[allow(clippy::suspicious_arithmetic_impl)]
impl Mul for Matrix {
    // Custom matrix multiplication using + for reduction step
    fn mul(self, rhs: Self) -> Self::Output {
        // ...
    }
}
```

## See Also

- [lint-deny-correctness](./lint-deny-correctness.md) - Deny definite bugs
- [lint-warn-style](./lint-warn-style.md) - Style warnings
- [lint-warn-complexity](./lint-warn-complexity.md) - Complexity warnings
