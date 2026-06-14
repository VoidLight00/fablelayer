# FableLayer Procedure Spec

This public-safe spec contains no private prompt text.

## verification grounding

Every completion claim needs measurable evidence: command exit code, test output, file path, rendered artifact, or source URL.

## investigation protocol

Before implementation, map the current state, collect evidence, and choose one path with a reason.

## multi-pass review

Separate generation from verification. Run structure, safety, and completeness passes.

## drift prevention

Record RUN_MANIFEST state, compare artifacts against acceptance criteria, and write recurring failures to FAILURE_LOG.
