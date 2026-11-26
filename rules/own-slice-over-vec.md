# own-slice-over-vec

> Take `&[T]`, `&str`, and `&Path` in parameters, not `&Vec<T>`, `&String`, or `&PathBuf`

## Why It Matters

`&[T]` accepts slices from arrays, vectors, and sub-ranges; `&str` accepts `String`, literals, and substrings. `&Vec<T>` and `&String` accept only the owned type, which forces callers to allocate (`arr.to_vec()`, `"x".to_string()`) just to call you. Deref coercion turns `&Vec<T>` into `&[T]` and `&String` into `&str` for free, so the slice form costs callers nothing.

## Bad

```rust
// Only accepts &Vec
fn sum(numbers: &Vec<i32>) -> i32 {
    numbers.iter().sum()
}

// Only accepts &String
fn greet(name: &String) {
    println!("Hello, {}", name);
}

// Same for &mut
fn double(numbers: &mut Vec<i32>) {
    for n in numbers.iter_mut() {
        *n *= 2;
    }
}

// Callers must allocate or are rejected:
// sum(&[1, 2, 3]);       // ERROR: expected &Vec<i32>
// greet("world");        // ERROR: expected &String
```

## Good

```rust
use std::path::{Path, PathBuf};

fn sum(numbers: &[i32]) -> i32 {
    numbers.iter().sum()
}

fn greet(name: &str) {
    println!("Hello, {}", name);
}

fn double(numbers: &mut [i32]) {
    for n in numbers.iter_mut() {
        *n *= 2;
    }
}

// Paths: &Path accepts &PathBuf via deref coercion
fn read_config(path: &Path) -> usize {
    path.as_os_str().len()
}

fn main() {
    let vec = vec![1, 2, 3];
    let arr = [4, 5, 6];
    sum(&vec);          // &Vec<i32> coerces to &[i32]
    sum(&arr);          // array
    sum(&vec[0..2]);    // sub-slice

    let string = String::from("Alice");
    greet(&string);     // &String coerces to &str
    greet("Bob");       // literal

    let mut nums = vec![1, 2, 3];
    double(&mut nums);

    read_config(&PathBuf::from("app.toml"));
    read_config(Path::new("app.toml"));
}
```

The same swap applies to other owned wrappers:

| Instead of | Take |
|------------|------|
| `&Vec<T>` | `&[T]` |
| `&String` | `&str` |
| `&PathBuf` | `&Path` |
| `&OsString` | `&OsStr` |
| `&Box<T>` | `&T` |

Clippy's `ptr_arg` lint (on by default) flags these:

```toml
[lints.clippy]
ptr_arg = "warn"
```

## Generic Inputs

Use `AsRef` when callers hold many types (`&str`, `String`, `&Path`, `Vec<u8>`) and you want to accept all of them.

```rust
use std::path::Path;

fn process(input: impl AsRef<str>) -> usize {
    input.as_ref().len()
}

fn checksum(data: impl AsRef<[u8]>) -> u32 {
    data.as_ref().iter().map(|&b| u32::from(b)).sum()
}

fn open(path: impl AsRef<Path>) -> bool {
    path.as_ref().exists()
}
```

## When to Take the Owned Type

Take `&Vec<T>`/`&String` only for methods slices lack (`capacity`, `push`). Take the owned value itself when you store it.

```rust
fn might_grow(v: &mut Vec<i32>) {
    v.push(42);  // Slices can't push
}

struct Logger {
    prefix: String,  // Needs to own the string
}

impl Logger {
    // Caller decides to clone or move
    fn new(prefix: String) -> Self {
        Self { prefix }
    }

    // Or accept anything convertible
    fn with_prefix(prefix: impl Into<String>) -> Self {
        Self { prefix: prefix.into() }
    }
}
```

## See Also

- [api-impl-asref](api-impl-asref.md) - Accept `impl AsRef<T>` for maximum flexibility
- [own-borrow-over-clone](own-borrow-over-clone.md) - Prefer borrowing over cloning
- [api-impl-rangebounds](api-impl-rangebounds.md) - Accept impl RangeBounds for ranges
