# Claude Code hypothesis generation

The user selected actual-use quality rather than equal-compute comparison, and confirmed ResearchBench generation tasks on 2026-10-08. They then clarified that the agent should receive one request invoking research-mode and continue autonomously until its final output. No scripted routing turns or fixed leaf-call counts are permitted.

## Conditions

All 12 ResearchBench tiny tasks run with the same clean claude-research launcher and MiMo-V2.6-Flash[1m]. Direct asks for a hypothesis. Reflection adds private draft, critique and revision. The skill condition begins with /autoresearch:research-mode and asks the agent to use suitable research operations and continue to a finished hypothesis. All receive the same evidence and final 80–150 English-word requirement.

Only Skill is exposed, so candidates cannot read local gold data or use web, shell, file or agent tools. Both baselines omit autoresearch. Built-in skills remain available and their actual calls are audited. Each candidate has a fresh neutral temporary cwd. The research plugin is copied into a neutral frozen directory with original skill contents. The common protocol is injected explicitly. No profile settings are changed.

A single user message and native agent loop are used. The model decides operations and stopping. A 600-second subprocess timeout is a runaway bound, not an assigned research-step count. The CLI default output limits and provider internal retry behavior are retained. No selective candidate reruns. Transport/model/format failures are preserved and counted. Two worker processes, seeded shuffled condition order per task. Main runs exclude separate functionality calibration.

## Observation and judgment

Save each prompt, argv, raw stream, stderr, final result, assistant turns, usage, elapsed time, Skill attempts and successful tool results. Entry expansion is checked from replayed native messages when available. If expansion cannot be established, report the weaker evidence. A recommendation without final hypothesis is not a completed task.

Reuse the installed ResearchBench generation scoring prompt and parser with blinded Ling-3.1-Flash. Candidate receives no gold hypotheses. Use the existing bounded scorer and one uniform retry of failed judge responses. The score is target-hypothesis match, not proof of novelty or empirical success. Missing hypotheses receive zero as a disclosed local extension, while judge failure leaves means unavailable until resolved. Retain word-format violations separately.

Report complete task denominator, per-task paired score changes, mean/median duration, successful and attempted skills, model request turns, input/cache/output tokens and all failures. CLI estimated cost is not billed cost. Extra compute and extra instructions remain part of the treatment; this run cannot isolate a causal benefit from routing alone. One run per task and one model is a pilot, not a stable general effect.

## Implementation sketch

Task rows retain task_id, sample_id and allowed prompt. Condition is a three-value registry. A candidate result owns status, final text, timing, init inventory, native result metadata and tool observations. One function launches a native request in a fresh cwd; one function parses its stream. The main function freezes inputs, creates a seeded schedule and writes results as each task completes. Scoring remains separate from candidate execution, keeping target data out of the runner.

The discarded design used two scripted user turns and a fixed leaf-call count. It was stopped after the user's clarification. The selected design delegates the research loop entirely to the agent.
