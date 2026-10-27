# Desk rail system (SolidCraft)

Parametric model: Apex Pro 4-leg frame (Jiecang OEM) + desktop + 20-series extrusion rail system.

- `desk_rails.solidcraft` — **source of truth**: the design. Edit it in SolidCraft (Parameters
  table, timeline) and save. The old generator (`tools/gen_desk.py`, `tools/joints.py`,
  `desk_rails.json`) was retired on 2026-10-27; it's in git history before commit `bd5ba5a`.
- `profiles/` — extrusion cross-section DXFs used by the model. `refs/` — PDFs and raw downloads.
- `tools/audit.py` — structural + balance audit (mass budget, tip margins, leg split, crossbar sag, joint loads) from a build `--json-out` report. Edit `MASS_INPUTS` when weighed.
- `tools/check.py` — one-command build + checks (see below). `tools/bom.py` — writes `BOM.md` (cut list, hardware, fastener estimate).
- `BOM.md` — generated bill of materials; don't hand-edit.
- `tools/svg2dxf.py` — converts an SVG profile drawing to DXF (used for HFS5-4040).
- `renders/` — snapshots.
- `docs/EXTRUSION_GUIDE.md` — extrusion rules (loads, joints, wobble, fasteners) + decision log. Check it before any extrusion decision.

Check (one command, reads the saved design, never overwrites it):

```sh
python tools/check.py            # report, overlap check, audit, BOM.md
python tools/check.py --renders  # also refresh renders/iso|front|back|right|top.png
```

It exits non-zero if the report fails or any bodies overlap. Outputs (report JSON,
interference results) go to `build/` (git-ignored). Save in SolidCraft, run the check, then
commit: the `.solidcraft` file is binary, so git history is the undo (`git checkout <rev> -- desk_rails.solidcraft`).

## Assemblies

Root holds only assemblies; every part has a part-number name; `DSK-00` is grounded, the rest
are rigid-jointed to it.

| Assembly | Contents |
|---|---|
| `DSK-00` Desk | desktop, frame (top supports, channel bars, legs, feet) |
| `FRM-00` Monitor rail frame | side rails, uprights, crossbars, stiles, modesty panel |
| `HW-00` Frame hardware | joining plates, gusset brackets, panel standoffs |
| `MON-00` Monitors | 32in main, 27in portrait |
| `SPK-00` Speakers | Klipsch R-40M pair + their swivel mounts |
| `PC-00` PC | Fractal North hung on one 6in x 1/2in strap (`pc_leg_gap`, `strap_w`), walnut slat front |
| `INP-00` Input devices | 16.5in mouse pad, Razer DeathAdder V3, ErgoDox EZ halves (`kb_gap`, `pad_kb_gap`, `kb_front_gap`, `pad_front_gap`). ErgoDox footprint = real case outline (202.3 x 176.3 mm per half) traced from ZSA's 1:1 printout (`refs/ergodox_ez/`), 15 mm case + 15 mm tapered keycap layer = ZSA's 30 mm. Mouse = DeathAdder V3 Pro, real STEP (`refs/razer_dav3pro/DAV3Pro.step`, 10 bodies `Mouse_DAV3Pro_*`) in `INP-02a`, rigid-jointed to the mouse pad's top-face centre so it follows `pad_x`/`pad_y` |
| `REF-00` Reference | `Eye` marker |

The 80/20 and V-slot configuration rows still exist, but switching to one puts its rails loose
at the root, outside `FRM-00`.

Axes: origin = floor under frame center. X = width (+ right), Y = depth (+ toward wall), Z = up.

## Parts

| Body | What | Color |
|---|---|---|
| `Desktop` | desktop | wood |
| `TopSupport_R/L` | frame end brackets the desktop screws to | black |
| `ChannelBar_{Back,Front}{Outer,Inner}` | 2 slim bars per channel; legs sit between them | black |
| `Leg_{RB,RF,LB,LF}`, `Foot_R/L` | placeholder legs / feet | black |
| `SideRail_R/L_<std>` | 2040 along each top support's outer face; end butts upright front face (T-joint) | silver |
| `Upright_R/L_<std>` | 4040 rear posts; outer face flush with side rail (= desktop edge − `up_side_inset`) | silver |
| `Crossbar_Low/High_<std>` | 2040 monitor bars between posts | silver |
| `Stile_Main/Side_<std>` | vertical 2040 between the crossbars (resting on the lower one, faces flush); monitors VESA-mount to these | silver |
| `Monitor_Main/Side` (+ `_Back`) | 32in 16:9, 27in portrait left: thin screen slab + rear bulge (no stands) | near-black |
| `Standoff_*` | panel standoffs (M5), hold the panel `pnl_back_gap` off the back faces | orange |
| `Plate_*`, `Bracket_*` | joint hardware: flat joining plates + gusset brackets (decisions D2, D6, D7 in the guide) | orange |
| `Speaker_R/L` (+ `SpkFace_*_Horn/Woofer`) | Klipsch R-40M (spec size, 3.2 kg) with horn + spun-copper woofer faces; hung from their back swivel; toe-in + tilt aimed at `Eye` | dark brown |
| `SpkMount_*` | speaker bracket: flange in the upright front slot, block, ball swivel | orange |
| `Eye` | your eye position marker (ergonomics check in `tools/audit.py`) | red |
| `ModestyPanel` | privacy panel behind the posts, from `pnl_drop` below the desk to just above the adapter tops, on standoffs; hangs free below the short upright stubs (`up_below`) | slate |

`<std>` = `HFS5`, `8020` or `VSLOT` (see Extrusion profiles).

## Measure checklist

Inches are fine (`"1.45 in"`). Set in the app's Parameters table.

**TopSupport_R / TopSupport_L** (end brackets under the desktop)
- `frame_w` is now **derived** (`desk_w - 2*(rail_s + up_side_inset)`): channel bars get cut to suit. Check result stays in frame's usable range (leg spacing, cable/PC clearance).
- [ ] `ts_len` — length front to back (Y)
- [ ] `ts_w` — width (X)
- [ ] `ts_h` — height (Z)
- [ ] cross-section shape (flat bar / angle / C / tube) + wall thickness — photo
- [ ] holes on the **outer face** (where the side rail bolts on): each hole's distance from front end + from top edge, diameter, threaded (M6?) or through

**ChannelBar_*** (the slim bars running left-right)
- [ ] `ch_bar_w` — width of one bar (Y)
- [ ] `ch_h` — height (Z)
- [ ] `ch_bar_gap` — gap between the 2 bars of one channel (Y)

**Leg_*** (top of each leg, where it meets the frame)
- [ ] `leg_x`, `leg_y` — top stage outside size (X, Y)
- [ ] `leg_yc` — frame center to leg center, front-back (Y). Easier: measure front leg center to back leg center and halve it.
- [ ] `leg_inset` — top support outer face to leg center (X)
- [ ] `ch_y_off` — only if the legs aren't centered front-back on the top support (else 0)

**Foot_*** (optional, only for looks/clearance)
- [ ] `foot_w`, `foot_h`

**Monitor_Main / Monitor_Side** (no stand; ruler is fine)
- [ ] `m1_w/h/t`, `m3_w/h/t` — outside width, height, max depth incl. rear bulge
- [ ] `mon_panel_t` — thin edge thickness (one value for all)
- [ ] each: VESA pattern (100/75) + hole-pattern center from bottom edge and from left edge (for the printed adapters)
- [ ] each: weight without stand (spec sheet)
- [ ] `vesa` — VESA pattern size

**You** (for the ergonomics check)
- [ ] `eye_above_desk` — sit as you type: floor-to-eye minus desk height
- [ ] `eye_back` — eyes out from the desktop front edge

**Speakers** (Klipsch bookshelf)
- [ ] `spk_w/d/h` — currently 5.75 x 7.5 x 11 in (W x D x H): confirm orientation
- [ ] weight each (for the audit)
- [ ] `spk_mount_frac` — swivel mount height on the back / speaker height (now 0.75)
- [ ] `spk_tw_down` — tweeter center below the top (now 3 in)
- [ ] swivel: thread size, how far it stands off the back (`spk_mount_d`), max turn / tilt angles

**Room / desk**
- [ ] desk back edge to wall (for `rear_gap` + panel clearance)
- [ ] `desk_h` — your usual sitting and standing heights (to check clearances at both)

## Design parameters

`desk_w/d/t/h`, `desk_y_off`, `up_side_inset`, `rear_gap`, `up_below`, `side_front`,
`m1_x`, `mon_clearance`, `m1_tilt` (main tilt back), `m3_yaw` (side toe-in about its inner front edge, default 15 deg; that edge stays at the main's front depth), `m1_tilt` tilts both monitors together, `spk_bot` (speaker height, slides on the upright slot), `spk_px` / `spk_mount_d` (swivel position), `spk_yaw_max` (toe-in limit; `spk_aim` = full aim at the Eye), `spk_tilt` (tilt down, auto-aimed at the Eye), `m3_bot`, `mon_gap`, `mon_standoff`, `m1_off/m3_off` (per-adapter thickness, to line
up screen fronts), `vesa_adp` (adapter size; adapter tops set the upper crossbar + panel top), `bar2_z`, `bar1_gap` (lower crossbar top below the monitor bottoms: it shows in the gap for mounting things), `bar_y_off` (crossbars sit on the uprights' back slot: +10 mm; front slot: -10 mm) (crossbar heights and upright
height follow the monitor stack),
`pnl_drop`, `pnl_cover`, `pnl_above`, `pnl_t`, `pnl_back_gap`, `pnl_side`.

## Extrusion profiles

Real cross-sections (DXF, mm, centered) in `profiles/`, inserted into sketches, extruded to
parameter lengths and placed with parametric moves. Pick the standard with a **configuration**
(SolidCraft Configure > configuration table, or `config.activate {"row": ...}`):

| Config row | 4040 (uprights) | 2040 (crossbars, side rails) | Source |
|---|---|---|---|
| `Misumi_HFS5` (default) | `misumi_hfs5_4040.dxf` | `misumi_hfs5_2040.dxf` | 4040: converted from SVG drawing in github.com/TheEnigmaBlade/dllpdf-frame-calculator (no license stated) via `tools/svg2dxf.py`; 2040: github.com/oysteinkrog/thing_libutils (LGPL-2.1) |
| `8020_20series` | `8020_20-4040.dxf` | `8020_20-2040.dxf` | github.com/Thaddeus-Maximus/designlib (no license stated) |
| `OpenBuilds_Vslot` | `openbuilds_vslot_4040.dxf` | `openbuilds_vslot_2040.dxf` | 4040: github.com/alex-crr/ExtrusionsGenerator (MIT); 2040: github.com/richard-scott/OpenBuilds |

Checked cross-section areas: HFS5 4040 497 / 2040 323 mm²; 80/20 423 / 275; V-slot 433 / 300.

Switch from the CLI:

```sh
echo '{"commands":[{"command":"config.activate","params":{"row":"8020_20series"}}]}' > cfg.json
solidcraft-cli run cfg.json --in desk_rails.solidcraft --save desk_rails.solidcraft --quiet
```

## Side rail to upright joint

T-joint: side rail end butts the upright's front face, outer faces flush. Fastening, strongest first:

1. Flat L/T joining plate on the shared outer face (tipping load from monitors is in this plane).
2. Inside corner gusset bracket under the rail.
3. End-tap screw or anchor fastener (hidden; locates the joint, weak alone).

Plate thickness sticks out past the outer face; set `up_side_inset` >= plate thickness to keep it
inside the desktop edge.
