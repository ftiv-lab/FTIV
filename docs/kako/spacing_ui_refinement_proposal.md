# Spacing UI & Terminology Refinement Proposal

## 1. Issue Analysis

### A. Default Value Discrepancy
- **User Report**: "Default line spacing becomes 0.5, but 0 is fine."
- **Code Finding**: `models/spacing_settings.py` defines `DEFAULT_LINE_SPACING = 0.2`.
- **Action**: Change `DEFAULT_LINE_SPACING` and `DEFAULT_V_LINE_SPACING` to `0.0`.

### B. Confusing Terminology (Legacy Mix)
- **Current Logic** (`TextSpacingDialog`):
  ```python
  label_char = tr("label_char_spacing_horz") + (" (縦)" if is_vertical else " (横)")
  # Result in Vertical Mode: "文字間隔 (横書き): (縦)" -> Confusing!
  ```
- **Action**: 
  - Create neutral keys: `label_spacing_char` and `label_spacing_line`.
  - Remove dynamic suffixing in Python code, OR use formatted strings if direction is needed.
  - Recommended: Just "Character Spacing" and "Line Spacing" as the dialog already shows "Current Mode: Vertical".

### C. Button Label Consistency
- **Current**: `menu_toggle_vertical` used for both Context Menu (Checkable) and Main Window Button.
- **User Request**: Main Window button should say "Switch Orientation" (横書き・縦書き切替) or similar, to indicate toggle action explicitly.
- **Action**: 
  - Create new key `btn_toggle_orientation` (or similar).
  - Japanese: "横書き・縦書き切替" (Switch Horizontal/Vertical).
  - English: "Switch Orientation".

## 2. Implementation Plan

### Step 1: Update Localization (`jp.json` / `en.json`)
Add/Update keys:
- `label_spacing_char`: "文字間隔" / "Character Spacing"
- `label_spacing_line`: "行間隔" / "Line Spacing"
- `btn_toggle_orientation`: "横書き・縦書き切替" / "Switch Orientation"
- `mode_vertical`: "縦書き" / "Vertical"
- `mode_horizontal`: "横書き" / "Horizontal"
- `label_current_mode_fmt`: "現在のモード: {}" / "Current Mode: {}"

### Step 2: Update `models/spacing_settings.py`
- Set `DEFAULT_LINE_SPACING = 0.0`
- Set `DEFAULT_V_LINE_SPACING = 0.0`

### Step 3: Update `ui/dialogs.py` (`TextSpacingDialog`)
- Use new keys `label_spacing_char` and `label_spacing_line`.
- Remove legacy suffix logic.
- Update "Current Mode" label to use `tr("label_current_mode_fmt").format(...)`.

### Step 4: Update `ui/tabs/text_tab.py`
- Update "Toggle Vertical" button to use `btn_toggle_orientation`.

## 3. Verification
- partial `verify_all.bat`
- Manual check of Dialog labels and Default values.
