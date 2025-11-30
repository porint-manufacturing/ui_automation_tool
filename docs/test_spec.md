# テスト仕様書

本プロジェクトの自動テスト（検証スクリプト）に関する仕様と実行方法を記述します。

## 1. テスト環境

- **実行場所**: `tests/` ディレクトリ配下のスクリプトを使用
- **依存関係**: プロジェクトの仮想環境 (`.venv`)

## 2. テスト一覧

### 2.1. ログ機能の検証 (`tests/verify_logging.py`)

- **目的**: `automator.py` が `--log-file` および `--log-level` オプションを正しく処理し、ログファイルを出力することを確認する。
- **テスト内容**:
  1.  ダミーの `actions.csv` を作成。
  2.  `automator.py` を `--log-file` 指定で実行。
  3.  生成されたログファイルを読み込み、特定のログメッセージ（"Loading actions", "Waiting" など）が含まれているか確認。
- **期待される結果**:
  - ログファイルが作成されること。
  - ログファイル内に期待されるメッセージが存在すること。
  - スクリプトが "Logging Verification: PASS" を出力して終了すること。

### 2.2. Dry-run モードの検証 (`tests/verify_dry_run.py`)

- **目的**: `automator.py` が `--dry-run` オプション指定時に、副作用のある操作（アプリ起動、クリック等）をスキップし、その旨をログ出力することを確認する。
- **テスト内容**:
  1.  メモ帳を起動するアクションを含むダミーの `actions.csv` を作成。
  2.  `automator.py` を `--dry-run` 指定で実行。
  3.  ログファイルを解析し、"[Dry-run] Would launch" などのメッセージが出力されているか確認。
- **期待される結果**:
  - 実際にアプリが起動しないこと（実行時間が極端に短いことで間接的に検証）。
  - ログに "[Dry-run]" プレフィックス付きのメッセージが記録されること。
  - スクリプトが "Dry-run Verification: PASS" を出力して終了すること。

### 2.3. スクリーンショット機能の検証 (`tests/verify_screenshot.py`)

- **目的**: アクション実行中にエラーが発生した場合、自動的にスクリーンショットが保存されることを確認する。
- **テスト内容**:
  1.  存在しないウィンドウを操作しようとする（必ず失敗する）ダミーの `actions.csv` を作成。
  2.  `automator.py` を実行。
  3.  `errors/` ディレクトリ内のファイル数をカウントし、実行後に増えているか確認。
- **期待される結果**:
  - `automator.py` がエラーで終了（またはエラーログを出力）すること。
  - `errors/` ディレクトリに新しい `.png` ファイルが生成されること。
  - スクリプトが "Screenshot Verification: PASS" を出力して終了すること。

### 2.4. 既存機能の検証

以下のスクリプトは、以前の実装フェーズで作成された機能検証用です。

#### 2.4.1. エイリアス機能の検証 (`tests/verify_alias_feature.py`)

- **目的**: Inspectorによるエイリアス定義ファイルの出力と、Automatorによるエイリアスの読み込み・解決を検証する。
- **テスト内容**:
  - **Inspector**: ダミーの記録データをセットし、`--output alias` モードでCSVが出力されるか確認。
  - **Automator**: ダミーのエイリアス定義とアクション定義を作成し、アクション実行時にエイリアスが正しいRPAパスに置換されるか確認。
- **期待される結果**:
  - Inspector: `inspector_YYYYMMDD_..._alias.csv` が生成され、正しいカラムを持つこと。
  - Automator: アクションの `Key` がエイリアス定義の内容に置き換わっていること。

#### 2.4.2. 階層化パスの検証 (`tests/verify_automator_chained_path.py`)

- **目的**: `Parent -> Child` 形式の階層化されたRPAパスを `automator.py` が正しく解析し、要素を特定できるか検証する。
- **テスト内容**:
  - メモ帳を起動。
  - `Window -> Pane -> Document` のような階層化パスを手動で構築。
  - `automator.find_element_by_path` を呼び出し、要素が見つかるか確認。
- **期待される結果**:
  - 指定した階層化パスで要素が正しく特定されること（Result: Found）。

#### 2.4.3. Inspector基本ロジックの検証 (`tests/verify_inspector.py`)

- **目的**: `inspector.py` が実際のアプリ（電卓）から適切なRPAパスを生成できるか検証する。
- **テスト内容**:
  - 電卓を起動。
  - ボタン「5」やメニューボタンを対象に `get_rpa_path` を実行。
- **期待される結果**:
  - 生成されたパスに `ClassName` や `foundIndex`、または `AutomationId` が適切に含まれていること。

#### 2.4.4. Inspectorモードの検証 (`tests/verify_inspector_modes.py`)

- **目的**: `modern` モードと `legacy` モードで生成されるパスの違いを検証する。
- **テスト内容**:
  - メモ帳を起動。
  - **Modern**: `Name` や `AutomationId` を優先したパスが生成されるか確認。
  - **Legacy**: `ClassName` と `foundIndex` を使用したパスが生成されるか確認。
- **期待される結果**:
  - 各モードのポリシーに従ったパスが生成されること。

#### 2.4.5. Inspector出力の検証 (`tests/verify_inspector_output.py`)

- **目的**: CSVファイル出力とクリップボード出力が正しく機能するか検証する。
- **テスト内容**:
  - ダミーデータをセットし、`output="csv"` と `output="clipboard"` を実行。
- **期待される結果**:
  - CSVファイルが生成されること。
  - クリップボードにCSV形式の文字列がコピーされること。

### 2.5. 多言語サポートの検証

#### 2.5.1. 日本語エイリアスの検証 (`tests/verify_japanese_alias.py`)

- **目的**: `AliasName` に日本語（マルチバイト文字）を使用しても正しく動作することを検証する。
- **テスト内容**:
  - 日本語のエイリアス名（例: "メモ帳テキストエリア"）を含むエイリアス定義ファイルを作成。
  - そのエイリアスを使用するアクション定義ファイルを作成。
  - Automatorで読み込み、正しくRPAパスに解決されるか確認。
- **期待される結果**:
  - 日本語エイリアスが文字化けせずに読み込まれ、対応するRPAパスに置換されること。

## 3. テスト実行方法

以下のコマンドですべての検証スクリプトを実行できます。

```bash
# 新機能の検証
python tests/verify_logging.py
python tests/verify_dry_run.py
python tests/verify_screenshot.py
python tests/verify_japanese_alias.py

# 既存機能の検証
python tests/verify_alias_feature.py
python tests/verify_automator_chained_path.py
python tests/verify_inspector.py
python tests/verify_inspector_modes.py
python tests/verify_inspector_output.py
```
