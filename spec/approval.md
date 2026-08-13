# AIOS Approval Boundary

## Purpose

Architect and Developer agents may propose changes, but AIOS must not persist consequential project changes without explicit human approval.

## Proposal

An agent execution produces a proposal.

A proposal may contain:

- Specifications
- Architecture decisions
- Task contracts
- Source changes
- Configuration changes

## Approval States

```text
PROPOSED
    ↓
APPROVED
    ↓
APPLIED