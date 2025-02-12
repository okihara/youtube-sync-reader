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
        # 既存の英語字幕ファイルをチェック
        en_subtitle_path = f"subtitles/en_{video_id}.json"
        if os.path.exists(en_subtitle_path):
            print(f"[INFO] 既存の英語字幕を読み込みます: {en_subtitle_path}")
            with open(en_subtitle_path, "r", encoding="utf-8") as f:
                transcript = json.load(f)
                # 既存の字幕もクリーニング
                for item in transcript:
                    item['text'] = clean_subtitle_text(item['text'])
                return transcript

        # 英語字幕を取得
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['ja', 'en'])
        
        # 字幕テキストをクリーニング
        for item in transcript:
            item['text'] = clean_subtitle_text(item['text'])
        
        # 字幕を保存
        print(f"[INFO] 英語字幕を保存します: {en_subtitle_path}")
        with open(en_subtitle_path, "w", encoding="utf-8") as f:
            json.dump(transcript, f, ensure_ascii=False, indent=2)
        
        return transcript
    except Exception as e:
        print(f"文字起こしの取得に失敗しました: {str(e)}")
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

def is_already_translated(video_id):
    """指定されたvideo_idの翻訳ファイルが存在するかチェックする"""
    try:
        # 翻訳済みファイルのパターンを作成
        pattern = f"subtitles/ja_{video_id}.json"
        return os.path.exists(pattern)
    except Exception as e:
        print(f"ファイルチェックに失敗しました: {str(e)}")
        return False

def process_video(video_id):
    try:
        print(f"[INFO] 動画ID {video_id} の処理を開始します")
        
        if is_already_translated(video_id):
            print(f"[INFO] 動画ID {video_id} は既に処理済みです")
            # 翻訳済みファイルを読み込んで返す
            with open(f"subtitles/ja_{video_id}.json", "r", encoding="utf-8") as f:
                return json.load(f)

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
        translated_data = translate_text(transcript)
        if not translated_data:
            print("[ERROR] 翻訳処理に失敗しました")
            return

        print(f"[INFO] {len(translated_data)} 件の字幕を翻訳しました")
        print(f"[DEBUG] 最初の翻訳結果: {translated_data[0]}")
        
        # 翻訳結果を保存
        ja_subtitle_path = f"subtitles/ja_{video_id}.json"
        print(f"[INFO] 翻訳結果を保存します: {ja_subtitle_path}")
        with open(ja_subtitle_path, "w", encoding="utf-8") as f:
            json.dump(translated_data, f, ensure_ascii=False, indent=2)

        return translated_data

    except Exception as e:
        print(f"[ERROR] 処理に失敗しました: {str(e)}")
        import traceback
        print(f"[DEBUG] スタックトレース:\n{traceback.format_exc()}")
        return None

if __name__ == "__main__":
    # YouTube動画のID
    video_id = "8Hw2-zAt-fw"

    # 動画の文字起こしと翻訳を処理する
    process_video(video_id)
