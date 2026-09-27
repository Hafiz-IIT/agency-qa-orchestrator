# Architecture

```mermaid
flowchart LR
    X0[client requirements] --> X1
    X1[artifacts] --> X2
    X2[coverage map] --> X3
    X3[acceptance checks] --> X4
    X4[verification evidence] --> X5
    X5[delivery gate]
```

## Requirements
Every requirement has explicit acceptance criteria.

## Artifacts
Outputs declare which requirement IDs they cover.

## Verification
Criteria are individually recorded as passed/failed/unverified.

## Delivery gate
A delivery is ready only when there are no coverage or verification gaps.

## Design principle
Treat QA evidence as a prerequisite for delivery, not as a post-hoc explanation after generation.
