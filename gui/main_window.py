"""
メイン GUI ウィンドウ
"""

import sys
import os
import json
from pathlib import Path
import logging
from typing import List, Dict

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLabel, QSlider, QSpinBox, QCheckBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QMessageBox, QComboBox, QLineEdit, QProgressBar, QListWidget, QListWidgetItem,
    QDialog, QFormLayout, QKeySequenceEdit
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtWidgets import QShortcut

from midi.midi_parser import MIDIParser
from midi.converter import MIDIToKeyboardConverter
from audio.audio_converter import AudioConverter
from audio.youtube_downloader import YouTubeDownloader

logger = logging.getLogger(__name__)


class WorkerThread(QThread):
    """バックグラウンド処理用スレッド"""
    progress_updated = pyqtSignal(str)
    task_completed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, task_type: str, **kwargs):
        super().__init__()
        self.task_type = task_type
        self.kwargs = kwargs
    
    def run(self):
        try:
            if self.task_type == "audio_to_midi":
                self._convert_audio_to_midi()
            elif self.task_type == "youtube_to_midi":
                self._download_youtube()
        except Exception as e:
            self.error_occurred.emit(str(e))
    
    def _convert_audio_to_midi(self):
        audio_path = self.kwargs.get('audio_path')
        output_path = self.kwargs.get('output_path')
        
        self.progress_updated.emit("音声を MIDI に変換中...")
        converter = AudioConverter()
        midi_path = converter.audio_to_midi(audio_path, output_path)
        self.task_completed.emit(f"変換完了: {midi_path}")
    
    def _download_youtube(self):
        url = self.kwargs.get('url')
        output_dir = self.kwargs.get('output_dir', 'downloads')
        
        self.progress_updated.emit("YouTube から音声をダウンロード中...")
        downloader = YouTubeDownloader(output_dir)
        midi_path = downloader.download_and_convert(url)
        self.task_completed.emit(f"ダウンロードと変換完了: {midi_path}")


class ShortcutSettingsDialog(QDialog):
    """ショートカット設定ダイアログ"""
    
    def __init__(self, parent=None, shortcuts=None):
        super().__init__(parent)
        self.shortcuts = shortcuts or {}
        self.setWindowTitle("ショートカット設定")
        self.setGeometry(100, 100, 400, 200)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # ショートカット設定
        self.play_pause_input = QKeySequenceEdit()
        self.play_pause_input.setKeySequence(QKeySequence(self.shortcuts.get('play_pause', 'Space')))
        form_layout.addRow("再生/停止:", self.play_pause_input)
        
        self.stop_input = QKeySequenceEdit()
        self.stop_input.setKeySequence(QKeySequence(self.shortcuts.get('stop', 'Escape')))
        form_layout.addRow("停止:", self.stop_input)
        
        layout.addLayout(form_layout)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_shortcuts)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_shortcuts(self):
        """ショートカットを保存"""
        self.shortcuts['play_pause'] = self.play_pause_input.keySequence().toString().lower()
        self.shortcuts['stop'] = self.stop_input.keySequence().toString().lower()
        self.accept()
    
    def get_shortcuts(self):
        """ショートカット設定を取得"""
        return self.shortcuts


class SettingsDialog(QDialog):
    """設定ダイアログ"""
    
    def __init__(self, parent=None, converter=None):
        super().__init__(parent)
        self.converter = converter
        self.setWindowTitle("キーマッピング設定")
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # キーマッピング表
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["ノート", "キー"])
        
        if self.converter:
            row = 0
            for note, key in sorted(self.converter.key_mapping.items()):
                self.table.insertRow(row)
                self.table.setItem(row, 0, QTableWidgetItem(note))
                key_item = QTableWidgetItem(key)
                self.table.setItem(row, 1, key_item)
                row += 1
        
        layout.addWidget(self.table)
        
        # ボタン
        button_layout = QHBoxLayout()
        
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_mapping)
        button_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("キャンセル")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def save_mapping(self):
        """キーマッピングを保存"""
        new_mapping = {}
        for row in range(self.table.rowCount()):
            note = self.table.item(row, 0).text()
            key = self.table.item(row, 1).text()
            new_mapping[note] = key
        
        if self.converter:
            self.converter.key_mapping = new_mapping
            self.converter.save_key_mapping()
            QMessageBox.information(self, "成功", "キーマッピングを保存しました")
        
        self.accept()


class MainWindow(QMainWindow):
    """メインウィンドウ"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MIDI Roblox Piano Converter")
        self.setGeometry(100, 100, 900, 700)
        
        # 初期化
        self.midi_parser = MIDIParser()
        self.converter = MIDIToKeyboardConverter()
        self.current_notes = None
        self.current_file = None
        self.shortcuts = {}
        
        # ログ設定
        logging.basicConfig(level=logging.INFO)
        
        self.init_ui()
        self.load_settings()
        self.setup_shortcuts()
    
    def init_ui(self):
        """UI を初期化"""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        layout = QVBoxLayout()
        
        # タブウィジェット
        tabs = QTabWidget()
        
        # タブ1: MIDI プレイヤー
        tab1 = self.create_midi_player_tab()
        tabs.addTab(tab1, "MIDI プレイヤー")
        
        # タブ2: 音声変換
        tab2 = self.create_audio_conversion_tab()
        tabs.addTab(tab2, "音声変換")
        
        # タブ3: 設定
        tab3 = self.create_settings_tab()
        tabs.addTab(tab3, "設定")
        
        layout.addWidget(tabs)
        main_widget.setLayout(layout)
    
    def create_midi_player_tab(self) -> QWidget:
        """MIDI プレイヤータブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # ファイル選択
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("ファイルが選択されていません")
        file_layout.addWidget(self.file_label)
        
        browse_btn = QPushButton("MIDI ファイルを選択")
        browse_btn.clicked.connect(self.load_midi_file)
        file_layout.addWidget(browse_btn)
        
        layout.addLayout(file_layout)
        
        # ノート表示
        notes_label = QLabel("ノート一覧:")
        layout.addWidget(notes_label)
        
        self.notes_table = QTableWidget()
        self.notes_table.setColumnCount(4)
        self.notes_table.setHorizontalHeaderLabels(["ノート", "キー", "時刻 (s)", "デュレーション (s)"])
        layout.addWidget(self.notes_table)
        
        # 再生コントロール
        control_layout = QHBoxLayout()
        
        self.play_btn = QPushButton("再生")
        self.play_btn.clicked.connect(self.play_midi)
        self.play_btn.setEnabled(False)
        control_layout.addWidget(self.play_btn)
        
        self.stop_btn = QPushButton("停止")
        self.stop_btn.clicked.connect(self.stop_midi)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        layout.addLayout(control_layout)
        
        # 再生速度調整
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("再生速度:"))
        
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(50)
        self.speed_slider.setMaximum(200)
        self.speed_slider.setValue(100)
        self.speed_slider.setTickPosition(QSlider.TicksBelow)
        self.speed_slider.setTickInterval(10)
        speed_layout.addWidget(self.speed_slider)
        
        self.speed_label = QLabel("100%")
        self.speed_slider.valueChanged.connect(
            lambda v: self.speed_label.setText(f"{v}%")
        )
        speed_layout.addWidget(self.speed_label)
        
        layout.addLayout(speed_layout)
        
        # タイミングオフセット
        timing_layout = QHBoxLayout()
        timing_layout.addWidget(QLabel("タイミングオフセット (ms):"))
        
        self.timing_spinbox = QSpinBox()
        self.timing_spinbox.setMinimum(-1000)
        self.timing_spinbox.setMaximum(1000)
        self.timing_spinbox.setValue(0)
        timing_layout.addWidget(self.timing_spinbox)
        
        layout.addLayout(timing_layout)
        
        # キープレス時間
        key_press_layout = QHBoxLayout()
        key_press_layout.addWidget(QLabel("キープレス時間 (ms):"))
        
        self.key_press_spinbox = QSpinBox()
        self.key_press_spinbox.setMinimum(10)
        self.key_press_spinbox.setMaximum(500)
        self.key_press_spinbox.setValue(100)
        key_press_layout.addWidget(self.key_press_spinbox)
        
        layout.addLayout(key_press_layout)
        
        # ショートカット情報表示
        shortcut_label = QLabel(
            f"ショートカット: {self.shortcuts.get('play_pause', 'Space')} - 再生/停止 | "
            f"{self.shortcuts.get('stop', 'Escape')} - 停止"
        )
        shortcut_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(shortcut_label)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_audio_conversion_tab(self) -> QWidget:
        """音声変換タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # 方法選択
        method_layout = QHBoxLayout()
        method_layout.addWidget(QLabel("変換方法:"))
        
        self.method_combo = QComboBox()
        self.method_combo.addItems(["MP3/WAV ファイル", "YouTube URL"])
        self.method_combo.currentIndexChanged.connect(self.on_method_changed)
        method_layout.addWidget(self.method_combo)
        
        layout.addLayout(method_layout)
        
        # ファイル/URL 入力
        self.input_layout = QHBoxLayout()
        
        self.file_input_btn = QPushButton("ファイルを選択")
        self.file_input_btn.clicked.connect(self.select_audio_file)
        self.input_layout.addWidget(self.file_input_btn)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube URL を入力...")
        self.url_input.setVisible(False)
        self.input_layout.addWidget(self.url_input)
        
        layout.addLayout(self.input_layout)
        
        self.input_file_label = QLabel("ファイルが選択されていません")
        layout.addWidget(self.input_file_label)
        
        # 変換ボタン
        convert_btn = QPushButton("MIDI に変換")
        convert_btn.clicked.connect(self.convert_audio)
        layout.addWidget(convert_btn)
        
        # プログレスバー
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # ステータス
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def create_settings_tab(self) -> QWidget:
        """設定タブを作成"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # キーマッピング編集
        mapping_btn = QPushButton("キーマッピングを編集")
        mapping_btn.clicked.connect(self.open_key_mapping_settings)
        layout.addWidget(mapping_btn)
        
        # ショートカット編集
        shortcut_btn = QPushButton("ショートカットを編集")
        shortcut_btn.clicked.connect(self.open_shortcut_settings)
        layout.addWidget(shortcut_btn)
        
        layout.addStretch()
        
        widget.setLayout(layout)
        return widget
    
    def load_midi_file(self):
        """MIDI ファイルを選択して読み込む"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "MIDI ファイルを選択", "", "MIDI Files (*.mid *.midi)"
        )
        
        if file_path:
            try:
                self.current_notes = self.midi_parser.load_midi(file_path)
                self.current_file = file_path
                
                # ファイル名を表示
                self.file_label.setText(Path(file_path).name)
                
                # テーブルにノートを表示
                self.display_notes()
                
                # 再生ボタンを有効化
                self.play_btn.setEnabled(True)
                
                QMessageBox.information(
                    self, "成功",
                    f"MIDI ファイルを読み込みました\n"
                    f"ノート数: {len(self.current_notes)}\n"
                    f"再生時間: {self.midi_parser.get_duration():.2f}秒"
                )
            except Exception as e:
                QMessageBox.critical(self, "エラー", f"MIDI ファイル読み込みエラー:\n{e}")
    
    def display_notes(self):
        """ノートをテーブルに表示"""
        self.notes_table.setRowCount(0)
        
        for i, note in enumerate(self.current_notes[:50]):  # 最初の50個のみ表示
            self.notes_table.insertRow(i)
            
            note_name = self.midi_parser.get_note_name(note['note'])
            key = self.converter.note_to_key(note_name)
            
            self.notes_table.setItem(i, 0, QTableWidgetItem(note_name))
            self.notes_table.setItem(i, 1, QTableWidgetItem(key or "N/A"))
            self.notes_table.setItem(i, 2, QTableWidgetItem(f"{note['time']:.3f}"))
            self.notes_table.setItem(i, 3, QTableWidgetItem(f"{note['duration']:.3f}"))
    
    def play_midi(self):
        """MIDI を再生"""
        if not self.current_notes:
            QMessageBox.warning(self, "警告", "MIDI ファイルが読み込まれていません")
            return
        
        playback_speed = self.speed_slider.value() / 100.0
        timing_offset = self.timing_spinbox.value() / 1000.0
        key_press_duration = self.key_press_spinbox.value() / 1000.0
        
        self.converter.play_midi(
            self.current_notes,
            key_press_duration=key_press_duration,
            playback_speed=playback_speed,
            timing_offset=timing_offset
        )
        
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        logger.info("MIDI 再生開始")
    
    def stop_midi(self):
        """MIDI 再生を停止"""
        self.converter.stop_playback()
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        logger.info("MIDI 再生停止")
    
    def on_method_changed(self):
        """変換方法が変更されたとき"""
        if self.method_combo.currentIndex() == 0:  # ファイル
            self.file_input_btn.setVisible(True)
            self.url_input.setVisible(False)
            self.input_file_label.setText("ファイルが選択されていません")
        else:  # YouTube
            self.file_input_btn.setVisible(False)
            self.url_input.setVisible(True)
            self.input_file_label.setText("")
    
    def select_audio_file(self):
        """オーディオファイルを選択"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, "オーディオファイルを選択", "",
            "Audio Files (*.mp3 *.wav *.m4a *.ogg)"
        )
        
        if file_path:
            self.input_file_label.setText(Path(file_path).name)
            self.current_audio_file = file_path
    
    def convert_audio(self):
        """オーディオを MIDI に変換"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        if self.method_combo.currentIndex() == 0:  # ファイル
            if not hasattr(self, 'current_audio_file'):
                QMessageBox.warning(self, "警告", "ファイルが選択されていません")
                return
            
            self.worker = WorkerThread(
                "audio_to_midi",
                audio_path=self.current_audio_file,
                output_path=None
            )
        else:  # YouTube
            url = self.url_input.text().strip()
            if not url:
                QMessageBox.warning(self, "警告", "URL を入力してください")
                return
            
            self.worker = WorkerThread(
                "youtube_to_midi",
                url=url,
                output_dir="downloads"
            )
        
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.task_completed.connect(self.on_conversion_completed)
        self.worker.error_occurred.connect(self.on_conversion_error)
        self.worker.start()
    
    def on_progress_updated(self, message: str):
        """進捗更新"""
        self.status_label.setText(message)
        self.progress_bar.setValue(self.progress_bar.value() + 10)
    
    def on_conversion_completed(self, message: str):
        """変換完了"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(message)
        QMessageBox.information(self, "成功", message)
    
    def on_conversion_error(self, error_message: str):
        """変換エラー"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"エラー: {error_message}")
        QMessageBox.critical(self, "エラー", f"変換エラー:\n{error_message}")
    
    def open_key_mapping_settings(self):
        """キーマッピング設定ダイアログを開く"""
        dialog = SettingsDialog(self, self.converter)
        dialog.exec_()
    
    def open_shortcut_settings(self):
        """ショートカット設定ダイアログを開く"""
        dialog = ShortcutSettingsDialog(self, self.shortcuts)
        if dialog.exec_():
            self.shortcuts = dialog.get_shortcuts()
            self.save_settings()
            self.setup_shortcuts()
            QMessageBox.information(self, "成功", "ショートカット設定を保存しました")
    
    def setup_shortcuts(self):
        """ショートカットキーをセットアップ"""
        play_pause_key = self.shortcuts.get('play_pause', 'Space')
        stop_key = self.shortcuts.get('stop', 'Escape')
        
        # 再生/停止ショートカット
        QShortcut(QKeySequence(play_pause_key), self, self.toggle_play_pause)
        
        # 停止ショートカット
        QShortcut(QKeySequence(stop_key), self, self.stop_midi)
        
        logger.info(f"ショートカットをセットアップ: {play_pause_key} (再生/停止), {stop_key} (停止)")
    
    def toggle_play_pause(self):
        """再生/停止を切り替え"""
        if self.play_btn.isEnabled():
            self.play_midi()
        elif self.stop_btn.isEnabled():
            self.stop_midi()
    
    def load_settings(self):
        """設定を読み込む"""
        settings_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'settings.json'
        )
        
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                self.speed_slider.setValue(int(settings.get('playback_speed', 1.0) * 100))
                self.timing_spinbox.setValue(int(settings.get('timing_offset_ms', 0)))
                self.key_press_spinbox.setValue(int(settings.get('key_press_duration_ms', 100)))
                self.shortcuts = settings.get('shortcuts', {
                    'play_pause': 'Space',
                    'stop': 'Escape'
                })
        except Exception as e:
            logger.warning(f"設定読み込みエラー: {e}")
            self.shortcuts = {
                'play_pause': 'Space',
                'stop': 'Escape'
            }
    
    def save_settings(self):
        """設定を保存"""
        settings_path = os.path.join(
            os.path.dirname(__file__), '..', 'config', 'settings.json'
        )
        
        try:
            settings = {
                'playback_speed': self.speed_slider.value() / 100.0,
                'timing_offset_ms': self.timing_spinbox.value(),
                'key_press_duration_ms': self.key_press_spinbox.value(),
                'shortcuts': self.shortcuts
            }
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
            logger.info("設定を保存しました")
        except Exception as e:
            logger.error(f"設定保存エラー: {e}")
    
    def closeEvent(self, event):
        """ウィンドウを閉じるときの処理"""
        self.save_settings()
        if self.converter.is_playing:
            self.converter.stop_playback()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
