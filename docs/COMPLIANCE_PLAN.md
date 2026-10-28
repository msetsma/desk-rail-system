# Compliance plan: bring the desk project in line with AGENTS.md + cad-best-practices

Status: **executed 2026-10-28**. Follow `AGENTS.md`, `PROJECT.md` and the skill
`.claude/skills/cad-best-practices/SKILL.md` (load it first). The HBLFSD5 bracket swap waits until this plan is done.

## Deviations

What was done differently from the plan below:

- **Placement**: parts are placed with planar joints (angle 0) from the root origin, not with moves.
- **Speaker tilt**: lives inside `SPK-01`, driven by the skeleton, not by the placement.
- **L/R files**: side rails (`FRM-03L/R`) and keyboards (`INP-03/04`) have two files each,
  because they're mirror images. A 180° turn can't reproduce them.
- **Display states**: SolidCraft has none, so they are config rows (Full, Frame only, No desktop,
  Monitors + speakers).
- **Library names**: `parts/lib/` files use vendor part numbers (`HW-L01_HPTTD5` …).
- **Baseline**: the legacy timeline had 66 warnings, not 36.

## Where we are (audit, 2026-10-28)

| Rule | Current state |
|---|---|
| Root holds components only | Root has 2 loose bodies (`SideBolts_R/L_M6x20`) and **39 sketches**. 3 empty `VND_*` components remain from STEP imports |
| One real part = one component | Mostly yes (89 components). But the speaker parts are many bodies split across L1-L3, monitor screen and back are separate components, and the 16 bolts are 2 bodies |
| Parts in their own files, linked | **None.** Everything is built in one ~680-feature timeline (10.8 MB) |
| Purchased hardware as linked library parts | No. Misumi plates and gussets are copied bodies; bolts are cylinders |
| Ground one + joints | `DSK-00` grounded with rigid joints between assemblies; parts are placed by `solid.move` |
| Names | **247 default-named features** (118 BodyTransfer, 76 Hole, 26 Move, 23 Remove, 3 Sketch). Sketches `Sketch1-3` |
| Properties / materials | No part numbers in properties, no materials (all "Default", 1.29 g/cm³) |
| Hidden = intentional | Hidden profile sketches, hidden vendor template bodies, suppressed 8020/V-slot features (32) |
| Timeline error free | 0 errors, **36 warnings** |
| Configurations | 8020 and V-slot rows broken. Only HFS5 is used |
| Named views / display states | None saved |
| Docs | README is stale (2040 side rails, box top supports, orange hardware) |

## Strategy

**Rebuild a clean assembly from part files rather than cleaning the legacy timeline.** The
legacy file is the reference for geometry and placement until the new one matches it. Then it
is archived. The legacy timeline is too large to rename or regroup in place: every early edit
costs a full rebuild.

## Phase 0: baseline (main agent, ~15 min)
1. Commit the current work (frame, top supports, 4040 rails, bolts, AGENTS/PROJECT/skill) as milestone
   `pre-compliance`.
2. Export a **baseline report** from the legacy file to `build/baseline.json`: every body's name,
   component, bbox, volume and center of mass. Also export the parameter table with
   `parameters.export` to `skeleton/params.json`.
3. Save legacy screenshots (iso, front, back, right, top) to `build/baseline/` for visual diffs.

## Phase 1: capability spike (subagents in parallel, scratch files only)
Answer these in scratch designs and record the answers in `PROJECT.md` (Known quirks / Capabilities):
1. `component.insert_design` + `component.update_links`: does editing a part file and refreshing update the assembly?
2. **Can a linked part be driven by assembly parameters?** (e.g. a channel bar's length = f(`frame_w`)).
   Options to test: per-occurrence parameter override, `parameters.import` from a shared
   `skeleton/params.json`, configurations inside the part file.
3. Joints between linked components (rigid / slider at a named frame) and moves driven by assembly parameters.
4. Can `solidcraft-cli` build or save part files headless **while** the live app is open? (This sets how
   parallel the part builds can be.)
5. Mirroring: can one part file be used twice, rotated (top supports L/R, legs, feet)?
6. Metadata and material APIs: `component.metadata.set`, `document.metadata.set`, `material.assign`,
   `assembly.bom` output.
7. Named views and display states: `view.save`; are visibility sets or display states supported?

**Fallback if (2) fails:** parts whose size depends on assembly layout (channel bars, cut-to-length
extrusions, desktop, modesty panel) stay as **in-assembly components built from the skeleton
parameters**: one component each, named features, grouped. Everything with a fixed shape becomes a
linked part file.

## Phase 2: shared resources (main agent + 1 subagent)
- `parts/_template.solidcraft`: mm units, property fields (part number, description, material,
  release state WIP/Released, revision), appearance scheme from `PROJECT.md`.
- `parts/lib/` hardware library (one file per part, single body, material and metadata set):
  - Misumi: `HPTTD5`, `HPTLD5`, `HBLFSN5` (from the stripped STEPs in `refs/misumi_brackets/`), later `HBLFSD5`.
  - Fasteners: M6x20 SHCS (ISO 4762), M5 CBM5 + HNTT5-5 T-nut (only if shown), panel standoff.
- Update `PROJECT.md` conventions: part-number list, materials table (steel/powder coat, Al 6063-T5
  extrusion, Al 383 cast, zinc-plated steel, walnut, butcher-block wood, ABS/PC plastics).

## Phase 3: part files (subagents in parallel, one file each, headless)
Each subagent gets a spec: geometry source (legacy feature or STEP), local origin, parameters,
material, part number, appearance, output path. One final body per part, everything named, no
default names. Each verifies its volume against the baseline.

| Group | Part files (occurrences) |
|---|---|
| DSK | Desktop (1), Top support (2, rotated), Channel bar (4)\*, Leg (4), Foot (2) |
| FRM | Upright 4040 (2), Crossbar 2040 (2)\*, Side rail 4040 drilled (2: L/R hole sets, or one mirrored)\*, Stile 2040 (2)\*, Modesty panel (1)\* |
| HW | library occurrences: HPTTD5 ×2, HPTLD5 ×4, HBLFSN5 ×14, standoff ×8, M6x20 ×16 |
| MON | Main monitor (1 body: screen + rear housing), Side monitor (1) |
| SPK | R-40M speaker (purchased reference model: subcomponents for finish colors are allowed, ×2), mount flange / block / swivel |
| PC | Fractal North case, walnut slat front, strap |
| INP | Mouse pad, DeathAdder V3 Pro (Razer STEP, subcomponents allowed), ErgoDox L, ErgoDox R |
| REF | Eye: a construction point or sketch in the skeleton, not a solid body |

\* layout-driven: these follow the Phase 1 (2) answer or the fallback.

Rule for purchased reference models (speaker, mouse): multiple bodies for finish colors are fine,
grouped as subcomponents of one purchased component. Write this down in the skill as an
allowed exception.

## Phase 4: new assembly (main agent only)
1. New `desk_rails.solidcraft` (same name, so tools and docs keep working). Move the legacy file to
   `legacy/desk_rails_legacy.solidcraft` (also tagged in git).
2. Skeleton: import `skeleton/params.json` (only HFS5; drop the 8020/V-slot configuration and
   its features). Add a layout sketch (or construction planes and points) at key datums: frame top, upright
   axes, monitor VESA centers, Eye.
3. Ground `DSK-00`. Insert linked parts under the same assembly tree (DSK/FRM/HW/MON/SPK/PC/INP/REF)
   and place them with joints, or with moves driven by skeleton parameters. Activate the target component
   before any in-assembly feature.
4. Root: components only. Every feature named; related features grouped (`timeline.group`).

## Phase 5: metadata, materials, display
- Every component: part number (+ `Rev A` once checked), description, material, release state WIP.
- Real materials assigned at part level (mass and COG now meaningful for `tools/audit.py`).
- Named views: iso, front, back, right, top, side-rail joint L/R, speaker mount, under-desk.
- Display states (or configurations) for visibility sets: "frame only", "no desktop",
  "monitors + speakers". Use the fallback from Phase 1 (7) if display states aren't supported.

## Phase 6: verification (main agent; the full checks are approved as part of this plan)
1. Regression: compare the new assembly's body bboxes and volumes to `build/baseline.json`.
   Tolerance 0.01 mm / 0.1 %. Every difference must be explained.
2. Full interference + clearance check, once.
3. Parameter sweep: `desk_w` ±100 mm, `rail_s`, `desk_h` sit/stand. Everything follows; no errors.
4. Cleanup checklist from the skill (8 items) passes; timeline has 0 errors and 0 warnings.
5. `tools/check.py`, `tools/bom.py`, `tools/audit.py` adapted to the new structure (BOM from
   part-number metadata instead of name parsing), run once.

## Phase 7: docs and release
- Rewrite `README.md` (tree, parts, parameters, measure checklist) from the new structure.
- Update `PROJECT.md` (capabilities, conventions, file map) and the AGENTS.md improvement log.
- Commit milestone `Rev A: compliant structure (parts linked, skeleton, metadata)`.
- Next task: HBLFSD5 2-slot gusset for the 4040 side-rail joint, added as a library part.

## Parallelism map
- Phase 0 ∥ Phase 1 spike (subagents in scratch files while the main agent takes the baseline).
- Phase 2 library ∥ Phase 3 part builds (one subagent per group: DSK, FRM, HW-lib, MON, SPK, PC/INP).
- Phase 4 and later: main agent only (single editor of the assembly file).

## Decisions for the user (defaults in bold)
1. Retire the 8020 / V-slot variants entirely: **yes** (they're broken, and HFS5 is what you buy).
2. Top supports, legs and feet: **one part file each, used rotated** (vs separate L/R files).
3. Purchased reference models (speaker, mouse): **subcomponents allowed for finish colors**.
4. Keep the assembly file name `desk_rails.solidcraft`: **yes**.

## Kickoff prompt (paste after compacting)
> Execute docs/COMPLIANCE_PLAN.md. Load the cad-best-practices skill first. Use the defaults for the
> open decisions unless I said otherwise. Use subagents in parallel per the parallelism map. Report
> after each phase with what changed and anything that deviates from the plan.
