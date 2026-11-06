# Security notes

## Threat model

`trysac-eval-harness-mini` is a library with no runtime dependencies. Its only I/O is reading the dataset file, writing the optional `--report` file and printing to stdout or stderr.

Defended:

- **Oversized datasets**: the file is read up to `max_bytes + 1` bytes; each line is limited to `max_line_bytes` (1 MiB by default); the case count is limited to `max_cases` (100,000 by default).
- **Deep nesting**: JSON nesting deeper than 64 levels is rejected by an iterative depth check; `RecursionError` from the parser maps to `dataset_invalid`. JSON equality is iterative.
- **Non-standard JSON**: NaN, Infinity and non-finite numbers such as 1e999 are rejected.
- **Invalid scorer output**: a score that is not a finite float in [0, 1] raises `scorer_out_of_range`; booleans and ints are rejected.
- **Log and error content**: error messages and the report never include inputs or outputs of cases beyond a 200-character quote of an error message; `CaseEvent` carries no inputs or outputs.

Not defended:

- **Code execution via `--target`**: the CLI imports `module:function` and runs it. This is equivalent to running the code directly, like pytest. Use only trusted code.
- **Hostile scorer or target code**: exceptions from scorers propagate unchanged; a target that loops forever or exhausts memory is not interrupted.
- **Untrusted datasets within the limits**: a dataset under the size limits is fully loaded into memory.
- **Supply chain of the package and CI**: mitigated only by the project process (no runtime dependencies, Dependabot, pinned actions, gitleaks); not enforced by the code.

To report a vulnerability, see [SECURITY.md](../SECURITY.md).

## Publishing

Releases are published to PyPI with trusted publishing (OIDC) when available, never with a long-lived token stored in the repository.
