# Windows UI Automation Tool

Python製のWindows UI自動化ツールキットです。`uiautomation` ライブラリをベースに、アクション定義ファイル（CSV）による自動化実行 (`automator.py`) と、UI要素の解析・パス生成ツール (`inspector.py`) を提供します。

## 特徴

- **Automator (`automator.py`)**:
  - CSVファイルに記述されたアクション（クリック、入力、待機など）を順次実行。
  - RPAパスによる柔軟な要素特定（階層化パス、正規表現サポート）。
  - エイリアス機能によるアクション定義の簡略化。
  - 変数の使用と検証機能。
- **Inspector (`inspector.py`)**:
  - マウスオーバーとクリックでUI要素を解析し、RPAパスを自動生成。
  - **Modernモード**: AutomationIdを優先するモダンアプリ向け。
  - **Legacyモード**: ClassNameを優先するレガシーアプリ向け。
  - **Chained Path**: 親子関係を利用した高速で堅牢なパス生成。
  - **Interactive Alias Mode**: 対話形式で効率的にエイリアスを作成。
  - CSV出力、クリップボードコピー、エイリアス定義テンプレート生成に対応。

## 必要要件

- Windows OS
- Python 3.x
- `uiautomation`
- `keyboard`

## インストール

```bash
# リポジリのクローン
git clone <repository-url>
cd automation

# 仮想環境の作成と有効化（推奨）
python -m venv .venv
.venv\Scripts\activate

# 依存ライブラリのインストール
pip install -r requirements.txt
```

## 使い方

### 1. UI要素の調査 (Inspector)

操作したいアプリケーションのUI要素を特定し、RPAパスを取得します。

```bash
# 基本的な使用法（クリップボードにコピー）
python inspector.py

# レガシーアプリ向けモード
python inspector.py --mode legacy

# エイリアス定義用のCSVテンプレートを作成（推奨）
python inspector.py --output alias

# 対話形式でエイリアスを作成（New!）
python inspector.py --output interactive_alias
```

- 要素をクリックすると、その要素のRPAパスが生成されます。
- `--output alias` を指定すると、`inspector_YYYYMMDD_HHMMSS_alias.csv` が生成されます。このファイルの `AliasName` 列に任意の名前（例: `Btn_Save`）を入力することで、アクション定義でその名前を使用できるようになります。
- `ESC` キーで終了します。

### 2. アクションの定義

`actions.csv` などのCSVファイルを作成し、自動化の手順を記述します。

**通常の方法（RPAパスを直接記述）:**

| TargetApp | Key                     | Action | Value |
| :-------- | :---------------------- | :----- | :---- |
| 電卓      | ButtonControl(Name='5') | Click  |       |

**エイリアスを使用する方法（推奨）:**

まず、Inspectorで生成したエイリアス定義ファイル（例: `aliases.csv`）を編集します。

| AliasName | RPA_Path                |
| :-------- | :---------------------- |
| Btn_Five  | ButtonControl(Name='5') |

次に、アクション定義ファイルでエイリアス名を使用します。

| TargetApp | Key      | Action | Value |
| :-------- | :------- | :----- | :---- |
| 電卓      | Btn_Five | Click  |       |

### 3. 自動化の実行 (Automator)

作成したアクション定義ファイルを指定して実行します。

```bash
# アクションファイルの実行
python automator.py actions.csv

# エイリアスファイルを使用して実行
python automator.py actions.csv --aliases aliases.csv
```

## ディレクトリ構成

- `automator.py`: 自動化実行のメインスクリプト
- `inspector.py`: UI解析ツール
- `docs/`: ドキュメント
- `tests/`: テストスクリプト
- `debug/`: デバッグ用スクリプト

## ライセンス

[MIT License](LICENSE)
