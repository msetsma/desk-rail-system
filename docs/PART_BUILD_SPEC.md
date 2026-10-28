# Part build spec (compliance Phase 3)

Shared rules for every part-file builder. Read `PROJECT.md` (section "SolidCraft capabilities")
and `.claude/skills/cad-best-practices/SKILL.md` first.

## Tools
- Use only the headless `solidcraft-cli`. Never use the MCP SolidCraft tools, which drive the live app,
  and never edit `desk_rails.solidcraft`.
- Script format: `{"commands":[{"command": id, "params": {...}}]}`. Use absolute paths with forward slashes.
- Docs: `solidcraft-cli commands`. Check results with `solidcraft-cli eval`, and look at
  `solidcraft-cli snapshot --in X --out build/parts_snapshots/<file>.png`.
- Reference geometry, in world coordinates of the legacy assembly, is exported as STEP in `build/export/`
  (`DSK.step`, `FRM.step`, `MON_PC_INP_REF.step`, `SPK.step`). Bodies keep their legacy names.
  Import a STEP into a scratch design to measure it. Legacy volumes, bboxes and centres of mass are in
  `build/baseline.json`.

## Every part file
1. The source of truth is a build script in `parts/src/<file>.json`. Its output is
   `parts/<PN>_<Name>.solidcraft`. Rebuild with
   `solidcraft-cli run parts/src/<file>.json --save parts/<file>.solidcraft`.
2. The script starts with the materials from `parts/_template.json`. Parts sized by the layout or by a
   `MEASURE` estimate then run
   `parameters.import {path: "C:/Users/2015m/DEV/CAD/desk/skeleton/params.json"}`, and drive their
   dimensions with those parameter names (e.g. `frame_w - 2*leg_inset`). Don't hard-code a number that a
   skeleton parameter already holds. Parts that are pure vendor geometry (STEP) skip the import.
3. Each file has **one final body**, with a `body_name` that is not a default name. Name the features
   too (pass `name`, or `timeline.rename`). Delete tool bodies and unused sketches.
   - Exception: purchased reference models (speaker, mouse) may have several bodies so each finish
     can have its own colour. Every body still gets a meaningful name.
4. Set metadata:
   - `document.metadata.set` with part_number, description and revision `A`.
   - The key `com.setsma.desk` = `{Material, ReleaseState: "WIP", Source}`.
5. Assign a material from the template with `material.assign`, and an appearance colour (PROJECT.md):
   - DeskHaus Silver powder-coated steel frame `#a8acaf`
   - aluminium extrusion `#d4d8dd`
   - wood: use what the legacy model had (measure the colour, or use a sensible walnut or butcher-block colour)
   - vendor parts keep their legacy colours. You can read colours in a scratch import, or ask in your report.
6. **Local origin**: choose a functional datum (mating face or centre line), and document it in the
   description, e.g. "origin: top face centre, +Y toward wall". For left/right pairs, one file serves both
   sides; the second occurrence is rotated 180° about Z. Check that the rotation reproduces the other
   side's legacy bbox. If it doesn't (e.g. hole patterns aren't symmetric), report it and make two files.
7. Verify:
   - The volume is within 0.1 % of `baseline.json`, and the bbox size matches within 0.01 mm. Explain any
     difference.
   - There are 0 timeline errors and 0 warnings.
8. Report, per file:
   - part number, file, body name(s) and volume (with the baseline delta)
   - local origin and axes
   - **placement**: the world position of the local origin for each legacy occurrence, as
     `x, y, z, yaw` **expressions in skeleton parameters** (yaw about Z). Also list any non-zero tilt.
   - whether the part imports the skeleton (it's layout-driven)
   - gotchas, with exact error text

## Part numbers (part files, not occurrences)
| PN | Name | Occ. | Legacy bodies |
|---|---|---|---|
| DSK-01 | Desktop | 1 | Desktop |
| DSK-02 | Top support | 2 | TopSupport_L_JC, TopSupport_R_JC |
| DSK-03 | Channel bar | 4 | ChannelBar_* |
| DSK-04 | Leg | 4 | Leg_LF/LB/RF/RB |
| DSK-05 | Foot | 2 | Foot_L, Foot_R |
| FRM-01 | Upright 4040 | 2 | Upright_L/R_HFS5 |
| FRM-02 | Crossbar 2040 | 2 | Crossbar_Low/High_HFS5 |
| FRM-03 | Side rail 4040, drilled | 2 | SideRail_L/R_4040_HFS5 |
| FRM-04 | Stile 2040 | 2 | Stile_Main/Side_HFS5 |
| FRM-05 | Modesty panel | 1 | ModestyPanel |
| MON-01 | Main monitor 32in | 1 | Monitor_Main + Monitor_Main_Back (one body) |
| MON-02 | Side monitor 27in | 1 | Monitor_Side + Monitor_Side_Back (one body) |
| SPK-01 | Klipsch R-40M speaker | 2 | Speaker_L_R40M + SpkFace_L_* (multibody allowed) |
| SPK-02 | Speaker mount flange | 2 | SpkMount_L_Flange |
| SPK-03 | Speaker mount block | 2 | SpkMount_L_Block |
| SPK-04 | Speaker mount swivel | 2 | SpkMount_L_Swivel |
| PC-01 | Fractal North case | 1 | PC_FractalNorth |
| PC-02 | Walnut slat front | 1 | PC_FrontSlats |
| PC-03 | Under-desk strap | 1 | PC_Strap |
| INP-01 | Mouse pad 16.5in | 1 | MousePad |
| INP-02 | Razer DeathAdder V3 Pro | 1 | Mouse_DAV3Pro_* (multibody allowed; source refs/razer_dav3pro/DAV3Pro.step) |
| INP-03 | ErgoDox EZ left | 1 | Keyboard_L (outline refs/ergodox_ez/*.dxf) |
| INP-04 | ErgoDox EZ right | 1 | Keyboard_R |

Hardware is in `parts/lib/` (HPTTD5, HPTLD5, HBLFSN5, M6x20 SHCS, standoff). Eye becomes a skeleton
point in the assembly, not a part.
