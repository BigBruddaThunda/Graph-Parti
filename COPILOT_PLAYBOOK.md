# GitHub Copilot Chat Assistant — Orchestration Plan & Playbook

This playbook defines a practical automation loop for Graph Parti using the Ralph Loop, SCL, and GitHub workflows. It is intended to guide a Codex/ChatGPT-style agent (or GitHub-integrated bot) as it audits, classifies, generates, and validates documentation and code artifacts.

---

## Short Answer
- Use the Ralph Loop as an automated, repeatable pipeline: ingest repo content → audit/context-scan → classify into Orders/districts and assign SCL zip codes → generate or update working documents (.md/.parti stubs) → create tasks (issues/PRs) with zip-coded scope → run automated validators/linters → iterate.
- Run that pipeline with a Codex/ChatGPT agent (via OpenAI API or a GitHub-integrated bot) plus lightweight automation (scripts + GitHub Actions) so the model executes “loops” and produces human-reviewable outputs.

**Operational directive (adopted):** We will use the Ralph Loop as the standard automation pipeline for Graph Parti. Each iteration must follow the ingest → audit → classify → generate → task → validate → iterate sequence, with results captured in artifacts that are reviewable and traceable via zip codes.

---

## 1) High-Level Architecture of the Orchestration
- **Ingest layer**: clone/read repository files (README.md, INDEX.md, SCL.md, each Order file, Ralph parti.txt).
- **Analysis / Audit layer (AI)**: run model tasks that produce structured outputs: file role, suggested Order, suggested SCL zip(s), missing documentation, dependencies, risks.
- **Organize layer (AI + templates)**: generate working documents per district (objectives, acceptance criteria, subtasks) and `.parti` stubs that map content onto the canvas model.
- **Task/Execution layer**: create issues, branches, and PRs (or local branches) with generated working docs and code skeletons; assign zip-coded labels.
- **Validation loop**: automated SCL/zip validators + human review + tests; feed results back into the Audit layer (Ralph Loop iteration).
- **Continuous integration**: GitHub Actions to run audits, linters, and (optionally) agent runs on schedule or PR events.

---

## 2) Setup & Required Components
- **Authentication**: GitHub token (repo write if automation should push PRs/issues), OpenAI API key for Codex/ChatGPT.
- **Repo structure**: keep the 7+1 Order files and an explicit `docs/working/` folder for generated docs and `.parti` artifacts.
- **Tooling**:
  - A small orchestrator (Python/Node) that:
    - reads files via GitHub API or local clone
    - calls the model(s) with well-formed prompts
    - translates model JSON outputs to files, issues, or PRs
  - GitHub Actions flows to run audits on push/PR/schedule
  - A lightweight SCL validator (script) to check zip formats and color termination rules

---

## 3) The Ralph Loop Automated Pipeline (Practical Steps)
- **Step A — Full repo scan (one-off / scheduled):**
  - Read every file, compute metadata (size, headings, existing zip tokens, existing TODOs).
  - Produce a “Context Wall” — a JSON summary of all content for the model.
- **Step B — Audit pass (AI):**
  - For each file, ask the model to: summarize the file, recommend an Order (🐂..🖼 or 🧮), propose canonical zip codes (one or more), and list missing architectural items or ambiguities.
- **Step C — District mapping:**
  - Aggregate file-level recommendations into a proposed district map consistent with INDEX.md.
  - Produce working-doc skeletons for each district: objective, scope, acceptance criteria, minimal interfaces (.parti schema), example zip codes.
- **Step D — Task generation:**
  - From working-doc skeletons, generate concrete coding tasks (issues) and break features into implementation steps, each with one or more zip codes and a clear acceptance test. Create labels based on Orders and Colors (e.g., Order:🐂, State:🔵).
- **Step E — Implementation scaffolding:**
  - Create branches & PRs that add the working docs, `.parti` skeletons, and simple code/test harnesses (e.g., SCL validator, interpreter stub, canvas data model).
- **Step F — Validation & audit loop:**
  - Run SCL rules, file-format validators, and automated unit tests. Feed results back to the model for remediation and refinement.
- **Step G — Iterate until stable.**

---

## 4) Prompt Engineering — Templates You Can Use

### A) Repo-scan prompt (system + user skeleton)
- **System**: You are a Graph Parti organization assistant. Output JSON following schema X.
- **User**: Here are files: (attach file list and short contents or links). Use SCL rules from SCL.md and the Ralph Loop from Ralph parti.txt. For each file return this JSON:
```json
{
  "path": "...",
  "summary": "short 1-2 sentence",
  "primaryOrder": "🐂|⛽|...|🖼|🧮",
  "suggestedZips": ["🐂📍🏛🔵", "🐂🧲🛒🟡"],
  "missingItems": ["e.g., missing acceptance criteria", "no example .parti stub"],
  "risk": "low|medium|high",
  "recommendedNextAction": "e.g., create working-doc, refactor, split file"
}
```

### B) District-skeleton generation prompt
- **Input**: aggregated file suggestions for an Order.
- **Request**: produce a working-doc with sections:
  - Objective
  - Scope
  - Files covered
  - Zip code conventions used in this district (canonical set)
  - Minimal `.parti` JSON stub (with header + one sample block)
  - Acceptance criteria (3–5 points)
  - Suggested tasks (title + description + zip + estimate)

### C) Task/Issue generator prompt
- **Input**: working-doc skeleton.
- **Request**: produce an array of issues where each issue is:
```json
{
  "title": "Short title",
  "body": "Description, acceptance criteria, example zip(s), files to modify",
  "labels": ["Order-🐂","state-🔵","area:core-architecture"],
  "assignees": [],
  "estimate": "2d / 4h"
}
```

### D) Zip refactor / validator prompt
- **Input**: a list of existing zip usages extracted from files.
- **Request**:
  - Identify invalid zips (color in middle, non-canonical emojis).
  - Propose canonical replacements abiding by SCL rules.
  - Output suggested edits as: file path, line, old text, new text, suggested commit message (include zip).

---

## 5) Example Small Audit Result (Illustrative)
- **File**: SCL.md  
  - **primaryOrder**: 🐂  
  - **suggestedZips**: `["🐂📍🧲🔵"]` (SCL reference)  
  - **missingItems**: `["explicit machine-readable zip index (JSON) for fast lookups"]`  
  - **recommendedNextAction**: "Add machine-readable zips file (scl_index.json) and link from SCL.md"

---

## 6) Automating with GitHub Actions & Scripts
- **Workflow triggers**:
  - on push to main or on schedule (nightly).
  - on pull_request to run the audit on the PR branch.
- **Steps in the Action**:
  1. checkout
  2. run `./scripts/repo_scan.py` — produces `context.json`
  3. call the AI (via openai CLI or local wrapper) with context.json and repo files
  4. parse model JSON output; if changes are suggested, create branch and push working-docs + `.parti` stubs and open a PR
  5. run SCL validator and basic unit tests
  6. report results (comment on PR, create issues for manual review)
- **Safety**: require human review before merging any AI-produced PR.

---

## 7) Example Orchestrator Pseudocode (Python Outline)
- list files via GitHub API
- for each file, fetch content
- call model with repo scan prompt, receive JSON
- aggregate by Order
- call model to produce district working docs
- create branch, add files, open PR (use GitHub API)
- create issues for high-priority tasks

---

## 8) Validation & SCL Linter Ideas
Implement rules:
- Color termination: no color emoji allowed in non-final positions in a zip
- Zip length limits
- Only use the 61 canonical emojis (load from SCL.md)
- Valid district zip patterns for parent headers

---

## 9) Naming Conventions, Commits & Traceability
- Commit titles and PR titles should include a primary zip for traceability, e.g.:
  - `🐂📍🏛🔵 add .parti schema for Core Architecture`
- Use labels for Orders and Colors: order/tuscan, state/planning, priority/urgent.
- Add a small file `scl_index.json` mapping canonical emoji → meaning to help parsers.

---

## 10) Human Review & Governance
- Keep a human‑in‑the‑loop gate:
  - AI opens PRs with working docs and code stubs.
  - A reviewer checks: correctness of zip assignment, acceptance criteria, tests.
- Maintain a change‑log for SCL changes (treat as an RFC process).

---

## 11) How to Use Ralph parti.txt as Central Vision
- Make Ralph parti.txt the "source of truth" for product vision and features:
  - Ingest it at the start of each audit pass, and require each working-doc to reference relevant Ralph sections.
  - When generating features, include the Ralph fragment used (line range) in the working doc so reviewers can see the rationale.

---

## 12) Example SCL Usage for Organizing Files (Mapping Examples)
- INDEX.md → 🐂📍🏛🔵 (Foundation / planning / structured)
- SCL.md → 🐂📍🧲🔵 (Foundation / language / structured)
- 🐂-tuscan.md → 🐂📍🏛🔵 (Foundation / core-architecture)
- 🦋-ionic.md → 🦋📍🔨🟢 (Building / implementation / active)
- Ralph parti.txt → 🧮🪐🟡 or 🐂🪐🟡 (System scratchpad + vision / exploring)
- When model suggests new district files, include their zip(s) in the new filename or front matter.

---

## 13) Example Minimal .parti JSON Stub (for an Order)
```json
{
  "header": {"id":"uuid","name":"core-architecture","version":"1.0.0","created":"2026-02-04T...Z"},
  "config": {"cellSize":48,"dialSystem":{},"theme":{}},
  "canvas": {"cells":[],"strokes":[],"viewport":{"x":0,"y":0,"zoom":1}},
  "content": {
    "blocks":[
      {"id":"b-core-zip","zip":"🐂📍🏛🔵","title":"Zip code system","type":"block","state":"🔵"}
    ],
    "districts":[],
    "layers":[]
  },
  "logic": {},
  "history": {"commits":[]},
  "assets": {}
}
```

---

## 14) Acceptance Criteria & Metrics for the Loop
- Per iteration, require:
  - Every file has a suggested primary Order or marked as scratchpad.
  - Working docs (for high-level features) authored for all key districts.
  - At least one `.parti` stub per Order covering core schema.
  - SCL linter passes for new/modified files.
  - PRs include acceptance criteria and at least one unit-test or integration harness where relevant.
- Metrics to track:
  - Percent files assigned to an Order
  - Number of zip violations per scan
  - Number of TODOs remaining
  - PR review turnaround time

---

## 15) Next Steps and a Recommended First Run
- **Manual initial run:**
  1. Run a repo-scan locally or via a one-off GitHub Action, ask the model to produce the JSON audit.
  2. Review the audit and accept proposed working-doc skeletons for 2–3 high-value districts (e.g., SCL, Core Architecture, Execution).
  3. Let the agent create branches with those working-docs (`.md` + `.parti` stubs).
  4. Review PRs, fix SCL misassignments, merge.
- After manual calibration, enable scheduled runs to keep the architecture up to date.

---

## Security & Governance Notes
- Never allow automatic merge of AI-generated changes without human approval.
- Keep API keys and tokens secret; run automation in controlled GitHub Actions with least privilege.
- Add a CONTRIBUTING.md that explains how AI-generated artifacts are reviewed and accepted.
