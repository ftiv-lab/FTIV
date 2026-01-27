# Phase 15: Stress & Chaos Testing Plan (意地悪なテスト計画)

## 目標 (Goal)
「動くかどうか (Happy Path)」だけでなく、「**どこまでやったら壊れるか (Limits)**」を知り、限界を超えたときにも安全に失敗（Graceful Degradation）できるかを検証する。

## 1. 負荷テスト (Stress Testing)
大量のオブジェクトを生成し、描画パフォーマンスとメモリ挙動を確認する。

### テストシナリオ
- [ ] **The "1000 Windows" Test**:
    - テキスト/画像ウィンドウを100個、500個、1000個と生成し、FPSの低下や操作ラグを測定する。
    - **期待値**: 100個程度なら快適に操作できること。1000個でもクラッシュしないこと。
- [ ] **Huge Image Load**:
    - 4K, 8K, 100MB超の巨大画像を読み込ませる。
    - **期待値**: メモリ不足で落ちる前にエラーメッセージが出る、または縮小して読み込まれること。
- [ ] **Rapid Fire Undo/Redo**:
    - 操作をプログラムで高速に100回行い、即座に100回Undoする。
    - **期待値**: スタックの整合性が保たれ、最終的に元の状態に戻ること。

## 2. カオスエンジニアリング (Chaos Engineering)
予期せぬ外部要因や異常な状態をシミュレートする。

### テストシナリオ
- [ ] **Save Interrupt (Atomic Save Verification)**:
    - 保存処理中にプロセスを強制終了（または例外発生）させ、`scenes.json` が0バイトになったり破損したりしないか検証する。
- [ ] **Corrupted Config Injection**:
    - `app_settings.json` にデタラメな値（文字列期待の場所に数値、不正なJSON形式など）を手動で書き込み、起動するか確認する。
    - **期待値**: `ConfigGuardian` が検知し、デフォルト値で起動すること。
- [ ] **Monkey Testing**:
    - ランダムな座標クリック、ランダムなキー入力を高速に送り続ける。
    - **期待値**: 未処理の例外（Unhandled Exception）で落ちないこと。

## 3. 実装計画

### 新規テストファイル
- **`tests/test_stress/`** ディレクトリを作成。
- **`test_heavy_load.py`**: 大量ウィンドウ生成テスト。
- **`test_chaos_config.py`**: 設定ファイル破損テスト。

### ツール拡張
- **`verify_all.bat`** には含めない（時間がかかるため）。
- 別途 **`verify_stress.bat`** を作成する。

## 4. タイムライン
- Step 1: `ConfigGuardian` の強化確認（破損設定テスト）
- Step 2: 負荷テストスクリプトの実装 (`test_heavy_load.py`)
- Step 3: Undo/Redo連打テスト (`test_rapid_undo.py`)
