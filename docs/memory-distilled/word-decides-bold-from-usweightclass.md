---
name: word-decides-bold-from-usweightclass
description: "Word has no ratio logic — below usWeightClass 600 it thickens by a constant, at 600+ it refuses."
metadata: 
  node_type: memory
  type: project
  originSessionId: e3dcb374-3d51-4830-81a8-031f01bcf06b
  modified: 2026-08-09T15:18:48.196Z
---

Measured on Windows GDI+ from WSL, 2026-08-09, `HHHH` at 128 pt:

```
Segoe UI Light      300   1.50x   synthesised
Segoe UI Semilight  350   1.36x   synthesised
Arial               400   1.56x   real drawn bold
Marlett             500   1.24x   synthesised
Segoe UI Semibold   600   1.00x   REFUSED — returns the face itself
Arial Black         900   1.00x   REFUSED
```

Synthetic bold is a **constant +23/1000 em**, not a percentage, so the ratio collapses
as weight rises (1.44x at stem 52.7, 1.17x at 115.2). A drawn bold's ratio is whatever
the designer chose — Arial 1.54x, Segoe UI 1.95x, Aeonik 1.73x. **There is no standard
ratio to preserve**, and quoting one as if there were is how a bad pairing gets
defended.

**Why:** the counter cost of a double-strike is 15–21 units, which destroys weight 700+
and nothing below. "Word must never synthesise a bold" was written for Bold and got
generalised to every weight, producing three days of structures protecting faces that
were never at risk.

**How to apply:** structure a multi-weight family the way Arial and Segoe UI do — one
RIBBI core with a real bold, every other weight a plain face in its own `nameID1`
(`nameID2 = Regular`, `macStyle 0`) grouped by `nameID16`. `Arial Black` is a plain
face, not Arial's bold. No Microsoft family links a light weight to a heavy one. See
[[drop-the-bold-slot-to-free-the-ladder]] and [[user-manual-qc-is-reliable]].
