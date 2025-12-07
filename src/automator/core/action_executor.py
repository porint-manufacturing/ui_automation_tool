"""
ActionExecutor - アクション実行を担当するクラス

automator.pyのexecute_actionメソッドから抽出。
各アクションタイプを個別メソッドに分割して可読性と保守性を向上。
"""

import time
import subprocess
import datetime
import re
import uiautomation as auto
from src.automator.utils.screenshot import capture_screenshot


class ActionExecutor:
    """アクション実行を担当するクラス"""
    
    def __init__(self, logger, element_finder, focus_manager, dry_run, force_run, wait_time=None):
        """
        ActionExecutorの初期化
        
        Args:
            logger: ロガーインスタンス
            element_finder: ElementFinderインスタンス
            focus_manager: FocusManagerインスタンス
            dry_run: Dry-runモードフラグ
            force_run: Force-runモードフラグ
            wait_time: アクション後の待機時間（秒）
        """
        self.logger = logger
        self.element_finder = element_finder
        self.focus_manager = focus_manager
        self.dry_run = dry_run
        self.force_run = force_run
        self.wait_time = wait_time
    
    def execute(self, target_app, key, act_type, value, variables):
        """
        アクションを実行する
        
        Args:
            target_app: ターゲットアプリケーション名
            key: 要素を特定するキー（RPAパスまたはエイリアス）
            act_type: アクションタイプ
            value: アクションの値
            variables: 変数辞書（参照渡し）
        """
        # Launch と Wait はウィンドウ不要
        if act_type == "Launch":
            return self._execute_launch(value)
        elif act_type == "Wait":
            return self._execute_wait(value)
        elif act_type == "SetVariable":
            return self._execute_set_variable(value, variables)
        
        # Focus はウィンドウが必要だが要素は不要
        if act_type == "Focus":
            window = self.element_finder.find_window(target_app)
            if not window:
                if self.dry_run:
                    self.logger.warning(f"[Dry-run] Window '{target_app}' not found. Subsequent actions might fail.")
                    return
                raise Exception(f"Window '{target_app}' not found.")
            return self._execute_focus(window, target_app)
        
        # 以下のアクションは要素が必要
        window = self.element_finder.find_window(target_app)
        if not window:
            if self.dry_run:
                self.logger.warning(f"[Dry-run] Window '{target_app}' not found. Subsequent actions might fail.")
                return
            raise Exception(f"Window '{target_app}' not found.")
        
        element = window
        if key:
            element = self.element_finder.find_element_by_path(window, key)
            if not element:
                key_display = self.element_finder.format_path_with_alias(key)
                if self.dry_run:
                    self.logger.warning(f"[Dry-run] Element not found for key: {key_display}")
                    return
                raise Exception(f"Element not found for key: {key_display}")
            if self.dry_run:
                self.logger.info(f"[Dry-run] Element found: {element.Name} ({element.ControlTypeName})")
        
        # アクションタイプに応じて処理
        if act_type == "Click":
            return self._execute_click(element)
        elif act_type == "Input":
            return self._execute_input(element, value, key)
        elif act_type == "Invoke":
            return self._execute_invoke(element, key)
        elif act_type == "SendKeys":
            return self._execute_sendkeys(value)
        elif act_type == "Select":
            return self._execute_select(element, value)
        elif act_type == "GetProperty":
            return self._execute_get_property(element, value, variables)
        elif act_type == "Screenshot":
            return self._execute_screenshot(element, value)
        elif act_type == "FocusElement":
            return self._execute_focus_element(element, key)
        elif act_type == "GetValue":
            return self._execute_get_value(element, value, variables)
        elif act_type == "SetClipboard":
            return self._execute_set_clipboard(value)
        elif act_type == "GetClipboard":
            return self._execute_get_clipboard(value, variables)
        elif act_type == "GetDateTime":
            return self._execute_get_datetime(value, variables)
        elif act_type == "VerifyValue":
            return self._execute_verify_value(element, value)
        elif act_type == "WaitUntilVisible":
            return self._execute_wait_until_visible(window, key, value)
        elif act_type == "WaitUntilEnabled":
            return self._execute_wait_until_enabled(window, key, value)
        elif act_type == "WaitUntilGone":
            return self._execute_wait_until_gone(window, key, value)
        elif act_type == "VerifyVariable":
            return self._execute_verify_variable(key, value, variables)
        elif act_type == "Paste":
            return self._execute_paste(element)
        elif act_type == "Exit":
            return self._execute_exit(window, target_app)
        
        # Unknown action
        raise NotImplementedError(f"Action type '{act_type}' not yet implemented in ActionExecutor")

    
    def _execute_launch(self, value):
        """Launchアクション - アプリケーションを起動"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would launch: {value}")
            return
        self.logger.info(f"Launching {value}...")
        subprocess.Popen(value, shell=True)
    
    def _execute_wait(self, value):
        """Waitアクション - 指定秒数待機"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would wait: {value} seconds")
            return
        self.logger.info(f"Waiting {value} seconds...")
        time.sleep(float(value))
    
    def _execute_focus(self, window, target_app):
        """Focusアクション - ウィンドウにフォーカス"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would focus window: {target_app}")
            return
        window.SetFocus()
    
    def _execute_set_variable(self, value, variables):
        """SetVariableアクション - 変数を設定"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would set variable: {value}")
            return
        
        # Parse "var_name = expression"
        match = re.match(r"(\w+)\s*=\s*(.+)", value)
        if not match:
            raise Exception(f"Invalid SetVariable format: {value}")
        
        var_name = match.group(1)
        expression = match.group(2).strip()
        
        # Replace variables in expression
        for v, val in variables.items():
            expression = expression.replace(f"{{{v}}}", str(val))
        
        # Evaluate expression
        try:
            result = eval(expression)
            variables[var_name] = result
            self.logger.info(f"Set variable '{var_name}' to '{result}'")
        except Exception as e:
            raise Exception(f"Failed to evaluate expression '{expression}': {e}")
    
    def _execute_click(self, element):
        """Clickアクション - 要素をクリック"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would click element: {element.Name}")
            return
        
        self.logger.info(f"Clicking element '{element.Name}'...")
        
        # Try InvokePattern first, fallback to Click
        try:
            invoke = element.GetPattern(auto.PatternId.InvokePattern)
            if invoke:
                self.logger.debug("Using InvokePattern...")
                invoke.Invoke()
                if self.wait_time is not None:
                    time.sleep(self.wait_time)
            else:
                if self.wait_time is not None:
                    element.Click(waitTime=self.wait_time)
                else:
                    element.Click()
        except Exception as e:
            self.logger.warning(f"Invoke failed, falling back to Click: {e}")
            if self.wait_time is not None:
                element.Click(waitTime=self.wait_time)
            else:
                element.Click()
    
    def _execute_input(self, element, value, key):
        """Inputアクション - テキスト入力"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would input text '{value}' into element: {element.Name}")
            return
        
        self.logger.info(f"Inputting text: {value}")
        success = False
        
        # Try ValuePattern first
        try:
            pattern = element.GetPattern(auto.PatternId.ValuePattern)
            if pattern:
                self.logger.debug("Using ValuePattern.SetValue()...")
                element.SetValue(value)
                success = True
        except Exception as e:
            self.logger.debug(f"SetValue failed: {e}")
        
        if not success:
            self.logger.debug("Fallback to SendKeys...")
            # Set focus with Win32 API fallback
            key_display = self.element_finder.format_path_with_alias(key) if key else element.Name
            self.focus_manager.set_focus_with_fallback(element, key_display)
            auto.SendKeys(value)
    
    def _execute_invoke(self, element, key):
        """Invokeアクション - 要素を実行"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would invoke element: {element.Name}")
            return
        
        self.logger.info(f"Invoking element '{element.Name}'...")
        
        # Set focus with Win32 API fallback (legacy app support)
        key_display = self.element_finder.format_path_with_alias(key) if key else element.Name
        self.focus_manager.set_focus_with_fallback(element, key_display)
        
        # Proceed with invoke
        pattern = element.GetPattern(auto.PatternId.InvokePattern)
        if pattern:
            pattern.Invoke()
            if self.wait_time is not None:
                time.sleep(self.wait_time)
        else:
            # Fallback to Toggle if Invoke not supported (e.g. Checkbox)
            toggle = element.GetPattern(auto.PatternId.TogglePattern)
            if toggle:
                self.logger.info("Invoke pattern not found, using Toggle pattern...")
                toggle.Toggle()
                if self.wait_time is not None:
                    time.sleep(self.wait_time)
            else:
                raise Exception("Element does not support Invoke or Toggle pattern")
    
    def _execute_sendkeys(self, value):
        """SendKeysアクション - キー送信"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would send keys: {value}")
            return
        
        self.logger.info(f"Sending keys: {value}")
        auto.SendKeys(value)
    
    def _execute_select(self, element, value):
        """Selectアクション - 要素を選択"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would select element: {element.Name} (Value: {value})")
            return
        
        if value:
            # 値が指定されている: 要素をコンテナとして扱い、子アイテムを選択
            self.logger.info(f"Selecting item '{value}' in '{element.Name}'...")
            
            # コンボボックスの場合は先に展開を試す
            expand = element.GetPattern(auto.PatternId.ExpandCollapsePattern)
            if expand:
                try:
                    expand.Expand()
                    time.sleep(0.5)  # 展開を待機
                except:
                    pass
            
            # 子アイテムを検索
            item = element.ListItemControl(Name=value)
            if not item.Exists(maxSearchSeconds=1):
                item = element.TreeItemControl(Name=value)
            
            if not item.Exists(maxSearchSeconds=1):
                item = element.Control(Name=value, searchDepth=1)
            
            if not item.Exists(maxSearchSeconds=1):
                raise Exception(f"Item '{value}' not found in '{element.Name}'")
            
            # 可能であればスクロールして表示
            scroll = item.GetPattern(auto.PatternId.ScrollItemPattern)
            if scroll:
                scroll.ScrollIntoView()
            
            # アイテムを選択
            sel_item = item.GetPattern(auto.PatternId.SelectionItemPattern)
            if sel_item:
                sel_item.Select()
                if self.wait_time is not None:
                    time.sleep(self.wait_time)
            else:
                self.logger.warning("Item does not support SelectionItemPattern, trying Click...")
                if self.wait_time is not None:
                    item.Click(waitTime=self.wait_time)
                else:
                    item.Click()
        else:
            # 値なし: 要素自体を選択
            self.logger.info(f"Selecting element '{element.Name}'...")
            sel_item = element.GetPattern(auto.PatternId.SelectionItemPattern)
            if sel_item:
                sel_item.Select()
                if self.wait_time is not None:
                    time.sleep(self.wait_time)
            else:
                raise Exception("Element does not support SelectionItemPattern")
    
    def _execute_get_property(self, element, value, variables):
        """GetPropertyアクション - 要素のプロパティを取得"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would get property from element: {element.Name}")
            variables[value] = "[DryRunValue]"
            return
        
        # "変数名 = プロパティ名" の形式を解析
        if "=" in value:
            parts = value.split("=", 1)
            var_name = parts[0].strip()
            prop_name = parts[1].strip()
        else:
            # '='がない場合、valueを変数名とプロパティ名の両方として使用
            var_name = value
            prop_name = "Value"
        
        # element_finderを使用してプロパティ値を取得
        prop_value = self.element_finder.get_element_property(element, prop_name)
        variables[var_name] = prop_value
        
        elem_desc = element.Name or element.ControlTypeName or "element"
        self.logger.info(f"Got {prop_name} = '{prop_value}' from '{elem_desc}', stored in '{var_name}'")
    
    def _execute_screenshot(self, element, value):
        """Screenshotアクション - スクリーンショット撮影"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would take screenshot: {value}")
            return
        
        self.logger.info(f"Taking screenshot: {value}")
        capture_screenshot(value, dry_run=self.dry_run)
    
    def _execute_focus_element(self, element, key):
        """FocusElementアクション - 要素にフォーカス"""
        # 要素の説明を決定
        if element.Name:
            element_desc = element.Name
        else:
            element_desc = key if key else f"{element.ControlTypeName} (AutomationId: {element.AutomationId or 'N/A'})"
        
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would focus element: {element_desc}")
            return
        
        self.logger.info(f"Focusing element '{element_desc}'...")
        
        # Set focus with Win32 API fallback
        success = self.focus_manager.set_focus_with_fallback(element, element_desc)
        
        if success:
            self.logger.info(f"✓ Focus successfully set on '{element_desc}'")

    def _execute_get_value(self, element, value, variables):
        """GetValueアクション - 要素の値を取得して変数に格納"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would get value from element: {element.Name} and store in '{value}'")
            variables[value] = "[DryRunValue]"
            return

        val = element.Name
        try:
            pattern = element.GetPattern(auto.PatternId.ValuePattern)
            if pattern:
                val = pattern.Value
        except Exception as e:
            self.logger.warning(f"Failed to get ValuePattern: {e}")

        if not val or val == element.Name:
            try:
                pattern = element.GetPattern(auto.PatternId.TextPattern)
                if pattern:
                    val = pattern.DocumentRange.GetText(-1)
            except Exception as e:
                self.logger.warning(f"Failed to get TextPattern: {e}")
        
        self.logger.info(f"Got value: '{val}'. Storing in variable '{value}'")
        variables[value] = val

    def _execute_set_clipboard(self, value):
        """SetClipboardアクション - クリップボードに値を設定"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would set clipboard to: {value}")
            return

        text_to_copy = value.replace("{ENTER}", "\r\n")
        self.logger.info(f"Setting clipboard: {text_to_copy}")
        auto.SetClipboardText(text_to_copy)

    def _execute_get_clipboard(self, value, variables):
        """GetClipboardアクション - クリップボードの値を取得して変数に格納"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would get clipboard text and store in '{value}'")
            variables[value] = "[DryRunClipboard]"
            return

        val = auto.GetClipboardText()
        self.logger.info(f"Got clipboard text: '{val}'. Storing in variable '{value}'")
        variables[value] = val

    def _execute_get_datetime(self, value, variables):
        """GetDateTimeアクション - 現在日時を取得して変数に格納"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would get current date/time based on: {value}")
            return

        if "=" in value:
            parts = value.split("=", 1)
            var_name = parts[0].strip()
            right_side = parts[1].strip()
            
            # Check for offset (e.g. + 1, - 1)
            offset = 0
            fmt = right_side
            
            # Regex to find offset at the end: "format + 1" or "format - 5"
            match = re.search(r'^(.*)\s*([+-])\s*(\d+)$', right_side)
            if match:
                fmt = match.group(1).strip()
                op = match.group(2)
                num = int(match.group(3))
                if op == '+':
                    offset = num
                else:
                    offset = -num

            # Convert C# style format to Python strftime format
            fmt = fmt.replace("yyyy", "%Y")
            fmt = fmt.replace("MM", "%m")
            fmt = fmt.replace("dd", "%d")
            fmt = fmt.replace("HH", "%H")
            fmt = fmt.replace("mm", "%M")
            fmt = fmt.replace("ss", "%S")
            
            now = datetime.datetime.now()
            if offset != 0:
                now = now + datetime.timedelta(days=offset)
                
            formatted_date = now.strftime(fmt)
            
            if offset != 0:
                self.logger.info(f"Got date/time: '{formatted_date}' (offset: {offset:+d} days). Storing in variable '{var_name}'")
            else:
                self.logger.info(f"Got date/time: '{formatted_date}'. Storing in variable '{var_name}'")
            variables[var_name] = formatted_date
        else:
            self.logger.warning(f"Invalid GetDateTime format: {value}. Expected 'variable = format'")

    def _execute_verify_value(self, element, value):
        """VerifyValueアクション - 要素の値を検証"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would verify value of element: {element.Name} against '{value}'")
            return

        current_val = element.Name
        try:
            pattern = element.GetPattern(auto.PatternId.ValuePattern)
            if pattern and pattern.Value:
                current_val = pattern.Value
        except Exception:
            pass

        if not current_val:
            try:
                pattern = element.GetPattern(auto.PatternId.TextPattern)
                if pattern:
                    current_val = pattern.DocumentRange.GetText(-1)
            except Exception:
                pass
            
        if current_val == value:
            self.logger.info(f"Verification PASSED: Value is '{current_val}'")
        else:
            self.logger.error(f"Verification FAILED: Expected '{value}', got '{current_val}'")
            raise Exception(f"Verification failed. Expected '{value}', got '{current_val}'")

    def _execute_wait_until_visible(self, window, key, value):
        """WaitUntilVisibleアクション - 要素が表示されるまで待機"""
        timeout = float(value) if value else 10.0
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would wait until element is visible: {key} (Timeout: {timeout}s)")
            return

        self.logger.info(f"Waiting until visible: {key} (Timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                found = self.element_finder.find_element_by_path(window, key)
                if found and found.Exists(maxSearchSeconds=0):
                    self.logger.info(f"Element became visible.")
                    return
            except:
                pass
            time.sleep(0.5)
        raise Exception(f"Timeout waiting for element to be visible: {key}")

    def _execute_wait_until_enabled(self, window, key, value):
        """WaitUntilEnabledアクション - 要素が有効になるまで待機"""
        timeout = float(value) if value else 10.0
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would wait until element is enabled: {key} (Timeout: {timeout}s)")
            return

        self.logger.info(f"Waiting until enabled: {key} (Timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                found = self.element_finder.find_element_by_path(window, key)
                if found and found.Exists(maxSearchSeconds=0) and found.IsEnabled:
                    self.logger.info(f"Element became enabled.")
                    return
            except:
                pass
            time.sleep(0.5)
        raise Exception(f"Timeout waiting for element to be enabled: {key}")

    def _execute_wait_until_gone(self, window, key, value):
        """WaitUntilGoneアクション - 要素が消えるまで待機"""
        timeout = float(value) if value else 10.0
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would wait until element is gone: {key} (Timeout: {timeout}s)")
            return

        self.logger.info(f"Waiting until gone: {key} (Timeout: {timeout}s)...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                found = self.element_finder.find_element_by_path(window, key)
                if not found or not found.Exists(maxSearchSeconds=0):
                    self.logger.info(f"Element is gone.")
                    return
            except:
                # If find raises exception (e.g. parent gone), then it's gone
                self.logger.info(f"Element is gone (exception).")
                return
            time.sleep(0.5)
        raise Exception(f"Timeout waiting for element to be gone: {key}")

    def _execute_verify_variable(self, key, value, variables):
        """VerifyVariableアクション - 変数の値を検証"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would verify variable '{key}' against '{value}'")
            return

        var_name = key
        expected_val = value
        actual_val = variables.get(var_name, '')
        self.logger.info(f"Verifying variable '{var_name}': Expected='{expected_val}', Actual='{actual_val}'")
        
        expected_normalized = expected_val.replace('\\r', '\r').replace('\\n', '\n')
        actual_normalized = str(actual_val).replace('\r\n', '\n')
        expected_normalized = expected_normalized.replace('\r\n', '\n')

        if expected_normalized != actual_normalized:
             raise Exception(f"Verification failed! Expected '{expected_normalized}' but got '{actual_normalized}'")
        self.logger.info("Verification passed.")

    def _execute_paste(self, element):
        """Pasteアクション - クリップボードから貼り付け"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would paste from clipboard to element: {element.Name}")
            return

        self.logger.info("Pasting from clipboard...")
        element.SetFocus()
        time.sleep(0.5)
        auto.SendKeys('{Ctrl}v')

    def _execute_exit(self, window, target_app):
        """Exitアクション - ウィンドウを閉じる"""
        if self.dry_run:
            self.logger.info(f"[Dry-run] Would exit window: {target_app}")
            return

        self.logger.info(f"Exiting {target_app}...")
        try:
            # まずWindowPattern.Close()を試す（最もクリーンな方法）
            pattern = window.GetPattern(auto.PatternId.WindowPattern)
            if pattern:
                pattern.Close()
                self.logger.info(f"Closed {target_app} using WindowPattern.Close()")
            else:
                # フォールバック: フォーカスを設定して特定のウィンドウにAlt+F4を送信
                self.logger.info(f"WindowPattern not available, using SendKeys method")
                window.SetFocus()
                time.sleep(0.1)  # フォーカスが設定されるまで少し待機
                # auto.SendKeys()の代わりにwindow.SendKeys()を使用して特定のウィンドウに送信
                window.SendKeys('{Alt}{F4}')
                self.logger.info(f"Sent Alt+F4 to {target_app}")
        except Exception as e:
            self.logger.error(f"Failed to exit window: {e}")
