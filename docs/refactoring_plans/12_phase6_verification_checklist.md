# Phase 6 Verification Checklist: Business Logic Extraction

Phase 6 では、`MainWindow` にあった「画像配置」「一括操作」などのロジックを独立したクラス (`LayoutActions`, `ConnectorActions`, `ImageActions`) に移動しました。
見た目の機能は変わらないはずですが、内部構造が大きく変わっているため、以下の機能がリグレッションしていないか確認をお願いします。

## 1. 画像の自動配置 (Layout)
- [ ] **整列ダイアログ (Advanced Align)**
    - メニュー > Align Images でダイアログが開くか。
    - 列数 (Columns) や間隔 (Space) を変更して、プレビュー（リアルタイム移動）が機能するか。
    - OK を押した後に Undo (Ctrl+Z) で元の位置に戻るか。
    - Cancel を押したときに元の位置に戻るか。
- [ ] **左上詰め / 中央集め**
    - メニューから Pack all Left-Top を実行し、左上に整列するか。
    - メニューから Pack all Center を実行し、中央に集まるか。

## 2. コネクタの一括操作 (Connector Bulk Ops)
- [ ] **一括色変更**
    - メニュー > Connector > Change All Colors... を実行し、色が反映されるか。
- [ ] **一括幅変更**
    - メニュー > Connector > Change All Widths... を実行し、線幅が変わるか。
- [ ] **一括不透明度変更**
    - メニュー > Connector > Change All Opacity... を実行し、不透明度が変わるか。

## 3. 画像の一括操作 (Image Bulk Ops)
- [ ] **一括不透明度**
    - メニュー > Image > Set All Opacity... でスライダー操作し、全画像の不透明度が追従するか。
- [ ] **一括サイズ変更**
    - メニュー > Image > Set All Size (%pos)... でスライダー操作し、全画像のサイズが変わるか。
- [ ] **一括回転**
    - メニュー > Image > Set All Rotation... でスライダー操作し、全画像が回転するか。
- [ ] **GIF/APNG 再生速度**
    - メニュー > Set All Animation Speed... で速度変更が反映されるか。
- [ ] **リセット系**
    - Reset All Flips / Reset All Animation Speeds が機能するか。

## 4. その他確認事項
- [ ] **エラー通知**
    - 操作中に「Unexpected Error」などのダイアログが出ないか。
- [ ] **Undo/Redo**
    - 上記の一括操作を行った後、Undo で元に戻り、Redo で再度適用されるか。
