# Visual joint review: hiding the frame hardware

Review only (2026-11-02). No design file, script or skeleton was changed. Goal: "hide joints where
possible" while three changes are planned at the same time:
- the privacy panel FRM-05 becomes dark grey felt;
- a new narrow side panel goes on each upright's outer face, the same height as FRM-05, meeting it at the
  corner with no gap;
- all extrusion goes black (HFSB5 black-anodized profiles) with end caps.

Sources: `skeleton/params.json` (numbers from `tools/skeleton_values.values()`), `skeleton/hw_placements.json`,
the body bboxes in `build/desk_rails_eval.json` (2026-11-02 03:59 build), `docs/EXTRUSION_GUIDE.md`, and the
vendor SET STEPs in `refs/misumi_brackets/` (a headless eval in scratch measured the screw heads).
Misumi part numbers marked **verify** came from web search, not from a product page with a drawing.

## 1. Geometry and viewpoints

World frame: X to the right, +Y toward the room behind the desk, Z up. Values in mm.

| Item | Value |
|---|---|
| Desktop | x ±939.8, y -330.2..330.2, top z 673.1, underside 635.0 |
| Uprights (4040) | outer faces at x = ±939.8 (flush with the desktop edge), y 340.2..380.2, z 440.0..1242.3 |
| Crossbars (2040) | y 360.2..380.2 (back faces flush with the uprights, D3); low bar z 771.3..811.3, high bar z 1202.3..1242.3 |
| Side rails (4040) | x 899.8..939.8, y -230.2..340.2, z 590..630 |
| Knee brace (2040, D20) | y 190.2..340.2, z 440..590, flush with the rail's outer face |
| FRM-05 panel | x ±939.8 (`pnl_side` 0), front face y 392.2 (`pnl_back_gap` 12), z 279.4..1257.3 |
| Rear gap, desktop to upright | 10 mm (desk back edge y 330.2, upright front face y 340.2) |

Viewpoints used below:
- **Eye**: seated, at the SKL_Eye point (0, -482.6, 1168.4).
- **Room**: someone standing behind the desk (+Y side), at any height. Oblique rear views are included.
- **Side**: someone standing at either end (±X), looking at the outer faces.
- **Under**: the seated user's knee area, looking at the inner faces below the desktop.

From the Eye, the desktop hides everything at the uprights' Y below about z 667 (sightline over the desk
back edge: z = 673.1 - 0.61 x (y - 330.2)). Visibility above the desk comes from bbox sightlines against the
monitors, speakers and laptop, worked by hand, not ray-cast. Where a call is marginal it's marked "partly".

## 2. Fastener heads that set the side-panel gap

Measured from the vendor SET STEPs:

| Kit | Screw | Head | Head top above the mounting face |
|---|---|---|---|
| HPTTD5-SET / HPTLD5-SET | CBM5-8 | Ø8.5 x 5.0 | 2.3 plate + 5.0 = **7.3 mm** |
| HBLFSD5-SET | CBM5-10 | Ø8.5 x 5.0 | on the 4.5 bracket leg |
| HBL45TS5-SET (TD5 the same) | CBM5-14 | Ø8.5 | on the bracket |
| M6x55 SHCS (HW-29..36, lib) | — | Ø10 x 6.0 | 6.0 mm (already black-oxide) |

## 3. Item by item

"Planned panels" means the felt FRM-05 plus the new side panels as specified in §4.

| HW | What / where | Seen from | Hidden by the planned panels? | Hide options (catalog only) | Don't |
|---|---|---|---|---|---|
| **01/02** HPTTD5 outer | T-plate on the outer faces. Bar runs up the upright (y 341.2..379.2, z 555..665, 4 heads at y 350.2/370.2, z 564/656). Stem lies on the rail (y 299.2..341.2, 2 heads at y 308.2/328.2, z 600/620). Bar top is 8 mm under the desktop top surface | **Side**: fully visible, at desk height. Room: no (behind FRM-05). Eye: no | **Bar: yes**, if the side panel stands off ≥ 8.5 mm (§4). **Stem: no**: it sits in front of the side panel's front edge (y 340.2) | Extend the side panel forward to y ≈ 295 to cover the stem too (side panel ~104 mm wide instead of ~58). Black-oxide M5 heads on the stem. No black HPTTD5 was found in the catalog (HPTTDB5 not listed, **verify**). Painting it black is user finishing, so it needs the user's OK | Remove or move it. It's the J1 / J3 / J4 moment plate of D2, in the bending plane, and the user doubled it (with HW-37/38) |
| **37/38** HPTTD5 inner | Same plate on the inner faces (x ±899.8) | Under only. Eye: hidden by the desktop (top at z 665 vs a z 667 sightline; ≤ 4 mm can peek through the 10 mm rear gap from a standing position at the front) | n/a (already hidden) | Nothing needed. Black-oxide screws if wanted | Same as 01/02 (D2) |
| **03–06** HPTLD5 | L-plates on the back faces of the upright/crossbar corners (y 380.2..382.5), low z 772..852, high z 1161..1241 | Room: no (behind FRM-05). Side: only through the 12 mm slot between the upright back face and FRM-05's edge | **Yes, fully**, once the side panel closes the corner (§4) | None needed | Remove (D6, J2 / J5) |
| **07/08** HBLFSD5 | 2-slot gusset under the rail at the upright front face, y 310..341, z 560..591. Its side face is flush with the outer face (x ±939.8) | **Side**: through the knee-brace triangle window. Under: from the front, low and dark | No (in front of the side panel) | **HBLFSDB5** black anodize, same body and 1470 N (listed in Misumi's bracket guide, **verify** the product page). `-C` option + a bracket cover | Remove or swap for blind or in-slot (D15 J2 gusset; blind is 620 N vs 1470, J9) |
| **09/10** HBLFSN5 low bar | Inside corner under the low bar at the upright inner faces, x ±(869.8..900.8), y 360.2..380.2, z 741..772 | **Eye: visible**, left below the side monitor and speaker; right partly behind the laptop. Room: no. Side: no | No | **HBLFSNB5** black anodize. Same part, 1176 N, confirmed in the catalog (also on Misumi CAD). Drop-in swap, no geometry change | Swap for blind / end-tap only (D6 J2 + J5; crossbars carry the stiles and monitors) |
| **11/12** HBLFSN5 high bar | Same, under the high bar, z 1172..1203 | **Eye: partly** (the top ~15 mm shows above the speaker tops at z 1175) | No | HBLFSNB5 | as 09/10 |
| **13–16** HBLFSN5 main stile | Both sides of the main stile ends, in the frame plane (D7). Low z 810..841, high z 1172..1203 | **Eye: low pair visible** just below the main monitor's bottom edge (z 876); high pair behind the monitor | No | HBLFSNB5 | Swap for blind or in-slot (J9: monitors hang on the stiles). A single back-face plate instead loses the J5 pairing, and at x = 0 it hits the panel standoffs HW-22/25 |
| **17–20** HBLFSN5 side stile | Same at the side stile (x ≈ -555) | **Eye: low pair visible** under the portrait monitor; high pair hidden | No | HBLFSNB5 | as 13–16 |
| **39–42** HBLFSN5 right stile | Same at the right stile (x ≈ +555) | **Eye: high pair (41/42) fully visible** (no monitor in front, laptop lid top at z 1082); low pair partly behind the laptop and its mount | No | HBLFSNB5. **Biggest single visible item from the seat** | as 13–16 (the laptop arm loads it, D19) |
| **21–26** standoffs, crossbars | M5x12 standoffs on the crossbars' upper back slots at x 0, ±459.9 | Room: no (but **the panel screws that go into them show on FRM-05's room face**). Side: no | Standoffs yes. Screw heads: no | Black button-head (ISO 7380) M5 + black nylon washer on the dark grey felt, so the heads nearly vanish. Black-oxide or black standoffs (**verify** a catalog item; HW-L11 is modelled zinc) | — (trim, J9 allows anything) |
| **27/28** standoffs, uprights | Upright back face, outer slot, z 530..540 | Side: through the 12 mm corner slot. Room: no | **Yes** (side panel closes the corner) | As 21–26 for the face screws | — |
| **29–36** M6x55 SHCS | Heads on the rail outer face, y ±107.5..±180.2, z 611, 6 mm proud. Already black-oxide | **Side**, under the desk edge | No (y is far in front of the side panel) | Black on black extrusion is already the fix. They sit between the rail's slots (z 600/620), so slot covers run past them | Move the heads inboard (D9 revised 2026-11-01 by the user: head on the outer face, straight drilling) |
| **43–46** HBL45TD5 | 45° brackets inside the knee-brace triangle, x ±(902.8..936.8), 3 mm in from the outer face | **Side**: through the triangle window, at knee height. Under: through the triangle | No | p2255 lists no black finish (options: SET / SST / SEU / SSU / SEP / SSP / C). The `C` option (M5 cover taps) takes a cover (**verify** which). Otherwise accept: clear anodize, low and in shadow | **Don't change the joint** (D20: the brace turns the D2 moment joint into a triangle, W2. HBL45TD5 is 1470 N and the only catalog 45° 2-slot part) |
| FRM-07L/R hanger plate (D21) | 5 mm zinc steel flat bar between the desktop and the rail, flush with the rail's outer face, y -261.7..268.3 | **Side**: a 5 mm bright line between walnut and black rail | No | **Order it black** (black oxide or black coat as the configurable-plate surface option, vendor finish, D14 OK). Its countersunk screws already sit under the desktop | Change the plate or screw stations (D21 asserts them) |

## 4. Side panel: clearing HW-01/02

The outer HPTTD5 bar covers 38 of the upright's 40 mm outer face, from z 555 to 665. That's inside the side
panel's span (z 279.4..1257.3). Its CBM5-8 heads stand **7.3 mm** off the upright face.

**Recommended: the side panel on 12 mm standoffs, full height, with FRM-05 widened 12 mm per side.**
- **Gap**: 12 mm, using the existing `HW-L11_Standoff_M5x12`. That leaves 4.7 mm over the heads, and the
  shadow line matches FRM-05's `pnl_back_gap`. The minimum is about 8.5 mm (7.3 + ~1 mm): a 10 mm standoff
  works with the stock heads. An 8 mm standoff works only if the 4 bar screws become ISO 7380 button heads
  (2.75 mm head, so 5.05 mm proud).
- **Corner, no gap**: the side panel's inner face lands at x = ±951.8. Set `pnl_side` = -12 mm (FRM-05 width
  = desk_w + 24) so FRM-05's edge butts the side panel's inner face. Run the side panel back from the
  upright front face (y 340.2) to FRM-05's back face (y = 392.2 + `pnl_t`, so 398.55 at 1/4 in) so it covers
  the panel's end. Side panel width ≈ 58.35 mm + any change in `pnl_t` (felt is often 9 or 12 mm thick).
  From the side, that reads as one continuous face. From behind, only the side panel's own edge shows.
- **Mounting stations**: drop-in T-nuts (post-assembly, F1: fine for trim, J9) in the upright's outer slot at
  **y 350.2**, away from:
  - the plate (keep standoffs outside z 551..669);
  - the D8 crossbar end-anchor access holes (M2). They go through the outer face in line with the crossbar
    bores (y 370.2, z 791.3 / 1222.3), and the side panel covers them, which is a bonus.

  For example z ≈ 470, 720, 1000 and 1200. The upright ends at z 440, so the side panel hangs 161 mm below
  its last standoff, which is fine for felt.
- **Clearances checked against the bboxes**:
  - The outer face lands at x ±(951.8 + t), about 18-24 mm proud of the desktop edge and the rail.
  - The M6 heads (to 945.8) and the HPTTD5 stem heads (to 947.1) stay inside that plane.
  - The speaker mount block (x ≤ 939.8) and cabinet (≤ 932.9) don't reach it.
  - The brace and the HBLFSD5 are in front of y 340.2.

**Alternative (not recommended): flush side panel, split above and below the plate.** Glued or screwed
straight to the upright, with no standoff: z 667..1257 above, 440 (or 279)..553 below. It meets FRM-05
without widening it (its inner face = FRM-05's edge at x ±939.8, wrapping back to y 398.55). But it leaves a
110 mm band of bare plate at exactly desk height, the most visible spot from the side. A pocket in a thick
felt panel would hide the plate, but that's user fabrication, and the felt over it would be ~1 mm thin.

## 5. What can't be hidden by changing the joint

Every frame joint is on the monitor or laptop load path:
- the uprights carry the crossbars;
- the crossbars carry the stiles (L1);
- the side rails carry the uprights (D2, D9, D20).

So no bracket can be swapped for a blind or in-slot connector (J9; blind is rated 620 N vs 1176-1470 N for
the brackets in use). An end-tap (M1) or counterbore (M3) can't stand in for one either: M3 has no published
load, and J2 needs internal plus external fasteners. M1 / M2 anchors are already the internal half (D8) and
are invisible anyway. Moving joints onto panel-covered faces doesn't work either:
- The D2 plates must stay on the flush outer and inner faces, in the bending plane (J1 / J3 / J4).
- The D7 stile gussets must stay paired (J5). The back face alone would give one-sided plates, and at x = 0
  they would hit HW-22/25.
- The D20 brackets are fixed by the triangle.

What's left is colour, covers and the panels.

## 6. Ranked recommendations (visual payoff vs effort)

| # | Do | Hides / improves | Effort | Rules |
|---|---|---|---|---|
| 1 | **HBLFSNB5** (black) for all 16 HBLFSN5 (HW-09..20, 39..42) | Every bracket the seated user sees (stile gussets under the monitors, the right-stile pair, the bar corners) disappears against black extrusion | Part-number swap. Same body, load and SET; recolour lib HW-L03 (or add a black variant) | D14, D6, D7 unchanged |
| 2 | **Black slot covers HSCA5-B** (resin, cut with scissors; HSCL5-B soft) on every exposed unused slot run (crossbar and upright front and inner faces, rail outer and inner faces, brace outer face, unused stile faces). Leave the speaker (D12) and laptop-mount (D19) slot runs open, or cover only their unused lengths | Turns the slotted faces into plain black bars, the largest visible area. Covers lift out for F2 spare nuts and later accessories | Low: buy by the metre, trim in place | J9 (trim), F2 |
| 3 | **Black end caps HFC5-4040-B** on both upright ends and the side-rail front ends (the rear ends butt the uprights). Crossbar and stile ends all butt, so they need none. The brace ends are mitred and bear on the brackets | Already planned. Confirmed catalog parts (HFCL5 long-leg variants exist for 2040) | Low | — |
| 4 | **Side panels on 12 mm standoffs + `pnl_side` -12 mm** (§4) | HW-01/02 bar, HW-03..06, HW-27/28, the D8 access holes, the open corner slot | Medium: new part + 8 standoffs + an FRM-05 width change (skeleton change, about a 25-part regen) | J9, F1 |
| 5 | **FRM-07 ordered black** (surface option on the configurable plate) | The bright 5 mm line under the desktop from the side | Trivial: the plate isn't ordered yet (D21) | D14 |
| 6 | **Black fasteners**: black-oxide M5 socket heads instead of the zinc SET screws where visible (HPTTD5 stems, HBLFSD5, HBL45TD5), and black button heads + black washers for the FRM-05 / side-panel face screws | Bright dots on black and on dark felt | Low: order screws without `-SET`, or swap them. Keep F3 torque 6.8 N·m and F4 locking | F3, F4, F5 (check thread engagement for the button-head length) |
| 7 | **HBLFSDB5** for HW-07/08 (**verify** on the Misumi site) | Gusset in the knee window, from the side | Low, if it's orderable | D15 unchanged |
| 8 | Optional: extend the side panel forward to y ≈ 295 | The HPTTD5 stem and its 2 heads | Low on top of #4. Gives a wider (~104 mm) side fin that overlaps the desktop's back corner in side view | — |
| 9 | Accept as is: HBL45TD5 (no black finish listed), zinc HPTTD5 / HPTLD5 (no black plate found; HPTLD5 is hidden anyway), the M6 heads (already black). Painting the plates or the HBL45TD5 is user finishing and needs the user's OK | — | — | D14, D20 |

**Not recommended** (each weakens a joint the guide relies on):
- removing or relocating the outer HPTTD5 (D2: J1 / J3 / J4);
- any blind, in-slot or end-tap-only replacement of a bracket (J9, J2, J5);
- touching the D20 brace brackets (W2);
- moving the M6 heads back inboard (D9, the user's 2026-11-01 call);
- back-face plates instead of the paired stile gussets (J5, standoff clash).

## 7. Follow-ups
- Check that HBLFSDB5, a black standoff and a black HBL45T5 cover can actually be ordered (product pages).
- When FRM-05 goes felt, set `pnl_t` to the felt's real thickness. The side panel's back edge follows it
  (y = 392.2 + `pnl_t`).
- After the side panel is built, run `python tools/near_check.py` on the new part and FRM-05 (plate heads,
  speaker block, desktop corner).
- If D19's laptop arm moves, recheck whether HW-39/40 become visible from the Eye.

Sources: [HSCA / HSCL slot covers](https://in.misumi-ec.com/vona2/detail/110302695120/),
[HFC5 end caps](https://uk.misumi-ec.com/vona2/detail/110300440510/),
[HBLFSN5 / HBLFSNB5](https://misumi.partcommunity.com/3d-cad-models/hblfsn5-hblfsn5-4-hblfsnb5-hblfsnm5-hblfsnk5-hblfsne5-brackets-hfs5-reversal-brackets-with-tab-misumi?info=misumi%2Fmetric%2F38_al_extrusions_blackets%2F5%2Fhblfsnm5_asmtab.prj&languageIso=cs),
[HBLFSD5](https://misumi.partcommunity.com/3d-cad-models/hblfsd5-brackets-hfs5-reversal-brackets-with-tab-2-slots-misumi?info=misumi%2Fmetric%2F38_al_extrusions_blackets%2F5%2Fhblfsd5_asmtab.prj&languageIso=en&countryIso=US),
[sheet-metal plates p2259](https://us.misumi-ec.com/pdf/fa/2010/p2259.pdf), `refs/misumi_brackets/HBL45T5/p2255.pdf`.
