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
  services/               # Domain services for HMI and preconditions
  keywords/               # Robot Framework facing entry points
```

Sample Robot Framework tests reside in `tests/features` and demonstrate how to
consume the published keywords.
