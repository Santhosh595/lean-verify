# Recovery notes

Working tree restored 2026-10-01. Before this, every tracked file was deleted
from disk (8 files, `git status` showed all of them as `D`) while the commit
itself was intact.

## This is the only copy of this code

`lean-verify` has **no git remote at all**. The commit `b80bf64` existed only
in this working copy. A backup bundle was written before the restore:

    ~/lean-verify-UNIQUE-b80bf64.bundle

`git bundle verify` on it reports "The bundle records a complete history", and
`git clone` from it reproduces all 473 lines of source. **Push this repo
somewhere before making further changes** -- a stray `rm` here is
unrecoverable.

## Test status: 25 pass, 3 fail

    PYTHONPATH=src python -m pytest tests/ -q

The 3 failures are bugs in the recovered code itself, not in the restore:

- `TestVerificationResult::test_verification_result_to_dict`
- `TestVerificationResult::test_verification_result_default_values`
- `TestExceptionClasses::test_lean_verify_error`

`to_dict()` returns `Status.COMPLETED` (a `Status` enum member) where the tests
assert the plain string `"completed"`. So `to_dict()` is either missing a
`.value` coercion or the tests encode the intended contract. Fixing this means
deciding which side is right, so it has been left as-is rather than guessed at.

## Packaging is missing entirely

`README.md` says:

    pip install -e .

but there is no `pyproject.toml` and no `setup.py` -- neither was ever
committed (`git ls-files` confirms). That command has therefore **never
worked**. The tests only run with the source directory on the path:

    PYTHONPATH=src python -m pytest tests/ -q

Adding a `pyproject.toml` would make the documented command true; that is new
work, not part of this restore.

## Note on scope

`DOCUMENTATION.md` states no Lean toolchain or elan install is sanctioned per
the project's Tool Acquisition Policy, so no `lean` binary was installed and the
tests that shell out to one were not exercised.
