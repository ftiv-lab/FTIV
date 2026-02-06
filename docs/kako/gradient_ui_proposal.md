# グラデーションUI実装提案書
**ステータス**: 提案段階
**著者**: Antigravity (Super Senior Specialist)

## 🎯 目的
ユーザーを圧倒することなく、「High Gravity Quality」の使いやすさの基準に準拠しつつ、**テキストグラデーション**と**背景グラデーション**の制御を`プロパティパネル`に統合します。

## 🧠 UX哲学: 「段階的開示 (Progressive Disclosure)」
グラデーション設定は複雑です（複数の分岐点、角度、色など）。
**悪いUX:** サイドパネルにすべての分岐点(Stop)設定を直接露出させる（ごちゃごちゃして使いにくい）。
**良いUX:** 「有効化」と「全体の不透明度」だけを直接露出し、複雑な編集は専用のモーダルダイアログ内に隠蔽する。

## 🛠️ 提案するUIアーキテクチャ

### 1. テキストスタイルセクション (`prop_grp_text`)
文字色/不透明度の設定の下に、新しいサブセクションを追加します。

| コントロール | タイプ | 説明 |
| :--- | :--- | :--- |
| **グラデーション** | `QPushButton (Checkable)` | グラデーションモードの切替。ON(押し込まれた状態)で有効。 |
| **編集...** | `QPushButton` | `GradientEditorDialog`を開くボタン。現在の角度や色の詳細設定を行う。 |
| **不透明度** | `Slider + Spin` | グラデーション全体の不透明度 (0-100%)。ベース色の上に重ねるように描画されます。 |

**操作フロー:**
1.  ユーザーが「グラデーション」ボタンをクリック → テキストがグラデーションで塗りつぶされる（デフォルト設定）。
2.  ユーザーが「編集...」をクリック → ダイアログが開く → 色や角度を調整 → 「OK」 → パネルに反映。

### 2. 背景セクション (`menu_bg_settings`)
背景色の下に、新しいサブセクションを追加します。

| コントロール | タイプ | 説明 |
| :--- | :--- | :--- |
| **グラデーション** | `QPushButton (Checkable)` | 背景グラデーションの切替。 |
| **編集...** | `QPushButton` | `GradientEditorDialog`を開く。 |
| **角度** | `QSpinBox` (オプション) | ※完全にオプション。頻繁に回転させる場合のみクイックアクセスとして配置（シンプルさを保つため、要望がなければ省略推奨）。 |

## 💻 実装詳細

### A. `ui/property_panel.py`

#### 1. 新規ウィジェット定義
`build_text_window_ui` メソッド内に追加します：
```python
# --- テキストグラデーション ---
self.btn_text_gradient_toggle = QPushButton(tr("menu_toggle_text_gradient"))
self.btn_text_gradient_toggle.setCheckable(True)
# target.text_gradient_enabled に接続

self.btn_edit_text_gradient = QPushButton("🎨 " + tr("menu_edit_text_gradient"))
# _open_text_gradient_dialog に接続

self.spin_text_gradient_opacity = ... # 標準のスライダースピン
```

#### 2. 同期処理 (`_update_text_values`)
テキストウィンドウ切り替え時に、パネルの状態を更新します：
*   `btn_text_gradient_toggle.setChecked(t.text_gradient_enabled)`
*   `spin_text_gradient_opacity.setValue(t.text_gradient_opacity)`

#### 3. ダイアログロジック (`_open_text_gradient_dialog`)
既存の `GradientEditorDialog` を再利用します：
```python
def _open_text_gradient_dialog(self):
    target = self.current_target
    dialog = GradientEditorDialog(target.text_gradient, target.text_gradient_angle)
    if dialog.exec():
        # Undo可能な操作として保存
        target.set_undoable_property("text_gradient", dialog.get_gradient())
        target.set_undoable_property("text_gradient_angle", dialog.get_angle())
```

## 📊 影響分析
*   **複雑さ**: 低。既存の `GradientEditorDialog` を再利用するため、パネル側のロジックはシンプルです。
*   **リスク**: 低。`PropertyPanel`のUI構築にのみ影響し、既存機能への影響はありません。
*   **スペース**: 各セクションにボタン2つ＋スライダー1行（約3行分）を追加。スクロール可能なパネルなので許容範囲です。

## 🇯🇵 推奨される翻訳キー (jp.json)
*   `menu_toggle_text_gradient`: "グラデーション (ON/OFF)"
*   `menu_edit_text_gradient`: "詳細編集..."
*   `label_gradient_opacity`: "合成不透明度"

## 🚀 実行手順
1.  **翻訳キーの追加**: `jp.json` に必要なキーを追加。
2.  **UI実装**: `PropertyPanel` にトグルボタン、編集ボタン、不透明度スライダーを追加。
3.  **シグナル接続**: 各ボタンのアクションを実装。
4.  **同期処理**: ウィンドウ選択時の値の反映処理を追加。
5.  **検証**: 実機での動作確認（トグル、編集、Undo/Redo）。
