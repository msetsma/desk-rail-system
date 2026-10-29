# Apple MacBook Pro 14in (M4, 2024): LAP-02 reference

Model: `parts/src/LAP-02_gen.py` -> `parts/src/LAP-02_MacBookPro14.json`. Parameters are `mbp14_*`.

## Sources
- Apple tech specs: https://support.apple.com/en-us/121552
  - 312.6 W x 221.2 D x 15.5 H mm (closed). 1.55 kg (M4).
  - 14.2in Liquid Retina XDR, 3024 x 1964, 254 ppi. Active area 302.4 x 196.4 mm (px / ppi).
  - Finishes: Space Black, Silver.
- NanoReview (https://nanoreview.net/en/laptop/apple-macbook-pro-14-m4-2024): trackpad 13.2 x 8.1 cm,
  side bezel 3.4 mm.

## Estimated (MEASURE, from photos; no published value)
| Param | Value | Note |
|---|---|---|
| mbp14_foot_h | 0.9 mm | foot height |
| mbp14_lid_t | 5.0 mm | lid; base slab = 15.5 - 0.9 - 5.0 = 9.6 |
| mbp14_r | 9 mm | plan corner radius |
| mbp14_lid_d | 220.2 mm | lid depth |
| mbp14_foot_dia / ix / iy | 13 / 25 / 18 mm | rubber feet |
| mbp14_kb_w x kb_d, kb_rear | 276 x 112, 10 mm | keyboard well |
| mbp14_tp_w x tp_d, tp_front | 132 x 81, 8 mm | trackpad (NanoReview). A 150 x 98 pad doesn't fit next to a 112 mm keyboard in 221 mm depth |
| mbp14_scr_rim, scr_chin | 1.5, 8 mm | Al rim around the black glass; hinge strip |
| hinge axis | base rear top edge, lid mid-thickness | simplified; the lid floats ~1.6 mm above the deck at the hinge when open |
| mbp14_lid_open | 110 deg | user choice |

Colours: Space Black #2e2f31 (Silver would be #d9dadc), glass #050608, keys #0b0c0d.
