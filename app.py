from flask import Flask, request, jsonify
from flask_cors import CORS
from subtitle_processor import process_video, is_already_translated, get_youtube_transcript
import re
import glob
import json
import os
from typing import List, Dict

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

def extract_video_id(url):
    """YouTubeのURLからビデオIDを抽出する"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?]*)',
        r'youtube\.com\/embed\/([^&\n?]*)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_translated_videos() -> List[Dict]:
    """翻訳済みの動画リストを取得する"""
    videos = []
    # 翻訳済みの字幕ファイルを検索
    subtitle_files = glob.glob('subtitles/ja_*.json')
    
    for file_path in subtitle_files:
        video_id = file_path.replace('subtitles/ja_', '').replace('.json', '')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                subtitles = json.load(f)
                # 最初の字幕からタイトルとして使用
                title = subtitles[0]['text'] if subtitles else '無題'
                videos.append({
                    'video_id': video_id,
                    'title': title,
                    'subtitle_count': len(subtitles)
                })
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
            continue
    
    # 字幕数の多い順にソート
    return sorted(videos, key=lambda x: x['subtitle_count'], reverse=True)

@app.route('/api/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        url = data.get('url')
        if not url:
            return jsonify({'error': 'URLが必要です'}), 400
            
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': '有効なYouTube URLではありません'}), 400
            
        # 既に処理済みかチェック
        if is_already_translated(video_id):
            return jsonify({'message': '既に処理済みです', 'status': 'completed', 'video_id': video_id})
            
        # 字幕が利用可能かチェック
        transcript = get_youtube_transcript(video_id)
        if not transcript:
            return jsonify({'error': '字幕が利用できません'}), 400
            
        # 非同期で処理を開始
        process_video(video_id)
        
        return jsonify({
            'message': '処理を開始しました',
            'status': 'processing',
            'video_id': video_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/transcripts/<video_id>')
def get_transcripts(video_id):
    try:
        # 翻訳済み字幕ファイルのパス
        ja_subtitle_path = f"subtitles/ja_{video_id}.json"
        
        if not os.path.exists(ja_subtitle_path):
            return jsonify({'error': '字幕ファイルが見つかりません'}), 404
            
        # ファイルを読み込む
        with open(ja_subtitle_path, 'r', encoding='utf-8') as f:
            transcripts = json.load(f)
            
        return jsonify(transcripts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/videos')
def list_videos():
    """翻訳済みの動画リストを返すAPI"""
    try:
        videos = get_translated_videos()
        return jsonify(videos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/video.html')
def video():
    return app.send_static_file('video.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
