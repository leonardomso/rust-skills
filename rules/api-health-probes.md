# api-health-probes

> Separate liveness from readiness, keep probes cheap, and never perform business side effects

## Why It Matters

An orchestrator uses probes to decide whether to restart a process or route
traffic to it. A probe that sends email, mutates the database, or waits on
every dependency can amplify an outage. Liveness answers whether the process
event loop is functioning. Readiness answers whether this instance should
receive new traffic. They are different failure policies.

## Bad

```rust
pub async fn health() -> Result<(), Error> {
    database.write_test_row().await?;
    mailer.send_test_message().await?;
    Ok(())
}
```

One dependency outage causes every replica to restart and the probe itself
creates load and side effects.

## Good

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Probe {
    Ready,
    NotReady,
}

pub fn liveness() -> Probe {
    Probe::Ready
}

pub fn readiness(startup_complete: bool, draining: bool) -> Probe {
    if startup_complete && !draining {
        Probe::Ready
    } else {
        Probe::NotReady
    }
}

fn main() {
    assert_eq!(liveness(), Probe::Ready);
    assert_eq!(readiness(true, false), Probe::Ready);
    assert_eq!(readiness(true, true), Probe::NotReady);
}
```

## Contract

- Liveness is local, bounded, allocation-light, and independent of remote
  dependencies. Failure requests a restart.
- Readiness becomes true only after required startup work and false before
  graceful shutdown. Failure removes the instance from routing without
  restarting it.
- Readiness may incorporate cached/circuit state for dependencies required to
  serve, but the probe itself does not synchronously fan out to every
  dependency on every poll.
- A separate diagnostic endpoint may report dependency state, but it must be
  authenticated where details are sensitive and must not drive a restart
  storm.
- Probe handlers have no business side effects and no per-request database
  writes.
- Tests assert the startup and draining transitions, not only the default
  healthy response.

## See Also

- [test-http-blackbox](test-http-blackbox.md) - verify probe routes through the production server
- [async-cancellation-token](async-cancellation-token.md) - mark readiness false before cancellation
- [obs-named-events](obs-named-events.md) - emit state transitions instead of logging every successful probe
- [err-result-over-panic](err-result-over-panic.md) - report startup failures without probe-triggered panics
