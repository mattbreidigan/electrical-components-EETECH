#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BL="/c/Program Files/Blender Foundation/Blender 5.1/blender.exe"
python "$ROOT/build/make_labels.py" >/dev/null
"$BL" -b -P "$ROOT/build/model_m2.py" 2>&1 | grep -E "SAVED|faces:"
R(){ "$BL" "$ROOT/deliverables/models/m2_970evo.blend" -b -P "$ROOT/build/render_shots.py" -- "$1" "$2" "" "${3:-}" 2>&1 | grep -E "DONE|Error|Traceback" | tail -2; }
echo "[hero]";      R hero      m2_hero
echo "[wireframe]"; R wireframe m2_wire
echo "[turntable]"; R turntable m2_turntable 48
echo "[exploded]";  R exploded  m2_exploded  48
echo "[macro]";     R macro     m2_macro     40
echo "[encode]"
bash "$ROOT/build/assemble.sh" m2_turntable m2_turntable 24
bash "$ROOT/build/assemble.sh" m2_exploded  m2_exploded  24
bash "$ROOT/build/assemble.sh" m2_macro     m2_macro     24
"$BL" "$ROOT/deliverables/models/m2_970evo.blend" -b -P "$ROOT/build/export_models.py" -- m2_970evo 2>&1 | grep -E "wrote|Error"
echo "M2 DONE"
