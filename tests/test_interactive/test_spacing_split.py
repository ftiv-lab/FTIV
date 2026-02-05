import os
import sys
from unittest.mock import MagicMock

import pytest
from PySide6.QtCore import QPoint, QSize
from PySide6.QtGui import QAction, QFont, QFontMetrics
from PySide6.QtWidgets import QApplication

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from windows.text_window import TextWindow


# Fixture for QApplication (Session scoped)
@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


class TestSpacingSplit:
    @pytest.fixture
    def setup_window(self, qapp):
        """Setup a TextWindow with mocked dependencies."""
        mw = MagicMock()
        mw.window_manager = MagicMock()
        mw.app_settings = MagicMock()

        # Real QActions are needed for C++ addAction compatibility

        mw.undo_action = QAction("Undo", None)
        mw.redo_action = QAction("Redo", None)

        # Mock specific settings used in TextWindow init
        mw.app_settings.glyph_cache_size = 512
        mw.app_settings.render_debounce_ms = 0  # No debounce for tests
        mw.app_settings.wheel_debounce_ms = 0

        # Create window
        tw = TextWindow(mw, "Test\nLine2", QPoint(0, 0))
        tw.font_size = 20
        # Ensure strict sync rendering for tests
        tw._render_debounce_ms = 0
        return tw

    def test_horizontal_spacing_logic(self, setup_window):
        """Test that split properties affect horizontal rendering logic."""
        tw = setup_window
        tw.is_vertical = False

        # 1. Base measurement
        tw.char_spacing_h = 0.0
        tw.line_spacing_h = 0.0
        tw.renderer.render(tw)
        size_base = tw.canvas_size

        # 2. Increase Char Spacing (Horizontal)
        tw.char_spacing_h = 0.5  # significant increase
        tw.renderer.render(tw)
        size_wide = tw.canvas_size

        assert size_wide.width() > size_base.width(), "Horizontal char spacing should increase width"
        # Height should remain roughly measuring errors aside (outline etc)
        # But specifically checking width is enough.

        # 3. Increase Line Spacing (Horizontal)
        tw.char_spacing_h = 0.0  # Reset char
        tw.line_spacing_h = 10.0  # significant increase (pixels or relative? Logic says: font_size * ratio)
        tw.renderer.render(tw)
        size_tall = tw.canvas_size

        assert size_tall.height() > size_base.height(), "Horizontal line spacing should increase height"

    def test_vertical_spacing_logic(self, setup_window):
        """Test that split properties affect vertical rendering logic."""
        tw = setup_window
        tw.is_vertical = True

        # 1. Base measurement
        tw.char_spacing_v = 0.0
        tw.line_spacing_v = 0.0
        tw.renderer.render(tw)
        size_base = tw.canvas_size

        # 2. Increase Char Spacing (Vertical Height)
        # Note: In vertical, char spacing adds to height (between chars in a column)
        tw.char_spacing_v = 0.5
        tw.renderer.render(tw)
        size_tall = tw.canvas_size

        assert size_tall.height() > size_base.height(), "Vertical char spacing should increase height"

        # 3. Increase Line Spacing (Vertical Width / Column gap)
        tw.char_spacing_v = 0.0  # Reset
        tw.line_spacing_v = 0.5  # Increase gap between columns
        tw.renderer.render(tw)
        size_wide = tw.canvas_size

        assert size_wide.width() > size_base.width(), "Vertical column spacing should increase width"

    def test_independence(self, setup_window):
        """Verify that horizontal settings do not affect vertical mode and vice-versa."""
        tw = setup_window

        # Setup Vertical Mode
        tw.is_vertical = True
        tw.char_spacing_v = 0.0
        tw.line_spacing_v = 0.0
        tw.renderer.render(tw)
        base_v = tw.canvas_size

        # Change Horizontal settings
        tw.char_spacing_h = 10.0
        tw.line_spacing_h = 10.0
        tw.renderer.render(tw)
        new_v = tw.canvas_size

        # Should be identical
        assert base_v.width() == new_v.width(), "Horizontal settings leaked into Vertical mode (Width)"
        assert base_v.height() == new_v.height(), "Horizontal settings leaked into Vertical mode (Height)"

    def test_horizontal_character_distribution(self, setup_window):
        """High Resolution Test: Verify that characters are actually drawn at different X positions."""
        tw = setup_window
        tw.is_vertical = False
        tw.text = "ABC"
        tw.font_size = 20
        # Use simple spacing
        tw.char_spacing_h = 0.0

        # Mock Painter to capture drawText calls
        mock_painter = MagicMock()
        mock_painter.font.return_value = QFont("Arial", 20)

        # We need to manually invoke the draw logic because render() creates its own painter usually
        # or we can check if TextRenderer exposes a method we can inject painter into.
        # _draw_horizontal_text_content is what we fixed.

        # Setup specific method call args
        fm = QFontMetrics(QFont("Arial", 20))
        lines = ["ABC"]
        margin = 0
        start_x = 0
        start_y = 0

        tw.renderer._draw_horizontal_text_content(mock_painter, tw, lines, fm, margin, start_x, start_y)

        # Analyze drawText calls
        # Expected: 3 calls.
        # Call args: (QPointF(x, y), char)
        draw_calls = mock_painter.drawText.call_args_list
        assert len(draw_calls) == 3, f"Expected 3 drawText calls, got {len(draw_calls)}"

        # Check X coordinates
        x_positions = [call.args[0].x() for call in draw_calls]

        # Ensure strictly increasing
        for i in range(len(x_positions) - 1):
            assert x_positions[i + 1] > x_positions[i], (
                f"Character {i + 1} is not to the right of Character {i} (Overlap detected!)"
            )

    def test_vertical_character_distribution(self, setup_window):
        """High Resolution Test: Verify that characters are drawn at different Y positions in vertical mode."""
        tw = setup_window
        tw.is_vertical = True
        tw.text = "AB"  # 1 line, 2 chars
        tw.font_size = 20
        tw.char_spacing_v = 0.0

        mock_painter = MagicMock()
        mock_painter.font.return_value = QFont("Arial", 20)

        # For vertical, we test _draw_vertical_text_elements roughly.
        # It's more complex, requiring QSize, margins etc.
        # Let's mock _draw_vertical_text_content if it exists/is used, or mimic the main call.
        # Viewing text_renderer lines 815+, it seems _draw_vertical_text_elements does the rendering.
        # We can call it directly.

        canvas_size = QSize(100, 200)
        lines = ["AB"]

        # Call the method
        tw.renderer._draw_vertical_text_elements(
            mock_painter,
            tw,
            canvas_size,
            lines,
            top_margin=0,
            margin=0,  # char_spacing
            right_margin=100,
            shadow_x=0,
            shadow_y=0,
            outline_width=0,
            line_spacing_ratio=0.5,
        )

        # Analyze calls. Vertical text might use drawText or drawPath depending on implementation.
        # If it uses drawText, we check positions.
        draw_calls = mock_painter.drawText.call_args_list

        # If vertical renderer uses transformations per char (rotate), it might use save/restore/translate/rotate -> drawText(0,0).
        # In that case, we need to check the transformations on the painter OR the coordinates if it relies on manual positioning.

        # Assuming current simple vertical implementation (might be drawText at x,y with @font, or vertical logic).
        # FTIV's vertical text uses explicit coordinate calculation loop?
        # If implementation was refactored to use _paint_direct_vertical logic which calls _draw_vertical_text_elements,
        # let's assume it draws characters descending.

        if not draw_calls:
            # Maybe it uses drawPath or transforms.
            pass

        # Vertical text uses painter.translate(cx, cy) to position characters,
        # then draws at local (dx, dy).
        # We must verify the TRANSLATE calls to check vertical stacking.
        translate_calls = mock_painter.translate.call_args_list

        # Filter calls: we expect at least one translate per char.
        # Note: renderer might call translate for other things (shadow?), so be careful.
        # But in this test setup, we only have main text loop or so.
        # Let's assume the calls corresponding to our chars are in order.

        y_positions = [call.args[1] for call in translate_calls]

        assert len(y_positions) >= 2, f"Expected translate calls for vertical placement, got {len(translate_calls)}"

        # Should increase (downwards)
        for i in range(len(y_positions) - 1):
            assert y_positions[i + 1] > y_positions[i], (
                f"Vertical Char {i + 1} is not below Char {i} (Translate Y: {y_positions})"
            )

    def test_vertical_spacing_metrics(self, setup_window):
        """Metric Accuracy Test: Verify that vertical step uses QFontMetrics.height() not just font_size."""
        tw = setup_window
        tw.is_vertical = True
        tw.text = "AB"
        font_size = 50
        tw.font_size = font_size
        tw.char_spacing_v = 0.0

        # Determine strict expected step (Refined: Ascent + Descent, no leading)
        font = QFont("Arial", font_size)
        fm = QFontMetrics(font)
        # expected_step = fm.height() # Old logic (too wide)
        expected_step = fm.ascent() + fm.descent()  # New refined logic

        # Mock dependencies
        mock_painter = MagicMock()
        mock_painter.font.return_value = font

        # Call low-level render content directly for precision
        lines = ["AB"]
        canvas_size = QSize(200, 500)

        tw.renderer._draw_vertical_text_content(
            mock_painter,
            tw,
            lines,
            x_shift=0.0,
            top_margin=0,
            margin=0,  # char_spacing_v
            right_margin=0,
            shadow_x=0,
            outline_width=0,
            canvas_size=canvas_size,
            is_main_text=True,
            custom_offset=QPoint(0, 0),
        )

        translate_calls = mock_painter.translate.call_args_list
        # Extract Y changes (translate cy)
        y_positions = [call.args[1] for call in translate_calls]

        assert len(y_positions) >= 2, "Need at least 2 chars to test spacing"

        actual_step = y_positions[1] - y_positions[0]

        # The key assertion: step should be roughly valid metric height
        # Allow small float tolerance
        msg = f"Vertical step {actual_step} is smaller than QFontMetrics.height() {expected_step}. This causes overlap!"

        # Currently, code uses font_size (50). QFontMetrics.height() for Arial 50 is likely ~58+
        # So this assertion will FAIL if current code is used.
        assert actual_step >= expected_step * 0.95, msg
