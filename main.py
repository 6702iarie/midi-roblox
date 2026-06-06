"""
MIDI Roblox Piano - メインエントリーポイント
MIDI ファイルを読み込んで Roblox のピアノをキーボード入力で演奏
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from gui.main_window import MainWindow


def setup_logging():
    """ログ設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('midi_roblox.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """メイン関数"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("MIDI Roblox Piano アプリケーション起動")
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
