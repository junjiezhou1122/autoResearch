---
name: research-mode
description: Route the current research task to useful research skills and execute them through to the requested output.
disable-model-invocation: true
---

# Research mode

You do not need to remember every research primitive.

Describe where the research currently stands. Route to the smallest useful primitive or short flow.

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

## Routing rule

Choose the smallest useful skill or short flow for the current research state.

Load each selected skill through the Skill tool and follow its instructions. Do not substitute this navigation map for the skill's work.

Use the result as intermediate work, reassess the research state, and continue with useful operations until you can deliver the original task's requested output. Do not ask for confirmation between operations the task already authorizes.

Let the research state determine which skills to use and when to stop. Preserve the task's evidence restrictions and final output format.
