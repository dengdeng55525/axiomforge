# Generated-code execution boundary

The implemented backend is **constrained_ast_subprocess**. The current host has
no Docker/bubblewrap, and a user/network namespace probe (`unshare -Urn true`)
fails with `Operation not permitted`. The application therefore does **not**
claim container, filesystem, or network namespace isolation.

Generated `model.py` is parsed as a small construction language. Approved sklearn
imports, `build_pipeline(task_spec)`, local assignments, literals, approved
`task_spec[...]` accesses and allowlisted estimator constructors are supported.
The source is never executed with Python `exec`, `eval`, `runpy`, or imported as
a module. All other Python operations are rejected before fitting. A JSON
constructor plan is independently rebuilt in the trusted worker.

Disallowed operations include file/network/OS APIs, dynamic imports, attributes
and method calls, callbacks, decorators, comprehensions, loops, lambda, string
formatting, argument unpacking, and arbitrary module/class constructors. Text
vectorizers accept content only, never filenames. Pipeline disk caching is
disabled. Estimator thread counts and resource-heavy parameters have bounds.

The fresh worker has a scrubbed environment, no API credentials, address-space
and CPU limits, bounded output files and open descriptors, CPU affinity,
threadpool limits, and a wall-time deadline. Cancellation or timeout kills the
whole process group. Native sklearn/numpy dependencies remain trusted; this
backend is unsuitable for arbitrary third-party Python or hostile native code.

Training labels are available to fitting; validation labels remain on the host
evaluator and are absent from worker requests and constructor task context. No
final-test data is materialized. The filesystem itself is **not** an access
control boundary: secrecy from generated code depends on the restricted grammar.
Only JSON predictions are deserialized on the host; no model pickle is loaded.

Results label this actual boundary in `containment`. OS-level container execution
can be implemented later behind a separate backend and must pass separate escape,
mount, network, quota, and cancellation tests before any stronger claim is made.

The host requires an explicit successful record for each applicable robustness
check, rejects missing/duplicate/false evidence, and independently verifies that
the final classifier family agrees with the planner when `expected_algorithm`
is supplied. `model_metadata.json` records the actual classifier and constructor
parameters derived from the AST, rather than accepting the model's description.

For bank data, `pdays=999` keeps the original documented sentinel in this baseline
feature policy. It is a legitimate pre-contact feature but can reduce linear
model quality; any alternative sentinel/missing-indicator transformation should
be a separately versioned feature policy evaluated without final-test leakage.
