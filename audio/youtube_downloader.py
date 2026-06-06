"""
YouTube から音声をダウンロードする
"""

import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from yt_dlp import YoutubeDL
except ImportError:
    logger.warning("yt-dlp not installed. Install with: pip install yt-dlp")


class YouTubeDownloader:
    """YouTube から音声をダウンロード"""
    
    def __init__(self, output_dir: str = "downloads"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
    
    def download_audio(self, youtube_url: str, format: str = "mp3") -> str:
        """
        YouTube 動画から音声をダウンロード
        
        Args:
            youtube_url: YouTube URL
            format: ダウンロード形式 ("mp3" または "wav")
            
        Returns:
            ダウンロードされたファイルのパス
        """
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': format,
                    'preferredquality': '192',
                }],
                'outtmpl': os.path.join(self.output_dir, '%(title)s'),
                'quiet': False,
                'no_warnings': False,
            }
            
            logger.info(f"YouTube 音声ダウンロード中: {youtube_url}")
            
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=True)
                filename = ydl.prepare_filename(info)
                base_name = os.path.splitext(filename)[0]
                output_file = f"{base_name}.{format}"
                
                logger.info(f"ダウンロード完了: {output_file}")
                return output_file
                
        except Exception as e:
            logger.error(f"YouTube ダウンロードエラー: {e}")
            raise
    
    def download_and_convert(self, youtube_url: str, output_path: str = None) -> str:
        """
        YouTube から音声をダウンロードして MIDI に変換
        
        Args:
            youtube_url: YouTube URL
            output_path: 出力 MIDI ファイルのパス
            
        Returns:
            生成された MIDI ファイルのパス
        """
        from audio.audio_converter import AudioConverter
        
        try:
            # MP3 をダウンロード
            audio_file = self.download_audio(youtube_url, format="mp3")
            
            # MIDI に変換
            converter = AudioConverter()
            midi_path = converter.audio_to_midi(audio_file, output_path)
            
            logger.info(f"YouTube → MIDI 変換完了: {midi_path}")
            return midi_path
            
        except Exception as e:
            logger.error(f"YouTube → MIDI 変換エラー: {e}")
            raise


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    downloader = YouTubeDownloader()
    # 使用例
    # audio_path = downloader.download_audio("https://www.youtube.com/watch?v=...")
