---
description: Define custom signals, slots, and secure connections in PySide6.
---

# Skill: Secure Qt Signal/Slot Pattern

> [!IMPORTANT]
> Qt/PySide6における「結合」は全て **Signal/Slot** で行うこと。
> 親が子を直接参照する (`view.child.method()`) は厳禁。

## 手順

### 1. Signalの定義
クラス変数として定義する。`__init__` 内ではない。
具体的で意味のある名前をつける (`changed` ではなく `text_changed`)。

```python
from PySide6.QtCore import QObject, Signal

class UserForm(QObject):
    # Payloadには必ず型ヒントをつける
    submitted = Signal(str, int)  # name, age
    canceled = Signal()
```

### 2. Slotの定義 (Type Hinted)
スロットメソッドには `@Slot` デコレータは必須ではないが、型ヒントは必須。

```python
    def _on_submit_clicked(self) -> None:
        name = self._name_input.text()
        age = self._age_input.value()
        # ロジックを書かず、シグナル発火に徹する
        self.submitted.emit(name, age)
```

### 3. 疎結合な接続 (In Parent/Controller)
親コンポーネントまたはコントローラーで接続を行う。

```python
class MainWindow(QMainWindow):
    def setup_ui(self):
        self._form = UserForm()
        
        # ✅ Good: Signal -> Slot
        self._form.submitted.connect(self._handle_form_submission)
        
        # ❌ Bad: Direct Call
        # self._form.button.clicked.connect(...) 
```

### 4. 切断 (Cleanup)
ウィジェットが破棄される際、PySide6は自動的に切断するが、循環参照を防ぐために手動切断が必要な場合もある。
カスタムウィジェットの `closeEvent` や `dispose` メソッドで明示的に行う。

```python
    def cleanup(self):
        try:
            self.submitted.disconnect()
        except RuntimeError:
            pass # 既に切断されている場合
```
