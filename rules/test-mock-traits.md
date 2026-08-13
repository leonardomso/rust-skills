# test-mock-traits

> Put nondeterministic system effects behind a crate-owned native/test backend and return the test controller with the service

## Why It Matters

A database trait alone does not make a library deterministic. Time, random bytes, files, sockets, process variables, and hardware calls can all prevent a test from reaching timeouts, short reads, clock rollback, exhausted entropy, or platform failures. A public service must give consumers a supported way to drive those outcomes.

Use a trait when downstream crates are expected to provide new implementations. For a closed native-versus-test choice owned by your crate, keep a private enum behind the service. That avoids exporting `Box<dyn ...>` and makes the test backend an intentional feature rather than a second architecture.

## Bad

```rust
use std::fs;
use std::time::{SystemTime, UNIX_EPOCH};

pub struct TokenFile;

impl Default for TokenFile {
    fn default() -> Self {
        Self
    }
}

impl TokenFile {
    pub fn read(&self) -> (u64, Vec<u8>) {
        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock moved backwards")
            .as_secs();
        let bytes = fs::read("token.bin").expect("token file");
        (now, bytes)
    }
}
```

The path, clock, and failure behavior are fixed inside the method. Tests can only manipulate the host machine.

## Good

```rust
use std::sync::{Arc, Mutex};

pub struct TokenFile {
    backend: Backend,
}

enum Backend {
    Native,
    #[cfg(feature = "test-util")]
    Test(TestCtrl),
}

#[cfg(feature = "test-util")]
#[derive(Clone)]
pub struct TestCtrl {
    state: Arc<Mutex<TestState>>,
}

#[cfg(feature = "test-util")]
struct TestState {
    now: u64,
    bytes: Vec<u8>,
}

impl TokenFile {
    pub fn new() -> Self {
        Self { backend: Backend::Native }
    }

    #[cfg(feature = "test-util")]
    pub fn new_test() -> (Self, TestCtrl) {
        let ctrl = TestCtrl {
            state: Arc::new(Mutex::new(TestState {
                now: 0,
                bytes: Vec::new(),
            })),
        };
        (
            Self {
                backend: Backend::Test(ctrl.clone()),
            },
            ctrl,
        )
    }

    pub fn read(&self) -> (u64, Vec<u8>) {
        match &self.backend {
            Backend::Native => native_read(),
            #[cfg(feature = "test-util")]
            Backend::Test(ctrl) => {
                let state = ctrl.state.lock().unwrap();
                (state.now, state.bytes.clone())
            }
        }
    }
}

fn native_read() -> (u64, Vec<u8>) {
    // The only place that calls the clock, filesystem, environment, or OS.
    (1, Vec::new())
}

#[cfg(feature = "test-util")]
impl TestCtrl {
    pub fn set_read(&self, now: u64, bytes: impl Into<Vec<u8>>) {
        let mut state = self.state.lock().unwrap();
        state.now = now;
        state.bytes = bytes.into();
    }
}

#[cfg(feature = "test-util")]
fn demonstrate_test_backend() {
    let (reader, ctrl) = TokenFile::new_test();
    ctrl.set_read(42, b"abc".to_vec());
    assert_eq!(reader.read(), (42, b"abc".to_vec()));
}

fn main() {
    let _ = TokenFile::new();
}
```

## Design Contract

- Centralize native effects in one backend; ordinary business methods never call the clock, filesystem, RNG, environment, or kernel directly.
- Return `(service, controller)` from the test constructor. Accepting a borrowed controller allows several services to share ambiguous mutable test state.
- Keep the controller cheap to clone around shared internal state, matching other service handles.
- If the library already selects Tokio, smol, or another runtime with a private enum, add the test backend to that enum instead of creating a parallel abstraction.
- Put a safe test backend and controller behind `test-util` when downstream
  integration tests need them. Assume feature unification can still place
  those symbols in a release artifact, so they must not weaken authentication,
  validation, or other production invariants.
- Keep security bypasses and destructive fault injectors in a separate test
  harness or test-only crate outside the production dependency graph.
- Do not offer `Default` when construction silently chooses unreplaceable ambient effects. Make the native policy visible through `new`.

## Traits vs a Closed Backend

A trait is correct when callers genuinely implement the port—for example, an application supplies its own object store. Use the crate-owned enum when the supported set is closed and the alternate exists only for deterministic tests. Follow the concrete → enum → generic → wrapped-dyn ladder in `trait-dyn-vs-generic`.

## Allocation Boundary

Ordinary allocation is stable enough that tests do not need a fake allocator. That does not grant unlimited memory: APIs that process attacker-controlled or potentially huge input need byte/item bounds and chunked or streaming forms. Kernel, allocator, or embedded crates may expose an allocator port because allocation behavior is part of their product.

## See Also

- [trait-dyn-vs-generic](trait-dyn-vs-generic.md) - choose the least infectious substitution mechanism
- [test-util-feature](test-util-feature.md) - remove testing controls from default builds
- [api-service-clone](api-service-clone.md) - controllers and services are cheap shared handles
- [api-impl-io](api-impl-io.md) - accept caller-provided one-shot I/O where that is the simpler seam
- [async-tokio-runtime](async-tokio-runtime.md) - keep runtime selection at an adapter boundary
