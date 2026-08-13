# proj-thin-vertical-slice

> Deliver the smallest end-to-end user journey before deepening any one layer

## Why It Matters

A database schema, handler library, or deployment manifest can each be
"complete" while no user can accomplish anything. Build one thin vertical
slice through transport, application logic, persistence, observability, and
deployment. That exposes integration mistakes early and leaves a runnable
product after every iteration.

## Bad

```text
Iteration 1: design every table
Iteration 2: build every repository
Iteration 3: build every handler
Iteration 4: discover the service cannot deploy
```

## Good

```text
Journey: submit a subscription
  -> reject malformed input
  -> persist one valid request
  -> return the documented response
  -> expose telemetry for success and failure
  -> run through the production server in an integration test
```

After that slice works, add confirmation, retry, secondary encodings, and
operator workflows one capability at a time.

## Quality Floor

Time-boxing may reduce feature scope; it does not reduce the quality floor:

- reachable behavior has an observable test;
- recoverable I/O returns an error rather than panicking;
- public interfaces are documented;
- lint, formatting, and dependency policy gates pass;
- request paths emit enough telemetry to diagnose their named failures;
- the increment can be deployed and rolled back or rolled forward safely.

## See Also

- [test-observable-coverage](test-observable-coverage.md) - prove the user-visible slice
- [test-http-blackbox](test-http-blackbox.md) - cross the actual HTTP boundary
- [proj-schema-migrations](proj-schema-migrations.md) - evolve persistence without blocking deployment
- [obs-request-correlation](obs-request-correlation.md) - make the slice operable
- [err-result-over-panic](err-result-over-panic.md) - do not trade error handling for iteration speed
