import os
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView

from ui.mindmap.mindmap_canvas import MindMapCanvas
from ui.mindmap.mindmap_edge import MindMapEdge
from ui.mindmap.mindmap_node import MindMapNode


@pytest.fixture(scope="function")
def canvas_setup(qapp):
    """Setup MindMapCanvas with a view for interaction testing."""
    canvas = MindMapCanvas()
    canvas.resize(800, 600)
    canvas.setDragMode(QGraphicsView.DragMode.NoDrag)
    canvas.show()
    QTest.qWaitForWindowExposed(canvas)
    return canvas


def test_folding_interaction_integrated(canvas_setup):
    """
    E2E Test: Verify clicking the Integrated Fold Button toggles child visibility.
    """
    canvas = canvas_setup
    scene = canvas._scene
    scene.setItemIndexMethod(QGraphicsScene.ItemIndexMethod.NoIndex)

    root = MindMapNode("Root")
    child = MindMapNode("Child")
    scene.addItem(root)
    scene.addItem(child)
    root.setPos(0, 0)
    child.setPos(200, 0)

    edge = MindMapEdge(root, child)
    scene.addItem(edge)

    QApplication.processEvents()
    QTest.qWait(200)

    # 1. Verify Structure
    assert root.has_children()
    assert not hasattr(root, "_fold_button")  # Should be removed

    # 2. Calculate Click Position (Integrated Button)
    btn_rect = root._get_fold_button_rect()
    print(f"DEBUG: Button Rect (Local): {btn_rect}")

    btn_center_local = btn_rect.center()
    btn_center_scene = root.mapToScene(btn_center_local)

    # 3. Click (Mouse Press on Node)
    view = canvas
    viewport_pos = view.mapFromScene(btn_center_scene)

    print(f"DEBUG: Clicking at Viewport {viewport_pos} (Scene {btn_center_scene})")
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, viewport_pos)
    QTest.qWait(100)

    # 4. Verify Folded
    assert not child.isVisible(), "Child should be hidden after folding"

    # 5. Click to Expand
    QTest.mouseClick(view.viewport(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, viewport_pos)
    QTest.qWait(100)

    # 6. Verify Expanded
    assert child.isVisible(), "Child should be visible after expansion"
