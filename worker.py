import time
from job_queue import JobQueue
from subtitle_processor import process_video

def run_worker(sleep_interval: int = 5):
    """ワーカープロセスのメインループ
    Args:
        sleep_interval: ジョブがない場合の待機時間（秒）
    """
    job_queue = JobQueue()
    
    print("[INFO] ワーカープロセスを開始します")
    
    while True:
        try:
            # 次の待機中ジョブを取得
            job = job_queue.get_next_pending_job()
            if not job:
                time.sleep(sleep_interval)
                continue
            
            job_id = job["job_id"]
            video_id = job["video_id"]
            
            print(f"[INFO] ジョブを開始します: {job_id} (video_id: {video_id})")
            
            # ジョブを処理中に更新
            job_queue.update_job_status(job_id, "processing")
            
            # 翻訳処理を実行
            try:
                process_video(video_id)
                job_queue.update_job_status(job_id, "completed")
                print(f"[INFO] ジョブが完了しました: {job_id}")
            except Exception as e:
                error_message = str(e)
                job_queue.update_job_status(job_id, "failed", error_message)
                print(f"[ERROR] ジョブが失敗しました: {job_id}\n{error_message}")
            
        except Exception as e:
            print(f"[ERROR] ワーカープロセスでエラーが発生しました: {e}")
            time.sleep(sleep_interval)

if __name__ == "__main__":
    run_worker()
