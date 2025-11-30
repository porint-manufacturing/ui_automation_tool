# 実装計画 - UI Inspector アプリ

# 目標の説明

マウスカーソル下の UI 要素を検査し、クリック時にその Automation 属性（AutomationId、Name など）をコンソールに出力する Python ベースのデスクトップツールを構築します。

## ユーザーレビュー必須事項

> [!IMPORTANT] > **ライブラリ選定**: 設計では、属性抽出に `pyautogui` ではなく `uiautomation` を使用します。これは `pyautogui` が UI Automation プロパティを読み取れないためです。マウス操作には `pyautogui` または `pynput` を使用します。
> **インタラクションモデル**: 計画では、クリックを検出するためにグローバルマウスフック（`pynput`）の使用を提案しています。これにより、インスペクターウィンドウがフォーカスされていない場合でもクリックをキャプチャできます。

## 提案される変更

### 依存関係

- `uiautomation`: Windows UI Automation 用。
- `pynput`: グローバルマウス/キーボードリスナー用。

### プロジェクト構造

#### [NEW] [inspector.py](file:///c:/Users/shion/OneDrive/ドキュメント/automation/inspector.py)

- メインエントリーポイント。
- `Inspector` クラスを含みます。
- マウス（クリック）とキーボード（Esc で終了）の `pynput` リスナーを処理します。
- 要素データを取得するために `uiautomation.ControlFromPoint` を使用します。

#### [NEW] [requirements.txt](file:///c:/Users/shion/OneDrive/ドキュメント/automation/requirements.txt)

- 依存関係をリストアップ: `uiautomation`, `pynput`。

## 検証計画

### 自動テスト

- この小規模なユーティリティについては計画していません（複雑なセットアップなしにグローバル UI インタラクションを信頼性高くモックすることは困難なため）。

### 手動検証

1.  **依存関係のインストール**: `pip install -r requirements.txt` を実行します。
2.  **アプリの実行**: `python inspector.py` を実行します。
3.  **選択テスト**:
    - 様々なウィンドウ（エクスプローラー、電卓、メモ帳）上にマウスを移動します。
    - 要素（ボタン、テキストフィールド）をクリックします。
    - コンソール出力に正しい `AutomationId`、`Name` などが表示されることを確認します。
4.  **終了テスト**: `Esc` を押してアプリが終了することを確認します。
