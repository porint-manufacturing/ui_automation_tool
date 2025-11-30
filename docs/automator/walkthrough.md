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
  - 例: `WindowControl(Name='電卓') -> ButtonControl(Name='5')`
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
  - `WaitUntilVisible`: 指定した要素が表示されるまで待機します。`Value`列でタイムアウト秒数を指定します（デフォルト10秒）。
  - `WaitUntilEnabled`: 指定した要素が有効化（操作可能）になるまで待機します。`Value`列でタイムアウト秒数を指定します（デフォルト10秒）。
  - `WaitUntilGone`: 指定した要素が画面から消えるまで待機します。`Value`列でタイムアウト秒数を指定します（デフォルト10秒）。
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

### 2.2. エイリアスの利用 (推奨)

長い `RPA_Path` を直接記述する代わりに、短い名前（エイリアス）を使用することで、CSV の可読性とメンテナンス性が向上します。

1.  **エイリアス定義ファイル (`aliases.csv`) の作成**:
    - `inspector.py --output alias` でテンプレートを作成するか、手動で作成します。
    - フォーマット: `AliasName,RPA_Path`

    ```csv
    AliasName,RPA_Path
    Btn_Calc_5,ButtonControl(Name='5')
    Btn_Calc_Plus,ButtonControl(Name='プラス')
    Result_Text,TextControl(AutomationId='CalculatorResults')
    ```

2.  **アクション定義ファイル (`actions.csv`) での使用**:
    - `Key` カラムにエイリアス名を記述します。

    ```csv
    TargetApp,Key,Action,Value
    電卓,Btn_Calc_5,Click,
    電卓,Btn_Calc_Plus,Click,
    ```

## 3. UI Inspector (要素調査ツール)

`inspector.py` は、画面上のUI要素をクリックするだけで、その要素を特定するためのRPAパスを自動生成するツールです。

#### 3.1. 起動方法

```bash
python inspector.py [オプション]
```

**オプション:**

- `--mode`: パス生成モードを指定します。
  - `modern` (デフォルト): `AutomationId` や `Name` を優先的に使用します。
  - `legacy`: `ClassName` と `foundIndex` を主体としたパスを生成します。
- `--output`: 出力先を指定します。
  - `clipboard` (デフォルト): 生成されたCSV形式のデータをクリップボードにコピーします。
  - `csv`: `inspector_YYYYMMDD_HHMMSS.csv` というファイルに保存します。
  - `alias`: `inspector_YYYYMMDD_HHMMSS_alias.csv` というファイルに、エイリアス定義形式で保存します。
  - `interactive_alias`: 対話形式でエイリアス名を入力しながら、次々と要素を記録します。

#### 3.2. 操作方法 (通常モード)

1. ツールを起動します。
2. 調査したいUI要素の上にマウスカーソルを移動します。
3. **左クリック**します。
4. コンソールに要素の情報と生成されたRPAパスが表示されます。
5. 続けて他の要素をクリックして記録できます。
6. 終了するには `ESC` キーを押します。

#### 3.3. 操作方法 (対話型エイリアスモード)

`--output interactive_alias` を指定した場合の操作手順です。

1.  ツールを起動します。
2.  コンソールに `[Interactive] Enter Alias Name:` と表示されるので、**エイリアス名を入力してEnter**を押します。
3.  `Click the element for 'エイリアス名'` と表示されたら、対象のUI要素を**左クリック**します。
4.  要素が記録され、次のエイリアス名の入力待ちになります。
5.  終了するには、エイリアス名入力時に `q` または `exit` を入力します。

## 4. 実行

PowerShell または コマンドプロンプトで実行します。

```powershell
# 仮想環境を有効化 (まだの場合)
& .\.venv\Scripts\Activate.ps1

# デフォルトの actions.csv を実行
python automator.py
```

### 3.2. オプション

- `--aliases <file>`: エイリアス定義ファイルを指定します。
- `--log-file <file>`: 実行ログをファイルに出力します。
- `--log-level <level>`: ログレベルを指定します (`DEBUG`, `INFO`, `WARNING`, `ERROR`)。デフォルトは `INFO`。
- `--dry-run`: 実際の操作を行わずに実行フローを確認します（副作用なし）。
  - アクションの読み込み、変数の展開、条件分岐などのロジックが正しく動作するかを、実際にクリックや入力をせずに安全に検証できます。
  - スクリプト作成時のデバッグや、本番環境で実行する前の最終確認に便利です。

### 3.3. 実行例

**基本実行**

```bash
python automator.py actions.csv
```

**エイリアスを使用**

```bash
python automator.py actions.csv --aliases aliases.csv
```

**ログ出力とDry-run**

```bash
python automator.py actions.csv --aliases aliases.csv --log-file execution.log --log-level DEBUG --dry-run
```

## 4. エラーハンドリング

実行中にエラーが発生した場合、`errors/` ディレクトリにスクリーンショットが自動的に保存されます。
ログファイルを確認することで、詳細なエラー原因を特定できます。

## 5. 注意点

- **要素が見つからない場合**: アプリの起動待ち時間が足りない可能性があります。`Wait` を長めに設定してみてください。
- **日本語入力**: `Input` アクションは、IME の状態によっては正しく入力されない場合があります。直接入力 (`SetValue`) を試みるか、クリップボード経由などを検討してください（現状は `SetValue` または `SendKeys` を使用）。
