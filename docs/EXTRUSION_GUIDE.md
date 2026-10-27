# Aluminum Extrusion Guide

Rules for designing and building with 20-series T-slot extrusion (Misumi HFS5 default; 80/20
20-series and V-slot behave the same). Every rule has an ID. Cite it when we make a decision
("side rail joint: J3 + J5"), and log the decision at the bottom.

**The one-line version:** the profile is almost never the weak spot. The **joints** are. Wobble is
a *stiffness* problem, not a strength problem. Fix it with triangles, wide bolt spacing and joints
braced in the plane of the load. Bigger extrusion comes last.

---

## 1. Loads: know which way it pushes

Every joint decision starts with: *what load, in which direction, at this joint?*

| Load type | What it looks like here | What resists it best | What resists it worst |
|---|---|---|---|
| **Axial tension** (pull apart) | crossbar pulled away from upright | anchor / end fastener (load runs down the profile axis) | T-nuts gripping thin slot lips |
| **Axial compression** (push together) | side rail end pushed into upright face | the profile itself, ends cut square and bearing on each other | nothing special needed if ends are square |
| **Shear / slip** (slide along slot) | monitor weight trying to slide a stile down the crossbar | members **resting on** a member below; many bolts; serrated or locking nuts | a single T-nut holding by friction |
| **Bending moment** (rotate the joint) | monitors leaning forward, tipping uprights | flat plate or gusset **in the plane of the bending**, bolts spread wide | a 2-hole bracket on one side; blind / in-slot connectors |
| **Torsion** (twist a member) | monitor hanging off the front face of one bar | closed / square sections (4040); tie two bars together so twist becomes push-pull | 2040 / 2020 open sections over long spans |
| **Dynamic / vibration** | typing, bumping the desk, desk motor moving | triangles, preload, locking fasteners | anything relying on friction alone |

- **L1. Find the load path.** Trace each load from where it's applied (monitor) to the ground (feet).
  Every joint on that path must handle that load *type*. One weak joint sets the stiffness of the whole path.
- **L2. Rest, don't hang.** Where possible a member should sit *on* the member below it, so the
  load goes straight down through the metal. A T-nut joint that only holds by friction can slip.
- **L3. Compression beats tension.** Arrange members so loads push joints together, not pull them apart.
- **L4. Short lever arms.** Moment = weight × distance. Mount loads close to the structure
  (direct VESA instead of arms is a big win). Halving the offset halves the moment on every joint.

## 2. Profiles: size and orientation

Misumi HFS5 values (A6005C-T5, E ≈ 70,000 N/mm²):

| Profile | Mass | I (weak axis) | I (strong axis) | Torsion |
|---|---|---|---|---|
| 2020 | 0.50 kg/m | 0.74×10⁴ mm⁴ | 0.74×10⁴ | poor |
| 2040 | 0.88 kg/m | 1.36×10⁴ | 5.13×10⁴ | poor (open, slotted) |
| 4040 | 1.28 kg/m | 8.89×10⁴ | 8.89×10⁴ | good (square) |

- **P1. Orient the long side in the bending plane.** A 2040 is 3.8× stiffer bending across its
  40 side than across its 20 side. Put the 40 dimension parallel to the load's direction.
- **P2. Span is cubed.** For a beam supported at both ends, sag grows with **L³**. A 25% shorter span
  sags about half as much. Shorten spans before upsizing profiles.
- **P3. Cantilever is squared.** For a post loaded by a moment at its top, deflection grows with
  **L²** (δ = M·L² / 2EI). Keep posts as short as the design allows.
- **P4. Open sections hate twist.** Never let a single 2040 / 2020 carry a twisting load over a
  long span. Tie two parallel bars together (a ladder) so the twist becomes push-pull on two
  bars, or use 4040.
- **P5. Size for stiffness, not strength.** Misumi's guideline: allowable load = load that
  bends the beam by **1/1000 of its length**. Stress is rarely the limit at desk scale (our
  2040 posts see about 1.5 MPa against roughly 200 MPa yield).
- **P6. Upsize when:** a member carries twist you can't tie out (P4), needs a wider face for
  bolt spacing (J4), will get future loads (overhead bar, shelf), or you just want the look.
  Otherwise upsizing is the most expensive and least effective fix for wobble.

**Quick formulas** (E = 70,000 N/mm², mm / N units):
- Cantilever, end moment M: δ = M·L² / (2·E·I)
- Cantilever, end force F: δ = F·L³ / (3·E·I)
- Simple span, center force F: δ = F·L³ / (48·E·I) (fixed ends: ÷4; real bolted joints land between)

## 3. Joints: the weak spot

### Connection types, ranked for load-bearing joints

| Rank | Connection | Best at | Weak at | Notes / rating |
|---|---|---|---|---|
| 1 | **Anchor + gusset / tab bracket** together | everything | needs machining | 80/20's standard "high load" combo |
| 2 | **Gusset / tab bracket, 4-bolt** (Misumi HBLFSD5 type) | bending, twist, vibration | blocks slot faces | HBLFSD5: 1470 N allowable |
| 3 | **Flat joining plate** (L / T / 4-5 hole) on coplanar faces | bending **in the plate's plane**; wide bolt spacing | loads that push out of its plane | needs the two faces flush (coplanar) |
| 4 | **Anchor / end fastener / end-tap screw** (internal) | tension, compression, squareness, hidden | bending and twist (nothing braces the outer faces) | locate + clamp; don't rely on it alone for moment |
| 5 | **2-bolt L bracket** (Misumi HBLFSN5 type) | light-to-medium general joints | can rock unless paired on opposite side | HBLFSN5: 1176 N allowable |
| 6 | **Blind / in-slot / hidden corner connector** | clean looks | everything structural | Misumi blind: 620 N; van builders report breakage |

### Joint rules

- **J1. Brace the joint in the same plane as the bending.** If monitors tip an upright
  front-to-back, the plate or gusset must lie in the front-to-back (side) plane. A bracket in
  the wrong plane does almost nothing.
- **J2. Combine internal + external.** An anchor or end-tap pulls the joint tight and keeps it square. An external
  plate or gusset resists rotation. On any joint that carries monitors, use both.
- **J3. Flush faces enable plates.** Design members so faces line up (coplanar). Then a
  flat plate can span both. This is why the side rail butts the upright with outer faces flush.
- **J4. Spread the bolts.** A joint's resistance to rotation is roughly force × bolt spacing.
  4 bolts spread 80 mm beat 2 bolts 20 mm apart by about 4×. Use long plates on load-bearing joints.
- **J5. Pair brackets.** A single bracket on one side lets the joint rock around it. Put brackets
  on opposite faces (top + bottom, or both sides) of load-bearing joints.
- **J6. Align to a slot.** A butting member's center bore / end tap should line up with a slot
  on the receiving face so anchors and end screws work. Centered between two slots means no
  fastener can reach it. (That's why the crossbars sit on the upright's back slot.)
- **J7. Square ends matter.** End-butting joints (anchors, end-tap) only work if the cut end is
  square. Order precision-cut lengths or have them cut on a saw with a fence and a stop. Hand cuts
  leave gaps that let the joint rock.
- **J8. Minimum two fasteners per member per joint.** One bolt is a pivot.
- **J9. Avoid blind / in-slot connectors on any loaded joint.** Use them only for trim, panels and
  cable covers.

## 4. Wobble: stiffness checklist

Work down this list in order. Each step is cheaper and more effective than the next.

- **W1. Find the source first.** Push the frame and watch. Is the *desk* swaying (legs, motor
  stages), the *joint* rotating, or the *member* bending? Fix the actual source. Standing desk
  legs get looser as they extend, and extrusion can't fix that.
- **W2. Triangulate.** A rectangle can rack (lean into a parallelogram); a triangle cannot. A short
  45° diagonal brace (even 2020) at a corner is the single biggest stiffness gain available.
- **W3. Close the frame.** A post on its own is a cantilever. Two posts plus two crossbars make a
  portal that is far stiffer side-to-side. Tie loose ends into something.
- **W4. Tie parallel members** (P4). Vertical stiles bolted across both crossbars turn bar
  twist into push-pull, which is much stiffer.
- **W5. Upgrade joints** (J1–J5) before upgrading profiles.
- **W6. Shorten** spans and posts (P2, P3).
- **W7. Upsize** profiles last (P6).
- **W8. Preload holds stiffness.** A loose bolt gives a joint a dead band of free movement.
  Torque to spec and use locking hardware (F-section) so preload survives vibration.

## 5. Fasteners

- **F1. T-nut types:**
  - **Pre-assembly / slide-in** nuts (inserted from the profile end): strongest and cheapest.
    You must load them *before* closing the frame.
  - **Post-assembly / drop-in** (rotating) nuts can be added later. They are weaker and smaller.
  - **Spring-loaded / ball-spring** nuts stay where you put them. Use them on vertical members so
    nuts don't slide down while you assemble.
- **F2. Load spare nuts.** Before closing any frame, slide 2–4 extra pre-assembly nuts into
  every slot you might use later (cable clips, accessories, panel mounts).
- **F3. Torque:** Misumi reference for M5 into an HFS5 T-nut is **6.8 N·m**. Don't exceed it.
  Over-torque spreads the slot lips and *reduces* clamp. Use a torque driver if you have one.
  (80/20 publishes no general torque figure; use the vendor's sheet for the hardware you buy.)
- **F4. Lock it.** Misumi test at 6.8 N·m: plain nut releases at 5.2 N·m, resin-coated
  (HNTTZ5) at 6.5 (6.2 after 5 reuses), adhesive (HNTTV5) at 7.6. Use resin-coated / locking nuts or
  medium (blue) threadlocker on joints that carry monitors. Threadlocker needs primer to grip
  bare aluminum threads (end taps). Steel T-nuts don't need primer.
- **F5. Bolt length:** long enough for full nut engagement, short enough not to bottom out in
  the slot. A bottomed bolt feels tight but clamps nothing. Use the vendor's bracket kits or check the
  catalog length.
- **F6. Don't mix brands.** HFS5 nuts in an 80/20 slot (or vice versa) seat badly and slip.
- **F7. Re-torque** all load-bearing joints after about 1 week of use and after any move.

## 6. Assembly

- **A1.** Assemble on a flat surface. Snug all bolts first; do not final-tighten yet.
- **A2.** Square each rectangle by measuring **both diagonals**. Adjust until they're equal.
  Check corner squareness locally too.
- **A3.** Tighten progressively in a cross pattern, rechecking diagonals as you go.
- **A4.** Load spare T-nuts (F2) before closing any loop.
- **A5.** After assembly: load it (hang the monitors), then inspect each bracket for gaps,
  movement or deformation. Re-torque (F7).

## 7. Machining options

- **M1. End tap:** the profile's center bore can be tapped (M5 typical for HFS5 20-series) for
  an end-tap screw into a slot of the mating member. Misumi and 80/20 offer this as a cut-to-length
  option; it's cheap and accurate.
- **M2. Access hole:** anchors / end fasteners need a drilled access hole for the wrench in the
  receiving member. Order it machined, or use a drill jig.
- **M3. Counterbore (Misumi "reverse tap"):** a screw-only connection with no brackets and a
  clean look. Misumi publishes no load value for it, so pair it with a bracket where it carries load (J2).

## 8. Decision checklist (run for every extrusion joint)

1. What loads hit this joint, and in which directions? (Section 1)
2. Is it on the monitor load path? If yes, it is load-bearing. Use J2 (internal + external).
3. In which plane does the bending act? Brace in that plane (J1). Are the faces flush so a plate fits (J3)?
4. Does the butting member land on a slot (J6)? Are the ends square (J7)?
5. Bolt spacing as wide as the faces allow (J4)? Brackets paired (J5)? At least 2 fasteners (J8)?
6. Locking hardware and torque spec (F3, F4)?
7. If wobble is still possible, where would a triangle go (W2)?

---

## Decision log (this desk)

| ID | Decision | Rules | Status |
|---|---|---|---|
| D1 | Side rail **butts** upright front face, outer faces flush (T-joint), not lapped to the upright's inner face (lap gave only 40 mm bolt spread) | J1, J3, J4 | done |
| D2 | Side rail–upright joint: T-plate on flush outer faces (80 mm arm, 60 mm past joint) + 2-slot gusset under rail + end anchor | J1, J2, J3, J4 | modelled (`Plate_/Bracket_SideRail_R/L`) |
| D3 | Crossbars sit on the upright's **back slot** (back faces flush). The end bore aligns with the slot, and the panel gets a flat mounting plane | J6, J3 | done |
| D4 | Monitors direct-VESA mount (no arms) on **vertical stiles tying both crossbars** | L4, P4, W4 | done |
| D6 | Crossbar ends: L-plate on flush back faces (lower bar leg up, clear of panel; upper bar leg down) + gusset under bar + end anchor | J2, J3, J5, J6 | modelled (`Plate_/Bracket_BarLow/High_R/L`) |
| D7 | Stiles sit **between** the crossbars (rest on the lower bar, L2; monitors 20 mm further back): 1-slot inside-corner bracket on **each side** of each stile end, in the frame plane so adapters and panel stay clear, + end anchors into the bar slot (J6) | J5, J8 | modelled (`Bracket_Stile*`) |
| D8 | End anchors (crossbar ends, side rail ends): internal, not modelled. Order those ends tapped + access holes in the uprights | J2, M1, M2 | BOM |
| D10 | Privacy panel (desk stands mid-room, back faces the room) top = highest of upright tops and VESA adapter tops + `pnl_cover` (ports sit at/below the VESA mount, so monitors may show above it); upper crossbar top defaults flush with the highest adapter top, and a stile runs past a lowered bar up to its own adapter top. Panel held 12 mm off the back faces on 8 M5 standoffs into T-nuts (crossbars' upper slot, uprights' outer slot), so plates and bolt heads stay clear | J6, F2 | modelled (`Standoff_*`) |
| D9 | Side rail to top support: bolts through top-support outer-face holes | J8 | waiting on hole measurements |
| D11 | Monitor aim: side (portrait) monitor toed in `m3_yaw` = 15 deg **about its inner front edge**, which lands at the main's left front edge at the same depth (`mon_front`), `mon_gap` apart. Stile_Side follows its VESA center (`m3_x`); its wedge adapter is `m3_off` (~66 mm at the center, print hollow). `m1_tilt` tilts **both** monitors about the main's VESA axis, so the edges stay matched (checked at 8 deg: 10 mm gap, no overlaps) | L4 | modelled |
| D12 | Speakers hang from their own back swivel mount (~3/4 up, `spk_mount_frac`) on a bracket bolted into the **upright front slot**: no shelf, no arm. Vertical slot = height freely adjustable (`spk_bot`), L2-friendly (the bracket can rest on a spare T-nut / stop below it). Swivel gives toe-in `spk_yaw` = min(`spk_aim` ~51 deg, `spk_yaw_max` 25 deg; left speaker 8.5 mm from the portrait monitor at 25) and tilt down `spk_tilt` = max(aim, 0): at `spk_bot` 8 in the tweeter is ~2 in below ear so tilt is 0; 12 in -> 2.6 deg down, 15 in -> 6.5 deg down. Load per bracket ~35 N at ~120 mm off the face: ~4 N*m on 2 M5 T-nuts, fine (F3/F4) | L2, L4, J8, F4 | modelled (`SpkMount_*`) |
| D13 | Screen height vs eyes: with `mon_clearance` 8 in and `eye_above_desk` 18 in (estimate), main top is ~6.5 in above eye, portrait top ~14 in. Trade-off between items-under-monitor space and neck angle | ergonomics | **open, needs eye measurement** |
| D5 | Upright profile: 2040 (40 side front-to-back) vs 4040. Inputs below | P1, P3, P6 | **open** |

### D5 inputs: 2040 vs 4040 uprights

Current load: 32in main (about 6.5 kg) + 27in portrait (about 4.5 kg), direct VESA, about 60–75 mm in front
of the uprights, so about 4 N·m per upright. Upright about 640 mm from the side rail joint to the top.

| | 2040 (40 side Y) | 4040 |
|---|---|---|
| Lean at top under monitor load | ~0.2 mm | ~0.1 mm |
| Twist resistance | poor (but the crossbars + stiles carry the twist, P4) | good |
| Face for side-rail plate (J3/J4) | 40 mm (outer face) | 40 mm |
| Faces with 2 slots | 2 (outer and inner) | 4 |
| Matches butting members | side rail end (20 wide) = front face exactly | front face 40 wide, side rail sits on outer slot |
| Mass / cost | lower | about 45% more |
| Future-proof (overhead bar, shelf, heavier monitors) | less | more |

Both are far below any wobble you'd see. The joints (D2) and the desk itself (W1) decide the
real feel. Choose 4040 for future loads, more slots or the look; choose 2040 for slim and cheap.

### Structural audit (2026-10-26, `tools/audit.py`, estimated masses)

Masses: frame ~52 kg (DeskHaus ships the Apex Pro 4 in 60 + 62 lb boxes), desktop ~28 kg (IKEA Karlby package 28.9-29.7 kg), monitors 6.5 + 4.5 kg, 1/4in plywood panel ~7 kg. Heavier frame/desktop **raises** the tip force (they sit centered); heavier monitors/panel lower it. Worst mix tested (light base, heavy monitors, acrylic panel): ~32 lbf back-tip standing.
Rerun after weighing: `python tools/audit.py build.json` (see the script's docstring).

| Check | Result | Verdict |
|---|---|---|
| Total / riding on lift | ~107 kg / ~75 kg | fine (check frame label rating) |
| Center of mass | ~90 mm (3.5in) behind frame center, ~260 mm inside rear foot ends | statically stable |
| Push at upright top to tip **backward** | ~150 N (33 lbf) standing, ~200 N (45 lbf) seated; worst case ~124 N (28 lbf) | **weakest case**: rails + panel sit behind the foot ends. Wall behind or an anti-tip strap fixes it |
| Push to tip forward / sideways | ~250 / ~490 N standing | fine |
| Leg split | rear legs ~95% of lift load | fine for strength; keep heavy desk items forward |
| Crossbar sag | 3.0 mm pinned (upper bound), ~1.5 mm with bolted ends; both bars sag together, monitors drop, don't tilt | at Misumi L/1000 (1.8 mm), acceptable |
| T-joint static moment | ~0 N*m (panel behind balances monitors in front) | fine; only dynamic loads |
| Side rail to top support (D9) | ~10 N*m per side, ~100 N bolt pull at 100 mm spread | fine if 2+ bolts, spread wide; **unverified until D9** |
| Upright lean | 0.1-0.2 mm | fine (D5 either way) |

Real-world limit is wobble at standing height (W1), not strength: masses sit high and rear-heavy on the legs.
Biggest stiffness wins: bolt the panel firmly so it acts as a shear wall (W2/W3), and an optional
45 deg knee brace between each side rail and the upright below the desk (W2, fore-aft).

---

## Sources

- [Misumi HFS5 catalog p2239: section properties](https://us.misumi-ec.com/pdf/fa/2010/p2239.pdf)
- [Misumi load capacity guideline p2433: 1/1000 rule, E](https://us.misumi-ec.com/pdf/fa/2010/p2433.pdf)
- [Misumi extrusion parts selection: brackets vs blind vs screw joints](https://th.misumi-ec.com/en/pdf/fa/2014/p2_513_519_521_523_525.pdf)
- [Misumi HNTT5 T-nut: torque 6.8 N·m, release torques](https://us.misumi-ec.com/vona2/detail/110302246150/?HissuCode=HNTT5-4)
- [Misumi HBLFSN5 bracket](https://misumi.partcommunity.com/3d-cad-models/hblfsn5-hblfsn5-4-hblfsnb5-hblfsnm5-hblfsnk5-hblfsne5-brackets-hfs5-reversal-brackets-with-tab-misumi?info=misumi%2Fmetric%2F38_al_extrusions_blackets%2F5%2Fhblfsnm5_asmtab.prj&languageIso=en&countryIso=US),
  [HBLFSD5](https://misumi.partcommunity.com/3d-cad-models/hblfsd5-brackets-hfs5-reversal-brackets-with-tab-2-slots-misumi?info=misumi%2Fmetric%2F38_al_extrusions_blackets%2F5%2Fhblfsd5_asmtab.prj&languageIso=en&countryIso=US),
  [HBLBCB5 blind](https://misumi.partcommunity.com/3d-cad-models/hblbcb5-shblbcb5-corner-blind-brackets-hfs5-20mm-square-three-way-type-misumi/?info=misumi%2Fmetric%2F38_al_extrusions_blackets%2F5%2Fshblbcb5_asmtab.prj)
- [80/20: internal vs external fasteners](https://8020.net/blog/8020-t-slot-framing-fasteners-internal-vs-external.html)
- [Industrial Profile Systems: joint design and assembly](https://www.industrialprofile.com/aluminum-extrusion-joints-design-and-assembly-considerations/)
- [ToolGuyd: anchors, end fasteners, brackets](https://toolguyd.com/hardware-for-connecting-t-slot-aluminum-anchors-end-fasteners-brackets/)
- [Engineers Who Van Life: fastener lessons](https://engineerswhovanlife.com/fasteners-80-20-van-building/)
- [Aluminum Compo: internal anchor FAQ](https://aluminumcompo.com/internal-anchor-connectors-faq/)
- [Clinalu: assembling square frames](https://clinalu.com/how-to-assemble-t-slot-aluminum-framing-without-alignment-problems/)
- [Thread-locking compound (aluminum priming)](https://en.wikipedia.org/wiki/Thread-locking_compound)
- Forum load reports (unverified):
  [Ford Transit forum](https://www.fordtransitusaforum.com/threads/8020-connector-strength-reviewed.97394/),
  [Chief Delphi](https://www.chiefdelphi.com/t/strongest-80-20-fastener/76342),
  [CNCZone](https://www.cnczone.com/forums/diy-cnc-router-table-machines/288122-cnc-forum.html)
