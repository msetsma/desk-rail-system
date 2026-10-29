# Herman Miller Mirra 2 work chair, Butterfly back: CHR-01 reference

Model: `parts/src/CHR-01_gen.py` -> `parts/src/CHR-01_HermanMillerMirra2.json`. Parameters are `chr_*`.
Downloads are in `raw/` (git-ignored: vendor files, local only).

## Identification
The user's chair is a Mirra with a fabric back. The original Mirra (2003) and the Mirra 2 TriFlex back
are all-polymer backs with holes. Only the **Mirra 2 Butterfly back** (polymer loop + AireWeave textile
suspension, called "Suspension Back" in Herman Miller's 3D library) has a fabric back. So the chair is a
Mirra 2 with the Butterfly back. Arms are modelled as the fully adjustable 4D arms (assumed; confirm with the user).

## Sources
- Product sheet (`raw/Mirra_2_product_sheet.pdf`):
  https://www.hermanmiller.com/content/dam/hermanmiller/documents/product_literature/product_sheets/Mirra_2_product_sheet.pdf
  - Seat height: standard 16-20.5 in, low 14.75-19, extended 16.75-22.25
  - Seat depth: fixed 16.25 in, FlexFront 16.25-18 in
  - Butterfly work chair statement-of-line: 30 in wide, 18.5 in, 41.75-43.75 in high
- Brochure (`raw/Mirra_2_brochure.pdf`), same folder on hermanmiller.com.
- Specs page: https://www.hermanmiller.com/products/seating/office-chairs/mirra-2-chair/specs/
  - Suspension back, adjustable arms: H 41.8-43.8 in, W 26.5-31 in, D 26.5 in, arm height 6-11.5 in
- HM store (https://store.hermanmiller.com/office-chairs-ergonomic-chairs/mirra-2-chair/1453.html): arms
  6-11.5 in from the seat to the armpad top; 350 lb rated.
- Back2 (UK dealer, https://www.back2.co.uk/products/herman-miller-mirra-2-butterfly-chair): backrest
  582 mm high, 391 / 541 mm wide (waist / shoulders), base 673 mm, seat width 495 mm, back angle 94-107 deg.
- BTOD review (https://www.btod.com/blog/herman-miller-mirra-2-review/): seat 19.25 in wide, 27 in base.
- Herman Miller 3D library, Suspension Back + Adjustable Arms:
  https://www.hermanmiller.com/resources/3d-models-and-planning-tools/product-models/individual/mirra-2-chair-suspension-back-adjustable-arms/
  - Only SketchUp, AutoCAD 2D/3D DWG and Revit are offered (`raw/*.skp`, `raw/*_2D.dwg`, `raw/*_3D.dwg`).
- Adjustable-arm travel (HM store tooltip, price book): height 5.5 in (6-11.5 in seat to pad top), width 1.125 in,
  depth 2 in front to back, pivot +-20 deg.

## Conversion (2026-10-29)
CHR-01 is Herman Miller's own 3D DWG geometry. SolidCraft imports STL/OBJ/glTF only as mesh bodies, and a
design with mesh bodies can't be STEP-exported or linked (`insert_design`: "no solid bodies to link"), so
the mesh is written as a STEP of planar triangle faces, which imports as ordinary B-rep bodies.
1. LibreDWG 0.14 `dwg2dxf` (free zip, https://github.com/LibreDWG/libredwg/releases; installed at
   `C:/Users/2015m/cad_tools/libredwg/`, override with env `DWG2DXF`): `raw/*_3D.dwg` (R2004) -> `converted/mirra2_3d.dxf`.
   The DWG is 33,963 3DFACEs (35,022 triangles) in inches, one layer per part group (SEAT-FRAME, SEAT-BACK,
   SEAT-BACKFABRIC, SEAT-FABRIC(TRIM), SEAT-BASE, SEAT-ARMPAD, SEAT-CASTER, SEAT-SHAFT, SEAT-KNOBS ...).
   The DWG faces +X with its origin on the floor at the cylinder axis; it's turned +90 deg about Z (faces +Y).
2. `parts/src/CHR-01_convert.py` (ezdxf, trimesh, fast-simplification): layers and connected pieces -> finish
   bodies, arm settings baked in, full vendor resolution (no decimation; 30 % / 1500-cap decimation looked too rough, 2026-10-29), written by
   `tools/mesh_step.py` to `converted/CHR-01_mirra2.step` (~35k triangles, 33 MB; frozen part 15 MB) + `CHR-01_mirra2.json`
   (reference heights, per-body triangles and bbox, STEP hash).
3. `parts/src/CHR-01_gen.py` writes the part script (`"input": "refs/herman_miller_mirra2/converted/..."`),
   then `python tools/regen_parts.py CHR`. `converted/` is git-ignored (derived from the vendor files).
Tried and not used: the `.skp` (no free reader installed; Blender + SketchUp importer would work but the
DWG carries the same layers); the 2D DWG (drawing views only).
Known limits: the star base is triangle soup in the DWG (T-junctions, no shared vertices), so it isn't
decimated; edges between pieces are kept apart, because welded touching pieces (seat fabric on its trim)
make edges with 3+ faces, which SolidCraft imports but can't export to STEP. In "shaded with edges" the
faceted bodies show their triangle edges; use the "shaded" visual style for presentation.

## User settings (2026-10-29)
- Seat all the way down: `chr_seat_h` = 16 in (406.4 mm, standard cylinder minimum), measured at the top of
  the seat suspension (vendor SEAT-FABRIC peak, 496.5 mm in the DWG = 19.5 in). Parametric in the part: a move
  of everything above the gas cylinder (`chr_seat_h - chr_seat_h_vendor`).
- Arms "all the way up": the user sees the pad tops about level with the desk frame (584-635 mm above the
  floor once the desk was measured at 26.5 in, 2026-10-29), so pad tops are 200 mm above the seat = 606 mm,
  i.e. the DWG's own arm height (199.7 mm). The spec's 11.5 in maximum (698 mm) would sit above the desktop
  and hit its front edge. `ARM_H_MAX` in CHR-01_convert.py sets it (posts stretched above z 590 mm vendor).
- Pads slid fully back: 25.4 mm back from the DWG position (MEASURE: assumes the DWG shows them mid-travel).
- User's seated eye height: 46 in (1168 mm) above the floor = 762 mm above the seat top.

## Colours
Herman Miller sells the Mirra 2 frame/base in **Alpine** (white) and **Graphite** today. Older Mirra 2s came in
Studio White frame + Fog base (yourchairguy.com/mirra-2). The user's "white/grey body" matches that
pair, and "black/grey fabric" matches the Graphite textile.
| Body | Finish | Hex (estimated from photos) |
|---|---|---|
| Chair_Frame (Butterfly polymer back, spine, seat pan, lumbar), Chair_Arm_R/L | Studio White | #e8e6e1 |
| Chair_Base, Chair_Mechanism (tilt housing: vendor layer SEAT-BASE) | Fog | #bdbfbe |
| Chair_BackFabric, Chair_Seat | Graphite AireWeave | #2d2e30 |
| Chair_ArmPad_R/L | Graphite | #262729 |
| Chair_Controls (paddles, lumbar knobs) | black | #1f2022 |
| Chair_Cylinder, Chair_GasRod | black | #1c1d1f |
| Chair_Caster_1..5 | black | #1f2022 |
If the chair is the current Alpine version, change the frame and base to Alpine (~#dcdcd8).

## Estimated (MEASURE)
| Item | Value | Note |
|---|---|---|
| seat height reference | top of the seat suspension | HM's spec point isn't stated |
| arm pads back | 25.4 mm (half the 2 in travel) | assumes the DWG pads are mid-travel |
| arm stretch | posts lengthened above z 590 mm | real arms telescope; the shape matches, the joint doesn't |
| resolution | full vendor mesh, 35k triangles | facets visible up close (vendor DWG is a triangle mesh) |
