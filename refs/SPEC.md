# Spec pack — Storage media modeling study

Two devices, modeled from manufacturer datasheets. All geometry in **millimetres**,
real-world scale, origin conventions noted per model.

> Trademark note: "Samsung", "970 EVO", "860 EVO", "V-NAND", "Phoenix", "MJX" and
> related marks belong to Samsung Electronics. Labels here are **recreated vector
> artwork** for a non-commercial modeling study; no manufacturer photos or brand
> font files are used.

---

## 1 — Samsung 970 EVO — M.2 NVMe SSD  (variant: 500 GB, MZ-V7E500)

Source: *Samsung V-NAND SSD 970 EVO Data Sheet, Rev 1.0, April 2018.*

| Property | Value |
|---|---|
| Overall size (max, incl. label + parts) | **80.15 × 22.15 × 2.38 mm** |
| PCB thickness | 0.8 mm ± 10 % (JEDEC M.2) |
| Form factor | M.2 2280, **M-key**, single-sided |
| Interface | PCIe Gen 3.0 ×4, NVMe 1.3 |
| Controller | Samsung **Phoenix** (nickel-plated lid), ~12 × 12 mm |
| DRAM | 512 MB **LPDDR4**, ~10 × 11 mm |
| NAND | Samsung **V-NAND** 3-bit MLC — 2 packages, ~13 × 18 × 1.0 mm |
| PMIC + passives | 1 PMIC ~3 × 3 mm; 0402 / 0603 caps + resistors along power rails |
| Label | heat-spreader sticker with **thin copper film** on the underside → label back reads copper, not black |
| Mounting | single M2 screw at the 80 mm end; semicircular notch ~3 mm dia with keep-out ring |

**Edge connector** — 75 positions, **0.5 mm pitch**, gold fingers on both faces,
offset front/back. M-key: short contact block (left) + key gap + long contact block.
Contact field occupies roughly the bottom 4 mm of the card.

**Component layout** (connector end → mount end): gold fingers → passive row →
Phoenix controller → LPDDR4 DRAM → NAND #1 → NAND #2 → PMIC; label/heat-spreader
covers the full PCB top except the gold fingers and the mount-notch tab.

**Model origin:** centre of the semicircular mounting-notch, PCB mid-plane. +X toward
the connector, +Z up (label side).

**Exploded order (bottom→top):** PCB → passives/ICs → NAND → DRAM → controller →
copper film → label; M2 screw pulls up out of the notch.

---

## 2 — Samsung 860 EVO — 2.5" SATA SSD  (variant: 1 TB, MZ-76E1T0)

Source: *Samsung V-NAND SSD 860 EVO Data Sheet, Rev 1.0, Dec 2017.*

| Property | Value |
|---|---|
| Overall size | **100.0 × 69.85 × 6.8 mm** (2.5-inch, 7 mm z-class) |
| Form factor | 2.5 inch |
| Interface | SATA 6 Gbps |
| Controller | Samsung **MJX**, ~12 × 12 mm |
| DRAM | 1 GB **LPDDR4** (1 TB variant), ~11 × 13 mm |
| NAND | Samsung **V-NAND** 3-bit MLC — 2 packages, ~14 × 18 mm |
| Case | two-piece **anodized aluminium-alloy**, dark grey, fine bead-blasted finish; 3 × P6 pentalobe screws (2 hidden under the back label) |
| Internal PCB | ~½ the drive footprint, mounted at the connector end on 2 locator pins; thermal pad between parts and the top shell |

**SATA device connector** — combined data + power on one short edge, **1.27 mm pitch**,
L-keyed tongues in a shroud. Data segment = 7 contacts (~10 mm), gap, power segment =
15 contacts (~20 mm); overall ~36 mm, offset ~4 mm from one long edge.

**External detail** — top perimeter chamfer ~0.6 mm; front label sticker (SAMSUNG /
Solid State Drive + play-triangle mark + capacity/serial sub-label); bottom
regulatory label + certification block + barcode. 2.5" mounting holes per SFF-8201:
4 on the bottom + 2 per side (M3).

**Model origin:** centre of the drive footprint, on the bottom face. +X toward the
SATA connector, +Z up (label side).

**Exploded order (bottom→top):** bottom shell → screws → internal PCB (+ SATA
connector) → NAND / DRAM / MJX → thermal pad → top shell → front label.

---

## Reference asset reviewed (not reused)

`storage_ssd_hdd_m.2.glb` — Sketchfab, *"Storage (SSD, HDD, M.2)"* by Blue Lantern,
CC-BY-4.0. Used only as a subject/scale sanity check and quality benchmark. No
geometry, UVs, or textures from it are used in this build.
