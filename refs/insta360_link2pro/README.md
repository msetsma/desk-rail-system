# Insta360 Link 2 Pro webcam: references

Collected 2026-11-06. **MON-03 is built from the Sketchfab Link 2 mesh** (the Link 2 has the Pro's outer size),
downloaded by the user on 2026-11-06 into `sketchfab_bswlife/` (git-ignored, like every download folder here):

- "Insta360 Link 2 4K AI Webcam" by bswlife, CC BY 4.0 (credit required):
  https://sketchfab.com/3d-models/insta360-link-2-4k-ai-webcam-b6e5aa185a95459a923acabaf4e48005
- glTF, 570k triangles, arbitrary units, Y up, camera faces +Z. The clip is modelled folded into its desk-stand pose.
- `parts/src/MON-03_convert.py` drops the decals, scales the mesh uniformly to the official 58.9 mm camera height
  (84.05 mm per unit; the result is 72.6 x 58.9 x 36.1 mm against the 71.3 x 58.9 x 38 spec, so W +1.8 %, D -4.9 %:
  **the scale is an estimate, MEASURE the real camera**), swings the clip's rear leg 28 deg down about its hinge onto
  the back of the M32U top edge (`m32u_slab_t`, itself a MEASURE), decimates to ~17.5k triangles, and writes
  `converted/MON-03_link2.step` plus a summary JSON (lens centre, bboxes).
- The 1/4-20 thread on the clip's underside isn't modelled.

## Kept files

| Dir / file | Source | Licence | What it is | Measured bbox (mm) | vs spec |
|---|---|---|---|---|---|
| `printables_kbj_skadis_holder/insta360link2.stp` | https://www.printables.com/model/1138425-insta360-link-2-webcam-skadis-holder (by kbj) | CC BY-SA | IKEA Skadis shelf for the **Link 2** (STEP, metres; 3 solids: shelf + 2 Skadis hooks; product names `Insta360 Link 2`, `Stand`). No camera body. | shelf 65.2 x 51.6 x 15.4; with hooks 75.2 x 51.6 x 15.4 | Not the camera. Its through-slot, **9.4 x 44.0 mm**, takes the rear leg of the Link 2 magnetic clip, so that leg is about 44 mm wide and under 9.4 mm thick (estimate). |
| `printables_augu5to_privacy_cover/insta360-link-2-privacy-cover_v1.3mf` | https://www.printables.com/model/1307077-insta360-link-2-privacy-cover (by AUGU5TO) | CC BY-NC | Slip-on cap for the **Link 2** gimbal head (mesh, 2700 triangles, mm). It's lined with foam whose thickness isn't stated. | 39.6 x 39.8 x 33.6 | Inner opening is 33.6 wide x 27.4 high and 36.5 deep. The head's lens-end section is therefore about **33 x 27 mm** less the foam (estimate). The 36.5 mm depth is consistent with the 38 mm spec depth. |

Bboxes were measured with a CARTESIAN_POINT/mesh parser and `solidcraft-cli eval` (STEP per body); slot and cover
openings come from mesh sections. Units checked: the STEP is in metres and imports at the correct mm size; the 3MF is in mm.

## Deleted downloads
- `printables_kbj_skadis_holder/insta360link2.stl` (13.6 MB, 272k triangles): the same shelf as the STEP, so redundant.
- `printables_afar_skadis_remix/insta360-link-2.f3d` (https://www.printables.com/model/1199294, CC BY-SA): a Fusion 360
  archive that SolidCraft can't import; it's a remix of the same Skadis bracket.

## Failed / not downloaded
- Sketchfab Link 2 mesh: the download API needs a login; the user downloaded it by hand (used, see top).
- 3dmodels.org Link 2 Pro / 2C Pro (STEP available): paid ($50/$100), and the site returns 403 to bots. Needs the user's approval to buy.
- MakerWorld (Link 2C body by Jet, Link 2 PTZ case, Link 2 storage box, Elgato 2C backplate): downloads need a login.
  The pages only expose preview images.
- RenderHub Link gen 1 (paid render asset), CGTrader Link 2C (delisted or paid), Cults3D Link 2 transport case (login).
- Thingiverse 6583205, a gen 1 Link cover: the API needs a token (401). It's a cover only.
- Printables 1595339 (Alienware brackets, mount only) and 1475576 (gen 1 Link case): skipped. They're not the camera
  and not the right generation.

## Spec (official where cited; the rest from reviews)

| Item | Link 2 Pro | Link 2 | Source |
|---|---|---|---|
| Camera dims W x H x D | 71.3 x 58.9 x 38 mm. The pose and whether the mount is included aren't stated. | 71.3 x 58.9 x 38 mm (same) | Insta360 spec FAQ [1][5] |
| Weight | 102.5 g bare; 167.5 g with magnetic mount (mount about 65 g) | 101.5 g / 166.5 g | [1][5] |
| Sensor / lens | 1/1.3 in, f/1.9, 24 mm eq. | 1/2 in, f/1.8, 26 mm eq. | [1]; [3][4] |
| FOV | 83.9 deg diagonal, about 71.4 deg horizontal | 79.5 deg diagonal, 67 deg horizontal | [3] reviews (unverified on official page) |
| Gimbal | 2-axis; yaw +/-282, pitch +/-180 deg (as listed; may be total travel) | yaw +/-141, pitch +/-90 deg | [1][5] |
| Mount | Magnetic foldable clip, 2 hinges. **1/4-20 thread on the bottom of the mount**, not the camera. Stronger and opens wider than the Link 2's. | Same style; FAQ recommends curved screens <= 25 mm thick | [3][4][6][7][8] |
| Colours | Graphite Black, Arctic White | | [2] |
| Link 2C Pro (no gimbal) | 62.7 x 30.2 x 26 mm, 48.5 g / 113.5 g | 2C: 46.5 g / 111.5 g | [1][5] |

Sources: [1] https://onlinemanual.insta360.com/link2pro/en-us/faq/specs/hardware ·
[2] https://store.insta360.com/product/link-2-pro ·
[3] https://www.cgmagonline.com/review/hardware/insta360-link-2-pro-webcam/ ·
[4] https://www.techradar.com/computing/webcams/insta360-link-2-pro-review ·
[5] https://onlinemanual.insta360.com/link2/en-us/faq/specs/hardware ·
[6] https://www.bhphotovideo.com/c/product/1942489-REG/insta360_cinsabpa_link2pro01_link_2_pro_black.html ·
[7] https://www.pickr.com.au/reviews/2026/insta360-link-2-pro-webcam/ ·
[8] https://onlinemanual.insta360.com/link2/en-us/operating-tutorials/camera-connect/connect

Photos: store main image https://wassets.insta360.com/store/a6e27500c22d48e79c2477e8764dd4e7/1798_81f4240b-0fce-4abe-831b-55628c932e87.png,
CGMag images (camera, mount) linked from [3]. No orthographic or dimensioned drawings were found.

## Estimated (MEASURE)
- How the 71.3 x 58.9 x 38 envelope splits between the gimbal head, the yoke and the base.
- Head section about 33 x 27 mm (from the privacy cover, less the unknown foam).
- Clip leg about 44 mm wide and under 9.4 mm thick (from the Skadis slot); clip opening range for the Pro (use <= 25 mm from the Link 2 FAQ);
  mount height; offset of the 1/4-20 thread.
