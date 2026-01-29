# Phase 16: Comprehensive Real-Object Testing & Hardening

## 1. 目的 (Objective)
これまでのテストは Mock を多用していたため、`AttributeError` や `TypeError` といった「実際のオブジェクトの振る舞い」に関連する単純なバグを見逃していました。
本フェーズでは、「**Real Objects (実体)**」を使用したテストカバレッジを徹底的に拡大し、特に動的な属性アクセス（`set_undoable_property` など）を行う箇所の安全性を保証します。

## 2. 現状の課題 (Current Issues)
*   **Mockの弊害**: `MagicMock` はあらゆる属性アクセスに対して成功を返してしまうため、`hasattr` チェックや `getattr` の失敗（存在しないプロパティへのアクセス）を検知できない。
*   **動的アクセスの多用**: `set_undoable_property("string_key", value)` という文字列ベースのアクセスが多用されており、静的解析やIDEの補完でミスに気づきにくい。
*   **ImageWindowのテスト不足**: TextWindowに比べてImageWindowのインタラクティブテスト（実体テスト）が少ない。

## 3. 実装計画 (Implementation Plan)

### 3.1. Audit & Fix (完了済み含む)
*   `set_undoable_property` で使用されている全プロパティ文字列を洗い出し、対応する `@property` がクラスに存在するか確認する。
    *   [x] `ImageWindow.position` (Fixed)
    *   [ ] `TextWindow` 全プロパティの再確認（Audit済み、概ねOKだがテストで保証する）

### 3.2. New Real-Object Test Suite (新規実体テストスイート)
`tests/test_interactive/` 配下に、実体を使った網羅的なテストを追加します。

#### A. `test_image_properties_comprehensive.py`
*   **検証対象**: `ImageWindow`
*   **内容**: 全プロパティ（`opacity`, `rotation_angle`, `scale_factor`, `flip_*`, `animation_speed_factor`, `is_locked`）に対して、`set_undoable_property` 経由での変更と Undo/Redo を実行する。
*   **期待値**: エラー落ちせず、値が反映されること。

#### B. `test_text_properties_comprehensive.py`
*   **検証対象**: `TextWindow`
*   **内容**: 膨大な数（約40個）あるプロパティ全てに対して、`set_undoable_property` をループで実行するテストを作成。
    *   `font_size`, `font_family`, `text_color`, `shadow_*`, `outline_*`, `gradient_*` ...
    *   パラメータライズドテスト (`@pytest.mark.parametrize`) を活用し、リスト化して管理する。

#### C. `test_actions_integration.py`
*   **検証対象**: `ImageActions`, `TextActions` (Controller)
*   **内容**: コントローラーのメソッド（`pack_all_*`, `reset_all_*`, `normalize_*`）を、Mockではなく「実体のWindowリスト」に対して実行する。
*   **目的**: コントローラーが呼ぶ `hasattr` チェックやメソッド呼び出しが実体と整合しているか確認。

### 3.3. Stress & Fuzzing (簡易)
*   プロパティ設定を乱数で大量に行う「モンキーテスト」的なシナリオを一つ追加し、例外落ちしないか確認する。

## 4. 成果物 (Deliverables)
1.  `tests/test_interactive/test_image_properties_comprehensive.py`
2.  `tests/test_interactive/test_text_properties_comprehensive.py`
3.  `tests/test_interactive/test_actions_integration.py`
4.  修正された `ImageWindow` / `TextWindow` (もしリファクタリングが必要なら)
5.  更新された `verify_all.bat`

## 5. スケジュール
*   **Step 1**: Test Setup Review (Mock MW improvements)
*   **Step 2**: Image Properties Coverage
*   **Step 3**: Text Properties Coverage
*   **Step 4**: Actions Integration
*   **Step 5**: Final Verification
