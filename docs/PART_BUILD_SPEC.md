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
  Import a STEP into a scratch design to measure it. (The legacy model and its `build/baseline.json` were removed 2026-10-31; both are in git history.)

## Every part file
1. The source of truth is the part's generator (`parts/src/<PN>_gen.py`), which writes the build script
   `parts/src/<file>.json` marked `"generated_by"`; a few older parts have a hand-written script and no
   generator. Rebuild with `python tools/regen_parts.py <PN>` (re-runs a stale generator, then builds and
   freezes `parts/<PN>_<Name>.solidcraft`). Pick points are computed in the generator (AGENTS §3).
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
   - wood: walnut veneer `#6b4a32` (desktop, modesty panel); the PC slat front is walnut too
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
| FRM-03L | Side rail 4040 left, drilled (mirror of FRM-03R, so its own file) | 1 | SideRail_L_4040_HFS5 |
| FRM-03R | Side rail 4040 right, drilled | 1 | SideRail_R_4040_HFS5 |
| FRM-04 | Stile 2040 | 3 | Stile_Main/Side/Right_HFS5 |
| FRM-05 | Privacy panel, 12 mm PET felt, top corners R `pnl_r` (V1) | 1 | ModestyPanel |
| FRM-06 | Knee brace 2040, 45 deg mitred (D20) | 2 | Brace_L/R (new, no legacy body) |
| FRM-07L | Hanger plate left, 5 x 80 x 530 steel, 14 M5 csk + 3 desktop-screw slots (D21; mirror of FRM-07R, so its own file) | 1 | HangerPlate_L |
| FRM-07R | Hanger plate right (D21) | 1 | HangerPlate_R |
| FRM-08 | Side panel (corner return on the upright outer face), 12 mm PET felt (V1); L = R turned 180 deg | 2 | SidePanel_L/R (new) |
| MON-01 | Main monitor 32in | 1 | Monitor_Main + Monitor_Main_Back (one body) |
| MON-02 | Side monitor 27in (generic, not picked yet) | 1 | Monitor_Side + Monitor_Side_Back (one body) |
| SPK-01 | Klipsch R-40M speaker | 2 | Speaker_L_R40M + SpkFace_L_* (multibody allowed) |
| SPK-02 | Speaker mount flange | 2 | SpkMount_L_Flange |
| SPK-03 | Speaker mount block | 2 | SpkMount_L_Block |
| SPK-04 | Speaker mount swivel | 2 | SpkMount_L_Swivel |
| SPK-05 | Speaker tilt wedge (62x32 variant only) | 2 | SpkWedge (new, no legacy body) |
| PC-01 | Fractal North case | 1 | PC_FractalNorth |
| PC-02 | Walnut slat front | 1 | PC_FrontSlats |
| PC-03 | Under-desk strap | 1 | PC_Strap |
| INP-01 | Mouse pad 16.5in | 1 | MousePad |
| INP-02 | Razer DeathAdder V3 Pro | 1 | Mouse_DAV3Pro_* (multibody allowed; source refs/razer_dav3pro/DAV3Pro.step) |
| INP-03 | ErgoDox EZ left | 1 | Keyboard_L (outline refs/ergodox_ez/*.dxf) |
| INP-04 | ErgoDox EZ right | 1 | Keyboard_R |
| LAP-01 | Laptop mount arm (user-built jig placeholder, bolts to the right stile's front slot, D19) | 1 | new (LaptopMount_Arm) |
| LAP-02 | MacBook Pro 14in M4 | 1 | new (MBP_*, multibody allowed) |
| LAP-03 | Laptop tray (user-built jig placeholder) | 1 | new (LaptopTray) |
| CHR-01 | Herman Miller Mirra 2 chair, Butterfly back (vendor 3D DWG mesh: seat down, arms up and back) | 1 | Chair_* (multibody allowed; source refs/herman_miller_mirra2/converted/CHR-01_mirra2.step via parts/src/CHR-01_convert.py) |
| ACC-01 | Desk cable grommet, printed, d80 flange, sleeve through the grom_d hole (D24) | 1 | new |
| ACC-02 | Console audio bay: Scarlett Solo + USB hub flush, tail under the bar (D24) | 1 | new |
| ACC-03 | Console phone bay: iPhone landscape + MagSafe puck (D24) | 1 | new |
| ACC-04 | (retired 2026-11-02: control bay; the fingerprint dongle plugs into the hub, the KVM key moved to ACC-05) | 0 | — |
| ACC-05 | Console duckyPad bay: KVM key column + duckyPad Pro case sunk flush (D24) | 1 | new |
| ACC-06 | Console inlay line, light grey strip (D24) | 1 | new |
| ACC-11..17 | Console devices (purchased refs): Scarlett Solo 3rd Gen, ABFCRTTW hub, iPhone 16 Pro Max, MagSafe charger, fingerprint dongle, duckyPad Pro (user's case STEP), KVM key | 1 each | new (multibody allowed) |

Hardware is in `parts/lib/` (HW-L01 HPTTD5, HW-L02 HPTLD5, HW-L03 HBLFSN5, HW-L04 HBLFSD5, HW-L10 M6x55
SHCS, HW-L11 standoff, HW-L12 end cap); its occurrences HW-01..HW-58 come from `skeleton/hw_placements.json`. Eye becomes a skeleton
point in the assembly, not a part.

## Edit speed (applies to every part)
Inserting a part or refreshing its link re-runs its whole history, so every second a part takes is paid
again on every assembly build, link refresh and sweep case.
- Profile the part with `solidcraft-cli run <script> --save <tmp> --timings --profile --json-out t.json`.
  Target **< 3 s** for layout-driven parts and **< 5 s** for detailed purchased models. Report the number.
- Booleans on the detailed HFS5 DXF profile are slow. Cut features into a plain box blank, then
  intersect it with the profile once (see FRM-03 `Intersect_SideBolts`).
- Fewer, larger features: one sketch plus one cut for a group of holes or keys, patterns instead of copies,
  no per-instance features. Avoid fillets on many tiny edges. Model the visible detail (outline, finish
  splits, key rows, grilles as a few slots), not internals.
- Purchased models with a fixed shape don't import the skeleton (they won't be rebuilt by `regen_parts`).
  If they're still slow, report it: they may be frozen to an imported-STEP part file.
- **Keep the existing local origin and axes** of a part you redo, so `tools/build_assembly.py` placements
  stay valid. If the real product needs a different datum (e.g. the VESA centre isn't the screen centre),
  keep the origin at the mounting datum, move the geometry, and report it.
- Don't edit `skeleton/params.json`. Propose parameter changes (name, new expression, source) in your
  report, and the main agent applies them.
