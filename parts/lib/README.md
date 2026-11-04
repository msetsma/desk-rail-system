# Hardware library (`parts/lib/`)

Standard purchased parts, one file per part, one named body each. Insert with
`component.insert_design {path, name}` and place with joints. Built headless with `solidcraft-cli`;
build scripts are in `src/` (`python src/gen_lib.py` regenerates them from `../_template.json`; then
`python tools/regen_parts.py HW-L` rebuilds the frozen files). `tools/assembly_finish.py` re-applies
the material and properties in the assembly.

| File | Part number | Body | Source | Material | Color | Local origin / frame | BBox min .. max (mm) |
|---|---|---|---|---|---|---|---|
| `HW-L01_HPTTD5.solidcraft` | HPTTD5 | `HPTTD5` | `refs/misumi_brackets/HPTTD5/HPTTD5_plate.stp` (vendor origin kept) | Steel, painted black (D23) | #1a1a1a | Vendor: T-plate in XY, top face Z=0, thickness to -Z; stem along +Y, symmetric in X | [-55, 0, -2.3] .. [55, 80, 0] |
| `HW-L02_HPTLD5.solidcraft` | HPTLD5 | `HPTLD5` | `refs/misumi_brackets/HPTLD5/HPTLD5_plate.stp` (vendor origin kept) | Steel, painted black (D23) | #1a1a1a | Vendor: L-plate in XY, corner at origin, top face Z=0, thickness to -Z | [0, 0, -2.3] .. [80, 80, 0] |
| `HW-L03_HBLFSN5.solidcraft` | HBLFSNB5 (black HBLFSN5, D23) | `HBLFSN5` | `refs/misumi_brackets/HBLFSN5/HBLFSN5_bracket.stp` (vendor origin kept) | Al ADC12 cast, black anodized | #1d1e20 | Vendor: bracket symmetric about Z=0 (20 wide), legs along +X and +Y from near origin | [-1, -1, -10] .. [30, 30, 10] |
| `HW-L04_HBLFSD5.solidcraft` | HBLFSD5 (retired by D23: no black version; not placed) | `HBLFSD5` | `refs/misumi_brackets/HBLFSD5/HBLFSD5_bracket.stp` (vendor origin kept) | Al ADC12 cast | #a9adb2 | Vendor: inside corner on the X axis, legs on the Y=0 / Z=0 faces running to +Y / +Z (30 mm), 40 wide symmetric in X; 1 mm tabs to -Y / -Z | [-20, -1, -1] .. [20, 30, 30] |
| `HW-L05_HBL45TD5.solidcraft` | HBL45TD5 | `HBL45TD5` | Section from `refs/misumi_brackets/HBL45T5/HBL45TS5-SET.stp` (vendor), widened to the catalog 34 mm with 4 x d5.5 at x = +/-10 (p2255) | Al 6063-T5 (catalog A6N01SS-T5), painted black (D23) | #1a1a1a | Vendor TS5 frame: vertex line on X, base on y=0 running z = 2.12..82.12 (holes z = 72.12), angled face on y=z (holes at y=z=51), 34 wide symmetric in X | [-17, 0, 2.12] .. [17, 57.65, 82.12] |
| `HW-L06_HBLTDB5.solidcraft` | HBLTDB5 | `HBLTDB5` | `refs/misumi_brackets/HBLTDB5/HBLTDB5_bracket.stp` (vendor origin kept) | Al 6063-T5, black anodized | #1d1e20 | Vendor frame as HBLFSD5: 2-slot gusset, 34 wide x 35 x 35 x 5, no tabs, holes 25 from the corner | see the vendor STEP |
| `HW-L10_M6x55_SHCS.solidcraft` | ISO 4762 M6x55 | `M6x55_SHCS` | Modelled: head d10 k6, hex 5 AF x 3 deep, shank d6 x 55, no thread | Steel black-oxide | #2b2b2b | Origin = center of head underside; head to +Z, shank along -Z | [-5, -5, -55] .. [5, 5, 6] |
| `HW-L11_Standoff_M5x12.solidcraft` | Standoff M5x12 d10 | `Standoff_M5x12` | Modelled: d10 x 12, d5 through bore (simplified M5) | Steel black-oxide (black, D23) | #1d1e20 | Origin = center of one end face; axis +Z | [-5, -5, 0] .. [5, 5, 12] |
| `HW-L12_HFC5-4040-B.solidcraft` | HFC5-4040-B | `EndCap_HFC5_4040` | Modelled: 40 x 40 x 3 plate (press-fit pins not modelled), Misumi drawing | PA6 | #141414 | Origin = center of the inner (end-face) side; +Z outward | [-20, -20, 0] .. [20, 20, 3] |

All files: revision A, ReleaseState Released, project `desk`. Volumes (HW-L01, L02, L03, L04, L10, L11):
12786 / 10174 / 6196 / 10644 / 972 / 707 mm³.

## Metadata notes
- Document metadata: `part_number`, `description`, `revision`, `project`, plus key `com.setsma.desk`
  = `{lib_id, Material, ReleaseState, Source}` (the project property set, plus `lib_id`). `Source` is
  `Misumi vendor STEP <path>` for the STEP parts and `Modelled (simplified)` for the screw and standoff.
  A part file has no component to hold free properties (`component.metadata.set` refuses the root),
  so they live under that key.
- On `component.insert_design` the metadata (including `com.setsma.desk`) is copied to the component,
  but `properties` is empty and the body material is `Default`. In the assembly, run
  `component.metadata.set {component, properties:{Material, ReleaseState, Source}}` and
  `material.assign {bodies, material}` (create the material there first, see `../_template.json`).
- HBLFSN5 orientation was taken from the vendor STEP as-is; its 16 placements in
  `skeleton/hw_placements.json` were checked against the catalog drawing.
