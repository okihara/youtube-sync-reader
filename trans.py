import re
import json
import os
import glob
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from translator import Translator, TranslationError
from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# OpenAI APIキーの設定
# openai.api_key = os.getenv('OPENAI_API_KEY')

def get_youtube_transcript(video_id):
    """YouTubeの文字起こしを取得する"""
    try:
        # まず英語の字幕を試す
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        print(transcript)
        return transcript
    except Exception as e:
        print(f"文字起こしの取得に失敗しました: {str(e)}")
        return None

def translate_text(texts):
    """ChatGPT APIを使用してテキストを翻訳する"""
    try:
        translator = Translator()
        return translator.translate_subtitles(texts)
    except TranslationError as e:
        print(f"翻訳に失敗しました: {str(e)}")
        return None

def is_already_translated(video_id):
    """指定されたvideo_idの翻訳ファイルが存在するかチェックする"""
    try:
        # ファイル名のパターンを作成
        pattern = f"transcript_{video_id}_*.txt"
        
        # 現在のディレクトリ内のファイルを検索
        matching_files = glob.glob(pattern)
        
        return len(matching_files) > 0
    except Exception as e:
        print(f"ファイルチェックに失敗しました: {str(e)}")
        return False

def process_video(video_id):
    try:
        print(f"[INFO] 動画ID {video_id} の処理を開始します")
        
        if is_already_translated(video_id):
            print(f"[INFO] 動画ID {video_id} は既に処理済みです")
            return

        # 字幕を取得
        print(f"[INFO] 字幕データの取得を開始します")
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            print("[ERROR] 字幕が見つかりませんでした")
            return

        print(f"[INFO] {len(transcript)} 件の字幕データを取得しました")
        print(f"[DEBUG] 最初の字幕: {transcript[0]}")

        # 翻訳を実行
        print("[INFO] 翻訳処理を開始します")
        translated_data = translate_text(json.dumps(transcript, ensure_ascii=False))
        if not translated_data:
            print("[ERROR] 翻訳処理に失敗しました")
            return

        print(f"[INFO] {len(translated_data)} 件の字幕を翻訳しました")
        print(f"[DEBUG] 最初の翻訳結果: {translated_data[0]}")
        
        # 結果を保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{video_id}_{timestamp}.txt"
        
        print(f"[INFO] 翻訳結果を {filename} に保存します")
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)

        print(f"[INFO] 字幕を {filename} に保存しました")

    except Exception as e:
        print(f"[ERROR] 処理に失敗しました: {str(e)}")
        import traceback
        print(f"[DEBUG] スタックトレース:\n{traceback.format_exc()}")

if __name__ == "__main__":
    # YouTube動画のID
    video_id = "8Hw2-zAt-fw"

    # 動画の文字起こしと翻訳を処理する
    process_video(video_id)
