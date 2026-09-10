# Samsung 970 EVO — M.2 NVMe SSD · 3D modeling study

A datasheet-accurate model, PBR materials, an engineering dimension drawing, and
turntable / exploded / macro renders of the **Samsung SSD 970 EVO 500 GB**
(M.2 2280, MZ-V7E500). Built as a sample deliverable for the Upwork posting
*"3D Modeler — Electrical Component Models & Renders"* (EETech).

Everything here is generated from scripts — the model, the textures, the shots,
and the breakdown page. Nothing uses manufacturer geometry, textures, or photos;
all label / silkscreen / chip artwork is recreated vector work.

## Layout

```
build/               the pipeline (Python + Blender bpy + a little shell)
  make_labels.py       recreated label / PCB / chip-mark textures  -> refs/textures/
  lib_common.py        shared Blender helpers: materials, lighting, camera, render cfg
  model_m2.py          builds deliverables/models/m2_970evo.blend  (45 named parts)
  render_shots.py      shot modes: look | hero | wireframe | turntable | exploded | macro
  diag_m2.py           clay diagnostic render to catch modeling defects
  assemble.sh          ffmpeg: PNG sequence -> mp4 (+ web version + poster)
  export_models.py     .blend -> .glb + .fbx
  pack_portfolio.py    inlines media into deliverables/portfolio.html (from portfolio_src.html)
  run_m2.sh            end-to-end: textures -> model -> all shots -> encode -> export
refs/
  SPEC.md              datasheet figures the model was built to
  textures/            generated source textures (regenerate with make_labels.py)
deliverables/
  models/              m2_970evo.blend / .glb / .fbx
  renders/             hero stills + wireframe passes
  video/               turntable / exploded / macro  (.mp4, _web.mp4, _poster.png)
  portfolio.html       single-page dimensioned breakdown (open in a browser)
storage_ssd_hdd_m.2.glb   third-party reference only — see "Reference asset" below
```

## Reproduce

Requirements: **Blender 5.1** on `PATH` (or edit the path in `run_m2.sh`),
**Python 3** with `pillow` + `numpy`, and **ffmpeg** for the video step.

```bash
bash build/run_m2.sh          # ~20 min on a 6-core CPU (no GPU needed; EEVEE only)
python build/pack_portfolio.py
```

Intermediate render frames (`deliverables/renders/m2_{turntable,exploded,macro}/`)
are git-ignored; the encoded `.mp4`s in `deliverables/video/` are the outputs.

## The model

| | |
|---|---|
| Overall | 80.15 × 22.15 × 2.38 mm (datasheet max); modeled 80.15 × 22.15 × 2.07 |
| PCB | 0.80 mm, black solder mask, ENIG-gold pads, white silkscreen |
| Parts | 45 named objects, one root, ~14 k triangles, no n-gons |
| Semiconductors | Phoenix controller, LPDDR4, 2× V-NAND, PMIC — modeled BGA/TFBGA packages |
| Connector | M.2 M-key edge, individual gold contacts, cut key notch |
| Stack | PCB → components → gap-fill → copper heat-spreader film → matte laminate label |
| Origin | mounting-notch centreline, PCB mid-plane; +X toward the connector |

## Reference asset

`storage_ssd_hdd_m.2.glb` is *"Storage (SSD, HDD, M.2)"* by **Blue Lantern**
(Sketchfab), **CC BY 4.0**. It was reviewed only as a scale check and quality
benchmark. None of its geometry, UVs, or textures appear in this build.

## Trademarks

"Samsung", "970 EVO", "V-NAND", "Phoenix" are trademarks of Samsung Electronics;
"EETech", "All About Circuits", "EEPower" are trademarks of their owner. Used here
only to identify the subject and the recipient. Non-commercial modeling study.
