# macro-no-implied-items

> Do not let a macro invent extra items the caller never wrote, especially public types

## Why It Matters

An expansion that quietly defines `SensorMeta` next to the user's `Temp` collides with a type already in that module, with the next invocation of the same macro, and with the crate's naming habits. The extra item is invisible in the source, so it is easy to forget when re-exporting a public API. Months later a refactor in an unrelated file fails with a duplicate-definition error that names a type nobody typed. Treat those generated ghosts as a hygiene and visibility defect.

## Bad

```rust
macro_rules! register_sensor {
    ($name:ident) => {
        pub struct $name;

        // Invented by the macro. A second expansion, or a user type of
        // the same name, fails in this module.
        pub struct SensorMeta;

        impl $name {
            pub fn meta() -> SensorMeta {
                SensorMeta
            }
        }
    };
}

register_sensor!(Temp);
// register_sensor!(Humidity); // colliding `SensorMeta`

fn main() {
    let _ = Temp::meta();
}
```

## Good

```rust
macro_rules! register_sensor {
    ($name:ident) => {
        pub struct $name;

        impl $name {
            pub fn kind() -> &'static str {
                stringify!($name)
            }
        }
    };
}

register_sensor!(Temp);
register_sensor!(Humidity);

fn main() {
    assert_eq!(Temp::kind(), "Temp");
    assert_eq!(Humidity::kind(), "Humidity");
}
```

If the expansion needs a helper, take a user-written type as an argument or call into a `#[doc(hidden)]` `__private` module (`macro-private-helpers`). Do not emit a public companion type the caller never declared.

## Exception

Rust namespaces are not modules. Value, type, and macro names live in separate buckets inside one module, so `fn enroll` and `struct enroll` can coexist, travel together on re-export, and almost never collide with a user type because types are `UpperCamelCase` (C-CASE). That pattern is acceptable for private dispatch tables in a binary or an FFI shim. It is still a poor *public* type: rustdoc shows a lowercase struct, and callers should not have to treat the generated name as API.

```rust
fn enroll() {}

#[expect(
    non_camel_case_types,
    reason = "type-namespace twin of the handler function, not a public type"
)]
struct enroll {
    _private: (),
}

impl enroll {
    fn path() -> &'static str {
        "/enroll"
    }
}

fn main() {
    enroll();
    assert_eq!(enroll::path(), "/enroll");
}
```

## Key Points

- A namespace in Rust is the naming bucket (`fn`, `struct`/`enum`/`trait`, `macro`), not a C#/Java package. A Rust module is the closest analogue of those foreign "namespaces."
- Repeated expansions must not fight each other over a fixed helper name.
- Implied items that must be re-exported will be forgotten; if the user did not write the name, do not make them ship it.

## See Also

- [macro-private-helpers](macro-private-helpers.md) - keep generated helpers in `#[doc(hidden)] __private`
- [macro-no-rewrite-item](macro-no-rewrite-item.md) - do not change the item the user did write
- [macro-declarative-before-proc](macro-declarative-before-proc.md) - keep expansions small enough to review
- [name-types-camel](name-types-camel.md) - the casing split that makes the same-name exception viable
- [proj-pub-use-reexport](proj-pub-use-reexport.md) - a type the user never wrote is a second public path waiting to leak
