# リファクタリング計画 01: 例外握りつぶしの撲滅

**対象**: 全コードベース（特に `ui/main_window.py` から開始）
**目的**: エラー発生時にログを残さず `pass` している箇所（「握りつぶし」）を修正し、デバッグ可能性と信頼性を向上させる。

## 1. 現状の課題
`grep` 検索の結果、コードベース内に 500 箇所以上の `except Exception:` または `except:` ブロックが存在します。
その多くが `pass` で処理をスキップしているため、以下の問題が発生しています：
1.  **サイレントエラー**: ユーザーが操作しても「何も起きない」だけで、裏でエラーが起きていることに気づけない。
2.  **デバッグ困難**: ログファイルを見てもエラーの痕跡がないため、原因究明に時間がかかる。
3.  **不安定な状態**: 部分的に処理が失敗したままアプリが動き続ける。

## 2. 修正方針 (ガイドライン)

全ての修正箇所で以下のルールを適用します。

### ルール1: 必ずログを出す
`pass` は原則禁止です。最低でも `logger.error` または `logger.warning` を出力します。

```python
# Bad
except Exception:
    pass

# Good
except Exception:
    import logging
    logging.getLogger(__name__).error("Failed to do something", exc_info=True)
```

### ルール2: 具体的な例外を捕捉する (可能な場合)
文脈から明らかな場合、`Exception` ではなく具体的な例外を捕捉します。

```python
# Bad
except Exception:
    return default_value

# Good
except (ValueError, TypeError) as e:
    logging.getLogger(__name__).warning(f"Invalid value parsing: {e}")
    return default_value
```

### ルール3: ユーザー通知 (UI操作時)
ファイルの保存や読み込み、ユーザーが明示的に実行したアクションの失敗時は、ログだけでなく `QMessageBox` でユーザーに通知します。

---

## 3. 実施フェーズ

数が膨大なため、以下のフェーズに分けて実施します。

### Phase 1: Main Window & UI (今回のスコープ)
最も影響範囲が広い `ui/main_window.py` と `ui/property_panel.py` を対象にします。
これらはユーザー操作の直接的な受け皿であり、ここでのエラー隠蔽はUXを著しく損ないます。

**主な修正ターゲット (`ui/main_window.py`):**
*   `closeEvent`: 終了時の保存失敗が隠蔽されている可能性がある。
*   `refresh_ui_text`: 言語切り替え失敗。
*   `_register_emergency_shortcuts`: 登録失敗。
*   各 `build_xxx_tab` メソッド内の安全策ブロック。
*   `dragEnterEvent` / `dropEvent`: ファイルドロップ時のエラー。

### Phase 2: Windows Core (次回以降)
`windows/text_window.py`, `windows/image_window.py` 等のレンダリングループ内。
ここは頻繁に呼び出されるため、ログ出力過多（ログ爆発）に注意しつつ、`utils.error_reporter` を活用します。

### Phase 3: Managers & Utils (次回以降)
`managers/*`, `utils/*` 内のエラーハンドリング詳細化。

---

## 4. Phase 1 作業手順

1.  `ui/main_window.py` を開き、`except Exception` を検索して上から順に査読する。
2.  `pass` している箇所を特定し、文脈に応じて以下のいずれかに書き換える。
    *   **ログ出力のみ**: 処理続行に支障がない、または回復可能な場合。
    *   **ログ + ユーザー通知**: ユーザーが期待した動作が完了しなかった場合。
3.  `logging` モジュールのインポートが不足していれば追加する。
4.  `ui/property_panel.py` についても同様に行う。

## 5. 検証プラン

### 自動テスト
現状は単体テストが存在しないため、自動テストでの検証は困難です。

### 手動検証手順
修正後、アプリを起動し、以下の操作を行ってクラッシュしないこと、およびログが出ることを確認します（意図的にエラーを起こすのは難しいため、通常動作確認が主になります）。

1.  **起動確認**: アプリが正常に起動すること。
2.  **終了確認**: アプリ終了時、ログファイルにエラーが出ていないこと。
3.  **タブ切り替え**: 各タブを表示し、UI構築エラーが出ないこと。
4.  **設定変更**: 設定を変更して保存し、エラーが出ないこと。

もし可能であれば、一時的に `raise ValueError`などを埋め込んで、意図通りにログが出るかテストします。

---
**承認待ち**: この計画で `ui/main_window.py` の修正に着手してよろしいでしょうか？
