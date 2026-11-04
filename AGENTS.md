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

- The design file named in `PROJECT.md` is the source of truth. Edit it live and save.
- **Commit each finished feature without asking** (conventional message, one commit per feature, after its
  narrow checks pass and the cleanup checklist is run). Don't push unless asked.
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
- An outside review or sketch (PDF, chat) proposes positions from estimates: check every station against the model and the vendor assembly guide before building, and have the generator assert them against the skeleton.
- Note estimated or unmeasured dimensions as such (e.g. a `MEASURE` comment) and say so when relying on them.
- Record how a measured value was taken (tape, calipers, spec sheet, display reading) and when. Check the
  datum everything else hangs from (e.g. desk height) with a direct measurement, not an indicator.
- Purchased parts: use real vendor CAD when it exists. If it's in a format the CAD app can't import (DWG,
  SKP, Revit), convert it first (see `PROJECT.md`). Model from photos or drawings only when no CAD exists
  or the conversion fails, and say which.
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
- Anything the CAD API takes only as numbers (edge/face pick points, sketch origins) is computed in the
  part's generator from the same values that drive the geometry. Never hand-type it: it silently goes
  stale when a parameter changes.
- One source of truth per part: a generated script is never hand-edited (fix the generator).
- **Profile any build slower than ~30 s once** (per-command timings / boolean profile). One slow
  feature in a part is paid again every time the part is inserted, refreshed, swept or rebuilt.
  Fix it before building on top of it.
- Query the design narrowly (single feature, single command schema). Full design dumps are huge.
  Write big listings to a file and summarize them with a script. Don't pull them into context.
- Long calls may move to the background. Wait for the completion notification and don't resend.
- Cross-file edits (a rename, a retired part): grep every reference first, then make all edits in one script
  written with the file tool. Don't build scripts with heredocs inside longer shell commands: a stray
  command reading stdin hangs until the timeout. Match multi-line text regardless of line endings.
- Retiring a shared layout parameter is a layout change and rebuilds everything that reads the layout.
  Leave it unused and remove it with the next real layout change.
- Run anything over ~1 min (builds, sweeps, full checks) in the background, and keep working.

## 4. Getting vendor parts and references

Use the **lightest, quickest path** that works, in this order:
1. Direct file URL, vendor API or JSON endpoint (`curl`, a WebFetch call or a short script).
2. Plain HTTP form posts or download links found in the page source.
3. Browser automation (Playwright) only when the vendor requires an interactive session.

- Batch every part you need into one run and run it in the background, so one slow vendor doesn't block other work.
- Vendor forms that ask for the user's email: fill it in from memory. Don't make the user re-enter it.
- When a request names a hardware type (a plate, a bracket), confirm a catalog part exists and fits its envelope
  before building geometry around it.
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
| 2026-10-29 | Rules audit: a hand-typed edge point broke DSK-02 on a parameter change; stale stored skeleton values had mis-placed PC fillet picks; a hand edit (walnut panel) lived only in a generated script; per-part link refresh was skipped for 25-part skeleton changes; mesh bodies came back "unchecked"; CRLF/LF handled by hand; a vendor DWG was skipped for an envelope; the desk height came from the paddle, 3.5 in off | §1: commit each finished feature unasked, record how values were measured, convert vendor CAD before modelling; §3: computed pick points, one source per part; PROJECT: expressions-only skeleton + `skeleton_values`, `generated_by` + auto-regen, refresh-vs-rebuild threshold, near_check bbox fallback, `.gitattributes` |
| 2026-10-29 | Laptop fit: angular-bbox checks flagged false blocks, and a coarse (10x10 ray) placement search passed a spot that hid 2% of the monitor at full resolution | §1: check sightlines by ray casting against front faces; re-verify a searched optimum at full resolution, then pick the middle of the clear window |
| 2026-11-01 | Bolt-length change (M6x20 -> M6x55) took several extra minutes: a heredoc command hung on a stray stdin read (2 min timeout), a CRLF file broke a multi-line match mid-script, a generator-created library part needed a second regen pass, parallel main/variant builds raced on a shared scratch file (one extra rebuild), and deleting 2 unused skeleton params rebuilt ~24 parts instead of ~5 | §3: one grep + one file-tool edit script, line-ending-agnostic matches, retire layout params lazily; tools: regen re-reads the part list after generators and flags orphaned frozen parts, finish scratch files named per design |
| 2026-11-01 | Crossbar drop + right stile: 4 subagents (part build, rules review, generator cleanup, docs/tools) ran while the main agent did skeleton, placements and assembly; one regen + build at the end. A near_check on main + variant raced on shared scratch files (second instance of the shared-scratch bug) | Tools: every design-aware tool (near_check, sightlines, assembly_finish) names its scratch files per design; §5 pattern confirmed: review agent first, cleanup agents on disjoint file sets, one final rebuild |
| 2026-11-01 | Knee brace: the requested part (flat 45 deg joining plate) does not exist in the Misumi catalog, and the catalog bracket that does (HBL45TD5) forced a longer brace (120 -> 150 mm). Found only after the brace part and skeleton were built; one extra 27-part regen | §4: when a request names a hardware type, confirm a catalog part exists (and its envelope) in the first research wave, before building geometry around it |
| 2026-11-01 | Hanger plate from an outside review PDF: its stations came from estimates and missed the channel bars (one screw landed on a bar) and the 8 desktop screws into them (Apex guide step 3) | §1: check every station an outside review proposes against the model and the vendor assembly guide; generators assert stations against the skeleton (FRM-07_gen) |
| 2026-11-02 | Visual phase (felt panels, black, end caps): research + joint review + vendor CAD ran as 3 subagents while the main agent built; two decisions batched per question round. An end-cap near_check ran > 5 min because new face-seated hardware wasn't in the MATING list; a template material addition re-ran every generator (29 parts) | PROJECT: add new seated hardware to `near_check.MATING`; XZ sketch v = -Z |
| 2026-11-02 | Console build: device parts ran in a parallel subagent off one shared layout module (ACC_layout.py) while the main agent built bays + assembly; 3 boolean retries came from tool faces landing on pocket faces or a fillet's tangent line; near_check reported 0 pairs for devices vs bays because its `skip_within: component` skips bodies in the same group | PROJECT: near_check skips same-group pairs, check them with inspect.clearance directly; §3 overrun rule also applies between tool bodies |
| 2026-11-04 | Doc audit after D20-D24: README parts table, totals, finishes and side-rail section, BOM.md, lib README and PART_BUILD_SPEC colours had drifted over 3 days of features; the README render still showed the pre-console desk with a wireframe chair (model screenshots always draw edges) | PROJECT: README render recipe (raytrace, `Readme` setup); update the README table and BOM with each feature that adds or retires a part |
| 2026-10-28 | Same audit: a 10 min headless baseline re-eval, late-spawned placement and colour jobs (~6 min), a serial sweep (17 min vs ~5 parallel), 2 rebuilds from an untested 180° convention | §5: first wave, conventions in specs, reuse the loaded design, parallel check cases; §3: background long runs, no big dumps in context |
