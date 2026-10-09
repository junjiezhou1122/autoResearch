# First real pilot

## Question

Does the current research skill suite improve task output over a direct prompt or generic reflection when the model, input evidence and number of API calls are held constant?

This run is a pilot on a fixed subset. It does not test the full research runtime or establish that state-conditioned routing beats random routing.

## Conditions

| Condition | Prompt | Calls per task |
| --- | --- | --- |
| direct | Original task and common protocol | 1 |
| reflection | Same task, plus generic draft/critique/revision instruction | 1 |
| skill-prompt | Same task, plus current skill suite as a prompt reference | 1 |

The suite is loaded from the actual SKILL.md files. Its router provides the map; the leaf skill instructions supply the local operations. Candidate generation never receives ground-truth labels or evaluation material. Input prompt length is not matched: the suite contains substantially more instruction tokens. Any advantage therefore concerns the suite prompt as a whole, not the effect of typed primitives isolated from instruction length.

## Tasks and scoring

Select published tasks through the installed adapters. Start with a seeded subset of comparative research-success forecasting, evaluated using its documented local metric and both presentation orders. If the scientific-generation evaluator is usable, add ResearchBench tiny with its 12 published generation tasks. Record any scoring deviation from the published benchmark.

Use the same tasks, evidence, provider, model, temperature and output cap across conditions. Interleave calls. Capture request/response artifacts, actual returned model identifier, usage, finish reason, errors and elapsed time. Invalid or missing outputs count as failures rather than disappearing from the denominator.

## Runtime verification

Separately verify a real task in claude-research with the temporary autoresearch plugin. Use a fresh clean working directory and explicitly load the common CLAUDE.md protocol. Read stream events to verify loaded skills and actual primitive execution. This check demonstrates runtime behavior; it is not pooled with the API comparison.

## Limits

The provider's routing label may not pin an upstream model version. Public scientific tasks can have training-data contamination. A small pilot may be inconclusive. An all-skills prompt differs from progressive disclosure through Claude Code. Generation judge scores and objective winner prediction measure different things. Report each result separately.

## Budget

Prefer TokenDance MiMo-V2.6-Flash if current access is available. Start with one connectivity request and a bounded pilot before scaling. Use a low output cap and fixed concurrency. Report usage-based cost estimates only when current pricing is verified; do not represent estimates as billed cost.
