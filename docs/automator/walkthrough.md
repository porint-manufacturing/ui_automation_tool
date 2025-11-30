# Automator App - 実行ガイド

## 1. 概要

`inspector.py` で取得した情報をもとに、Windows アプリを自動操作するツールです。
CSV ファイルに記述された手順に従って操作を実行します。

## 2. 準備

### 2.1. 操作手順の作成 (`actions.csv`)

`inspector.py` を使って操作したい要素の `RPA_Path` を取得し、CSV ファイルを作成します。

**フォーマット:**
`TargetApp,Key,Action,Value`

- **TargetApp**: 操作対象のアプリ名（ウィンドウ名の一部で OK）。例: `電卓`, `メモ帳`
- **Key**: `inspector.py` で取得した `RPA_Path`。
  - 例: `ButtonControl(Name='5')`
  - アプリ起動(`Launch`)や待機(`Wait`)の場合は空欄で OK。
- **Action**:
  - `Launch`: アプリ起動 (`Value`にパス)
  - `Click`: クリック
  - `Input`: テキスト入力 (`Value`にテキスト)。`{変数名}` で変数の値を参照可能。
  - `Wait`: 待機 (`Value`に秒数)
  - `Focus`: ウィンドウをフォーカス
  - `GetValue`: 要素の値を取得して変数に保存 (`Value`に変数名)
  - `SendKeys`: キー送信 (`Value`にキーコード)。例: `{Ctrl}n` (新規作成), `{ENTER}`
  - `SetClipboard`: クリップボードにテキストを設定 (`Value`にテキスト)。`{ENTER}` で改行可能。
  - `GetClipboard`: クリップボードからテキストを取得して変数に保存 (`Value`に変数名)
  - `Paste`: クリップボードの内容を貼り付け (`Ctrl+V` 送信)
  - `VerifyValue`: 要素の値が期待値と一致するか検証 (`Value`に期待値)
  - `VerifyVariable`: 変数の値を検証 (`Key`に変数名, `Value`に期待値)
  - `Exit`: アプリを終了する
- **Value**: アクションのパラメータ。

**例 (`actions.csv`):**

```csv
TargetApp,Key,Action,Value
電卓,,"Launch","calc.exe"
電卓,,"Wait","2"
電卓,"ButtonControl(Name='5')","Click",
電卓,"ButtonControl(Name='プラス')","Click",
電卓,"ButtonControl(Name='3')","Click",
電卓,"ButtonControl(Name='等号')","Click",
電卓,"TextControl(AutomationId='CalculatorResults')","GetValue","result"
メモ帳,,"Launch","notepad.exe"
メモ帳,,"Wait","2"
メモ帳,,"Focus",
メモ帳,,"Focus",
メモ帳,,"SendKeys","{Ctrl}n"
メモ帳,,"SetClipboard","計算結果: {result}"
メモ帳,,"Click",
メモ帳,,"Paste",
メモ帳,,"Wait","2"
メモ帳,,"Exit",
電卓,,"Exit",
```

> [!TIP] > **フォーカスのコツ**: メモ帳などの一部のアプリでは、特定のコントロール（`DocumentControl`など）ではなく、ウィンドウ自体（`Key`を空にする）にフォーカスを当ててショートカットキー（`{Ctrl}v`など）を送信する方が確実な場合があります。また、`Click` アクションを使って明示的にクリックするのも有効です。

## 3. 実行

PowerShell または コマンドプロンプトで実行します。

```powershell
# 仮想環境を有効化 (まだの場合)
& .\.venv\Scripts\Activate.ps1

# デフォルトの actions.csv を実行
python automator.py

# 別のCSVファイルを指定して実行
python automator.py my_scenario.csv
```

## 4. 注意点

- **要素が見つからない場合**: アプリの起動待ち時間が足りない可能性があります。`Wait` を長めに設定してみてください。
- **日本語入力**: `Input` アクションは、IME の状態によっては正しく入力されない場合があります。直接入力 (`SetValue`) を試みるか、クリップボード経由などを検討してください（現状は `SetValue` または `SendKeys` を使用）。
