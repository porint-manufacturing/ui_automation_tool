import sys
import os

# モジュールインポート用にカレントディレクトリをPythonパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import csv
import time
import subprocess
import re
import argparse
import logging
import datetime
import ctypes
import uiautomation as auto
from src.automator.utils.focus import FocusManager
from src.automator.utils.screenshot import capture_screenshot
from src.automator.core.element_finder import ElementFinder
from src.automator.core.action_executor import ActionExecutor

# 正確な座標を確保するためにHigh DPI Awarenessを有効化
try:
    auto.SetProcessDpiAwareness(2) # Process_PerMonitorDpiAware
except Exception:
    pass # サポートされていない場合は無視（例: 古いWindows）

class Automator:
    def __init__(self, action_files, log_file=None, log_level="INFO", dry_run=False, force_run=False, wait_time=None):
        self.actions = []
        self.variables = {}
        self.aliases = {}  # エイリアス名 -> RPAパス
        self.reverse_aliases = {}  # RPAパス -> エイリアス名（エラーメッセージ用）
        self.dry_run = dry_run
        self.force_run = force_run
        self.wait_time = wait_time  # Noneはライブラリデフォルトを使用
        
        # ロギング設定
        level = getattr(logging, log_level.upper(), logging.INFO)
        handlers = [logging.StreamHandler(sys.stdout)]
        if log_file:
            handlers.append(logging.FileHandler(log_file, encoding='utf-8'))
        
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True # 既に設定されている場合は再設定
        )
        self.logger = logging.getLogger(__name__)
        
        # FocusManager初期化
        self.focus_manager = FocusManager(force_run=force_run)
        
        # ElementFinder初期化
        self.element_finder = ElementFinder(
            logger=self.logger,
            aliases=self.aliases,
            reverse_aliases=self.reverse_aliases
        )
        
        # ActionExecutor初期化
        self.action_executor = ActionExecutor(
            logger=self.logger,
            element_finder=self.element_finder,
            focus_manager=self.focus_manager,
            dry_run=self.dry_run,
            force_run=self.force_run,
            wait_time=self.wait_time
        )
        
        # action_filesがリストであることを確保
        if isinstance(action_files, str):
            self.action_files = [action_files]
        else:
            self.action_files = action_files
            
        if self.dry_run:
            self.logger.info("=== DRY RUN MODE ENABLED ===")

    def load_aliases(self, alias_files):
        """1つ以上のCSVファイルからエイリアスを読み込む"""
        if isinstance(alias_files, str):
            alias_files = [alias_files]
            
        for alias_file in alias_files:
            self.logger.info(f"Loading aliases from {alias_file}...")
            try:
                with open(alias_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        alias = row.get("AliasName")
                        path = row.get("RPA_Path")
                        if alias and path:
                            if alias in self.aliases:
                                self.logger.warning(f"Duplicate alias '{alias}' found in {alias_file}. Overwriting.")
                            self.aliases[alias] = path
                            self.reverse_aliases[path] = alias  # 逆引きを構築
            except Exception as e:
                self.logger.error(f"Error loading aliases from {alias_file}: {e}")
                sys.exit(1)
        self.logger.info(f"Loaded {len(self.aliases)} aliases total.")

    def load_actions(self):
        for csv_file in self.action_files:
            self.logger.info(f"Loading actions from {csv_file}...")
            try:
                with open(csv_file, 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # エイリアスが存在する場合は解決
                        key = row.get("Key", "")
                        if key and key in self.aliases:
                            self.logger.debug(f"Resolved alias '{key}' -> '{self.aliases[key]}'")
                            row["Key"] = self.aliases[key]
                        
                        # アクションタイプを正規化
                        act_type = row.get("Action", "")
                        if act_type.upper() == "IF": row["Action"] = "If"
                        elif act_type.upper() == "ELSE": row["Action"] = "Else"
                        elif act_type.upper() == "ENDIF": row["Action"] = "EndIf"
                        elif act_type.upper() == "LOOP": row["Action"] = "Loop"
                        elif act_type.upper() == "ENDLOOP": row["Action"] = "EndLoop"
                        
                        self.actions.append(row)
            except FileNotFoundError:
                self.logger.error(f"File not found: {csv_file}")
                sys.exit(1)
            except Exception as e:
                self.logger.error(f"Error loading actions from {csv_file}: {e}")
                sys.exit(1)
        self.logger.info(f"Loaded {len(self.actions)} actions total.")

    def evaluate_condition(self, condition):
        """{status} == 'OK' のような条件文字列を評価する"""
        # 変数置換
        if '{' in condition and '}' in condition:
            for var_name, var_val in self.variables.items():
                condition = condition.replace(f"{{{var_name}}}", str(var_val))
        
        # 安全性チェック: 単純な比較のみ許可
        # これは基本的な実装。本番環境では、より安全なパーサーを使用すること。
        try:
            # 柔軟性のためeval()を使用しているが、信頼できない入力には危険。
            # CSVは信頼できると仮定。
            return eval(condition)
        except Exception as e:
            self.logger.error(f"Condition evaluation failed: {condition} - {e}")
            return False

    def find_matching_end(self, start_index, start_type):
        """指定された開始アクションに対応するEndIf/Else/EndLoopを見つける"""
        nesting = 0
        for i in range(start_index + 1, len(self.actions)):
            act = self.actions[i].get('Action', '')
            
            if start_type == 'If':
                if act == 'If':
                    nesting += 1
                elif act == 'EndIf':
                    if nesting == 0:
                        return i
                    nesting -= 1
                elif act == 'Else':
                    if nesting == 0:
                        return i
            
            elif start_type == 'Loop':
                if act == 'Loop':
                    nesting += 1
                elif act == 'EndLoop':
                    if nesting == 0:
                        return i
                    nesting -= 1
        return -1

    def run(self):
        i = 0
        loop_stack = [] # (start_index, loop_info)を格納
        
        while i < len(self.actions):
            action = self.actions[i]
            self.logger.info(f"--- Action {i+1} ---")
            target_app = action.get('TargetApp', '')
            key = action.get('Key', '')
            act_type = action.get('Action', '')
            value = action.get('Value', '')
            if value is None:
                value = ""

            # 変数置換（制御フロー以外のValue用、制御フローは個別に処理）
            if act_type not in ['If', 'Loop', 'SetVariable']:
                 if '{' in value and '}' in value:
                    for var_name, var_val in self.variables.items():
                        value = value.replace(f"{{{var_name}}}", str(var_val))

            self.logger.info(f"Target: {target_app}, Action: {act_type}, Value: {value}")
            
            # --- 制御フロー ---
            if act_type == 'If':
                condition = value
                result = self.evaluate_condition(condition)
                self.logger.info(f"Condition '{condition}' evaluated to: {result}")
                
                if result:
                    # 次のアクションに続行（Trueブロック）
                    i += 1
                else:
                    # ElseまたはEndIfにジャンプ
                    jump_to = self.find_matching_end(i, 'If')
                    if jump_to == -1:
                        self.logger.error("Missing matching EndIf/Else for If")
                        break
                    
                    # Elseにジャンプした場合、Elseブロックの次を実行する必要がある（i = jump_to + 1）
                    # しかし待て、Elseにジャンプした場合、次の反復で'Else'アクションを処理する？
                    # いいえ、'Else'アクション自体は自然に遇遇した場合、初めてEndIfにジャンプするべき。
                    # Elseにジャンプする場合、Elseの後のブロックに入る必要がある。
                    
                    next_act = self.actions[jump_to].get('Action', '')
                    if next_act == 'Else':
                        i = jump_to + 1
                    else: # EndIf
                        i = jump_to + 1
                continue

            elif act_type == 'Else':
                # Elseに自然に達した場合、Trueブロックを実行したことを意味する。
                # そのため、EndIfにスキップする必要がある。
                # このブロックを開始したIfに対応するEndIfを見つける必要がある。
                # しかし、スタックを追跡しない限り、ここでは開始Ifへの参照を簡単に持っていない。
                # あるいは、単に前方にスキャンしてEndIfを見つけ、ネストを尊重する。
                # Elseブロック内にいる（概念的に）、EndIfを検索する。
                # しかし待て、'Else'は'If'と同じネストレベルにある。
                
                # 前方にスキャンしてEndIfを検索
                jump_to = self.find_matching_end(i, 'If') # Ifロジックを再利用？いいえ、IfロジックはElse/EndIfを探す。
                # EndIfのみを探すファインダが必要。
                
                nesting = 0
                found = -1
                for j in range(i + 1, len(self.actions)):
                    act = self.actions[j].get('Action', '')
                    if act == 'If':
                        nesting += 1
                    elif act == 'EndIf':
                        if nesting == 0:
                            found = j
                            break
                        nesting -= 1
                
                if found != -1:
                    i = found + 1
                else:
                    self.logger.error("Missing matching EndIf for Else")
                    break
                continue

            elif act_type == 'EndIf':
                # 続行するだけ
                i += 1
                continue

            elif act_type == 'Loop':
                # このループが既にアクティブかどうかをチェック
                active_loop = None
                if loop_stack and loop_stack[-1][0] == i:
                    active_loop = loop_stack[-1]
                
                if active_loop:
                    # 条件を再評価
                    condition = value
                    # valueが数値の場合、カウントループ
                    if value.isdigit():
                         # カウントは状態で処理
                         pass # 以下のロジック
                    else:
                         # 条件ループ
                         pass
                else:
                    # 新しいループエントリ
                    pass

                # 統一されたループロジック
                # valueが数字 -> カウントループ
                # それ以外 -> 条件ループ
                
                should_loop = False
                
                # 評価用にvalue内の変数を展開
                eval_value = value
                if '{' in eval_value and '}' in eval_value:
                    for var_name, var_val in self.variables.items():
                        eval_value = eval_value.replace(f"{{{var_name}}}", str(var_val))

                if eval_value.isdigit():
                    max_count = int(eval_value)
                    # スタックをチェック
                    if loop_stack and loop_stack[-1][0] == i:
                        # カウンタをインクリメント
                        loop_stack[-1][1]['current'] += 1
                        if loop_stack[-1][1]['current'] < max_count:
                            should_loop = True
                        else:
                            should_loop = False
                            loop_stack.pop() # ループ終了
                    else:
                        # 最初のエントリ
                        if max_count > 0:
                            should_loop = True
                            loop_stack.append((i, {'type': 'count', 'current': 0, 'max': max_count}))
                        else:
                            should_loop = False
                else:
                    # 条件ループ
                    result = self.evaluate_condition(value) # 変数を含む元のvalueを使用
                    if result:
                        should_loop = True
                        if not (loop_stack and loop_stack[-1][0] == i):
                            loop_stack.append((i, {'type': 'condition'}))
                    else:
                        should_loop = False
                        if loop_stack and loop_stack[-1][0] == i:
                            loop_stack.pop()

                if should_loop:
                    i += 1
                else:
                    # EndLoopにジャンプ
                    jump_to = self.find_matching_end(i, 'Loop')
                    if jump_to == -1:
                        self.logger.error("Missing matching EndLoop")
                        break
                    i = jump_to + 1
                continue

            elif act_type == 'EndLoop':
                # Loop開始位置に戻る
                if loop_stack:
                    start_index = loop_stack[-1][0]
                    i = start_index
                else:
                    self.logger.error("EndLoop without active Loop")
                    i += 1
                continue

            # --- 通常アクション ---
            try:
                self.execute_action(target_app, key, act_type, value)
            except Exception as e:
                self.logger.error(f"Action failed: {e}")
                capture_screenshot(f"error_action_{i+1}", dry_run=self.dry_run)
                if not self.force_run:
                    self.logger.error("Stopping execution due to error. Use --force-run to continue on errors.")
                    sys.exit(1)
            
            i += 1








    def execute_action(self, target_app, key, act_type, value):
        """単一アクションをActionExecutorに委譲して実行"""
        return self.action_executor.execute(target_app, key, act_type, value, self.variables)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automator: Execute UI automation from CSV.")
    parser.add_argument("csv_files", nargs='+', default=["actions.csv"], help="Path to the actions CSV file(s).")
    parser.add_argument("--aliases", nargs='+', help="Path to the aliases CSV file(s).")
    parser.add_argument("--log-file", help="Path to the log file.")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Logging level.")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no side effects).")
    parser.add_argument("--force-run", action="store_true", help="Continue execution even if errors occur.")
    parser.add_argument("--wait-time", type=float, help="Wait time (in seconds) after each action. If not specified, uses library default.")
    
    args = parser.parse_args()
    
    app = Automator(args.csv_files, log_file=args.log_file, log_level=args.log_level, dry_run=args.dry_run, force_run=args.force_run, wait_time=args.wait_time)
    
    if args.aliases:
        app.load_aliases(args.aliases)
        
    app.load_actions()
    app.run()
