"""
オーディオファイル (MP3, WAV) を MIDI に変換
AI (basic-pitch) を使用して正確な変換を行う
"""

import os
import numpy as np
from typing import Tuple, List
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    import librosa
    import soundfile as sf
    from basic_pitch.inference import predict
    from basic_pitch import ANNOTATION_HOP_TIME
except ImportError:
    logger.warning("Required audio libraries not installed. Install with: pip install librosa basic-pitch soundfile")


class AudioConverter:
    """オーディオを MIDI に変換するクラス"""
    
    def __init__(self):
        self.sample_rate = 22050
        
    def load_audio(self, file_path: str) -> Tuple[np.ndarray, int]:
        """
        オーディオファイルを読み込む
        
        Args:
            file_path: MP3 または WAV ファイルのパス
            
        Returns:
            (オーディオデータ, サンプリングレート)
        """
        try:
            # librosa は多くのフォーマットに対応
            y, sr = librosa.load(file_path, sr=self.sample_rate, mono=True)
            logger.info(f"オーディオを読み込みました: {file_path} (SR: {sr})")
            return y, sr
        except Exception as e:
            logger.error(f"オーディオ読み込みエラー: {e}")
            raise
    
    def audio_to_midi(self, audio_path: str, output_path: str = None) -> str:
        """
        オーディオファイルを MIDI に変換
        
        Args:
            audio_path: 入力オーディオファイルのパス
            output_path: 出力 MIDI ファイルのパス（指定なしの場合は自動生成）
            
        Returns:
            生成された MIDI ファイルのパス
        """
        try:
            # オーディオを読み込む
            y, sr = self.load_audio(audio_path)
            
            logger.info("basic-pitch で音声分析中...")
            # basic-pitch で予測を行う
            model_output, midi_data, note_activations = predict(
                audio_path,
                onset_threshold=0.5,
                frame_threshold=0.3,
                minimum_note_length=27.5,  # 最小ノート長 (Hz)
                minimum_freq=27.5,  # 最小周波数
                maximum_freq=2093.0,  # 最大周波数
                melodia_trick=True,  # Melodia トリックを使用
            )
            
            # 出力パスを生成
            if output_path is None:
                base_name = Path(audio_path).stem
                output_path = f"{base_name}_converted.mid"
            
            # MIDI を保存
            midi_data.write(output_path)
            
            logger.info(f"MIDI に変換完了: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"音声変換エラー: {e}")
            raise
    
    def convert_batch(self, audio_dir: str, output_dir: str = None) -> List[str]:
        """
        ディレクトリ内の全オーディオファイルを MIDI に変換
        
        Args:
            audio_dir: オーディオファイルが含まれるディレクトリ
            output_dir: 出力ディレクトリ
            
        Returns:
            生成された MIDI ファイルのパスのリスト
        """
        if output_dir is None:
            output_dir = audio_dir
        
        os.makedirs(output_dir, exist_ok=True)
        
        audio_files = []
        for ext in ['*.mp3', '*.wav', '*.m4a', '*.ogg']:
            audio_files.extend(Path(audio_dir).glob(ext))
        
        converted_files = []
        for audio_file in audio_files:
            try:
                output_path = os.path.join(output_dir, f"{audio_file.stem}.mid")
                self.audio_to_midi(str(audio_file), output_path)
                converted_files.append(output_path)
            except Exception as e:
                logger.error(f"変換失敗 {audio_file}: {e}")
                continue
        
        return converted_files


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    converter = AudioConverter()
    # 使用例
    # midi_path = converter.audio_to_midi("input.mp3")
