import time
from app import app
from models import db, Job
from subtitle_processor import process_video

def run_worker(sleep_interval: int = 5):
    """ワーカープロセスのメインループ
    Args:
        sleep_interval: ジョブがない場合の待機時間（秒）
    """
    print("[INFO] ワーカープロセスを開始します")
    
    with app.app_context():
        while True:
            try:
                # 次の待機中ジョブを取得
                job = Job.query.filter_by(status='pending').first()
                if not job:
                    time.sleep(sleep_interval)
                    continue
                
                print(f"[INFO] ジョブを開始します: {job.id} (video_id: {job.video_id})")
                
                # ジョブを処理中に更新
                job.status = "processing"
                db.session.commit()
                
                # 翻訳処理を実行
                success, error = process_video(job.video_id)
                
                # ジョブの状態を更新
                if success:
                    job.status = "completed"
                    print(f"[INFO] ジョブが完了しました: {job.id}")
                else:
                    job.status = "failed"
                    job.error = error
                    print(f"[ERROR] ジョブが失敗しました: {job.id}\n{error}")
                
                db.session.commit()
                
            except Exception as e:
                print(f"[ERROR] ワーカープロセスでエラーが発生しました: {e}")
                time.sleep(sleep_interval)

if __name__ == "__main__":
    run_worker()
