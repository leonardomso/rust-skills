# proj-split-crates

> Extract independently useful modules into crates; join them again only as a thin umbrella

## Why It Matters

Rust compiles crate-by-crate. A client-only change that still type-checks a server module pays for that module every time, and two modules that import each other cannot become crates later without a rewrite. Move a submodule that outsiders could depend on by itself into its own package. Bias toward more crates when the split is real; do not invent a package for a helper that has no independent user.

## Bad

```text
web/
  src/
    server.rs
    client.rs
    protocols.rs
```

A consumer that only performs client calls still compiles `web::server`. The three modules also tend to grow `use super::*` cycles that a crate graph would have rejected.

```rust
// One crate: the client reaches across into server-only `pub(crate)` state.
pub mod server {
    pub(crate) struct Listener;

    pub(crate) fn bind() -> Listener {
        Listener
    }
}

pub mod client {
    pub fn connect() -> crate::server::Listener {
        crate::server::bind()
    }
}
```

## Good

```text
web_server
web_client
web_protocols
web            # optional umbrella; features may enable the three above
```

Callers take only `web_client`. Shared wire types live in `web_protocols`, which both sides depend on, so the graph stays acyclic.

```rust
// web_client — no path into a server crate.
pub fn connect(host: &str) -> String {
    format!("https://{host}")
}

fn main() {
    assert_eq!(connect("api.example"), "https://api.example");
}
```

## Losing `pub(crate)`

A split hides former `pub(crate)` fields and methods. Treat that as a design signal, not a reason to stay monolithic: the old in-crate shortcut was often an API you would not have given callers. Rebuild the seam so downstream crates get the same affordance through a public type, a trait, or an explicit handle.

## Umbrella Facades

Proc-macro crates and runtime stacks sometimes need a single name on crates.io. Re-join the pieces as a facade that `pub use`s what users should type.

- A technical proc-macro split may be re-exported from `foo` when one facade is
  the intended product API. A separately versioned macro crate is also valid
  when users need independent dependency/features or the macro is useful
  without the runtime crate. Pick one public path and document the versioning
  relationship; do not expose accidental duplicate paths.
- Re-export other members sparingly. An umbrella is a convenience crate, not a second public path for every item (`proj-pub-use-reexport`).

```text
# foo/src/lib.rs
pub use foo_proc::Widget;

# downstream code
use foo::Widget;
#[derive(Widget)]
struct Record;
```

## Crates vs Features

| Split | Use when |
| --- | --- |
| New crate | The item is useful on its own (`web_client` without `web_server`) |
| Cargo feature | The extra code cannot stand alone (a `serde` impl, a TLS backend) |
| Feature on an umbrella | The work already lives in member crates; the feature only turns those members on |

Features do not replace a crate split: `web` with `server` / `client` features still type-checks both sides in one rustc invocation unless the code has already moved out.

## Pathological Microcrates

Do not ship a crate per 20-line helper, or a pair of crates that cannot compile unless they are always used together. If nothing outside the original module would take a dependency on the extract, keep it as a module (`proj-mod-by-feature`, `proj-flat-small`).

## See Also

- [proj-feature-additive](proj-feature-additive.md) - features unlock extra capability; they do not substitute for a crate boundary
- [macro-proc-two-crate](macro-proc-two-crate.md) - `foo` must re-export `foo_proc` / `foo-derive`
- [proj-pub-use-reexport](proj-pub-use-reexport.md) - one public path; umbrellas re-export on purpose
- [proj-pub-crate-internal](proj-pub-crate-internal.md) - `pub(crate)` is an in-crate seam, not a substitute for a package
- [proj-workspace-large](proj-workspace-large.md) - sibling crates belong in one workspace
- [proj-mod-by-feature](proj-mod-by-feature.md) - split modules by capability before you split crates
