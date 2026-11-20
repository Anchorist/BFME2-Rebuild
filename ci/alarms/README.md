# Alarm issues

`alarm.py` keeps one GitHub issue per kind of failure, labelled `alarm`. A workflow raises a kind
when something that must not happen happens and clears it when the same job next succeeds.
Raising an open alarm only edits its text; raising a closed one reopens it; clearing closes it.
The kinds and their titles are listed in `KINDS` at the top of `alarm.py`. The token needs
`issues: write` only and is passed as `ALARM_TOKEN`.
