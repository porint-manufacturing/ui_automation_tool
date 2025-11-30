# UI Inspector アプリ - 実行ガイド

## 前提条件

- Python 3.x がインストールされていること。
- インターネット接続（ライブラリのインストール用）。

## 1. インストール

プロジェクトディレクトリでターミナルを開きます:
`c:\Users\shion\OneDrive\ドキュメント\automation`

以下のコマンドを実行して必要なライブラリをインストールします:

```bash
pip install -r requirements.txt
```

_注意: エラーが発生した場合は、コマンドプロンプトを管理者として実行するか、`python -m pip install -r requirements.txt` を試してください。_

## 2. アプリの実行

インスペクターを起動します:

```bash
python inspector.py
```

## 3. 使用方法

### 基本的な使い方（モダンモード & クリップボード出力）

1.  **起動**:
    ```bash
    python inspector.py
    ```
2.  **検査**: 任意の UI 要素（ボタン、ウィンドウ、アイコン）の上にマウスを移動し、**左クリック**します。
3.  **出力**:
    - コンソールに要素の属性（Name, AutomationId, ClassNameなど）と生成された `RPA_Path` が表示されます。
    - `TargetApp`（ウィンドウタイトル）も表示されます。
4.  **終了**: `ESC` キーを押すとアプリケーションが停止し、記録された内容が **CSV形式でクリップボードにコピー** されます。

### 高度な使い方（オプション指定）

起動時にオプションを指定することで、動作モードを変更できます。

#### モード指定 (`--mode`)

- `modern` (デフォルト): `AutomationId` や `Name` を優先してパスを生成します。UWPやWPFなどのモダンアプリに適しています。
- `legacy`: `ClassName` と `foundIndex` を優先してパスを生成します。`Name` が不安定なWin32アプリやレガシーアプリに適しています。

#### 出力先指定 (`--output`)

- `clipboard` (デフォルト): 終了時にクリップボードにコピーします。
- `csv`: 終了時に `inspector_YYYYMMDD_HHMMSS.csv` というファイル名で保存します。
- `alias`: エイリアス定義用のCSVテンプレート (`inspector_YYYYMMDD_HHMMSS_alias.csv`) を保存します。このファイルは `AliasName` と `RPA_Path` の列を持ち、`AliasName` を埋めることで `automator.py` のエイリアスファイルとして使用できます。
- `normal`: コンソール表示のみ行い、記録しません。

**コマンド例:**

```bash
# レガシーアプリを調査し、CSVファイルに保存する場合
python inspector.py --mode legacy --output csv

# エイリアス定義用のCSVを作成する場合
python inspector.py --output alias

# 記録せず、コンソールで確認だけしたい場合
python inspector.py --output normal
```

### CSV出力の内容

出力されるCSV（またはクリップボード内容）は以下の形式です：
`TargetApp,Key,Action,Value`

- `TargetApp`: 操作対象のウィンドウタイトル。
- `Key`: 生成されたRPAパス。
- `Action`: 空欄（ユーザーが記述）。
- `Value`: 空欄（ユーザーが記述）。

## トラブルシューティング

- **出力がない**: コンソールウィンドウが表示されていることを確認してください。
- **クリックが反応しない**: 一部のアプリケーションはグローバルフックをブロックする場合があります。ターミナルを管理者として実行してみてください。
- **"ModuleNotFoundError"**:
  - 仮想環境（`.venv`）を使用している場合は、必ずアクティベートしてから `pip install` と実行を行ってください。
  - PowerShell: `& .\.venv\Scripts\Activate.ps1`
- **終了時にフリーズする**:
  - Git Bash などの一部のターミナル環境では、終了時にフリーズする報告があります。その場合は **PowerShell** または **コマンドプロンプト** での実行を推奨します。
