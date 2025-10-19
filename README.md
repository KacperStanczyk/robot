# Validation Framework Skeleton

This repository hosts a Python implementation of the integrated validation platform
blueprint.  It includes configuration-driven orchestration, a layered HAL, middleware,
domain services, and Robot Framework keywords.

## Layout

```
validation-framework/
  config/                 # YAML configuration used during wiring
src/validation_framework/
  config_loader/          # Typed models and YAML loaders
  hal/                    # HAL contracts, types, and implementations
  middleware/             # Interaction broker and error types
  services/               # Domain, HMI, and precondition services
  keywords/               # Robot Framework facing entry points
```

Sample Robot Framework tests reside in `tests/features` and demonstrate how to
consume the published keywords.

## Keyword families

The `validation_framework.keywords` library now exposes dedicated namespaces that
mirror the blueprint expectations:

* `PRECOND.*` – declarative preconditions (Standby, InUse, Driving, Charging,
  HVAC Base, Lighting Base, and arbitrary catalog entries).
* `BUS.*` – raw signal access (`Set`, `Get`, `Wait For Signal ==`).
* `HMI.*` – user interactions for pressing controls, navigating menus, opening
  applications, and asserting cluster telltales.
* `BACKEND.*` – remote command dispatch, acknowledgement tracking, and
  consistency checks between backend, SOME-IP, and vehicle state.
* `DIAG.*`, `VERIFY.*`, `CAPTURE.*`, and `EVIDENCE.*` – diagnostics, fault
  detection, trace capture, and evidence snapshots.
* Domain-specific namespaces such as `RTCU.*`, `ADAS.*`, `ZONAL.FRONT.*`,
  `ZONAL.CABIN.*`, `LIGHTS.*`, `WIPERS.*`, `ACCESS.*`, and `PACE.*` wrap the
  orchestration-heavy scenarios defined in the blueprint.

Configuration files under `validation-framework/config/interfaces` provide the
signal dictionary and precondition catalog powering these keywords.  The
`DomainService` orchestrates the InteractionBroker, ensures rigorous HAL
contracts, and surfaces the high-level capabilities consumed by Robot Framework.
