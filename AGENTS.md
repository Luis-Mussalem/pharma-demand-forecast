Section 1 — Universal Instructions for the LLM (Reusable Across Projects)

These instructions define how the assistant must behave independently of the specific repository. They are reusable across engineering, ML, analytics, software architecture, and technical projects.

Mandatory Response Structure

Every answer must follow this order:

Reflection before implementation

Minimal change proposal

Exact file-level instruction

Architectural explanation

Test command

Commit suggestion

Explicit continuation cue

Reflection Before Code

Before suggesting any change, always explain:

what problem is being solved

why this change is needed now

why this specific file is the correct layer

why other files should not be changed yet

The explanation must come before code instructions.

Minimal Change Philosophy

Always prefer:

smallest correct change

local change before refactor

direct solution before abstraction

Never introduce new helpers, classes, wrappers, or abstractions unless there is real architectural pressure.

Surgical Precision Standard

Every implementation answer must specify:

exact file name

exact block

exact insertion point

exact replacement

exact ordering of changes

Avoid vague suggestions.

Ordered Execution Pattern

Implementation answers must always be sequenced as:

Step 1

Architectural rationale

Step 2

Exact file modification

Step 3

Code insertion or replacement

Step 4

Why architecture improved

Step 5

How to test

Step 6

Suggested commit

Architectural Meaning Requirement

After every code change, explicitly explain:

what became more robust

what duplication was removed

what future capability became possible

Commit Discipline

One commit must represent one clear architectural intention.

Avoid mixing:

cleanup + refactor

feature + documentation + bugfix in one commit

Preferred Commit Logic

Commits must read like engineering history.

Good examples:

add schema registry

activate schema version selection

stabilize inference pipeline after schema refactor

promote trained model as champion automatically

Test-First Closure

Every implementation answer must end with:

exact test command

expected result

exact executable git add + git commit command block

continuation cue

Continuation Cue

Always close implementation guidance with:

comente feito para prosseguirmos

Full Teaching Mode Requirement

For learning-oriented projects, answers must not stop at conceptual instruction. They must teach complete implementation.

Whenever code is changed, the assistant must provide:

full corrected code block for the local section being modified

final expected result after modification

exact before vs after understanding

The user must be able to understand not only what changes, but what the final code should look like.

Code Delivery Standard

Enforcement Addendum — Mandatory Delivery Shape

For every implementation response, the assistant must include:

Exact insertion instruction
exact file path
exact anchor block
exact insertion point (before/after which line/block)
Full final code block
never send partial delta when local structure matters
always send the complete final function or complete final local block
Explicit replacement instruction
state exactly what to replace
state exact final text that must remain in file
Verification closure
exact test command
expected result
executable git add + git commit command block
If any of these items is missing, the response is non-compliant.

Whenever a function is modified:

Do not describe only the delta.

Also provide:

complete final function

complete final block when imports are affected

final surrounding context if indentation matters

Teaching Priority Over Minimal Diff When Learning Is the Goal

If the project explicitly has educational purpose, the assistant must optimize for understanding.

That means:

Even when the change is small, show the final full local code when it improves comprehension.

Explain Why The Code Looks Like This

After presenting code, always explain:

why each block is placed there

why indentation matters

why this exact order is correct

Avoid Partial Fragment Confusion

Never leave the user needing to infer missing lines when the local structure matters.

Especially for:

functions

imports

control flow

YAML files

config files

Preferred Teaching Sequence For Code Answers

Reflection

Exact file

Exact block

Full final code block

Why this final structure is correct

Test

Executable commit command block

Every creation/change in a document must generate a unique commit.

Commits must respect "xxx: xxxxxxxx" format (example = add: add a new feature or document.)

comente feito para prosseguirmos

Tone Requirements

Responses must be:

clear

objective

precise

technically rigorous

calm

ordered

Avoid:

excessive verbosity

generic abstractions

speculative complexity

Anti-Inflation Rule

Never add complexity only to make code look advanced.

Only introduce complexity when current architecture justifies it.

Duplication Detection Rule

If duplicated logic exists:

identify owner layer

centralize ownership

remove secondary copies

Repository Thinking Rule

Every suggestion must consider:

readability for future reviewers

historical coherence

realistic professional standards

Conversation Continuity Rule

When continuing an ongoing implementation thread, the assistant must anchor the next answer to the current chat history before proposing changes.

The answer must explicitly identify:

what was already completed in prior turns

what remains open now

which previous architectural decisions constrain the next step

why the proposed next step follows from the existing repository evolution

If the new answer could apply equally to any repository, it is too generic and must be rewritten using the current project history.

Repository-State Grounding Rule

Before proposing a new architectural step, the assistant must verify that the proposal matches the actual repository state.

At minimum, the assistant must ground the proposal in:

current artifact ownership

current runtime orchestration files

current active model-selection policy

current persistence and archive behavior

The assistant must not propose a design that conflicts with the repository's actual governance model, even if the proposal is generically valid.

Depth Consistency Rule

When the user asks to continue a multi-day implementation, the answer must preserve the same reasoning depth and architectural granularity already established in the conversation.

The assistant must not regress into a generic or greenfield-style explanation if the repository already has a known history in the current chat.

The answer must connect the next step to the named work that came immediately before it.

Mismatch Recovery Rule

If the assistant detects that a new answer is materially more generic, shallower, or less repository-specific than the immediately preceding implementation guidance, it must self-correct before finalizing the response.

The corrected answer must restate:

the active project phase

the relevant completed work from the current chat

the repository constraint that invalidates the generic answer






Section 2 — Project-Specific Instructions (pharma-demand-forecast)

These instructions apply specifically to this repository.

Project Identity
Name

pharma-demand-forecast

True Purpose

This project was deliberately designed with two simultaneous goals:

Build real maturity in Data Engineering and ML Architecture.

Produce a repository that demonstrates professional technical reasoning to recruiters.

This is not only a forecasting project. It is a controlled architecture exercise.

Core Design Philosophy

Every layer must justify its existence.

Nothing should exist only to look sophisticated.

The repository must show:

modularity

explicit ownership of responsibilities

reproducible runtime

governance over artifacts

clean evolution by small commits

architecture without premature abstraction

Current Technical State (End of Day 14)
Data Ingestion

File:

[ingestion.py](http://_vscodecontentref_/49)

Responsibilities:

controlled CSV loading

dtype enforcement

date parsing

immediate validation handoff

Training Validation Layer

File:

[validation.py](http://_vscodecontentref_/50)

Responsibilities:

expected columns

expected dtypes

granularity validation

fail-fast contract enforcement

Inference Validation Layer

File:

[inference_validation.py](http://_vscodecontentref_/51)

Responsibilities:

required inference columns

null control

semantic validation of DayOfWeek

leakage protection (Sales removal)

known null handling for Open

Schema Governance

Files:

[schema_registry.py](http://_vscodecontentref_/52)

[schema_version.yaml](http://_vscodecontentref_/53)

Current behavior:

Training and inference contracts are versioned.

Runtime flow:

schema_version.yaml -> schema_registry.py -> validation modules

Feature Engineering

Files:

[processing.py](http://_vscodecontentref_/54)

[feature_registry.py](http://_vscodecontentref_/55)

Implemented features:

calendar

lag

rolling

promo

Training Layer

File:

[training.py](http://_vscodecontentref_/56)

Champion baseline:

HistGradientBoostingRegressor

Current benchmark:

MAE ≈ 508

RMSE ≈ 779

Evaluation Layer

File:

[evaluation.py](http://_vscodecontentref_/57)

Outputs:

predictions

metrics

diagnostics

feature importance

Artifact Governance

File:

[artifacts.py](http://_vscodecontentref_/58)

Current artifact lifecycle:

timestamped artifacts

archive rotation

benchmark history

diagnostics persistence

champion promotion

promotion explainability report

distribution baseline persistence

inference drift report persistence

Drift Monitoring Layer

File:

[drift.py](http://_vscodecontentref_/59)

Responsibilities:

model-input baseline statistics

z-score mean-shift drift evaluation

non-blocking drift status generation

Inference Layer

Files:

[inference.py](http://_vscodecontentref_/60)

[predict.py](http://_vscodecontentref_/61)

Current inference supports:

latest model policy

explicit champion file policy

champion-aligned baseline lookup

drift report generation

Model Governance

Files:

[model_registry.yaml](http://_vscodecontentref_/62)

Current champion policy:

latest

explicit filename

Champion Promotion Lifecycle

Current behavior:

Training evaluates and promotes based on policy.

Inference consumes active governed model.

Architecture Already Built by Days
Day 1–3

Foundation:

ingestion

validation

splitting

baseline training

Day 4–5

Feature engineering maturity:

lag

rolling

calendar

Day 6–7

Artifacts and diagnostics:

predictions

benchmark history

diagnostics

Day 8

Inference separation:

inference data isolation

runtime path separation

Day 9

Inference validation layer:

dedicated inference validation module

Day 10

Schema governance:

schema registry

schema version selection

training and inference symmetry

Day 11

Model governance:

model registry

explicit champion selection

automatic champion promotion

Day 12

Benchmark-aware promotion policy

Day 13

Explainable promotion decision trace

promotion report artifact

Day 14

Champion-aligned drift baseline and inference drift report

Immediate Future Likely Direction
Day 15

Most natural next step:

dashboard-oriented consumption of promotion and drift governance artifacts

Possible directions:

store-level drift segmentation

alert thresholds by feature family

promotion and drift unified observability panel

Project-Specific Golden Rule

Every step must answer:

Is this relevant now?

Does this improve architecture?

Does this improve governance?

Does this improve repository maturity?

Is this minimal enough?

Preferred Closure Inside This Project

Implementation answers must always finish with:

- exact test command
- exact executable git add + git commit command block
- what this unlocks next

Day Closure Checklist (mandatory)
When closing a "Day", perform and record all items below before marking the Day complete:

- Update `docs/engineering_decisions.md` with a "Day X" block that:
  - lists decisions implemented during the day,
  - lists verification commands and their results,
  - records any remaining TODOs and next steps.
- Update `README.md` 
- Update `AGENTS.md` if the agent contract or workflow rules changed.
- Add/Update automated tests that exercise new governance or runtime behavior.
- Run required local verification:
  - governance tests: `python -m unittest discover -s tests -p "test_model_governance.py" -v`
  - optional pipeline smoke: `python main.py --config config/pipeline_config.yaml`
- Commit documentation changes with an exact git add + git commit block.
- Push commits and tag to remote.

Always include a short "closure note" in `docs/engineering_decisions.md` describing verification results and tag name.

comente feito para prosseguirmos





Section 3 — Historical Errors, Real Fixes, and Anti-Regression Memory

This section documents real errors already encountered in the project. Its purpose is to prevent repeating solved problems and to preserve architectural reasoning.

Error History Must Be Treated as Architectural Knowledge

An error is not only a bug. It usually reveals:

a missing contract

a wrong ownership layer

an incomplete runtime assumption

a hidden duplication

Future suggestions must consider these historical lessons before proposing new changes.

Historical Error 1 — Mixed dtype in StateHoliday
Error Observed

DtypeWarning: mixed types

Root Cause

The Rossmann dataset mixes numeric and string representations in StateHoliday.

Correct Fix Applied

Explicit dtype control during CSV load inside src/ingestion.py.

Architectural Lesson

Ingestion is not raw reading. It is the first contract boundary.

Anti-Regression Rule

Never remove explicit dtype declaration for StateHoliday.

Historical Error 2 — Training Validation Applied to Inference Data
Error Observed

Missing columns: {'Customers', 'Sales'}

Root Cause

Training validation contract was being applied to inference input.

Correct Fix Applied

Created dedicated inference validation layer:

src/inference_validation.py

Architectural Lesson

Training and inference contracts are structurally different and must evolve independently.

Anti-Regression Rule

Never reuse validation.py for inference.

Historical Error 3 — Lag Features Broke Inference
Error Observed

KeyError: 'Sales'

Root Cause

Lag and rolling features depend on historical target values. Future inference data does not contain Sales.

Correct Fix Applied

Created inference context reconstruction:

build_inference_context() in src/inference.py

Using recent historical observations before feature generation.

Architectural Lesson

Forecast inference requires context reconstruction before temporal features.

Anti-Regression Rule

Never generate lag or rolling features on future-only data.

Historical Error 4 — Nulls in Open During Inference
Error Observed

Inference input contains null values in required columns.

Root Cause

future_data.csv contains known nulls in Open.

Correct Fix Applied

Inside src/inference_validation.py:

Known nulls in Open are filled before null enforcement.

Architectural Lesson

Known dataset conventions must be handled before fail-fast validation.

Anti-Regression Rule

Do not generalize fillna globally. Only treat known semantic exceptions.

Historical Error 5 — Feature Name Mismatch During Inference
Error Observed

Feature names unseen at fit time: Id

Root Cause

Inference dataset still carried Id into model input.

Correct Fix Applied

Explicit drop of Id inside inference preparation.

Architectural Lesson

Operational identifiers must not leak into model feature space.

Anti-Regression Rule

Keep Id removal explicit inside inference pipeline.

Historical Error 6 — Empty Inference Matrix After Dropna
Error Observed

Found array with 0 sample(s)

Root Cause

Aggressive dropna removed all inference rows after rolling features.

Correct Fix Applied

Fill only rolling feature columns after preparation.

Architectural Lesson

Missing-value policy must distinguish structural missingness from feature-generated edge missingness.

Anti-Regression Rule

Never apply broad dropna to inference feature matrix.

Historical Error 7 — Wrong Pandas sort_values Signature
Error Observed

takes 2 positional arguments but 3 were given

Root Cause

Incorrect sort_values call.

Correct Fix Applied

Use list syntax:

sort_values(["Store", "Date"])

Architectural Lesson

Temporal ordering must remain explicit and stable.

Anti-Regression Rule

Always use list-based sort for multi-column ordering.

Historical Error 8 — Nullable Integer Mismatch in Training Validation
Error Observed

Column 'Open' has dtype 'Int64' but expected 'int64'

Root Cause

Pandas nullable integer type reached validation layer.

Correct Fix Applied

Schema contract updated in schema_registry.py:

Open -> Int64

Architectural Lesson

Schema must reflect runtime reality, not idealized assumptions.

Anti-Regression Rule

Do not force schema to ideal dtypes when runtime uses nullable pandas types.

Historical Error 9 — Inference Runtime Config Missing
Error Observed

KeyError: 'inference'

Root Cause

pipeline_config.yaml lacked inference runtime block.

Correct Fix Applied

Added:

data_path

history_window_days

Architectural Lesson

Runtime parameters belong in pipeline config, not in schema registry.

Anti-Regression Rule

Keep runtime config separate from contract config.

Historical Error 10 — Duplicated Inference Validation Logic
Error Observed

Validation existed both in:

src/inference.py

src/inference_validation.py

Root Cause

Refactor left old validation logic in orchestration layer.

Correct Fix Applied

Removed local validation function from src/inference.py.

Single owner became:

src/inference_validation.py

Architectural Lesson

Validation ownership must remain unique.

Anti-Regression Rule

Never duplicate contract logic across orchestration and validation layers.

Historical Error 11 — Champion Model Governance Was Implicit
Problem Observed

Inference selected latest model implicitly.

Root Cause

No explicit model policy existed.

Correct Fix Applied

Created:

config/model_registry.yaml

Added:

explicit champion support

automatic promotion after training

Architectural Lesson

Latest artifact is not always equivalent to promoted model.

Anti-Regression Rule

Champion policy must remain external to inference code.

Historical Error 12 — Empty Promotion Benchmark CSV Crash
Error Observed

pandas.errors.EmptyDataError while generating promotion report

Root Cause

benchmark_history.csv existed but was empty (no header, no rows), and read_csv raised before empty dataframe checks.

Correct Fix Applied

Added EmptyDataError fallback in [artifacts.py](http://_vscodecontentref_/65) save_promotion_report:
empty file now maps to an empty DataFrame and follows benchmark_history_empty report path.

Architectural Lesson

Artifact readers must treat empty files as a governed state, not an unhandled runtime exception.

Anti-Regression Rule

Keep explicit EmptyDataError handling in promotion report generation.

Historical Error 13 — Inference Contract Mismatch After Drift Integration
Error Observed

ValueError too many values to unpack in [predict.py](http://_vscodecontentref_/66)

Root Cause

[predict.py](http://_vscodecontentref_/67) expected run_inference to return predictions and inference matrix, while [inference.py](http://_vscodecontentref_/68) still returned only predictions.

Correct Fix Applied

Updated [inference.py](http://_vscodecontentref_/69) run_inference to return both result and scored matrix.

Architectural Lesson

Cross-layer return contracts must evolve atomically when observability depends on model input matrices.

Anti-Regression Rule

Keep inference return contract synchronized with [predict.py](http://_vscodecontentref_/70) drift orchestration expectations.

Global Anti-Regression Rule for Future Changes

Before modifying any pipeline layer, first ask:

does this touch a previously solved contract?

does this recreate a solved duplication?

does this violate an existing ownership boundary?

does this hide a runtime assumption already documented?