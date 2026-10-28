# Hardware library (`parts/lib/`)

Standard purchased parts, one file per part, one named body each. Insert with
`component.insert_design {path, name}` and place with joints. Built headless with `solidcraft-cli`;
build scripts are in `src/` (`python src/gen_lib.py` regenerates them from `../_template.json`).

| File | Part number | Body | Source | Material | Color | Local origin / frame | BBox min .. max (mm) |
|---|---|---|---|---|---|---|---|
| `HW-L01_HPTTD5.solidcraft` | HPTTD5 | `HPTTD5` | `refs/misumi_brackets/HPTTD5/HPTTD5_plate.stp` (vendor origin kept) | Steel zinc-plated | #c4c9d0 | Vendor: T-plate in XY, top face Z=0, thickness to -Z; stem along +Y, symmetric in X | [-55, 0, -2.3] .. [55, 80, 0] |
| `HW-L02_HPTLD5.solidcraft` | HPTLD5 | `HPTLD5` | `refs/misumi_brackets/HPTLD5/HPTLD5_plate.stp` (vendor origin kept) | Steel zinc-plated | #c4c9d0 | Vendor: L-plate in XY, corner at origin, top face Z=0, thickness to -Z | [0, 0, -2.3] .. [80, 80, 0] |
| `HW-L03_HBLFSN5.solidcraft` | HBLFSN5 | `HBLFSN5` | `refs/misumi_brackets/HBLFSN5/HBLFSN5_bracket.stp` (vendor origin kept) | Al ADC12 cast | #a9adb2 | Vendor: bracket symmetric about Z=0 (20 wide), legs along +X and +Y from near origin | [-1, -1, -10] .. [30, 30, 10] |
| `HW-L04_HBLFSD5.solidcraft` | HBLFSD5 | `HBLFSD5` | `refs/misumi_brackets/HBLFSD5/HBLFSD5_bracket.stp` (vendor origin kept) | Al ADC12 cast | #a9adb2 | Vendor: inside corner on the X axis, legs on the Y=0 / Z=0 faces running to +Y / +Z (30 mm), 40 wide symmetric in X; 1 mm tabs to -Y / -Z | [-20, -1, -1] .. [20, 30, 30] |
| `HW-L10_M6x20_SHCS.solidcraft` | ISO 4762 M6x20 | `M6x20_SHCS` | Modelled: head d10 k6, hex 5 AF x 3 deep, shank d6 x 20, no thread | Steel black-oxide | #2b2b2b | Origin = center of head underside; head to +Z, shank along -Z | [-5, -5, -20] .. [5, 5, 6] |
| `HW-L11_Standoff_M5x12.solidcraft` | Standoff M5x12 d10 | `Standoff_M5x12` | Modelled: d10 x 12, d5 through bore (simplified M5) | Steel zinc-plated | #c4c9d0 | Origin = center of one end face; axis +Z | [-5, -5, 0] .. [5, 5, 12] |

All files: revision A, ReleaseState Released, project `desk`. Volumes: 12786 / 10174 / 6196 / 10644 / 972 / 707 mm³.

## Metadata notes
- Document metadata: `part_number`, `description`, `revision`, `project`, plus key `com.setsma.desk`
  = `{lib_id, Material, ReleaseState}`. A part file has no component to hold free properties
  (`component.metadata.set` refuses the root), so Material/ReleaseState live under that key.
- On `component.insert_design` the metadata (including `com.setsma.desk`) is copied to the component,
  but `properties` is empty and the body material is `Default`. In the assembly, run
  `component.metadata.set {component, properties:{Material, ReleaseState}}` and
  `material.assign {bodies, material}` (create the material there first, see `../_template.json`).
- HBLFSN5 orientation was taken from the vendor STEP as-is; check the leg/face directions against
  the catalog drawing before mating.
