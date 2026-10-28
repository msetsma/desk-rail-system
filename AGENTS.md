# Agent instructions: CAD projects

Generic rules for parametric CAD work driven by an agent.
Project-specific facts (files, launch command, vendors, standards, known quirks) live in
`PROJECT.md`. Read it first.

These are living rules. When a session finds a better way, or something goes wrong, change the
rule here (or in `PROJECT.md` if it's project-specific) and add a line to the **Improvement log**.
Keep rules short and actionable. Delete rules that turn out to be wrong.

Detailed modeling practices (structure, naming, metadata, checks, versioning) and the
pre-milestone cleanup checklist are in the skill `.claude/skills/cad-best-practices/SKILL.md`.
Load it before starting a new part or assembly, restructuring components, or preparing a milestone or commit.
Core rules that always apply:
- Mirror the physical object: one real part = one component; parts installed together = a subassembly.
- Root holds components only. Activate the target component before modeling in it.
- Ground one component; place the rest with joints or parameter-driven moves.
- Name everything that matters at creation; key dimensions are named user parameters.
- Parts reference a shared skeleton or layout parameters, not each other.
- One editor per design file at a time (this applies to subagents too).
- Run the cleanup checklist before each milestone or commit.

## 1. Workflow

- The design file named in `PROJECT.md` is the source of truth. Edit it live, save, commit when asked.
- Verify narrowly after each change: measure or interference-check only the changed bodies and their
  neighbours. Run full checks, audits or BOM builds only when asked.
  - Narrow means each changed body against only the bodies whose bounding boxes come near it, as
    separate pairs. One all-against-all call over the same lists checks every combination.
  - Skip designed face-to-face contacts (catalog hardware on its host) unless asked: exact checks of
    coincident faces are very slow, and placement already verifies them.
  - A quick check can run in the live app if the user isn't using it. Anything over ~10 s runs headless
    in the background with capped threads, because the live app has a single command queue.
- Before restructuring, dump a baseline (every body's bbox, volume, centre of mass). Afterwards, verify
  by regression against it, not by screenshots.
- Note estimated or unmeasured dimensions as such (e.g. a `MEASURE` comment) and say so when relying on them.
- Purchased parts: use real vendor CAD when it exists, and model from photos or drawings only when it doesn't.
- Color every part in its real finish, never a placeholder color.
- Log design decisions where `PROJECT.md` says (decision log, guide) with the reasoning.

## 2. File organization: parts vs assembly

Every feature in a big assembly timeline makes later rebuilds slower, and editing early features
triggers a full rebuild.

- **Each self-contained part lives in its own file** (`parts/<PART-NO>_<name>.<ext>`), built around its
  own local origin with its own parameters. Bring it into the assembly as a linked component and place
  it with a joint or a parametric move. Refresh links after editing a part.
- The assembly keeps layout parameters, placement, configurations, and features that need
  assembly context (matched hole patterns across parts, lengths driven by assembly parameters).
- Vendor CAD: strip kits (screws, nuts, internal joints) down to the part body in a scratch
  design. Save the result next to the raw download and insert that.
- Move existing in-assembly parts out to part files whenever you touch them.
- When parts are built from scripts, link **frozen** outputs (geometry import + finishes), not files
  with history. Inserting a part re-runs its history, so freezing makes inserts and refreshes cheap.
  Keep the history version as a build artifact for inspection.
- Refresh only the links that changed. Refreshing everything re-evaluates every link.
- Keep an existing object (e.g. a desk you already own) in the main assembly unless nesting has been
  measured to help. Nested links can flatten the BOM and need chained refreshes.

## 3. Modeling rules (performance)

- Add new features at the **end** of the timeline. Replace old bodies by removing them, not by editing or
  renaming early features. When early edits are unavoidable, batch them into one rebuild.
- Change several parameters in one call when the API allows it, so the model rebuilds once.
- Name bodies when you create them, with unique names. Renames may propagate through features.
- Repeated features (holes, bolts, slats): one sketch + one feature, or a pattern. Never one feature
  per instance.
- Cut and join tools should overrun the faces they start or end on by ~0.1 mm. Coincident faces
  cause slow boolean retries.
- **Profile any build slower than ~30 s once** (per-command timings / boolean profile). One slow
  feature in a part is paid again every time the part is inserted, refreshed, swept or rebuilt.
  Fix it before building on top of it.
- Query the design narrowly (single feature, single command schema). Full design dumps are huge.
  Write big listings to a file and summarize them with a script. Don't pull them into context.
- Long calls may move to the background. Wait for the completion notification and don't resend.
- Run anything over ~1 min (builds, sweeps, full checks) in the background, and keep working.

## 4. Getting vendor parts and references

Use the **lightest, quickest path** that works, in this order:
1. Direct file URL, vendor API or JSON endpoint (`curl`, a WebFetch call or a short script).
2. Plain HTTP form posts or download links found in the page source.
3. Browser automation (Playwright) only when the vendor requires an interactive session.

- Batch every part you need into one run and run it in the background, so one slow vendor doesn't block other work.
- Vendor forms that ask for the user's email: fill it in from memory. Don't make the user re-enter it.
- Save downloads and photos under `refs/<vendor-or-part>/` with a short README giving the source
  and what is estimated.

## 5. Subagents and parallel work

**Use subagents by default whenever parallel work could plausibly speed things up, even marginally.
Don't ask first.**

A live CAD app usually holds one open design and one command queue, so only one agent drives the
live assembly at a time. Parallelize around it:

| Subagents (parallel) | Main agent |
|---|---|
| Research, specs, photos, datasheets | Editing the assembly |
| Vendor CAD downloads | Placement, joints, assembly parameters |
| Building parts in their **own** files (headless CLI or a separate session) | Final interference check, save, commit |
| Reviews: rule or guide checks, design critique, checks the user asked for | Integrating the results |

Pattern: the main agent writes a short spec per part (dimensions, origin, parameters, output path).
Subagents build the parts in parallel. The main agent inserts and places them, then verifies. While
subagents run, the main agent keeps working on non-conflicting tasks.

- **First wave = everything whose inputs exist.** As soon as the reference data is exported, spawn
  every independent job (part builds, placement solving, research). Don't hold a job for a later
  phase when its inputs are already there.
- **Specs carry the verified API conventions.** Put every tested convention (placement joint form,
  sign rules, required flags) into the subagent spec. When a spike leaves a case untested (e.g. a
  180° flip), test it before the specs go out.
- **Reuse what's already loaded.** Take baselines, exports and measurements from the open live
  design rather than re-evaluating a big file headless.
- **Independent check cases run in parallel** (sweep cases, per-group checks), each in its own
  scratch output.

## Improvement log

| Date | What happened | Rule change |
|---|---|---|
| 2026-10-27 | Full check after every edit took 10+ min | §1: verify narrowly; full checks only on request |
| 2026-10-27 | Renaming early-timeline bodies forced a full rebuild per rename | §3: build at end, name at creation |
| 2026-10-27 | Vendor screw and nut kits slowed every command | §2: strip kits to the part body |
| 2026-10-27 | A rename rippled into an unrelated feature and broke it | §3: unique names at creation |
| 2026-10-27 | One feature per bolt hole and coincident-face cuts: slow and a bloated file | §3: patterns + 0.1 mm overrun |
| 2026-10-28 | Parts-in-assembly history slows everything | §2: part per file, linked in |
| 2026-10-28 | User wants subagents used proactively, the lightest download path, no re-entering email | §4, §5 |
| 2026-10-28 | User supplied a CAD best-practice list | New skill `cad-best-practices` + core rules at top |
| 2026-10-28 | Compliance rebuild: 4 part-builder subagents ran headless in parallel (~10 min) while the main agent built the assembly | §5 pattern confirmed; spike the CAD API first (scratch, parallel) before restructuring |
| 2026-10-28 | Generated assemblies (script + regression vs a baseline bbox dump) caught a placement bug at once | §1: take a baseline before restructuring; verify by regression, not screenshots |
| 2026-10-28 | Audit of the 1 h 42 min compliance run: one 46 s hole feature cost ~25-30 min across inserts, builds and the sweep | §3: profile builds over 30 s and fix the hot feature first |
| 2026-10-28 | Speed spike: freezing linked parts and targeted link refresh. Inserts 42 s -> 9 s; a one-part refresh 40 s -> 0.3 s; a nested desk file flattened the BOM and saved < 1 s | §2: link frozen outputs, refresh only changed links, don't nest without measuring |
| 2026-10-28 | A thread-eval suggested live-app checks. Measured: loading the frozen assembly takes 0.65 s; a 14-pair check took 113 s because hardware-on-extrusion contacts took ~25 s per pair, and one all-against-all call re-added them | §1: per-body neighbour pairs, skip designed contacts, cap threads -> 4 s |
| 2026-10-28 | Same audit: a 10 min headless baseline re-eval, late-spawned placement and colour jobs (~6 min), a serial sweep (17 min vs ~5 parallel), 2 rebuilds from an untested 180° convention | §5: first wave, conventions in specs, reuse the loaded design, parallel check cases; §3: background long runs, no big dumps in context |
