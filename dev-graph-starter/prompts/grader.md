# Grader (Phase 3 placeholder — not wired in Phase 1)

When wired in Phase 3, the Grader reads the Spec, the diff of artifacts,
and the Integration Runner output. It returns:

```json
{
  "verdict": "pass" | "fail",
  "feedback": "specific criticism referencing acceptance criteria",
  "criteria_status": {"AC1": "pass", "AC2": "fail", ...}
}
```

Rules for whoever wires this:

- Runs on Opus (judgment task).
- Owned by an engineer OTHER than the one who owns the Coder prompt —
  keeps the Grader from becoming a rubber stamp.
- Fail must produce actionable feedback tied to a specific AC. Vague
  fails ("code could be better") are not permitted.
- If Grader fails twice in a row on the same task, the graph escalates
  to a human instead of retrying.
