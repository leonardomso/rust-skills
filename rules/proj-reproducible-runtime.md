# proj-reproducible-runtime

> Build a pinned release artifact in one stage and run it in a minimal, non-secret runtime image

## Why It Matters

Copying a developer workstation into production makes builds depend on
untracked tools, caches, and credentials. A runtime image containing the Rust
toolchain, source tree, and package manager expands both attack surface and
size. Build from a pinned toolchain and dependency graph, then copy only the
release binary and its explicit runtime requirements into a minimal image.

## Contract

- Pin the Rust toolchain and base image by an immutable version or digest.
- Build with the release profile in a builder stage; the final stage contains
  no compiler, Cargo registry, source, or test artifacts.
- Include only runtime libraries the binary actually needs, such as a matching
  libc and CA roots for outbound TLS.
- Run as a non-root user with a read-only filesystem unless the application has
  a named writable path.
- Treat the build context as an allowlist. Exclude `.git`, `target`, local
  configuration, credentials, editor state, and generated check artifacts.
- Inject runtime configuration and secrets at deployment, never as image
  layers or build arguments.
- Produce the same artifact in CI that is promoted through environments.
- Generate an SBOM and scan the final image; do not confuse a small image with
  a secure one.

## Bad

```text
FROM rust:latest
COPY . .
RUN cargo run --release
```

## Good

```text
builder: pinned Rust toolchain -> cargo build --locked --release
runtime: pinned minimal OS -> copy binary + CA roots -> non-root entrypoint
```

## Verification

- A clean checkout builds without reading parent directories or user state.
- Scanning the final filesystem finds no source, Cargo credentials, or secret
  configuration.
- The binary starts with production-equivalent dynamic libraries and CA roots.
- Rebuilding from the same inputs produces a reproducible or provenance-linked
  artifact.

## See Also

- [proj-works-out-of-box](proj-works-out-of-box.md) - keep host setup out of default builds
- [proj-build-rs-minimal](proj-build-rs-minimal.md) - build scripts are not network installers
- [proj-typed-config](proj-typed-config.md) - inject settings at runtime
- [lint-cargo-metadata](lint-cargo-metadata.md) - keep package and dependency metadata reviewable
- [obs-no-sensitive-data](obs-no-sensitive-data.md) - secrets must not appear in build logs
