from PySide6.QtGui import QDragEnterEvent, QDropEvent


class DnDMixin:
    """Drag and Drop 機能を提供する Mixin。

    MainWindow に継承させて使用する。
    """

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """ドラッグ進入時の処理。"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        """ドロップ時の処理。

        ファイルパスを取得し、画像として追加する。
        """
        # MainWindowのメソッドを呼ぶため self 経由でアクセス
        # self.add_image_from_path は MainWindow に定義されている前提
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if hasattr(self, "add_image_from_path") and path:
                self.add_image_from_path(path)
