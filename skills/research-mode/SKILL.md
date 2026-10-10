---
name: research-mode
description: Route the current research task to useful research skills and execute them through to the requested output.
disable-model-invocation: true
---

# Research mode

Use the research skills to carry out the user's research task.

## Execution rule

For a research task, identify the current research state, choose the smallest useful operation, and load its leaf through the Skill tool before doing its work. Skill use is required in this mode; being able to answer directly is not a reason to skip it.

Follow the loaded skill's instructions, use its result as intermediate work, and reassess what the task still needs. Load the next applicable skill when further research work is needed. Choose operations from the current state, not a fixed sequence.

Apply the task's evidence, resource and tool restrictions to every operation. Loading a skill does not authorize web access or additional data. When search is restricted, check prior mechanisms within the supplied evidence and state the limit.

Keep intermediate skill outputs separate from the final deliverable. Return the original task's requested content and format, and continue without confirmation between authorized operations.

If a needed skill cannot be loaded, report that limitation accurately. Do not claim the skill was used.

## Starting from a paper or existing method

If the mechanism is unclear:
→ [`/autoresearch:reconstruct`](../reconstruct/SKILL.md)

If the mechanism is understood and you want to know what it depends on:
→ [`/autoresearch:assumption-map`](../assumption-map/SKILL.md)

From there, common branches are:

- questionable assumption → [`/autoresearch:assumption-break`](../assumption-break/SKILL.md)
- fixed design choice → [`/autoresearch:unfreeze`](../unfreeze/SKILL.md)
- narrow operating regime → [`/autoresearch:boundary-push`](../boundary-push/SKILL.md)
- unexplained residual behavior → [`/autoresearch:missing-mechanism`](../missing-mechanism/SKILL.md)

## Starting from observations or results

If you have raw results but no clear pattern:
→ [`/autoresearch:observe`](../observe/SKILL.md)

If two comparable cases behave differently:
→ [`/autoresearch:contrast`](../contrast/SKILL.md)

If one apparent failure may contain several distinct causes:
→ [`/autoresearch:factorize-failure`](../factorize-failure/SKILL.md)

If the current explanation cannot account for an observation:
→ [`/autoresearch:missing-mechanism`](../missing-mechanism/SKILL.md)

## Starting from an existing mechanism

To challenge one condition while keeping the rest similar:
→ [`/autoresearch:counterfactual`](../counterfactual/SKILL.md)

To apply the same abstract mechanism elsewhere:
→ [`/autoresearch:transfer`](../transfer/SKILL.md)

To replace a fixed decision with feedback:
→ [`/autoresearch:close-loop`](../close-loop/SKILL.md)

## Starting from a candidate research idea

First try to kill the novelty claim:
→ [`/autoresearch:prior-art-falsify`](../prior-art-falsify/SKILL.md)

If it survives and the mechanism is concrete:
→ [`/autoresearch:prediction`](../prediction/SKILL.md)

When the hypothesis and its strongest alternative make different predictions:
→ [`/autoresearch:minimal-experiment`](../minimal-experiment/SKILL.md)

## Common flows

Paper → new research problem:

[`/autoresearch:reconstruct`](../reconstruct/SKILL.md)
→ [`/autoresearch:assumption-map`](../assumption-map/SKILL.md)
→ choose one perturbation:
[`/autoresearch:assumption-break`](../assumption-break/SKILL.md), [`/autoresearch:unfreeze`](../unfreeze/SKILL.md), [`/autoresearch:boundary-push`](../boundary-push/SKILL.md), or [`/autoresearch:missing-mechanism`](../missing-mechanism/SKILL.md)

Observation → mechanism:

[`/autoresearch:observe`](../observe/SKILL.md)
→ [`/autoresearch:contrast`](../contrast/SKILL.md)
→ [`/autoresearch:missing-mechanism`](../missing-mechanism/SKILL.md)

Failure → intervention:

[`/autoresearch:factorize-failure`](../factorize-failure/SKILL.md)
→ [`/autoresearch:missing-mechanism`](../missing-mechanism/SKILL.md)

Candidate idea → test:

[`/autoresearch:prior-art-falsify`](../prior-art-falsify/SKILL.md)
→ [`/autoresearch:prediction`](../prediction/SKILL.md)
→ [`/autoresearch:minimal-experiment`](../minimal-experiment/SKILL.md)
