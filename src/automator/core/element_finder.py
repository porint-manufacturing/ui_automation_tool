"""
Element Finder Module

UI要素の検索と取得操作を処理。
"""

import logging
import re
import uiautomation as auto


class ElementFinder:
    """UI要素の検索とプロパティ取得を管理する。"""
    
    def __init__(self, logger=None, aliases=None, reverse_aliases=None):
        """
        ElementFinder初期化。
        
        Args:
            logger: Loggerインスタンス
            aliases: エイリアスマッピングの辞書
            reverse_aliases: エイリアス用の逆引き辞書
        """
        self.logger = logger or logging.getLogger(__name__)
        self.aliases = aliases or {}
        self.reverse_aliases = reverse_aliases or {}
    
    def format_path_with_alias(self, rpa_path):
        """エラーメッセージ用にエイリアス名でRPA_PATHをフォーマット。"""
        if rpa_path in self.reverse_aliases:
            alias = self.reverse_aliases[rpa_path]
            return f"'{alias}' ({rpa_path})"
        return rpa_path
    
    def find_window(self, target_app):
        """アプリケーション名でウィンドウを検索。"""
        self.logger.debug(f"Searching for window '{target_app}'...")
        
        # 明示的な正規表現モード
        if target_app.startswith("regex:"):
            pattern = target_app[6:] # 'regex:' を除去
            self.logger.debug(f"Using regex pattern: {pattern}")
            win = auto.WindowControl(searchDepth=1, RegexName=pattern)
            if win.Exists(maxSearchSeconds=1):
                return win
            return None

        # 標準モード（まず完全一致、次に部分一致の正規表現フォールバック）
        win = auto.WindowControl(searchDepth=1, Name=target_app)
        if win.Exists(maxSearchSeconds=1):
            return win
        
        # フォールバック: RegexNameを使用した部分一致
        safe_name = re.escape(target_app)
        win = auto.WindowControl(searchDepth=1, RegexName=f".*{safe_name}.*")
        if win.Exists(maxSearchSeconds=1):
            return win
            
        return None
    
    def find_element_by_path(self, root, path_string):
        """パス文字列で要素を検索。"""
        parts = [p.strip() for p in path_string.split('->')]
        current = root
        
        for part in parts:
            if not part:
                continue
            
            match = re.match(r"(\w+)(?:\((.*)\))?", part)
            if not match:
                self.logger.error(f"Invalid path part format: {part}")
                return None
            
            control_type = match.group(1)
            props_str = match.group(2)
            
            search_params = {"ControlTypeName": control_type}
            found_index = 1

            if props_str:
                name_match = re.search(r"\bName='([^']*)'", props_str)
                regex_name_match = re.search(r"\bRegexName='([^']*)'", props_str)
                id_match = re.search(r"\bAutomationId='([^']*)'", props_str)
                class_match = re.search(r"\bClassName='([^']*)'", props_str)
                index_match = re.search(r"\bfoundIndex=(\d+)", props_str)
                depth_match = re.search(r"\bsearchDepth=(\d+)", props_str)
                
                if name_match:
                    search_params["Name"] = name_match.group(1)
                if regex_name_match:
                    search_params["RegexName"] = regex_name_match.group(1)
                if id_match:
                    search_params["AutomationId"] = id_match.group(1)
                if class_match:
                    search_params["ClassName"] = class_match.group(1)
                if index_match:
                    found_index = int(index_match.group(1))
                if depth_match:
                    search_params["searchDepth"] = int(depth_match.group(1))

            self.logger.debug(f"Searching descendant: {search_params} (Index: {found_index}) under {current.Name}...")
            
            target = current.Control(
                foundIndex=found_index,
                **search_params
            )
            
            if not target.Exists(maxSearchSeconds=2):
                # フォールバック: 検索深度を1増やして試す
                current_depth = search_params.get("searchDepth", 1)
                self.logger.warning(f"Element not found at depth {current_depth}. Trying depth {current_depth + 1}...")
                search_params["searchDepth"] = current_depth + 1
                self.logger.debug(f"Fallback 1 params: {search_params}")
                target = current.Control(
                    foundIndex=found_index,
                    **search_params
                )

            if not target.Exists(maxSearchSeconds=1):
                # フォールバック2: 再帰検索を試す（深度を無視）
                self.logger.warning(f"Element not found at depth {current_depth + 1}. Trying recursive search...")
                if "searchDepth" in search_params:
                    del search_params["searchDepth"]
                
                self.logger.debug(f"Fallback 2 params: {search_params}")
                target = current.Control(
                    foundIndex=found_index,
                    **search_params
                )
                
            if not target.Exists(maxSearchSeconds=1):
                self.logger.warning(f"Not found: {part}")
                return None
            
            current = target
            
        return current
    
    def get_element_property(self, element, prop_name):
        """要素からプロパティ値を取得。"""
        try:
            # 基本プロパティ
            if prop_name == 'Name':
                return element.Name or ''
            elif prop_name == 'AutomationId':
                return element.AutomationId or ''
            elif prop_name == 'ControlType':
                return element.ControlTypeName or ''
            elif prop_name == 'ClassName':
                return element.ClassName or ''
            elif prop_name == 'IsEnabled':
                return str(element.IsEnabled)
            elif prop_name == 'IsVisible':
                return str(not element.IsOffscreen)
            elif prop_name == 'IsKeyboardFocusable':
                return str(element.IsKeyboardFocusable)
            elif prop_name == 'HasKeyboardFocus':
                return str(element.HasKeyboardFocus)
            
            # パターンベースのプロパティ
            elif prop_name == 'Value':
                try:
                    pattern = element.GetPattern(auto.PatternId.ValuePattern)
                    return pattern.Value if pattern else ''
                except Exception:
                    return ''
            elif prop_name == 'Text':
                try:
                    pattern = element.GetPattern(auto.PatternId.TextPattern)
                    if pattern:
                        return pattern.DocumentRange.GetText(-1)
                except Exception:
                    pass
                return element.Name or ''
            elif prop_name == 'IsChecked':
                try:
                    pattern = element.GetPattern(auto.PatternId.TogglePattern)
                    if pattern:
                        state = pattern.ToggleState
                        return 'True' if state == 1 else 'False'  # 1 = On, 0 = Off
                except Exception:
                    return ''
            elif prop_name == 'IsSelected':
                try:
                    pattern = element.GetPattern(auto.PatternId.SelectionItemPattern)
                    return str(pattern.IsSelected) if pattern else ''
                except Exception:
                    return ''
            else:
                self.logger.warning(f"Unknown property: {prop_name}")
                return ''
        except Exception as e:
            self.logger.warning(f"Failed to get property '{prop_name}': {e}")
            return ''
    
    def get_relative_element(self, element, window, direction):
        """方向に基づいて相対的な要素を取得。"""
        try:
            if direction == 'self':
                return element
            elif direction == 'parent':
                parent = element.GetParentControl()
                return parent if parent else None
            elif direction == 'next':
                sibling = element.GetNextSiblingControl()
                return sibling if sibling else None
            elif direction in ['prev', 'previous']:
                sibling = element.GetPreviousSiblingControl()
                return sibling if sibling else None
            elif direction in ['left', 'right', 'up', 'down', 'above', 'below']:
                # 座標ベースの検索
                return self._find_element_by_position(element, window, direction)
            else:
                self.logger.warning(f"Unknown direction: {direction}")
                return None
        except Exception as e:
            self.logger.warning(f"Failed to get {direction} element: {e}")
            return None
    
    def _find_element_by_position(self, element, window, direction):
        """相対位置（left, right, up, down）で要素を検索。"""
        rect = element.BoundingRectangle
        center_x = rect.left + rect.width() // 2
        center_y = rect.top + rect.height() // 2
        
        # ウィンドウ内の全コントロールを取得
        all_controls = []
        def collect_controls(ctrl):
            all_controls.append(ctrl)
            for child in ctrl.GetChildren():
                collect_controls(child)
        
        try:
            collect_controls(window)
        except Exception as e:
            self.logger.debug(f"Error collecting controls: {e}")
            return None
        
        # 最も近い要素をフィルタリングして検索
        candidates = []
        for ctrl in all_controls:
            if ctrl == element:
                continue
            try:
                ctrl_rect = ctrl.BoundingRectangle
                ctrl_center_x = ctrl_rect.left + ctrl_rect.width() // 2
                ctrl_center_y = ctrl_rect.top + ctrl_rect.height() // 2
                
                if direction == 'left':
                    # Left: X is less, Y overlaps
                    if ctrl_center_x < center_x and abs(ctrl_center_y - center_y) < rect.height():
                        distance = center_x - ctrl_center_x
                        candidates.append((distance, ctrl))
                elif direction == 'right':
                    # Right: X is greater, Y overlaps
                    if ctrl_center_x > center_x and abs(ctrl_center_y - center_y) < rect.height():
                        distance = ctrl_center_x - center_x
                        candidates.append((distance, ctrl))
                elif direction in ['up', 'above']:
                    # Up: Y is less, X overlaps
                    if ctrl_center_y < center_y and abs(ctrl_center_x - center_x) < rect.width():
                        distance = center_y - ctrl_center_y
                        candidates.append((distance, ctrl))
                elif direction in ['down', 'below']:
                    # Down: Y is greater, X overlaps
                    if ctrl_center_y > center_y and abs(ctrl_center_x - center_x) < rect.width():
                        distance = ctrl_center_y - center_y
                        candidates.append((distance, ctrl))
            except Exception:
                continue
        
        # 最も近い要素を返す
        if candidates:
            candidates.sort(key=lambda x: x[0])
            return candidates[0][1]
        return None
