# Automator App - 実行ガイド

## 1. 概要

`inspector.py` で取得した情報をもとに、Windows アプリを自動操作するツールです。
CSV ファイルに記述された手順に従って操作を実行します。

## 2. 準備

### 2.1. 操作手順の作成 (`actions.csv`)

`inspector.py` を使って操作したい要素の `RPA_Path` を取得し、CSV ファイルを作成します。

**フォーマット:**
`TargetApp,Key,Action,Value`

- **TargetApp**: 操作対象のアプリ名（ウィンドウ名の一部で OK）。
  - 例: `電卓`, `メモ帳`
  - **正規表現**: `regex:` 接頭辞を付けると正規表現として扱われます。例: `regex:^日報 \d{4}-\d{2}-\d{2}$`
- **Key**: `inspector.py` で取得した `RPA_Path`。
  - 例: `WindowControl(Name='電卓') -> ButtonControl(Name='5')`
  - **正規表現**: `RegexName` プロパティを使用可能。例: `WindowControl(RegexName='.*日報.*')`
  - アプリ起動(`Launch`)や待機(`Wait`)の場合は空欄で OK。
- **Action**:
  - `Launch`: アプリ起動 (`Value`にパス)
  - `Click`: クリック
  - `Input`: テキスト入力 (`Value`にテキスト)。`{変数名}` で変数の値を参照可能。
  - `Wait`: 待機 (`Value`に秒数)
  - `Focus`: ウィンドウをフォーカス (`Key`は空欄)
  - `FocusElement`: 指定した要素をフォーカス (`Key`にRPAパス)。ボタンを押す前にフォーカスを当てたい場合などに使用。
    - **注意**: 要素がフォーカス可能（`IsKeyboardFocusable`）でない場合、フォーカスは移動せず、警告ログが出力されます。
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
  - `SetVariable`: 変数を設定 (`Value`に `name = value`)。
  - `GetDateTime`: 現在の日時を取得して変数に保存 (`Value`に `variable = format`)。
    - フォーマット例: `current_time = yyyy/MM/dd HH:mm:ss`
    - 対応フォーマット: `yyyy` (年), `MM` (月), `dd` (日), `HH` (時), `mm` (分), `ss` (秒)
  - `If`: 条件分岐開始 (`Value`に条件式)。例: `{status} == 'OK'`
  - `Else`: `If` の偽ブロック開始。
  - `EndIf`: `If` ブロック終了。
  - `Loop`: ループ開始 (`Value`に回数または条件式)。例: `5` または `{count} < 10`
  - `EndLoop`: ループ終了。
  - `Invoke`: 要素を `InvokePattern` で実行します。ボタンクリックなどに使用します。`Click` より安定している場合があります。
  - `Select`: リストやコンボボックスから項目を選択します。`Value` に項目名を指定すると子要素を選択、空の場合は要素自体を選択します。
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

> [!TIP]
> **フォーカスのコツ**: メモ帳などの一部のアプリでは、特定のコントロール（`DocumentControl`など）ではなく、ウィンドウ自体（`Key`を空にする）にフォーカスを当ててショートカットキー（`{Ctrl}v`など）を送信する方が確実な場合があります。また、`Click` アクションを使って明示的にクリックするのも有効です。

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

### 2.3. 制御構文と変数

条件分岐やループ、変数の操作が可能です。

**変数操作**

| Action          | Value          | 説明                                                                                             |
| :-------------- | :------------- | :----------------------------------------------------------------------------------------------- |
| **SetVariable** | `name = value` | 変数 `name` に `value` を代入します。数式や他の変数も使用可能です（例: `count = {count} + 1`）。 |

**条件分岐 (If - Else - EndIf)**

| Action    | Value              | 説明                                            |
| :-------- | :----------------- | :---------------------------------------------- |
| **If**    | `{status} == 'OK'` | 条件式が真の場合、次の行から実行します。        |
| **Else**  |                    | `If` が偽の場合に実行されるブロックの開始です。 |
| **EndIf** |                    | 条件分岐ブロックの終了です。                    |

**ループ処理 (Loop - EndLoop)**

| Action      | Value          | 説明                                    |
| :---------- | :------------- | :-------------------------------------- |
| **Loop**    | `5`            | 指定回数（この場合は5回）繰り返します。 |
| **Loop**    | `{count} < 10` | 条件式が真の間、繰り返します。          |
| **EndLoop** |                | ループブロックの終了です。              |

**使用例:**

```csv
TargetApp,Key,Action,Value
,,SetVariable,count = 0
,,Loop,{count} < 3
メモ帳,Edit,Input,Test {count}
,,SetVariable,count = {count} + 1
,,EndLoop
```

## 3. UI Inspector (要素調査ツール)

`inspector.py` は、画面上のUI要素をクリックするだけで、その要素を特定するためのRPAパスを自動生成するツールです。

### 3.1. 起動方法

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

### 3.2. 操作方法 (通常モード)

1. ツールを起動します。
2. 調査したいUI要素の上にマウスカーソルを移動します。
3. **左クリック**します。
4. コンソールに要素の情報と生成されたRPAパスが表示されます。
5. 続けて他の要素をクリックして記録できます。
6. 終了するには `ESC` キーを押します。

### 3.3. 操作方法 (対話型エイリアスモード)

`--output interactive_alias` を指定した場合の操作手順です。

1.  ツールを起動します。
2.  コンソールに `[Interactive] Enter Alias Name:` と表示されるので、**エイリアス名を入力してEnter**を押します。
3.  `Click the element for 'エイリアス名'` と表示されたら、対象のUI要素を**左クリック**します。
4.  要素が記録され、次のエイリアス名の入力待ちになります。
5.  終了するには、エイリアス名入力時に `q` または `exit` を入力します。

## 4. 実行

PowerShell または コマンドプロンプトで実行します。

### 4.1. 基本的な実行

```powershell
# 仮想環境を有効化 (まだの場合)
& .\.venv\Scripts\Activate.ps1

# デフォルトの actions.csv を実行
python automator.py
```

### 4.2. オプション

- `--aliases <file>`: エイリアス定義ファイルを指定します。
- `--log-file <file>`: 実行ログをファイルに出力します。
- `--log-level <level>`: ログレベルを指定します (`DEBUG`, `INFO`, `WARNING`, `ERROR`)。デフォルトは `INFO`。
- `--dry-run`: 実際の操作を行わずに実行フローを確認します（副作用なし）。
- `--force-run`: エラーが発生しても実行を継続します。デフォルトでは、要素が見つからないなどのエラーが発生した時点で実行を停止します。
- `--wait-time <seconds>`: 各アクション実行後の待機時間を秒数で指定します。指定しない場合はライブラリのデフォルト値が使用されます。例: `--wait-time 0.3`
  - アクションの読み込み、変数の展開、条件分岐などのロジックが正しく動作するかを、実際にクリックや入力をせずに安全に検証できます。
  - スクリプト作成時のデバッグや、本番環境で実行する前の最終確認に便利です。

### 4.3. Dry-Run モードの詳細

`--dry-run` オプションを指定した場合の挙動は以下の通りです。

**実行される処理:**

- **アクションファイルの読み込み**: CSVの構文エラーやエイリアスの解決を確認します。
- **ウィンドウの検索**: `TargetApp` で指定されたウィンドウが存在するかチェックします（存在しない場合は警告ログを出力）。
- **UI要素の検索**: `Key` で指定されたRPAパスに基づいて要素を検索します（存在しない場合は警告ログを出力）。これにより、パスの間違いを事前に検知できます。
- **変数の展開**: `{変数名}` の置換が正しく行われるか確認します。

**スキップされる処理（ログ出力のみ）:**

- **アプリの起動 (`Launch`)**: 実際には起動しません。
- **待機 (`Wait`, `WaitUntil...`)**: 実際には待機しません。
- **操作 (`Click`, `Input`, `SendKeys` 等)**: クリックやキー送信は行いません。
- **値の取得 (`GetValue`, `GetClipboard`)**: 実際には取得せず、ダミー値（`[DryRunValue]`など）を変数にセットして続行します。
- **アプリの終了 (`Exit`)**: 終了しません。

**注意点:**

- Dry-Runモードでは画面遷移が発生しないため、2つ目以降のアクションで「前の画面でボタンを押した結果表示されるはずの要素」が見つからず、警告が出る場合があります。これは正常な挙動です。

### 4.4. 実行例

**基本実行**

```bash
python automator.py actions.csv
```

**複数ファイルを指定して実行**

セットアップ、メイン処理、ティアダウンなどを分割して管理できます。指定した順序で結合されて実行されます。

```bash
python automator.py setup.csv main.csv teardown.csv
```

**エイリアスを使用**

```bash
python automator.py actions.csv --aliases aliases.csv
```

**複数のエイリアスファイルを指定**

共通エイリアスとプロジェクト固有エイリアスなどをマージできます。後から指定したファイルの定義が優先されます。

```bash
python automator.py actions.csv --aliases common_aliases.csv project_aliases.csv
```

**ログ出力とDry-run**

```bash
python automator.py actions.csv --aliases aliases.csv --log-file execution.log --log-level DEBUG --dry-run
```

## 5. Chrome / Electron アプリ操作のTips

ChromeやElectron製アプリ（VS Code, Teams, Slackなど）を操作する際の留意事項です。

### 5.1. 起動オプション

安定した操作のために、以下のオプションを付けてアプリを起動することを推奨します。

- `--force-renderer-accessibility`: アクセシビリティツリーを強制的に構築させます。

### 5.2. 要素の特定

- **AutomationId**: HTMLの `id` 属性がそのまま `AutomationId` として認識されることが多いです。
- **Name**: `aria-label` 属性やボタン内のテキストが `Name` として認識されます。
- **階層**: Webページは階層が深くなりがちです。InspectorのModernモードを活用し、`AutomationId` で特定することでパスを短縮できます。

### 5.3. 入力操作

- **Input vs SendKeys**: Reactなどのフレームワークでは、`Input` (SetValue) で値を設定しても内部ステートに反映されないことがあります。その場合は、`Click` でフォーカスしてから `SendKeys` で入力する方法を試してください。

### 5.4. キー操作

- ブラウザ独自のショートカットキー（`Ctrl+T` など）と競合しないように注意してください。

## 6. エラーハンドリング

実行中にエラーが発生した場合、`errors/` ディレクトリにスクリーンショットが自動的に保存されます。
ログファイルを確認することで、詳細なエラー原因を特定できます。

## 7. 注意点

- **要素が見つからない場合**: アプリの起動待ち時間が足りない可能性があります。`Wait` を長めに設定してみてください。
- **日本語入力**: `Input` アクションは、IME の状態によっては正しく入力されない場合があります。直接入力 (`SetValue`) を試みるか、クリップボード経由などを検討してください（現状は `SetValue` または `SendKeys` を使用）。

## 8. 付録: SendKeys 特殊キー一覧

`SendKeys` アクションで使用できる特殊キーの記述方法一覧です。`{}` で囲んで指定します。

| カテゴリ           | キー記述                      | 説明                                      |
| :----------------- | :---------------------------- | :---------------------------------------- |
| **修飾キー**       | `{Ctrl}`                      | Control キー                              |
|                    | `{Alt}`                       | Alt キー                                  |
|                    | `{Shift}`                     | Shift キー                                |
|                    | `{Win}`                       | Windows キー                              |
| **移動**           | `{Up}`                        | 上矢印 (↑)                                |
|                    | `{Down}`                      | 下矢印 (↓)                                |
|                    | `{Left}`                      | 左矢印 (←)                                |
|                    | `{Right}`                     | 右矢印 (→)                                |
|                    | `{Home}`                      | Home                                      |
|                    | `{End}`                       | End                                       |
|                    | `{PageUp}`                    | Page Up                                   |
|                    | `{PageDown}`                  | Page Down                                 |
| **編集・操作**     | `{Enter}`                     | Enter                                     |
|                    | `{Esc}`                       | Esc                                       |
|                    | `{Tab}`                       | Tab                                       |
|                    | `{Space}`                     | Space                                     |
|                    | `{Back}` または `{Backspace}` | Backspace                                 |
|                    | `{Del}` または `{Delete}`     | Delete                                    |
|                    | `{Ins}` または `{Insert}`     | Insert                                    |
| **ファンクション** | `{F1}` ～ `{F12}`             | F1 ～ F12                                 |
| **その他**         | `{PrintScreen}`               | Print Screen                              |
|                    | `{Apps}`                      | アプリケーションキー (右クリックメニュー) |
|                    | `{NumLock}`                   | Num Lock                                  |
|                    | `{CapsLock}`                  | Caps Lock                                 |
|                    | `{ScrollLock}`                | Scroll Lock                               |

**組み合わせ例:**

- `{Ctrl}c`: コピー (Ctrl + C)
- `{Ctrl}v`: 貼り付け (Ctrl + V)
- `{Alt}{Tab}`: アプリ切り替え
- `{Win}r`: 「ファイル名を指定して実行」を開く
