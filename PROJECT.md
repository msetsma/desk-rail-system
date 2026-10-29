# Project specifics: desk rail system

Companion to the generic `AGENTS.md`. Update this file when project facts or quirks change.

## Files and tools
- Assembly: `desk_rails.solidcraft` (SolidCraft, driven over MCP). It holds only linked part files placed
  with joints from the skeleton parameters. Live app:
  `solidcraft --control 27878 --allow-path "C:\Users\<user>\DEV\CAD\desk"`.
- Skeleton: `skeleton/params.json`, the shared layout and `MEASURE` parameters. Both the assembly and
  every layout-driven part import it. `skeleton/hw_placements.json` holds the hardware placements.
- Parts: the scripts `parts/src/<PN>_<Name>.json` and `parts/lib/src/HW-*.json` are the source of
  truth. A script may name a vendor file to start from (`"input": "refs/..."`). New parts start from
  `parts/_template.json` (materials) and follow `docs/PART_BUILD_SPEC.md`.
  - `parts/<PN>_<Name>.solidcraft` are **frozen** outputs: a STEP import plus materials, colours and
    metadata. They're what the assembly links, at about 1 s per insert. Don't edit them by hand.
  - Each part's build history is in `build/parts_hist/<stem>.solidcraft`. Open that one to inspect a part,
    then change the script.
- **Edit loop (fast):**
  1. Edit `skeleton/params.json` or a part script.
  2. Run `python tools/regen_parts.py` (it rebuilds only the parts whose script or skeleton changed, in
     parallel). It prints the components to refresh.
  3. In the live assembly, run `component.update_links {"component": "<name>"}` for each one (~0.3 s each).
     **Never use the bare `update_links {}`**: it re-evaluates every link (~40 s).
  4. A skeleton change also needs `parameters.import` of the skeleton into the assembly, for the placements.
- Parameter sweep (parallel, on private copies): `python tools/sweep.py`.
- Rebuild the whole assembly from scratch (~20 s): `python tools/build_assembly.py --out desk_rails.solidcraft`.
  Build straight to that path (the design name comes from the build path, so a copied file keeps the
  wrong name). Run `new_design` in the live app first, then `open`.
  `tools/assembly_finish.py` adds materials, properties, views and display rows.
- The desk (DSK group) stays in the main assembly rather than a nested file, as tested on 2026-10-28:
  - a linked sub-assembly is flattened to one BOM row
  - links don't chain, so every change becomes a two-step refresh
  - all of DSK costs < 1 s to insert
- Legacy single-timeline model (pre-compliance, reference only): `legacy/desk_rails_legacy.solidcraft`.
- Headless CLI: `solidcraft-cli run <script.json> [--in X] --save Y`.
- Narrow clearance after a change: `python tools/near_check.py <body prefixes>` (~4 s). It checks each
  changed body against its bbox neighbours and skips hardware-on-extrusion contacts.
  `--print-params` prints the commands for the live app. `--include-mating` keeps the contacts (slow).
- Sightlines + laptop fit: `python tools/sightlines.py [--set lap_az=36 ...]` (seconds). Ray-casts from the Eye to the
  speaker baffles, monitor screens and laptop screen, and box-checks the laptop against monitors, speakers and the frame.
  A coarse grid search can miss a small block: re-run the chosen point at the default resolution.
- Full check: `tools/check.py` (slow; run only on request). BOM: `tools/bom.py` -> `BOM.md`.
- Decision log and extrusion rules: `docs/EXTRUSION_GUIDE.md`. Cite rule IDs (J*, M*, P*, W*) and
  log decisions (D*) there.

## Standards and constraints
- Extrusion: Misumi HFS5 (5 series) only; the 8020 and V-slot variants are retired. Profiles come from
  `profiles/misumi_hfs5_*.dxf`, so `rail_l` and `rail_s` follow the profile and aren't free parameters.
- Buy, don't fabricate: joints use catalog parts. Vendor machining is OK, and user drilling is OK when
  the user agrees.
- Desk frame: DeskHaus Apex Pro 4-leg (Jiecang OEM), finished in Silver. No CAD exists; it's modelled
  from the dimension sheet and photos in `refs/`. `MEASURE` parameters are estimates.

## Conventions (for the cad-best-practices skill)
- Part numbers belong to part **files**, not occurrences. Group components `DSK-00`, `FRM-00`, `HW-00`,
  `MON-00`, `SPK-00`, `PC-00`, `INP-00`, `LAP-00`, `CHR-00`, `REF-00`; parts `DSK-01`…, library `HW-L01`…. Add `Rev X` when a
  part is released. `DSK-00` is grounded. The full list is in `docs/PART_BUILD_SPEC.md`.
- One file per left/right pair when a 180° turn about Z reproduces the other side. Mirror-image parts
  (side rails, keyboards) get two files.
- Purchased reference models (speaker, mouse) may hold several bodies, one per finish.
- Appearance: purchased parts get their real finish:
  - DeskHaus Silver powder-coated steel frame #a8acaf (refs/apex_pro)
  - aluminium extrusion #d4d8dd
  - zinc plates #c4c9d0
  - as-cast Al gussets #a9adb2
  - desktop (IKEA KARLBY walnut veneer, 503.352.08) and modesty panel (walnut veneer to match) #6b4a32,
    estimated from product descriptions

  Reference geometry is red.
- Materials are the custom set in `parts/_template.json`. They are stored in each part as
  `com.setsma.desk {Material, ReleaseState, Source}`, and the assembly re-applies them, because links
  don't carry them.
- Masses are envelope estimates: legs, PC case and monitors are solid blocks, so `mass_g` overstates them.

## SolidCraft capabilities (spike 2026-10-28, CLI v0.24.0)
- Script format: `{"commands":[{"command": id, "params": {...}}]}`. Use forward slashes in paths.
- `solidcraft-cli` builds and saves headless while the live app is open. Parallel runs are fine.
- Linked parts: `component.insert_design {path, name, parent?, reuse?}` stores a STEP copy plus a link.
  It only refreshes on `component.update_links {}`. `reuse:true` adds another occurrence of the same
  component.
- **Linked parts can't read assembly parameters**: there's no per-occurrence override, and insert_design
  ignores extra keys. Layout-driven parts import the shared skeleton instead with
  `parameters.import {path}`. Re-importing overwrites the values and rebuilds (tested).
- **Standard placement**: a planar joint from the root origin to the part's local origin:
  `{type:"planar", a:{occurrence:0, point:[0,0,0], z:[0,0,1], x:[1,0,0]}, b:{occurrence, point:[0,0,0], z:<zl>, x:<xl>}, flip:true, values:["<x>","<y>","<yaw>"], offset:"<z>", angle:"0 deg"}`.
  - `zl` and `xl` are the part-local directions that land on world +Z and +X; they encode any fixed
    rotation (a fixed half turn is `xl:[-1,0,0]`).
  - `angle:"0 deg"` is required. Without it, SolidCraft adds a half turn whenever that turns b less.
  - Only parametric yaws go in `values`. The placement follows parameter changes.
  - `occurrence.move` and `joint.origin` points take numbers only. `joint.drive` replaces expressions.
- Metadata: `component.metadata.set {component, part_number, description, revision, properties}` and
  `document.metadata.set`. Linked parts copy document metadata **once, at insert**. Material and free
  properties don't come through.
- Materials: `material.create {name, density_g_cm3}`, `material.assign {bodies, material}`.
- BOM: `assembly.bom {levels, group_by, path}`. The CSV has no material column; the JSON includes properties.
- Appearance: `appearance.assign {bodies|components, color}`; precedence face > body > component > material.
- Views: `view.save {name, camera:{target, yaw, pitch, distance}}`. Yaw 0 looks from the front (-Y);
  yaw < 0 orbits toward +X. `snapshot --view NAME` works.
- **No display states**: use config rows that suppress link features
  (`config.row {name, values:{"suppress:<feature>": true}}`). Rows: Full, Frame only, No desktop,
  Monitors + speakers.
- Naming: `timeline.rename`, `timeline.group {name, features}`. `solid.extrude` ignores `name` (the body
  stays `Body1`), so use `body_name` and check it. Patterns, chamfers and mirrors take `name`.
- `solidcraft-cli script` fails on designs with components (#886).

## Known quirks
- SolidCraft `body.rename` renames the string across all features.
- The MCP call timeout moves long calls to the background, and `pending` may say nothing is running.
- MCP `open` of a path whose design is already loaded (even after the file changed on disk) keeps the
  in-memory design. Run `new_design` first, then `open`.
- Linked inserts split multi-lump bodies into separate bodies (`PC_FrontSlats (2)` …).
- `component.insert_design` and `update_links` **re-evaluate the part's history**: an insert costs about
  what the part takes to build. Profile slow parts with
  `solidcraft-cli run <script> --timings --profile --json-out t.json`.
  - Booleans on the detailed HFS5 DXF profile are the expensive case: one `solid.hole` with 8 counterbores
    took 46 s.
  - The assembly build is ~120 s, of which the two side rails are ~105 s (2026-10-28).
- `component.update_links {}` re-evaluates every link, even unchanged ones (~40 s). Pass `component`.
- Full assembly builds log repeated non-fatal `knot vector consists single value` panics (source part
  not yet identified; likely a vendor NURBS body). The run still succeeds.
- Edge-pick points (`solid.chamfer`/`fillet` `edges`) are plain numbers, so a hand-written script breaks when its driving parameters change (DSK-02 `TS_EndTaper` failed after `ts_h` changed). Update the points with the parameter.
- `inspect.clearance` can report `0.000 mm` for a real 0.1 mm gap (seen on the laptop clamp vs the 2040 bar).
  Treat sub-0.2 mm "near" values as contact-level, not as a measurement.
- MCP `parameters.export` returns the full text even when given a `path`. `component.list` on the full
  assembly is large; use `solidcraft-cli ... --results --json-out` and summarize it.
- Eval names a body in a repeated placement with its occurrence path:
  `Leg (DSK-00 Desk frame:1/DSK-04 Leg:3)`.
- `solidcraft-cli eval <script> --in X` ignores the script; use `run --in X --save tmp`, then `eval`.
- `sketch.rectangle.*` rejects expressions; use `sketch.line` with expression points. `sketch.create`
  takes a numeric origin only, and `{face, body}` needs `index`.
- Mesh imports (`file.insert_mesh`: STL/OBJ/glTF) stay mesh bodies: no STEP export, and `insert_design` refuses a
  design with only mesh bodies. Vendor meshes go through `tools/mesh_step.py` (planar-face STEP, imports as B-rep;
  ~2 s linked insert per 11k triangles; the chair keeps the full 35k for looks). Keep touching pieces unwelded: edges with 3+ faces break STEP export.
  DWG -> DXF: LibreDWG `dwg2dxf` (C:/Users/2015m/cad_tools/libredwg/), see refs/herman_miller_mirra2/README.md.
- Misumi: 3D CAD is generated server-side (slow) and needs a login or email. HFS5 extrusion 3D
  CAD isn't offered; profiles come from DXFs in `profiles/` / `refs/ext_*`.
