# Translation Audit Report
## 1. Parity Check (Key Mismatch)
- ✅ Parity OK: en.json and jp.json have identical keys.
## 2. Usage Check (Code vs JSON)
- ✅ All `tr()` keys are defined in JSON.
### Potentially Unused Keys (Defined but not found in `tr(...)`):
> Note: Keys might be constructed dynamically or used in other ways.
- `anchor_auto`- `anchor_bottom`- `anchor_left`- `anchor_right`- `anchor_top`- `btn_apply`- `btn_change_all_line_color`- `btn_change_all_line_opacity`- `btn_change_all_line_width`- `btn_close_all_text`- `btn_toggle_anim`- `grp_batch_adj`- `grp_danger`- `grp_defaults`- `grp_global_anim`- `grp_global_vis`- `grp_img_all_normalize_ops`- `grp_img_all_pack_ops`- `grp_layout_control`- `menu_anchor_point`- ... and 142 more.
## 3. Potential Hardcoded Strings
> Please manually review these. Many might be valid (IDs, tech terms).
- [ ] `ui\main_window.py:460` : `setText("+ ")`- [ ] `ui\main_window.py:513` : `setText("+ ")`- [ ] `ui\tabs\image_tab.py:40` : `QPushButton("+ ")`- [ ] `ui\tabs\image_tab.py:712` : `setText("+ ")`- [ ] `ui\tabs\text_tab.py:45` : `QPushButton("+ ")`- [ ] `ui\tabs\text_tab.py:124` : `QPushButton("+ ")`- [ ] `ui\tabs\text_tab.py:452` : `setText("+ ")`- [ ] `ui\tabs\text_tab.py:465` : `setText("+ ")`