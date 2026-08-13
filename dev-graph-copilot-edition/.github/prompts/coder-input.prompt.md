---
description: 'Hand an approved Spec off to the Coder mode with proper framing.'
mode: 'Coder'
---

I have an approved Spec. Implement it now, following your Coder discipline.

## Approved Spec

```json
${input:spec:Paste the approved JSON spec}
```

## Additional context (optional)

${input:context:Paste any additional files or constraints not in the Spec, or leave empty}

---

## Instructions

1. Start by reading the affected files. Use `codebase` search to locate them.
2. Propose your edit plan in one sentence before making the first edit.
3. Make the minimum change to satisfy each AC. No unrelated cleanup.
4. When you believe every AC is satisfied, stop and give me:
   - A one-line summary
   - For each AC: which file(s) address it and how
   - Any follow-ups (backfills, eval runs, migrations) the Grader should
     also check
