---
name: drop-the-bold-slot-to-free-the-ladder
description: SUPERSEDED — the real answer was Arial's structure, not a cleverer bold-slot assignment.
metadata:
  type: project
---

I spent three structures trying to assign heavy weights into light families' bold slots
so every family would hold a real bold. Siwatch rejected it — *"bolding light to
extrabold is not make sense, and microsoft word itself do not make it happen
naturally"* — and named the reference: Arial.

**Why:** the constraint I was solving was self-inflicted. "Every family holds a real
bold" existed to stop synthetic bold filling Thai counters, which is only true at
weight 700+. Below that, synthesis is safe, and the whole assignment problem dissolves:
every weight becomes a plain face and only the RIBBI core needs a bold.

**How to apply:** when an assignment problem has no good answer, check whether the
constraint generating it is load-bearing before optimising inside it. And look at how a
shipping product solves the same problem — `C:\Windows\Fonts` was one `fc-list` away
the whole time. See [[word-decides-bold-from-usweightclass]] and
[[user-manual-qc-is-reliable]].
