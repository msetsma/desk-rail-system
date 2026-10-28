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

## 3. Modeling rules (performance)

- Add new features at the **end** of the timeline. Replace old bodies by removing them, not by editing or
  renaming early features. When early edits are unavoidable, batch them into one rebuild.
- Change several parameters in one call when the API allows it, so the model rebuilds once.
- Name bodies when you create them, with unique names. Renames may propagate through features.
- Repeated features (holes, bolts, slats): one sketch + one feature, or a pattern. Never one feature
  per instance.
- Cut and join tools should overrun the faces they start or end on by ~0.1 mm. Coincident faces
  cause slow boolean retries.
- Query the design narrowly (single feature, single command schema). Full design dumps are huge.
- Long calls may move to the background. Wait for the completion notification and don't resend.

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
