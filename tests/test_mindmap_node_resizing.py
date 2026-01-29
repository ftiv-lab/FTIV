def test_mindmap_node_inline_edit_resizing(qapp):
    """インプレース編集中の動的リサイズテスト"""
    from PySide6.QtWidgets import QGraphicsScene

    from ui.mindmap.mindmap_node import MindMapNode

    node = MindMapNode(text="Initial")
    scene = QGraphicsScene()
    scene.addItem(node)

    initial_rect = node.boundingRect()
    initial_width = initial_rect.width()

    # シーンに追加しないと itemChange などが一部動かない可能性があるが、
    # _start_inline_edit は scene() をチェックするので追加必須。

    # 1. 編集開始
    node._start_inline_edit()
    assert getattr(node, "_inline_text_item", None) is not None

    # 2. テキストを変更（長くする）
    text_item = node._inline_text_item
    cursor = text_item.textCursor()
    cursor.clearSelection()  # 全選択を解除
    cursor.movePosition(cursor.MoveOperation.End)  # 末尾に移動
    cursor.insertText(" Very Long Text Added Here To Increase Width")

    # contentsChanged シグナルは即座に処理されない可能性があるため、少し待つか
    # 直接シグナルが発火したと仮定して検証（PySide6のシグナルは基本同期的にハンドラを呼ぶことが多いが）

    # サイズが更新されたか確認
    current_rect = node.boundingRect()
    assert current_rect.width() > initial_width

    # 3. 編集終了
    node._finish_inline_edit(True)
    assert node.text == "Initial Very Long Text Added Here To Increase Width"
    assert getattr(node, "_inline_text_item", None) is None

    # 編集終了後もサイズが維持されているか（再計算されているか）
    # _finish_inline_edit -> _update_size が呼ばれるはず
    final_rect = node.boundingRect()
    assert final_rect.width() > initial_width
