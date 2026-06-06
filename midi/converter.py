"""
MIDI からキーボード入力への変換
"""

import json
import os
from typing import List, Dict
import logging
from pynput.keyboard import Controller, Key
import threading
import time

logger = logging.getLogger(__name__)


class MIDIToKeyboardConverter:
    """MIDI ノートをキーボード入力に変換するクラス"""
    
    def __init__(self, key_mapping_path: str = None):
        """
        Args:
            key_mapping_path: キーマッピング JSON ファイルのパス
        """
        self.controller = Controller()
        self.key_mapping = self._load_key_mapping(key_mapping_path)
        self.is_playing = False
        self.play_thread = None
        
    def _load_key_mapping(self, mapping_path: str = None) -> Dict[str, str]:
        """キーマッピングを読み込む"""
        if mapping_path is None:
            # デフォルトパス
            mapping_path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'config', 
                'key_mapping.json'
            )
        
        try:
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"キーマッピングを読み込みました: {mapping_path}")
                return data.get('key_mapping', {})
        except Exception as e:
            logger.error(f"キーマッピング読み込みエラー: {e}")
            return {}
    
    def note_to_key(self, note_name: str) -> str:
        """
        ノート名をキーに変換
        
        Args:
            note_name: ノート名 (例: "C4", "A#5")
            
        Returns:
            キーボード入力文字列
        """
        return self.key_mapping.get(note_name, None)
    
    def press_key(self, key: str, duration: float = 0.1):
        """
        キーを押す
        
        Args:
            key: キー文字
            duration: キーを押す時間（秒）
        """
        try:
            self.controller.press(key)
            time.sleep(duration)
            self.controller.release(key)
        except Exception as e:
            logger.warning(f"キー入力エラー: {e}")
    
    def play_midi(self, notes: List[Dict], key_press_duration: float = 0.1, 
                  playback_speed: float = 1.0, timing_offset: float = 0.0):
        """
        MIDI ノートを再生（別スレッドで実行）
        
        Args:
            notes: ノート情報のリスト
            key_press_duration: キーを押す時間（秒）
            playback_speed: 再生速度 (1.0 = 通常速度)
            timing_offset: タイミングオフセット（秒）
        """
        self.is_playing = True
        self.play_thread = threading.Thread(
            target=self._play_midi_thread,
            args=(notes, key_press_duration, playback_speed, timing_offset)
        )
        self.play_thread.daemon = True
        self.play_thread.start()
    
    def _play_midi_thread(self, notes: List[Dict], key_press_duration: float,
                         playback_speed: float, timing_offset: float):
        """再生スレッド"""
        from midi.midi_parser import MIDIParser
        
        parser = MIDIParser()
        
        try:
            if not notes:
                logger.warning("再生するノートがありません")
                return
            
            # 最初のノートまで待機
            first_note_time = notes[0]['time']
            time.sleep(max(0, first_note_time / playback_speed + timing_offset))
            
            for i, note in enumerate(notes):
                if not self.is_playing:
                    break
                
                # ノート名を取得
                note_name = parser.get_note_name(note['note'])
                key = self.note_to_key(note_name)
                
                if key:
                    # 前のノートからの遅延を計算
                    if i > 0:
                        delay = (note['time'] - notes[i-1]['time']) / playback_speed
                        time.sleep(delay)
                    
                    # キーを押す
                    self.press_key(key, key_press_duration / playback_speed)
                    logger.debug(f"キー押下: {note_name} ({key})")
                else:
                    logger.warning(f"マッピングなし: {note_name}")
            
            logger.info("再生完了")
            self.is_playing = False
            
        except Exception as e:
            logger.error(f"再生エラー: {e}")
            self.is_playing = False
    
    def stop_playback(self):
        """再生を停止"""
        self.is_playing = False
        if self.play_thread:
            self.play_thread.join(timeout=1)
    
    def update_key_mapping(self, note_name: str, key: str):
        """キーマッピングを更新"""
        self.key_mapping[note_name] = key
        logger.info(f"キーマッピング更新: {note_name} -> {key}")
    
    def save_key_mapping(self, path: str = None):
        """キーマッピングを保存"""
        if path is None:
            path = os.path.join(
                os.path.dirname(__file__), 
                '..', 
                'config', 
                'key_mapping.json'
            )
        
        try:
            data = {
                "description": "Roblox Piano Key Mapping",
                "version": "1.0",
                "key_mapping": self.key_mapping
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"キーマッピングを保存しました: {path}")
        except Exception as e:
            logger.error(f"キーマッピング保存エラー: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    converter = MIDIToKeyboardConverter()
    # 使用例
    # converter.play_midi(notes)
