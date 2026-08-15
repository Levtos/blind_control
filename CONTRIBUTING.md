# Contributing to Blind Control

Issue [#2](https://github.com/Levtos/blind_control/issues/2) is the current
scope contract. AP2 adds the deterministic backend Shadow slice and read-only
UX contract; Apply, Cover-Rename, Cutover, Release, and Live work remain out of
scope.

Run the local checks from the repository root:

```text
python -m pytest -q
python -m compileall -q custom_components tests
python -m ruff check custom_components tests
python -m ruff format --check custom_components tests
git diff --check
```

Do not start a preview server or perform a browser/live Home Assistant check
for this slice. A pull request stays Draft until the documented scope, tests,
open gates, and `Not Live` status are reviewable.
