# api-impl-asref

> Use `AsRef<T>` when you only need to borrow the inner data

## Why It Matters

`AsRef<T>` provides a cheap borrowed view of data without taking ownership or copying. Functions accepting `impl AsRef<T>` can work with multiple types that contain or represent `T`, making APIs flexible while avoiding unnecessary allocations. Use `AsRef` when you only need to read, `Into` when you need to own.

## Bad

```rust
// Forces callers to provide exact types
fn process_text(text: &str) { ... }
fn read_file(path: &Path) { ... }

// Can't call directly with owned types
let s = String::from("hello");
process_text(&s);  // Works but verbose

let p = PathBuf::from("/file");
read_file(&p);  // Works but verbose
read_file("/file");  // Error! &str != &Path
```

## Good

```rust
// Accept anything that can be viewed as the target type
fn process_text(text: impl AsRef<str>) {
    let s: &str = text.as_ref();
    println!("{}", s);
}

fn read_file(path: impl AsRef<Path>) -> io::Result<Vec<u8>> {
    std::fs::read(path.as_ref())
}

// All of these work:
process_text("literal");        // &str
process_text(String::from("owned"));  // String
process_text(Cow::from("cow")); // Cow<str>

read_file("/path/to/file");     // &str  
read_file(Path::new("/path"));  // &Path
read_file(PathBuf::from("/path")); // PathBuf
read_file(OsStr::new("/path")); // &OsStr
```

## AsRef vs Into vs Borrow

```rust
// AsRef<T>: cheap borrow, no ownership transfer
fn read(p: impl AsRef<Path>) {
    let path: &Path = p.as_ref();
}

// Into<T>: ownership transfer, may allocate
fn store(p: impl Into<PathBuf>) {
    let owned: PathBuf = p.into();
}

// Borrow<T>: like AsRef but with Eq/Hash consistency guarantee
use std::borrow::Borrow;
fn lookup<Q: ?Sized>(map: &HashMap<String, V>, key: &Q) -> Option<&V>
where
    String: Borrow<Q>,
    Q: Hash + Eq,
{
    map.get(key)
}
```

Use `impl AsRef<_>` at call boundaries, not as infectious storage:

```rust
// Avoid: every use of User now carries an unrelated type parameter.
struct GenericUser<N: AsRef<str>> {
    name: N,
}

// Store the representation the type owns; keep input flexibility in `new`.
struct User {
    name: String,
}

impl User {
    fn new(name: impl AsRef<str>) -> Self {
        Self { name: name.as_ref().to_owned() }
    }
}
```

For low-volume configuration APIs the convenience is usually worth a small
conversion. In high-volume hot paths, measure monomorphization and conversion
cost; a direct `&str`, `&Path`, or `&[u8]` parameter may be the clearer and
smaller interface.

## Implement AsRef for Custom Types

```rust
struct Name(String);

impl AsRef<str> for Name {
    fn as_ref(&self) -> &str {
        &self.0
    }
}

impl AsRef<[u8]> for Name {
    fn as_ref(&self) -> &[u8] {
        self.0.as_bytes()
    }
}

// Now Name works with functions expecting AsRef<str>
fn greet(name: impl AsRef<str>) {
    println!("Hello, {}!", name.as_ref());
}

greet(Name("Alice".into()));
```

## Common AsRef Implementations

```rust
// Standard library provides many
impl AsRef<str> for String { ... }
impl AsRef<str> for str { ... }
impl AsRef<[u8]> for str { ... }
impl AsRef<[u8]> for String { ... }
impl AsRef<[u8]> for Vec<u8> { ... }
impl AsRef<Path> for str { ... }
impl AsRef<Path> for String { ... }
impl AsRef<Path> for PathBuf { ... }
impl AsRef<Path> for OsStr { ... }
impl AsRef<OsStr> for str { ... }
```

## When to Use Which

| Trait | Use When |
|-------|----------|
| `&T` | Single type, simple API |
| `AsRef<T>` | Read-only access, multiple input types |
| `Into<T>` | Need to store/own the value |
| `Borrow<T>` | HashMap/HashSet keys, Eq/Hash needed |
| `Deref<Target=T>` | Smart pointer semantics |

## Pattern: Optional AsRef Bound

```rust
// When T itself might be passed
fn process<T: AsRef<U>, U>(value: T) {
    let inner: &U = value.as_ref();
}

// More flexible: accept T or &T
fn process<T: AsRef<U> + ?Sized, U: ?Sized>(value: &T) {
    let inner: &U = value.as_ref();
}
```

## See Also

- [api-impl-into](./api-impl-into.md) - When to use Into instead
- [own-slice-over-vec](./own-slice-over-vec.md) - Using slices for flexibility
- [own-borrow-over-clone](./own-borrow-over-clone.md) - Preferring borrows
- [api-impl-io](./api-impl-io.md) - Accept Read/Write the same way you accept AsRef
- [api-impl-rangebounds](./api-impl-rangebounds.md) - Accept RangeBounds the same way you accept AsRef
