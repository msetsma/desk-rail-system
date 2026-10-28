# Project specifics: desk rail system

Companion to the generic `AGENTS.md`. Update this file when project facts or quirks change.

## Files and tools
- Design: `desk_rails.solidcraft` (SolidCraft, driven over MCP). Live app:
  `solidcraft --control 27878 --allow-path "C:\Users\<user>\DEV\CAD\desk"`.
- Headless CLI: `solidcraft-cli run <script.json> [--in X] --save Y`.
- Parts directory: `parts/` (to be created, see AGENTS.md §2). Vendor raw files: `refs/`.
- Full check: `tools/check.py` (slow; run only on request). BOM: `tools/bom.py` -> `BOM.md`.
- Decision log and extrusion rules: `docs/EXTRUSION_GUIDE.md`. Cite rule IDs (J*, M*, P*, W*) and
  log decisions (D*) there.

## Standards and constraints
- Extrusion: Misumi HFS5 (5 series). Config row `Misumi_HFS5` is the only maintained one; the
  `8020_20series` / `OpenBuilds_Vslot` rows are broken (body transfers name HFS5 bodies).
- Buy, don't fabricate: joints use catalog parts. Vendor machining is OK, and user drilling is OK when
  the user agrees.
- Desk frame: DeskHaus Apex Pro 4-leg (Jiecang OEM). No CAD exists; it's modelled from the dimension
  sheet and photos in `refs/`. `MEASURE` parameters are estimates.

## Conventions (for the cad-best-practices skill)
- Part numbers: assembly groups `DSK`, `FRM`, `HW`, `MON`, `SPK`, `PC`, `INP`, `REF` + `-NN`
  (e.g. `FRM-05`). Add `Rev X` when a part is released. `DSK-00` is grounded.
- Appearance: purchased parts get their real finish (black steel frame, aluminium extrusion
  #d4d8dd, zinc plates #c4c9d0, as-cast Al gussets #a9adb2). Reference geometry is red.
- Hardware library: `parts/lib/` (to be created). Vendor raw files go in `refs/<vendor>/`.
- Known gaps against the skill: the legacy assembly still has many default names and no materials
  or part properties. Fix them as parts move out to their own files.

## Known quirks
- SolidCraft `body.rename` renames the string across all features.
- The MCP call timeout moves long calls to the background, and `pending` may say nothing is running.
- Misumi: 3D CAD is generated server-side (slow) and needs a login or email. HFS5 extrusion 3D
  CAD isn't offered; profiles come from DXFs in `profiles/` / `refs/ext_*`.
