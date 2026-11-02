# Black frame + dark grey felt panel: parts research (2026-11-02)

Research only: no design, part-script or skeleton changes. Misumi facts were read from the live US product
pages (us.misumi-ec.com, Playwright, 2026-11-02) unless marked otherwise. Prices and ship dates are from that day.
**C** = confirmed on the vendor page, **E** = estimate or inference.

Files here: `HBLTD5_drawing.png`, `HFC5_drawing.png`, `HFCB5_drawing.png` (Misumi catalog drawings, screenshots).

## Summary table

| Item now | Black part | Finish | Status |
|---|---|---|---|
| HFS5-2040 (crossbars, stiles, braces) | **HFSB5-2040** | black anodize | C. Same page, same alterations |
| HFS5-4040 (uprights, side rails) | **HFSB5-4040** | black anodize | C |
| HPTTD5 T-plate | **none** | only bright chromate steel or 304 SS | C. Paint or powder-coat (E) |
| HPTLD5 L-plate | **none** | trivalent / bright chromate steel or 304 SS | C. Paint or powder-coat (E) |
| HBLFSN5 | **HBLFSNB5** (-SET OK) | black anodize, 383.0 cast Al | C |
| HBLFSD5 | **none** (types HBLFSD5 / HBLFSDK5 only) | - | C. Nearest: **HBLTDB5** (different envelope) |
| HBL45TD5 | **none** (clear anodize only) | - | C. No black 45 deg bracket found. Paint (E) |
| CBM5-10 screws | **HCBMTB5-10** | trivalent chromate black, 10.9 | C (Misumi puts these with black brackets) |
| HNTT5-5 T-nut | **none** | trivalent chromate (zinc) | C. Hidden in the slot anyway |
| M5 x 12 standoff | Misumi black-anodized standoffs (configurable) / Lyn-Tron `-14` finish | black anodize | Series C; exact part number not built (E) |
| M6x55 SHCS | Black-oxide 12.9 ISO 4762 | black oxide | C (Fastener Superstore 225511, Aspen ME053-61X55) |
| Hanger plate 5 x 80 x 530 | Laser-cut steel + black powder coat | powder coat | E. See section 3 |
| End caps | **HFC5-4040-B**, **HFC5-2040-B**, **HFCB5-2040-B** | black polyamide | C |

## 1. Black HFS5 extrusion

- **HFSB5-2040**: https://us.misumi-ec.com/vona2/detail/110302684350/ (same series page as HFS5-2040 and CAF5-2040). C
  - The spec table lists HFS5-2040 (clear anodize) and HFSB5-2040 (black anodize) on the same row values:
    A6N01SS-T5 / 6005A-T5, L 50-4000 in 0.5 steps, 0.88 kg/m, 324 mm2, Ix 1.358e4, Iy 5.13e4 mm4.
  - Configurator test: `HFSB5-2040-212-LAT45-RAT45` resolves to a valid part, $20.59, ships Dec 2 2026. That is the
    D20 brace with both ends cut at 45 deg (code convention: `refs/misumi_brackets/_cut45/README.md`).
    `HFSB5-2040-500-LTP-RTP` (both ends tapped) also resolves, $26.00, ships Dec 2. The type filter shows
    "20 Day(s) or Less" for black 2040, so allow about 4 weeks. C
- **HFSB5-4040**: https://us.misumi-ec.com/vona2/detail/110302684530/ C
  - Same values for clear and black: 1.28 kg/m, 472 mm2, Ix = Iy 8.89e4 mm4.
  - The black part's alteration list includes LTP/RTP/TPW tapping, Heli-Coil (LHP/RHP/HPW), SC precision cut and
    LAT45/RAT45. The shared alteration table also lists wrench access holes (LWP/RWP, AH/BH/AV/BV) and counterbores
    (Z6/XA100). Misumi notes: "Alterations are not applicable to all frames". The filter showed "1 Day(s) or Less" for
    the base part.
- **Profile**: the type code stays HFS. Black only adds B, with the same section area and inertia. **E (strong):** same die,
  so the existing `profiles/misumi_hfs5_*.dxf` stays valid. The CAD download on the HFSB5 page wasn't compared.
- **Raw aluminium shows on black parts (C/E):** the 45 deg cut faces aren't anodized (catalog, `_cut45/README.md`, C),
  so bare aluminium shows on black braces where the mitre is visible. Plain cut-to-length ends are probably bare too
  (E, not stated on the page); end caps hide them. A black touch-up pen covers small areas: Misumi links an anodize
  repair item from the HBLFSNB5 and HBLTDB5 pages.
- Wrench access holes and M6 through-holes drilled by the user will also show bare aluminium inside the bore (E).

## 2. Brackets

- **HBLFSNB5** (black HBLFSN5): https://us.misumi-ec.com/vona2/detail/110300437260/?HissuCode=HBLFSNB5-SET C
  - Type list: CHBLFSN5, HBLFSN5, HBLFSN5-4, HBLFSNB5, HBLFSNF5, HBLFSNM5. 383.0 cast Al, black anodize, 15 g,
    2 x CBM5-10 + 2 x HNTT5-5, 1176 N. Same geometry as HBLFSN5, so the existing lib part and STEP stay valid (E).
  - `HBLFSNB5-SET` resolves: $4.31, ships Nov 5. Page note: "Screws for black anodized parts are HCBMTB (Trivalent
    Chromate Black)". **E:** -SET on a black bracket probably ships black HCBMTB screws, but the page doesn't say what is
    in the kit. Confirm before relying on it, or order HCBMTB5-10 separately.
- **HBLFSD5 2-slot: no black version on the US site.** https://us.misumi-ec.com/vona2/detail/110300437620/ lists only
  HBLFSD5 and HBLFSDK5. The guessed `HBLFSDB5` returns 404. C
  - Nearest black part: **HBLTDB5** "Thick Brackets, 2 Slots",
    https://us.misumi-ec.com/vona2/detail/110300437870/?HissuCode=HBLTDB5 (`HBLTDB5-SET` is listed). C
    - A6N01SS-T5 extruded, black anodize, 36 g, 4 x CBM5-10 + 4 x HNTT5-5, **1470 N** (same as HBLFSD5). $4.77, ships Nov 7.
      Has a 3D CAD download.
    - Envelope (drawing `HBLTD5_drawing.png`, C): **34 wide, 35 x 35 legs, 5 thick, no tabs**, 4 x d5.5 on a 20 mm pitch,
      holes 25 mm from the inside corner. HBLFSD5 is 40 wide x 30 x 30 x 4.5 with tabs.
    - **Fit risk (E):** D15 says the upright reaches only 6 mm below the HBLFSD5's 30 mm leg, and it clears the HPTTD5
      by 1 mm. A 35 mm leg leaves 1 mm of upright below it and may hit the HPTTD5. Run a near_check before swapping. If it
      doesn't fit, `up_below` grows (it is currently driven by the brace, D20, so there may be room) or the gusset
      gets painted.
- **HBL45TD5: no black version.** https://us.misumi-ec.com/vona2/detail/110300439270/ lists HBL45TS5, HBL45TD5,
  HBL135TS5 and HBL135TD5 in A6N01SS-T5 clear anodize only. No "HBL45TDB5" was found anywhere. C
  - Nearest: none in the catalog at 45 deg for 2 slots. Options (E): (a) have the clear part stripped and black-anodized
    by a local anodizer; (b) satin-black paint or powder coat (holes masked); (c) accept clear. Misumi's free-angle
    brackets (HBLTBA20 etc.) are 20 mm single-slot only.
- **HPTTD5 / HPTLD5: no black version.** C
  - HPTTD5: https://us.misumi-ec.com/vona2/detail/110302245970/ (HPTTD5, HPTTS5, SHPTTS5). Low-carbon steel with
    bright chromate, or 304 SS; finish filter "Not Provided / Trivalent Chromate".
  - HPTLD5: https://us.misumi-ec.com/vona2/detail/110302245720/ (HPTLN/HPTLS/HPTLD steel chromate, SHPTL* 304 SS).
  - Nearest (E): black powder coat or paint on the steel HPTTD5/HPTLD5. Steel takes powder coat well, and the coat adds
    about 0.05-0.1 mm per face (E). Mask or ream the d5.5 holes. Third-party black-anodized 20-series T/L plates (Amazon,
    Bulkman3D PL21B, Alux "connection plate 20x40 black" RAL 9005) are 60 x 60 x 4 five-hole or 80 x 38 straight plates.
    None matches the 110 x 80 / 8-hole HPTTD5, so the joint would change (J4).
  - Plates are 2.3 mm on the outer faces, so their finish is very visible. Painting them is the cheapest consistent fix (E).

## 3. Fasteners, standoffs, hanger plates

- **Black bracket screws:** Misumi **HCBMTB5-10** (SCM435 / 4137, trivalent chromate black, class 10.9, M5 head
  8.5 dia x 5) on the same series page as CBM5-10: https://us.misumi-ec.com/vona2/detail/110302261370/?HissuCode=HCBMTB5-10
  (seen on the MY site; the US catalog P.2858 lists HCBMT). C. For HBL45TD5 use HCBMTB5-14 (E: assumed to exist in
  that length; the M5 lengths seen were 8, 10 and 14).
- **HNTT5-5:** US variants are HNTT5 (S10C trivalent chromate), HNTTV5, HNTTZ5, HNTTSN5 and HNTTSS5. **No black version.** C (search
  of the Misumi page text). The nut sits inside the slot behind the bracket and isn't seen in normal use (E).
- **M5 x 12 standoffs (D10):** Misumi sells configurable female-female **round** standoffs in A2017 with "Black
  Anodized" as a finish option: https://us.misumi-ec.com/vona2/selector/standoffs/female-female-threaded-round-standoffs/ (C).
  Hex ones with a black option: https://us.misumi-ec.com/vona2/selector/standoffs/one-end-male-threaded-hex-standoffs/ (C, male-female).
  The exact part number wasn't built (E). Alternative: Lyn-Tron aluminium M5 hex female-female standoffs with finish suffix
  `-14` = black anodize type II (e.g. AA5088-5080-xx.x-14, C for the finish code; 12 mm length not confirmed).
  McMaster lists black-anodized aluminium standoffs, but its pages didn't render for the part number (not confirmed).
- **M6x55 SHCS (D9, D21):** black-oxide alloy steel ISO 4762 / DIN 912 12.9 is standard stock. Fastener Superstore 225511
  (box of 100, $53.79): https://www.fastenersuperstore.com/products/225511/socket-head-cap-screws?pid=17920 ;
  Aspen Fasteners ME053-61X55 (made in USA):
  https://www.aspenfasteners.com/m6-1-0-x-55mm-iso-4762-metric-hex-socket-head-cap-screws-alloy-steel-black-oxide-class-12-9-steel-made-in-u-s-a/ . C.
  McMaster's 91290A family is black-oxide metric SHCS, but the exact 55 mm part number wasn't confirmed (E). The D21 M5
  countersunk screws (ISO 10642) also come in black-oxide 10.9 (E: standard stock).
- **Hanger plates FRM-07L/R (5 x 80 x 530, now zinc steel):** Misumi configurable SS400 plates stop at **500 mm** length
  (A 20-500, C on the SG listing), so 530 doesn't fit that family. Options (E):
  - **SendCutSend** laser-cut mild steel with countersinks, then **Matte Black** powder coat (Axalta Black Magic BK120,
    0-9 % gloss per their FAQ). Powder-coat size limit 30 x 36 in for .187/.250 mild steel, so 530 mm fits (C:
    https://sendcutsend.com/services/powder-coating/ , https://sendcutsend.com/materials/processing-min-max/).
    Their steel gauges are 3/16 in (4.76) or 1/4 in (6.35), **not 5.0 mm**, so `hang_t` would change (+/-). They recommend
    cold-rolled 1008 under powder coat. Countersinking with powder coat wasn't confirmed for those thicknesses.
  - Or buy a 5 x 80 flat bar and have a local shop powder-coat or black-oxide it (no vendor checked).
  - The plate sits under the desktop on the flange, mostly out of sight except its outer edge, flush with the rail.

## 4. End caps (black)

Misumi pages: HFC5 https://us.misumi-ec.com/vona2/detail/110300440510/ ; HFCB5 (screw affixed)
https://us.misumi-ec.com/vona2/detail/110302249040/ . Polyamide, colour B (black) or S (light grey). C. Drawings
`HFC5_drawing.png`, `HFCB5_drawing.png`.

| Profile | Part | Plate thickness | Fixing | Source |
|---|---|---|---|---|
| 4040 | **HFC5-4040-B** | 3 mm, 40 x 40, 4-R1 | press fit: 4 pins, 7 mm long | C (drawing) |
| 2040 | **HFC5-2040-B** | 3 mm, 20 x 40 | press fit: 2 pins, 8 mm, into the two centre holes | C (drawing) |
| 2040 | **HFCB5-2040-B** | 2.5 mm | 2 bosses (7.5 mm) + 1 x HFBMB3-12 black flat-head screw (included) | C. How the screw holds (into a boss in the centre hole) is E |
| 4040 screw type | **none** (HFCB5 is 2020/2040 only) | | | C |

- A press-fit cap is a friction fit. Misumi notes the pin shape may change to stop caps falling off (C). There's
  also HFCL5 (LDPE, longer legs) for 2020/2040, which isn't for frames with wrench holes or D/L holes.
- **Tapped ends:** an end tapped M5 for an end anchor (D7, D8, M1) is a joint face, butted against the other member,
  so it gets no cap. If a cap goes on a tapped free end, its pin enters a threaded centre hole: likely looser but still
  holds (E). An end with an access hole near it doesn't affect the cap.
- **45 deg mitred ends (FRM-06 braces): no cap fits** (C: flat caps for square ends only; Misumi's angled caps
  HFC30A5/45A5/60A5 are for the HFS30A5/45A5/60A5 angled profiles, not mitre cuts). The mitre rests on the HBL45TD5 face,
  and only its bare cut edge shows.
- Probable free ends (E, check the model): upright tops and bottoms, and side-rail front ends, which are 4040, so about
  **6 x HFC5-4040-B**. Crossbars and stiles are anchored at both ends, so none for 2040 unless a free end exists.

## 5. Dark grey felt privacy panel (~1880 x 980 + two narrow side panels)

**Sheet fit:** standard PET felt sheets are 4 x 8 ft = **1219 x 2438 mm**, so 1880 x 980 fits, with 1880 along the
2438 length (C, arithmetic). Offcuts from one sheet: 239 x 2438 and 558 x 980 (E: side-panel sizes not known here;
a second sheet may be needed). Kirei sheets are 2800 x 1200 (110.24 x 47.24 in), which leave 220 x 2800 and 920 x 1200.

### (a) Solid PET acoustic felt board
1. **Kirei PET Panels** (San Diego): https://www.kireiusa.com/products/pet-panels (C)
   - 9 / 12 / 24 mm, 2800 x 1200 sheets. Weights 14 / 18 / 22 lb per sheet, so 12 mm is about **2.4 kg/m2** and
     the 1880 x 980 panel is about 4.5 kg (E, arithmetic).
   - Class A (ASTM E84). Colours are numbered swatches (e.g. PET 101 ... 908). Grey and charcoal codes weren't identified,
     and "not all colours come in all thicknesses". Request samples and a quote (no web price).
2. **Felt Right Commercial Felt Sheet** (US): https://feltright.com/products/commercial-felt-sheet (C)
   - **9 mm** (3/8 in) x 48 x 96 in, $174.95 per sheet, plus freight on a pallet from **$750**. Also sold as Layered (18 mm)
     and 1 in.
   - 42 colours. Greys: **Ebony, Cast, Mineral, Armor, Nickel, Fog, Zinc, Ash**. Colour sample kit $49.95. Lead time 3-5 days.
   - Hex estimates from the names, not measured (E): Ebony ~#1e1f21, **Cast ~#3a3c3f**, **Armor ~#4b4d50**,
     Mineral ~#5f6265, Nickel ~#77797c. Pick from the sample kit.
3. **AcoustiGuard Eco-Felt**: https://acoustiguard.com/product/felt-acoustic-panels-eco-felt/ (C)
   - **12 mm (1/2 in)** and 25 mm, 48 x 96 in. 25 mm comes in white or grey only. Quote only, 1-888-625-8944. Colour
     chart not read.
4. Others (not checked in detail): Acoufelt Solid 12 mm (US-made, cut to size 12-48 in wide x up to 108 in, "Grey GR02"),
   https://www.acoufelt.com/product/wall/panels/solid-walls/12mm/ ; AcousticSoundPanels.com 9 mm 4x8, Dark Gray offered for
   panels 24 x 48 in or smaller.

**Rounded corners:** PET felt cuts with a sharp knife against a template, a CNC drag knife or a laser (a laser seals the
edge). Acoufelt and Felt Right "Custom Projects" cut to shape (E: radius not quoted). A DIY radius of 20-50 mm with a
knife is easy (E).

**Rigidity at 1880 wide on 8 standoffs (E, engineering judgement, not tested):**
- PET felt is a soft board, about 200 kg/m3 at 12 mm (2.4 kg/m2). Hung vertically, gravity acts in its plane, so it
  won't sag much. The issue is **flatness**: it bows and waves between support points and can curl at free edges,
  especially at 9 mm.
- With 8 standoffs (say 4 top and 4 bottom, ~600 mm apart), **12 mm** is likely acceptable. 9 mm will probably show waves.
- Clamp with large black washers or caps (>= 25 mm dia) under the screw heads. A bare M5 head pulls through felt.

### (b) Rigid core with dark grey felt laminated on
No US product sold as "PET felt pre-laminated on MDF, 4 x 8" was found (two searches). The practical route (E):
- **9 mm felt (e.g. Felt Right Cast/Armor) bonded with contact adhesive or spray adhesive to 3 mm black ACM**
  (Dibond-type aluminium composite, 4 x 8 sheets, ~3.8 kg/m2, so ~7 kg core for the main panel; flat, stiff, light,
  and its black edge and back match the frame). Total ~3.5 + 7 = ~10.5 kg (E).
- Or a **6 mm MDF / 1/4 in Baltic birch** core: cheaper, heavier (~4.5 kg/m2 for MDF, E), and the edge needs paint.
- Or skip the felt: **Valchromat Dark Grey** coloured-through MDF (Trinity Innovations, CA, US distributor;
  https://trinityinnovations.net/product/colored-mdf-panels/), rigid, with no acoustic effect.
- A laminated panel is stiff enough for the 8 standoffs. Drill the core and counterbore the felt so the standoff screws
  bear on the core, not on the felt (E).

## Open points
1. Confirm what `HBLFSNB5-SET` and `HBLTDB5-SET` contain (black HCBMTB screws?) before ordering.
2. Check the HBLTDB5 envelope (35 mm legs, no tabs) against the HPTTD5 and the upright end (D15 clearances) in the model.
3. Pick a black option for HPTTD5/HPTLD5 and HBL45TD5 (paint, powder coat, re-anodize, or accept the mix).
4. Hanger plate: 5 mm (local shop) or 4.76 / 6.35 mm (SendCutSend) changes `hang_t`.
5. Felt colour from physical samples. The hex values above are guesses from names.
