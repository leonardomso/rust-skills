# unsafe-no-mangle-unsafe

> In Rust 2024, write `#[unsafe(no_mangle)]`, `#[unsafe(export_name = "...")]`, and `#[unsafe(link_section = "...")]` — not the bare attribute forms.

## Why It Matters

`#[no_mangle]`, `#[export_name]`, and `#[link_section]` were reclassified as
unsafe in Rust 2024 because they can violate global symbol and linker-section
invariants without an `unsafe` block at the call site. A duplicate symbol might
be rejected, interposed, or selected according to the linker and artifact
format; if a caller reaches an incompatible definition, the result can be
undefined behavior. Requiring `#[unsafe(...)]` makes the responsibility visible
and auditable, but it does not validate the symbol graph.

## Bad

```rust
// Rust 2021 — bare attributes accepted, no warning about linker UB
#[no_mangle]
pub extern "C" fn init() {
    // ...
}

#[export_name = "plugin_entry"]
pub fn plugin_main() {
    // ...
}

#[link_section = ".init_array"]
static INIT: extern "C" fn() = init;
```

## Good

```rust
// Rust 2024 — unsafe(...) wrapper makes the risk explicit
#[unsafe(no_mangle)]
pub extern "C" fn init() {
    // ...
}

#[unsafe(export_name = "plugin_entry")]
pub extern "C" fn plugin_main() {
    // ...
}

// Section names are platform-specific: ELF takes ".init_array", Mach-O
// takes a "segment,section" pair. Rust 1.97 rejects an invalid specifier
// instead of ignoring it.
#[cfg_attr(target_os = "macos", unsafe(link_section = "__DATA,__mod_init_func"))]
#[cfg_attr(not(target_os = "macos"), unsafe(link_section = ".init_array"))]
static INIT: extern "C" fn() = init;
```

## Migration

| Rust 2021 | Rust 2024 |
|-----------|-----------|
| `#[no_mangle]` | `#[unsafe(no_mangle)]` |
| `#[export_name = "sym"]` | `#[unsafe(export_name = "sym")]` |
| `#[link_section = ".sec"]` | `#[unsafe(link_section = ".sec")]` |

Run `cargo fix --edition` when migrating to the 2024 edition — it rewrites bare attribute forms to `#[unsafe(...)]` automatically. Review each one afterward: confirm that the exported symbol name is unique across the binary.

## Key Points

- The `unsafe(...)` wrapper does **not** require an `unsafe {}` block at the call site; it marks the *attribute itself* as load-bearing for safety. The annotation documents that the programmer accepted responsibility for symbol uniqueness and ABI correctness.
- Symbol collisions are especially dangerous in plugin architectures, `cdylib` crates, embedded firmware with custom linker scripts, and any codebase that links multiple Rust crates into a single binary.
- These attributes interact with `unsafe extern` blocks (see `unsafe-extern-block`): external symbols you import and symbols you export follow the same 2024-edition safety rules.
- The bare forms (`#[no_mangle]` without `unsafe`) are a hard error in Rust 2024
  edition code. In earlier editions, `unsafe_attr_outside_unsafe` is
  allow-by-default and belongs to the `rust-2024-compatibility` lint group;
  enable that group (as `cargo fix --edition` does) to find migration sites.
- Rust 1.96 made the first duplicate `export_name`, `link_name`, or `link_section` attribute take precedence. Never stack duplicate symbol attributes; keep one audited source of truth.
- `link_section` values are validated in Rust 1.97: a bare ELF name like `.init_array` is an error on Mach-O. Use a `cfg_attr` per target, or a name your linker script actually defines.
- Rust 1.97 also rejects empty `export_name` values and validates `link_name` / `link` parameters. Treat those diagnostics as contract defects, not warnings to suppress.

## See Also

- [unsafe-extern-block](unsafe-extern-block.md) - wrap `extern` blocks in `unsafe extern` in Rust 2024
- [type-repr-transparent](type-repr-transparent.md) - use `#[repr(transparent)]` for FFI newtypes
