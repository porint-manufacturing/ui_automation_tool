# RPA Path 仕様書

本ドキュメントでは、`inspector.py` が生成し、`automator.py` が解釈する **RPA Path** の構文と仕様について定義します。

## 1. 概要

RPA Path は、Windows アプリケーションの UI 要素を一意に特定するための文字列です。
`ControlType` と `Properties` の組み合わせで表現され、`->` で繋ぐことで階層構造（親子関係）を表現できます。

## 2. 基本構文

```text
ControlType(Property1='Value1', Property2='Value2', ...)
```

- **ControlType**: `uiautomation` ライブラリで定義されているコントロールタイプ（例: `ButtonControl`, `EditControl`, `WindowControl`）。
- **Properties**: 要素を特定するための属性。カンマ区切りで複数指定可能。

### 例

```text
ButtonControl(Name='保存')
EditControl(AutomationId='TextBox1', ClassName='Edit')
```

## 3. 階層化パス (Chained Path)

要素をより確実かつ高速に特定するために、親要素からのパスを `->` で繋いで記述します。

```text
ParentControl(...) -> ChildControl(...) -> TargetControl(...)
```

- **探索ロジック**:
  1.  左側の `ParentControl` をルート（または直前の要素）から探索します。
  2.  見つかった `ParentControl` を起点として、次の `ChildControl` を探索します。
  3.  これを最後まで繰り返します。
- **メリット**:
  - **高速化**: 各ステップの探索範囲を直下の子要素（`searchDepth=1`）に限定できるため、全探索に比べて非常に高速です。
  - **一意性**: 画面内に同じ名前のボタンが複数あっても、親要素が異なれば区別できます。

### 例

```text
WindowControl(Name='電卓') -> GroupControl(Name='NumberPad') -> ButtonControl(Name='5')
```

## 4. サポートされるプロパティ

`automator.py` は以下のプロパティを解釈します。

| プロパティ名   | 説明                                   | 例                         | 備考                                                                 |
| :------------- | :------------------------------------- | :------------------------- | :------------------------------------------------------------------- |
| `Name`         | 要素の表示名（アクセシビリティ名）。   | `Name='OK'`                | シングルクォートで囲む。内部のシングルクォートは `\'` でエスケープ。 |
| `AutomationId` | 開発者が付与したID。最も信頼性が高い。 | `AutomationId='SubmitBtn'` | モダンアプリ（WPF, UWP等）で有効。                                   |
| `ClassName`    | ウィンドウクラス名。                   | `ClassName='Button'`       | レガシーアプリ（Win32）で有効。                                      |
| `foundIndex`   | 兄弟要素の中での順序（1始まり）。      | `foundIndex=3`             | 同一属性の要素が複数ある場合に使用。                                 |
| `searchDepth`  | 探索する深さ。                         | `searchDepth=1`            | `1` は直下の子要素のみ。省略時は全子孫（遅い）。                     |

## 5. 探索挙動の詳細

### 5.1. プロパティのマッチング

- **文字列プロパティ** (`Name`, `AutomationId`, `ClassName`):
  - 指定された値と **完全一致** する要素を探します。
  - `inspector.py` は、値に含まれるシングルクォート `'` を自動的に `\'` にエスケープして生成します。
- **数値プロパティ** (`foundIndex`, `searchDepth`):
  - 整数として解釈されます。

### 5.2. `foundIndex` の扱い

- `foundIndex=1`（デフォルト）: 条件に一致する **最初** の要素を返します。
- `foundIndex=N` (N > 1): 条件に一致する要素を上から順に数え、**N番目** の要素を返します。
  - _注意_: `searchDepth=1` と組み合わせることで、「N番目の子要素」を正確に特定できます。

### 5.3. `searchDepth` の扱い

- `searchDepth=1`: 起点となる要素の **直下の子要素のみ** を探索します。
  - `inspector.py` が生成する階層化パスでは、基本的にすべてのセグメントに `searchDepth=1` が付与されます。
- 省略時（または `0xFFFFFFFF`）: 起点となる要素の **すべての子孫要素** を探索します。
  - 探索範囲が広いため、処理時間が長くなる可能性があります。

## 6. エイリアス (Alias)

長い RPA Path を短い名前に置き換える機能です。

- **定義**: `aliases.csv` などの別ファイルで `AliasName,RPA_Path` の形式で定義。
- **利用**: `actions.csv` の `Key` カラムに `AliasName` を記述。

### 例

**aliases.csv**

```csv
AliasName,RPA_Path
Btn_Save,WindowControl(Name='App') -> ButtonControl(Name='Save')
```

**actions.csv**

```csv
TargetApp,Key,Action,Value
App,Btn_Save,Click,
```
