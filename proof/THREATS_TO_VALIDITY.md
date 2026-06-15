# Threats to Validity

This document records limits that can make FableLayer evidence look stronger than it really is.

## Task selection bias

If benchmark tasks are written only around FableLayer's strengths, results will overstate general usefulness.

Mitigation:

- include negative controls
- include tasks where FableLayer should not help
- publish raw fixtures

## Prompt familiarity

Models may perform better because the task wording resembles the layer wording.

Mitigation:

- use paraphrased tasks
- use held-out fixtures
- use external reviewer tasks when possible

## Model variance

Different model versions can change behavior without any FableLayer change.

Mitigation:

- record model name and date
- keep raw outputs
- rerun benchmark after major provider updates

## Gate overfitting

Gates may catch known patterns while missing new defect classes.

Mitigation:

- add new fixtures when failures are found
- keep false negative examples
- separate hard gates from advisory checks

## Capability-transfer overclaim

FableLayer may make a model follow better procedure, but that is not the same as transferring another model's underlying capability.

Mitigation:

- keep capability-transfer language out of public claims
- describe FableLayer as procedure transfer
- cite benchmark limitations

## Environment dependence

Local success on one machine does not prove installability everywhere.

Mitigation:

- run CI across Python versions
- add macOS and Linux smoke checks where practical
- keep runtime dependencies at zero

## History hygiene limits

Current HEAD can be clean while historical commits still contain older strings.

Mitigation:

- scan current tracked tree for release claims
- document history rewrite as a separate destructive operation
- avoid force push unless the remaining artifact is sensitive enough to justify it

