"""
MIDI ファイルパーサー
MIDI ファイルを読み込んでノート情報を抽出します
"""

import mido
from typing import List, Tuple, Dict
import logging

logger = logging.getLogger(__name__)


class MIDIParser:
    """MIDI ファイルを解析するクラス"""
    
    def __init__(self):
        self.notes = []
        self.tempo = 120
        self.ticks_per_beat = 480
        
    def load_midi(self, file_path: str) -> List[Dict]:
        """
        MIDI ファイルを読み込み、ノート情報を抽出
        
        Args:
            file_path: MIDI ファイルのパス
            
        Returns:
            ノート情報のリスト [{'note': 60, 'velocity': 100, 'time': 0.5, 'duration': 0.5}, ...]
        """
        try:
            mid = mido.MidiFile(file_path)
            self.ticks_per_beat = mid.ticks_per_beat
            
            # テンポを取得
            self.tempo = self._extract_tempo(mid)
            
            # ノート情報を抽出
            notes = self._extract_notes(mid)
            
            logger.info(f"MIDI ファイルを読み込みました: {file_path}")
            logger.info(f"テンポ: {self.tempo}, ノート数: {len(notes)}")
            
            self.notes = notes
            return notes
            
        except Exception as e:
            logger.error(f"MIDI ファイルの読み込みエラー: {e}")
            raise
    
    def _extract_tempo(self, mid: mido.MidiFile) -> int:
        """テンポを抽出 (BPM)"""
        for track in mid.tracks:
            for msg in track:
                if msg.type == 'set_tempo':
                    # マイクロ秒/ビートからBPMに変換
                    return int(60000000 / msg.tempo)
        return 120  # デフォルト値
    
    def _extract_notes(self, mid: mido.MidiFile) -> List[Dict]:
        """全トラックからノート情報を抽出"""
        notes = []
        current_time = 0
        
        for track in mid.tracks:
            current_time = 0
            note_on_dict = {}  # ノート番号をキーに、開始時刻を値に持つ辞書
            
            for msg in track:
                current_time += msg.time
                
                if msg.type == 'note_on' and msg.velocity > 0:
                    # ノート開始
                    note_on_dict[msg.note] = current_time
                    
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    # ノート終了
                    if msg.note in note_on_dict:
                        start_time = note_on_dict.pop(msg.note)
                        duration = current_time - start_time
                        
                        # 秒に変換
                        start_seconds = self._ticks_to_seconds(start_time)
                        duration_seconds = self._ticks_to_seconds(duration)
                        
                        notes.append({
                            'note': msg.note,
                            'velocity': msg.velocity if msg.type == 'note_on' else 0,
                            'time': start_seconds,
                            'duration': duration_seconds,
                            'channel': msg.channel
                        })
        
        # 時刻順にソート
        notes.sort(key=lambda x: x['time'])
        return notes
    
    def _ticks_to_seconds(self, ticks: int) -> float:
        """MIDI チックを秒に変換"""
        # マイクロ秒に変換してから秒に変換
        microseconds = (ticks / self.ticks_per_beat) * (60000000 / self.tempo)
        return microseconds / 1000000
    
    def get_note_name(self, note_number: int) -> str:
        """ノート番号をノート名に変換 (例: 60 -> C4)"""
        note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (note_number // 12) - 1
        note_name = note_names[note_number % 12]
        return f"{note_name}{octave}"
    
    def get_duration(self) -> float:
        """MIDI ファイルの総再生時間を取得（秒）"""
        if not self.notes:
            return 0
        last_note = max(self.notes, key=lambda x: x['time'] + x['duration'])
        return last_note['time'] + last_note['duration']


if __name__ == "__main__":
    # テスト用
    parser = MIDIParser()
    logging.basicConfig(level=logging.INFO)
    
    # 使用例
    # notes = parser.load_midi("example.mid")
    # print(notes)
