# Contributing to Blind Control

Issue [#1](https://github.com/Levtos/blind_control/issues/1) is the current
scope contract. Functional policy, source binding, frontend, apply, and live
cutover work belongs to later issues and must not be folded into AP1.

Run the local checks from the repository root:

```text
python -m pytest -q
python -m compileall -q custom_components tests
python -m ruff check custom_components tests
python -m ruff format --check custom_components tests
git diff --check
```

Do not start a preview server or perform a browser/live Home Assistant check
for this AP1 slice. A pull request stays Draft until the documented scope,
tests, open gates, and `Not Live` status are reviewable.
