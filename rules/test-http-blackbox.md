# test-http-blackbox

> Test HTTP behavior through the production router and a real ephemeral listener

## Why It Matters

Calling a handler directly skips routing, extraction, middleware, response
conversion, and socket startup—the boundaries where web services often fail.
Start the same application composition used by the binary on a loopback
OS-assigned port, drive it with a generic HTTP client, and assert observable
status, headers, body, and side effects.

## Bad

```rust
#[test]
fn health_is_ok() {
    assert_eq!(health_handler(), "ok");
}
```

This passes even if the route is missing or the server cannot bind.

## Good

```text
listener = bind("127.0.0.1:0")
server = production_app(listener, test_settings, test_dependencies)
server_task = spawn(server)

response = generic_http_client.get(listener.local_addr() + "/health/live")
assert response.status == 200
assert response.headers["content-type"] == expected
assert response.body == expected

shutdown(server_task)
```

The fixture binds before spawning so startup errors are returned synchronously.
The production composition consumes that listener and returns a pollable server
future or task handle. A focused executable socket round-trip in
`checks/tests/source_guidance.rs` guards against regressing this into a
bind-only tautology.

## Contract

- Build routes, middleware, state, and telemetry through the production
  composition function.
- Bind before spawning so startup errors are returned synchronously.
- Use an OS-assigned port so parallel tests do not contend.
- Send a real HTTP request and assert status, headers, body, and externally
  visible side effects. A port-allocation assertion alone is not a server test.
- Assert invalid input and dependency failure as well as the happy path.
- Verify a write through a public read path or a narrow store query; never add
  a production endpoint solely for a test.
- Give each persistence test a database isolation boundary.
- Put shared client/startup helpers in a library module; remember that each
  file under `tests/` is a separate crate.

## See Also

- [test-integration-dir](test-integration-dir.md) - organize external-boundary tests
- [test-observable-coverage](test-observable-coverage.md) - assert behavior rather than implementation
- [test-fixture-raii](test-fixture-raii.md) - stop the server and remove resources on failure
- [test-descriptive-names](test-descriptive-names.md) - name the contract and failure mode
- [proj-typed-config](proj-typed-config.md) - inject test configuration explicitly
