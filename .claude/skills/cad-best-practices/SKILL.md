---
name: cad-best-practices
description: CAD modeling best practices (structure, design intent, naming, shared resources, display, checking, versioning, cleanup) plus the pre-milestone cleanup checklist. Load before starting a new part or assembly, restructuring components, preparing a milestone/commit/release, or reviewing a design.
---

# CAD best practices

Generic rules. Each has an agent note (→) on how to apply it when driving CAD through an API
or CLI. Project-specific choices (part-number prefix, colors, materials, library location) live
in `PROJECT.md`. Items marked *(when relevant)* are worth doing for released or shared parts and
can be skipped for quick studies.

## 1. Structure
- **Mirror the physical object.** Each real part is one component. Parts installed together as a
  unit form a subassembly.
  → Before modeling, write the component tree (assembly > subassemblies > parts).
- **Root holds components only.** No loose bodies or sketches at the top level.
  → After any feature that creates a body at the root, move the body into its component.
- **One final body per released part.** Multibody files are fine while working; split or derive them
  into separate parts for the assembly. Exception: a purchased reference model (vendor speaker,
  mouse) may keep one body per finish colour, all inside its one component.
- **Activate before modeling.** Activate the target component before sketching, so geometry lands in
  the right place. → `component.activate` (or the equivalent) before every sketch or feature.
- **Purchased hardware as separate components:** screws, inserts, bearings, electronics, inserted as
  linked references from the hardware library (§4).
- **Ground one component and use joints.** Position everything else with joints or mates, or with
  parametric moves driven by parameters. Never with fixed numeric drags.

## 2. Design intent and references
- **User parameters for key dimensions**, with clear names (`wall_thickness`, `rail_len`) and a
  comment. Mark unmeasured values (e.g. `MEASURE`).
- **Skeleton for multi-part designs.** Parts reference a shared layout sketch, component or
  parameter set, not each other.
- **Dimension for function.** Measure from the datum or mating surface that matters, not from a
  convenient edge.
- **Fully constrain driving sketches.** Sketch on origin planes or offset planes rather than model
  faces where possible.
- **Lock or document in-context references,** so editing one part can't silently change another.
  → Note every cross-part reference in the part's description or in `PROJECT.md`.
- **Configurations or parameters for variants,** not copied files. *(when relevant)*

## 3. Naming and metadata
- **Name everything that matters:** components, bodies, driving sketches, major features,
  parameters. No `Sketch14` or `Body3`. → Pass `name` / `body_name` at creation (renames are costly).
- **Simple part numbers with revision letters**, e.g. `DESK-04 Rev B`. A part that no longer fits the
  old way gets a new number, not a new revision.
- **Fill in file properties:** at least part number, description and material, so the BOM generates.
  → `component.metadata.set` / `document.metadata.set`.
- **Assign real materials**, for mass, center of gravity and simulation. → `material.assign`.

## 4. Shared resources
- **Template:** one starting file with units, properties and the color scheme set.
- **Standard hardware library:** one shared set of fasteners and common parts with fixed part
  numbers, so every assembly uses the same models. → `parts/lib/` (or as `PROJECT.md` says).
- **Consistent appearance scheme:** one color per class (printed, purchased, stock, reference), set
  at component or body level. Purchased parts may use their real finish color instead; follow `PROJECT.md`.

## 5. Display and visibility
- **Named views** for camera angles you return to. → `view.save`.
- **Display states or configurations for visibility sets.** Don't toggle visibility by hand every time.
- **Hidden means intentional.** Delete unused sketches, planes and tool bodies. Keep hidden only
  what something depends on.
- **Simplified representations** of heavy purchased parts in large assemblies. *(when relevant)*

## 6. Checking
- **Interference and clearance** checks, including motion through the full range of joints.
  → Day to day, check only the changed bodies and their neighbours. Do a full check at milestones or
  on request.
- **Manufacturability** for the chosen process: wall thickness, overhangs, insert hole sizes, bend
  radii, tool and wrench access.
- **Tolerances on critical features:** note fits and critical dimensions on a simple drawing when a
  part goes to someone else or to a shop. *(when relevant)*

## 7. Versioning and collaboration
- **Version history:** save a named milestone before major changes. → A git commit (binary
  design files) plus the CAD app's own versions if it has them.
- **One editor per file at a time.** → Only one agent edits a given design file. Subagents
  work in separate part files.
- **Short change notes:** one line per milestone, e.g. `Rev C: widened slot for M5 bolt`.
  → Use it in the commit message.
- **Informal design review** before building (cutting, printing, ordering). *(when relevant)*
  → A review subagent against these rules and the project guide.
- **Release state:** mark parts WIP or Released (property, name or folder). *(when relevant)*

## 8. Timeline hygiene
- **Keep the timeline error free.** Fix errors and warnings when they appear. Group related
  features (`timeline.group`).

## Cleanup checklist (before each milestone)
1. Root holds only components. Every body sits in its component.
2. One visible body per finished part.
3. Unused sketches, planes and tool bodies are deleted. Hidden items are only dependencies.
4. Timeline errors and warnings are cleared; related features are grouped.
5. Default names (`Sketch14`, `Body3`, `Extrude7`) are replaced.
6. Part number, description, material and release state are set on each part.
7. A narrow interference check passes (a full check if requested).
8. Save the milestone with a one-line change note, and export each part separately if needed.
