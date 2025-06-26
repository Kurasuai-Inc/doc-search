"""doc-search TUIメインモジュール

Textualフレームワークを使用した星座的デザインのUI実装
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import Header, Footer, Input, Static, Label, Button
from textual.binding import Binding
from textual import events
from rich.text import Text
from rich.panel import Panel
import asyncio
from typing import Optional, List, Dict, Any


class StarryBackground(Static):
    """星空背景のアニメーション"""
    
    def __init__(self) -> None:
        super().__init__()
        self.stars = ["✨", "⭐", "🌟", "💫", "✦", "✧"]
        self.frame = 0
        
    def on_mount(self) -> None:
        """マウント時にアニメーション開始"""
        self.set_interval(0.5, self.animate_stars)
        
    def animate_stars(self) -> None:
        """星のアニメーション更新"""
        self.frame += 1
        # TODO: 星空アニメーション実装


class SearchInput(Input):
    """検索入力フィールド"""
    
    def __init__(self) -> None:
        super().__init__(
            placeholder="🔍 検索キーワードを入力...",
            id="search-input"
        )


class SearchResult(Static):
    """検索結果アイテム"""
    
    def __init__(self, file_path: str, line_number: int, content: str, score: int = 5) -> None:
        super().__init__()
        self.file_path = file_path
        self.line_number = line_number
        self.content = content
        self.score = score
        
    def render(self) -> Panel:
        """検索結果を星評価付きで表示"""
        stars = "★" * self.score + "☆" * (5 - self.score)
        
        content = Text()
        content.append(f"📄 {self.file_path}", style="bold cyan")
        content.append(f"  {stars}\n", style="yellow")
        content.append(f"  L{self.line_number}: ", style="dim")
        content.append(self.content.strip(), style="white")
        
        return Panel(content, border_style="blue")


class SearchResultsContainer(ScrollableContainer):
    """検索結果を表示するスクロール可能なコンテナ"""
    
    def __init__(self) -> None:
        super().__init__(id="results-container")
        self.results: List[SearchResult] = []
        
    def add_result(self, result: SearchResult) -> None:
        """検索結果を追加"""
        self.results.append(result)
        self.mount(result)
        
    def clear_results(self) -> None:
        """検索結果をクリア"""
        for widget in self.results:
            widget.remove()
        self.results.clear()


class StatusBar(Static):
    """ステータスバー"""
    
    def __init__(self) -> None:
        super().__init__(id="status-bar")
        self.status = "Ready"
        self.speed = "0.00s"
        self.files = 0
        self.matches = 0
        
    def render(self) -> str:
        """ステータス情報を表示"""
        return (
            f"💫 Status: {self.status} | "
            f"🚀 Speed: {self.speed} | "
            f"📊 Files: {self.files} | "
            f"🎯 Matches: {self.matches}"
        )
        
    def update_status(self, status: str = None, speed: str = None, 
                     files: int = None, matches: int = None) -> None:
        """ステータスを更新"""
        if status is not None:
            self.status = status
        if speed is not None:
            self.speed = speed
        if files is not None:
            self.files = files
        if matches is not None:
            self.matches = matches
        self.refresh()


class DocSearchApp(App):
    """doc-search メインアプリケーション"""
    
    CSS = """
    Screen {
        background: #0a0e27;
    }
    
    #search-input {
        dock: top;
        height: 3;
        margin: 1;
        background: #1a1e37;
        border: solid #00bfff;
    }
    
    #results-container {
        height: 100%;
        background: #0a0e27;
        padding: 1;
    }
    
    SearchResult {
        margin: 0 0 1 0;
    }
    
    #status-bar {
        dock: bottom;
        height: 1;
        background: #1a1e37;
        color: #ffd700;
        text-align: center;
    }
    
    Header {
        background: #1a1e37;
        color: #ffd700;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "終了"),
        Binding("ctrl+c", "quit", "終了"),
        Binding("/", "focus_search", "検索"),
        Binding("ctrl+r", "toggle_regex", "正規表現"),
        Binding("f1", "help", "ヘルプ"),
    ]
    
    def __init__(self) -> None:
        super().__init__()
        self.title = "⭐ doc-search - 検索の星座 v0.1.0"
        self.search_input: Optional[SearchInput] = None
        self.results_container: Optional[SearchResultsContainer] = None
        self.status_bar: Optional[StatusBar] = None
        
    def compose(self) -> ComposeResult:
        """UIコンポーネントを構成"""
        yield Header()
        yield SearchInput()
        yield SearchResultsContainer()
        yield StatusBar()
        yield Footer()
        
    def on_mount(self) -> None:
        """アプリケーションマウント時の初期化"""
        self.search_input = self.query_one(SearchInput)
        self.results_container = self.query_one(SearchResultsContainer)
        self.status_bar = self.query_one(StatusBar)
        
        # 起動時アニメーション
        self.show_startup_animation()
        
    def show_startup_animation(self) -> None:
        """起動時の星座アニメーション"""
        # TODO: 起動アニメーション実装
        pass
        
    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """検索実行"""
        query = event.value
        if not query:
            return
            
        # ステータス更新
        self.status_bar.update_status(status="Searching...")
        
        # 検索結果をクリア
        self.results_container.clear_results()
        
        # TODO: 実際の検索処理を実装
        # 仮の検索結果を表示
        await self.perform_search(query)
        
    async def perform_search(self, query: str) -> None:
        """検索を実行（仮実装）"""
        # TODO: ripgrep統合後に実装
        # 仮のデータで動作確認
        import time
        start_time = time.time()
        
        # 仮の検索結果
        dummy_results = [
            ("docs/README.md", 23, f"This is the matched {query} in context...", 5),
            ("src/main.py", 102, f"def search_{query}(text):", 4),
            ("tests/test_search.py", 45, f"# Test for {query} functionality", 3),
        ]
        
        for file_path, line_num, content, score in dummy_results:
            result = SearchResult(file_path, line_num, content, score)
            self.results_container.add_result(result)
            await asyncio.sleep(0.1)  # アニメーション効果
            
        # ステータス更新
        elapsed = time.time() - start_time
        self.status_bar.update_status(
            status="Ready",
            speed=f"{elapsed:.2f}s",
            files=523,  # 仮の値
            matches=len(dummy_results)
        )
        
    def action_focus_search(self) -> None:
        """検索フィールドにフォーカス"""
        self.search_input.focus()
        
    def action_toggle_regex(self) -> None:
        """正規表現モード切り替え"""
        # TODO: 正規表現モード実装
        self.notify("正規表現モード: 未実装", severity="warning")
        
    def action_help(self) -> None:
        """ヘルプ表示"""
        # TODO: ヘルプ画面実装
        self.notify("ヘルプ: 未実装", severity="information")


def main():
    """メインエントリーポイント"""
    app = DocSearchApp()
    app.run()


if __name__ == "__main__":
    main()