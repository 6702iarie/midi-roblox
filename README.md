# MIDI Roblox Piano Converter 🎹

MIDI ファイルを読み込んでキーボード入力に変換し、Roblox でピアノを演奏するアプリケーションです。

## 機能 ✨

- 📁 **MIDI ファイル読み込み** - 標準的な MIDI ファイルに対応
- 🎹 **キーボード入力変換** - MIDI ノートを QWERTY キーボード入力に変換
- 🎮 **Roblox 統合** - Roblox のピアノをキーボード入力で演奏
- 🎚️ **再生速度調整** - 50% ～ 200% の再生速度に対応
- ⏱️ **タイミング調整** - ミリ秒単位のオフセット設定
- 🎵 **音声変換** - MP3/WAV → MIDI 変換（AI 使用）
- 🔗 **YouTube 対応** - YouTube から音声をダウンロードして MIDI に変換
- ⚙️ **カスタマイズ** - キーマッピングを自由に設定可能
- 🖥️ **GUI インターフェース** - PyQt5 による使いやすい UI

## インストール 📦

### 必要な環境
- Python 3.8 以上
- Windows / macOS / Linux

### セットアップ

1. リポジトリをクローン
```bash
git clone https://github.com/6702iarie/midi-roblox.git
cd midi-roblox
```

2. 依存ライブラリをインストール
```bash
pip install -r requirements.txt
```

3. 追加の依存関係（FFmpeg）
   - **Windows**: [FFmpeg 公式サイト](https://ffmpeg.org/download.html)からダウンロード、PATH に追加
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt-get install ffmpeg`

## 使用方法 🚀

### アプリケーション起動

```bash
python main.py
```

### MIDI ファイルの再生

1. **「MIDI プレイヤー」** タブを選択
2. **「MIDI ファイルを選択」** ボタンをクリック
3. MIDI ファイルを選択
4. **「再生」** ボタンをクリック

### 音声ファイルの変換

#### MP3/WAV から MIDI へ

1. **「音声変換」** タブを選択
2. 変換方法を **「MP3/WAV ファイル」** に設定
3. **「ファイルを選択」** をクリック
4. MP3 または WAV ファイルを選択
5. **「MIDI に変換」** をクリック

#### YouTube から MIDI へ

1. **「音声変換」** タブを選択
2. 変換方法を **「YouTube URL」** に変更
3. YouTube 動画の URL を入力
4. **「MIDI に変換」** をクリック

### キーマッピング設定

1. **「設定」** タブを選択
2. **「キーマッピングを編集」** をクリック
3. テーブルでノートとキーの対応関係を変更
4. **「保存」** をクリック

## キーマッピング 🎯

デフォルトのキーマッピング（Roblox Piano 対応）:

| ノート | キー | ノート | キー |
|--------|------|--------|------|
| C4 | A | C5 | X |
| C#4 | S | C#5 | C |
| D4 | D | D5 | V |
| D#4 | F | D#5 | B |
| E4 | G | E5 | N |
| F4 | H | F5 | M |
| F#4 | J | F#5 | , |
| G4 | K | G5 | . |
| G#4 | L | G#5 | / |
| A4 | ; | A5 | Q |
| A#4 | ' | A#5 | W |
| B4 | Z | B5 | E |

設定ダイアログから自由にカスタマイズできます。

## トラブルシューティング 🔧

### キーが入力されない
- 別のアプリケーションがウィンドウフォーカスを持っていないか確認
- Roblox ウィンドウがアクティブになっていることを確認

### 音声変換が遅い
- 初回実行時は AI モデルをダウンロードするため時間がかかります
- インターネット接続を確認

### YouTube ダウンロードエラー
- yt-dlp が最新版であることを確認: `pip install --upgrade yt-dlp`
- FFmpeg がインストールされていることを確認

## 設定ファイル ⚙️

### `config/key_mapping.json`
キーマッピング設定ファイル。以下のような形式：

```json
{
  "key_mapping": {
    "C4": "a",
    "C#4": "s",
    ...
  }
}
```

### `config/settings.json`
アプリケーション設定ファイル：

```json
{
  "playback_speed": 1.0,
  "timing_offset_ms": 0,
  "auto_play_on_load": false,
  "show_notes_on_screen": true,
  "note_display_duration_ms": 500,
  "key_press_duration_ms": 100
}
```

## プロジェクト構成 📁

```
midi-roblox/
├── main.py                      # メインエントリーポイント
├── requirements.txt             # 依存ライブラリ
├── README.md                    # このファイル
├── gui/
│   └── main_window.py          # メイン GUI ウィンドウ
├── midi/
│   ├── midi_parser.py          # MIDI ファイル解析
│   └── converter.py            # MIDI → キーボード変換
├── audio/
│   ├── audio_converter.py      # MP3/WAV → MIDI 変換
│   └── youtube_downloader.py   # YouTube 音声ダウンロード
└── config/
    ├── key_mapping.json        # キーマッピング設定
    └── settings.json           # アプリケーション設定
```

## ライセンス 📄

MIT License

## 参考情報 📚

- [MIRP (Midi Input for Roblox Piano)](https://github.com/search?q=mirp+roblox)
- [mido - MIDI library](https://github.com/mido/mido)
- [basic-pitch - AI MIDI transcription](https://github.com/spotify/basic-pitch)
- [yt-dlp - YouTube downloader](https://github.com/yt-dlp/yt-dlp)

## 注意事項 ⚠️

- このツールは Roblox の利用規約に違反しないように注意してください
- 著作権のある音楽の使用には十分な注意が必要です
- AI による音声変換は完璧ではない場合があります
