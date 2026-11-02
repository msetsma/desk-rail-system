# SolidCraft: improvements for agent-driven CAD

Notes from the desk-rail project (2026-11-02, CLI v0.24.0) on how an agent works with SolidCraft today,
why, and what would let it work natively. Project rules referenced here are in `AGENTS.md` and `PROJECT.md`.

## How the agent works today, and why

### Generated scripts and the headless CLI, not live MCP calls
- **One source of truth.** Each part is a JSON command script written by a Python generator
  (`parts/src/*_gen.py`). It replays, diffs in git, and rebuilds the same part every time. Geometry built
  by live MCP calls only lives in the design file's history, which the next session can't easily read or
  regenerate.
- **Parallel builds.** The live app has one command queue, and the user may be using it.
  `solidcraft-cli` runs headless, many at once (e.g. 28 parts rebuilt in parallel). Over MCP they run one
  after another.
- **Gaps in expression support.** `sketch.slot.*`, `sketch.rectangle.*`, edge/face pick points and
  `sketch.create` origins take plain numbers only. Generators compute them from the evaluated skeleton
  (`tools/skeleton_values.py`) so they follow parameter changes. Typed by hand, they go stale silently
  (DSK-02 broke this way).
- **Checks before geometry exists.** A generator can assert the layout in plain Python before any CAD runs
  (e.g. `FRM-07_gen.check_stations`: no screw on a channel bar, off the rail or on a desktop screw).
- **Speed in the assembly.** Parts are frozen to STEP and linked, so loading or refreshing the assembly
  doesn't replay each part's history.

MCP is the interactive layer: command discovery (`describe_command`), loading the result into the
viewport, inspecting, measuring and quick spikes.

### Python scripts for file edits
The Edit tool covers ordinary code changes. Small Python scripts are used when:
- **The file is structured JSON** (`skeleton/params.json`): load, insert, dump always gives valid JSON, and
  the script asserts its assumptions first (e.g. `frame_top` is still `desk_h - desk_t`).
- **One change touches several files**: one script with an "exactly one match" check per edit applies
  everything or fails loudly (`AGENTS.md` §3).
- **Line endings differ** (CRLF/LF working copies): the script matches using the file's own line ending.

## What would make an agent native to SolidCraft

### 1. A code API in place of JSON command lists
An in-process library on the same kernel:

```python
import solidcraft as sc

plate = sc.box(hang_w, hang_len, hang_t).at(x=rail_l - hang_w, y=ts_len/2 - hang_len)
plate.holes(sc.csk("M5"), at=[(x, y) for y in TNUT_Y for x in TNUT_X])
assert plate.clearance(channel_bars) >= 0
```

Loops, functions, asserts and checks live in one language. The generator layer and the "numbers only"
problem disappear, because values are values. The app becomes a live viewer that watches the source files
and reloads only what changed.

### 2. Text as the native source of truth
Parts and assemblies are diffable text that the app opens directly. Git history is the design history, with
no frozen copies of the geometry to keep in sync.

### 3. Selecting by meaning, not coordinates
- **Edges and faces by query:** "top face of HangerPlate", "edges parallel to Y on the rail's outer face",
  with stable names that survive rebuilds. Typed pick points are the most fragile part of the current setup.
- **Spatial queries:** "what's under this point", "bodies within 10 mm of X". The hanger-plate channel-bar
  conflict was found by hand from bounding boxes.

### 4. Parameters that flow down, and incremental rebuilds
- **Assembly parameters passed into linked parts,** with per-occurrence overrides. Replaces the
  shared-skeleton `parameters.import` pattern.
- **Caching by content hash** for each feature and each part. The app rebuilds only what a change actually
  affects. Manual refresh lists, frozen STEP files and the "more than 3 parts means rebuild" rule go away.

### 5. Design intent as native checks
- **Assertions stored in the model:** `clearance(A, B) >= 3 mm`, `hole lies on slot`,
  `screw length within the T-nut range`. The app re-checks them on every change and flags the ones that fail.
  `check_stations` and much of `tools/near_check.py` become model data.
- **Contacts known from the joints:** the app knows which faces are meant to touch, so interference checks
  skip those pairs without the hand-kept `MATING` list.

### 6. Hardware as real objects
- **Fasteners that understand their stack:** "M5 countersunk into an HNTT5 through a 5 mm plate" picks a
  valid length, cuts the matching hole and adds the BOM line.
- **Vendor catalogs** (Misumi and others) usable directly, with their published limits.

### 7. Sessions and branches
- **Copy-on-write forks of the open design:** try a change, see a geometric diff, then commit or discard it.
- **Several agents at once** on separate branches, each with its own command queue. No file copies and no
  shared-scratch-file races.
- **Transactional batches** that roll back as a unit.

### 8. Feedback suited to an agent
- **Cheap targeted renders:** a section at y = 0, or a before/after diff with changed bodies highlighted.
- **Structured errors and full typed schemas** for every command. Some commands still return `null`
  schemas, so they get spike-tested before use.

## Smaller fixes to the current tool
- Expressions accepted by every numeric parameter (slots, rectangles, pick points, sketch origins).
- `solidcraft-cli script` working on designs with components (#886), so live work can be round-tripped
  into source.
- A non-blocking or multi-document command queue in the live app.
- `solid.hole` speed: 13 countersunk holes on a plain box took ~10 s, while a sketch + extrude cut of the
  same count takes milliseconds.

## Shortest path
If only three of these existed:
1. Python bindings with file watching.
2. Selection by query.
3. Assembly parameters passed into parts, with incremental caching.

Together they would remove most of this project's tooling (generators, skeleton import, frozen parts,
refresh bookkeeping), leaving the effort for the design itself.
