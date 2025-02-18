import re
import json
import os
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import JSONFormatter
from translator import Translator, TranslationError
from dotenv import load_dotenv
from models import db, Translation
from typing import List, Dict, Optional, Tuple

# 環境変数の読み込み
load_dotenv()

def get_youtube_transcript(video_id: str) -> Optional[List[Dict]]:
    """YouTubeの字幕を取得する"""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        return transcript
    except Exception as e:
        print(f"Error getting transcript: {e}")
        return None

def clean_subtitle_text(text):
    """字幕テキストをクリーニングする"""
    # \xa0（ノーブレークスペース）を通常のスペースに変換
    text = text.replace('\xa0', ' ')
    # 改行文字を空白に変換
    text = text.replace('\n', ' ')
    # 連続する空白を1つに
    text = ' '.join(text.split())
    # 前後の空白を除去
    return text.strip()

def translate_text(texts):
    """ChatGPT APIを使用してテキストを翻訳する"""
    try:
        translator = Translator()
        return translator.translate_subtitles(texts)
    except TranslationError as e:
        print(f"翻訳に失敗しました: {str(e)}")
        return None

def is_already_translated(video_id: str) -> bool:
    """既に翻訳済みかどうかをチェックする"""
    return Translation.query.filter_by(video_id=video_id).first() is not None

def process_video(video_id: str) -> Tuple[bool, Optional[str]]:
    """動画の字幕を処理する
    
    Args:
        video_id: YouTube動画のID
        
    Returns:
        Tuple[bool, Optional[str]]: (成功したかどうか, エラーメッセージ)
    """
    try:
        # 字幕を取得
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            return False, '字幕の取得に失敗しました'

        # 翻訳処理を実行
        translated_data = translate_text(transcript)
        if not translated_data:
            return False, '翻訳処理に失敗しました'

        # 翻訳結果を保存
        translation = Translation(
            video_id=video_id,
            title=translated_data[0]['text'] if translated_data else '無題',
            subtitles=translated_data
        )
        db.session.add(translation)
        db.session.commit()

        return True, None

    except Exception as e:
        error_message = str(e)
        print(f"Error processing video: {error_message}")
        return False, error_message

if __name__ == "__main__":
    from app import app
    # YouTube動画のID
    video_id = "8Hw2-zAt-fw"
    
    with app.app_context():
        success, error = process_video(video_id)
        if success:
            print("処理が完了しました")
        else:
            print(f"エラーが発生しました: {error}")
