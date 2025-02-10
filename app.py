from flask import Flask, request, jsonify
from flask_cors import CORS
from trans import process_video, is_already_translated, get_youtube_transcript
import re
import glob
import json

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
        # 字幕ファイルを検索
        pattern = f"transcript_{video_id}_*.txt"
        matching_files = glob.glob(pattern)
        
        if not matching_files:
            return jsonify({'error': '字幕ファイルが見つかりません'}), 404
            
        # 最新のファイルを使用
        latest_file = max(matching_files)
        
        # ファイルを読み込む
        with open(latest_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 字幕データを解析
        sections = content.split('=== Transcript ===')
        if len(sections) != 2:
            return jsonify({'error': '字幕ファイルの形式が不正です'}), 500
            
        # タイミング情報を取得
        timing_section = sections[0].split('=== Timing Info ===')[1].strip()
        timings = json.loads(timing_section)
        
        # 字幕テキストを取得
        transcript_lines = [line.strip() for line in sections[1].strip().split('\n') if line.strip()]
        
        # タイミングと字幕を組み合わせる
        transcripts = []
        for timing, text in zip(timings, transcript_lines):
            transcripts.append({
                'start': timing['start'],
                'duration': timing['duration'],
                'text': text
            })
                
        return jsonify(transcripts)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)
