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
        if is_already_translated(video_id):
            print("この動画は既に処理済みです。")
            return

        # 字幕を取得
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            print("字幕が見つかりませんでした。")
            return

        # 翻訳を実行
        translated_data = translate_text(json.dumps(transcript))
        if not translated_data:
            return

        print(translated_data)
        
        # 結果を保存
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{video_id}_{timestamp}.txt"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)

        print(f"字幕を {filename} に保存しました。")

    except Exception as e:
        print(f"処理に失敗しました: {str(e)}")

if __name__ == "__main__":
    # YouTube動画のID
    video_id = "8Hw2-zAt-fw"

    # 動画の文字起こしと翻訳を処理する
    process_video(video_id)
