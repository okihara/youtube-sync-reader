from flask import Flask, request, jsonify
from flask_cors import CORS
from subtitle_processor import process_video, is_already_translated, get_youtube_transcript
import re
import uuid
from typing import List, Dict
from models import db, Translation, Job
from config import Config
from flask_migrate import Migrate
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)

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
    translations = Translation.query.all()
    return [{
        'video_id': t.video_id,
        'title': t.title or '無題',
        'subtitle_count': len(t.subtitles)
    } for t in translations]

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
        if Translation.query.filter_by(video_id=video_id).first():
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
        translation = Translation.query.filter_by(video_id=video_id).first()
        if not translation:
            return jsonify({'error': '字幕が見つかりません'}), 404
            
        return jsonify(translation.subtitles)
        
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

@app.route('/api/translate', methods=['POST'])
def translate_video():
    video_id = request.json.get('video_id')
    if not video_id:
        return jsonify({'error': 'video_id is required'}), 400

    # 既に翻訳済みかチェック
    if Translation.query.filter_by(video_id=video_id).first():
        return jsonify({'status': 'completed', 'message': '既に翻訳済みです'})

    # ジョブをキューに追加
    job_id = str(uuid.uuid4())
    job = Job(id=job_id, video_id=video_id, status='pending')
    db.session.add(job)
    db.session.commit()
    
    return jsonify({
        'job_id': job_id,
        'status': 'pending',
        'message': '翻訳ジョブをキューに追加しました'
    })

@app.route('/api/job_status/<job_id>', methods=['GET'])
def get_job_status(job_id):
    job = Job.query.get(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())

@app.route('/api/jobs', methods=['GET'])
def list_jobs():
    status = request.args.get('status')
    query = Job.query
    if status:
        query = query.filter_by(status=status)
    jobs = [job.to_dict() for job in query.all()]
    return jsonify(jobs)

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/video.html')
def video():
    return app.send_static_file('video.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
