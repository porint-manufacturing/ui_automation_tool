# 実装計画 - Automator App

# 目標の説明

CSV ファイルで定義された手順に従い、Windows アプリを自動操作する `automator.py` を作成する。

## ユーザーレビュー必須事項

> [!IMPORTANT] > **要素特定の信頼性**: `inspector.py` で取得したパスは動的に変わる可能性があります（特に `Name` 属性）。`AutomationId` がある場合はそれを優先しますが、ない場合は `Name` に頼るため、アプリの状態によっては失敗する可能性があります。
> **CSV フォーマット**: 文字コードは `utf-8` (BOM 付き推奨) または `cp932` (Shift-JIS) を想定。Excel での編集を考慮し `utf-8-sig` で読み込む予定。

## 提案される変更

### 新規ファイル

#### [NEW] [automator.py](file:///c:/Users/shion/OneDrive/ドキュメント/automation/automator.py)

- **クラス `Automator`**:
  - `load_actions(csv_path)`: CSV 読み込み。
  - `run()`: アクションの順次実行。
  - `find_element(window, path_string)`: パス文字列から要素を特定するロジック。
  - `execute_action(element, action, value)`: 操作実行。

#### [NEW] [actions.csv](file:///c:/Users/shion/OneDrive/ドキュメント/automation/actions.csv)

- サンプル用の CSV ファイル。

### 依存関係

- `uiautomation` (既存)

## 検証計画

### 手動検証

1.  **準備**: `inspector.py` を使って「電卓」または「メモ帳」のキーを取得し、`actions.csv` を作成。
    - 例: 電卓を起動 -> 「5」を押す -> 「+」を押す -> 「3」を押す -> 「=」を押す。
2.  **実行**: `python automator.py` を実行。
3.  **確認**: 電卓が勝手に動き、計算結果が表示されることを確認。
