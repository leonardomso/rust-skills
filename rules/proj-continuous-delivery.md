# proj-continuous-delivery

> Keep the protected mainline releasable and make deployment consume the exact admitted artifact

## Why It Matters

Deployment is not a cleanup phase after coding. If main can contain changes
that cannot roll out with the current schema, configuration, probes, or
previous binary, the team accumulates an untested release branch. Continuous
delivery treats every admitted commit as a complete candidate and promotes the
same immutable artifact through environments.

## Contract

- Protected-main admission runs build, lint, tests, dependency/security policy,
  schema compatibility, and artifact construction.
- The artifact is immutable and identified by its content digest. The commit is
  provenance metadata, not permission to rebuild different bytes in each
  environment.
- Environment promotion changes declarative configuration, not source or the
  binary.
- The deployment declares listen port, readiness/liveness paths, replica
  policy, TLS boundary, resources, and rollout strategy.
- Schema changes use expand/backfill/contract and run through a controlled
  release job with database network access; a laptop is not the production
  migrator.
- Rollout observes health and service-level signals, halts on regression, and
  has a tested roll-forward or rollback policy.
- Secrets are referenced from a secret provider, never copied into deployment
  manifests.

## Failure Tests

- deploy the candidate against the previous compatible schema;
- keep old and new replicas live during the expand phase;
- force readiness failure and verify traffic is not routed;
- force a migration or startup failure and verify rollout stops;
- prove the promoted digest matches the admitted artifact; a rebuild from the
  same commit is a new candidate and must pass admission again.

## See Also

- [proj-schema-migrations](proj-schema-migrations.md) - evolve database state across mixed versions
- [proj-reproducible-runtime](proj-reproducible-runtime.md) - build one promotable artifact
- [api-health-probes](api-health-probes.md) - separate restart and routing signals
- [proj-typed-config](proj-typed-config.md) - vary configuration without rebuilding
- [test-http-blackbox](test-http-blackbox.md) - exercise the deployed process boundary
