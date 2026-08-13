# Architect Proposal Schema

## Proposal

Every Architect execution produces one proposal.

### Required

- proposal_id
- task_id
- status
- architecture
- reusable_modules
- task_contracts
- dependencies
- acceptance_criteria
- risks
- unresolved_decisions

## Status

A proposal starts as:

PROPOSED

It may transition to:

APPROVED
REJECTED
REVISION_REQUIRED
APPLIED

## Task Contracts

Each generated task must contain:

- id
- title
- role
- owner
- status
- priority
- depends_on
- capabilities
- knowledge
- shared_modules
- inputs
- outputs
- acceptance_criteria

## Rules

The Architect may propose artifacts.

The Architect must not mark a proposal APPROVED.

Only the human approval workflow may transition:

PROPOSED → APPROVED

AIOS owns proposal persistence and state transitions.