import os
import json
import time
from datetime import datetime
from typing import Dict, Optional, List
import uuid

class JobQueue:
    def __init__(self, base_dir: str = "jobs"):
        """ジョブキューの初期化
        Args:
            base_dir: ジョブ情報を保存するディレクトリ
        """
        self.base_dir = base_dir
        self._ensure_directories()

    def _ensure_directories(self):
        """必要なディレクトリを作成"""
        for dir_name in ["pending", "processing", "completed", "failed"]:
            os.makedirs(os.path.join(self.base_dir, dir_name), exist_ok=True)

    def _generate_job_id(self) -> str:
        """一意のジョブIDを生成"""
        return str(uuid.uuid4())

    def enqueue(self, video_id: str) -> str:
        """新しいジョブをキューに追加
        Args:
            video_id: 翻訳対象の動画ID
        Returns:
            job_id: 生成されたジョブID
        """
        job_id = self._generate_job_id()
        job_data = {
            "job_id": job_id,
            "video_id": video_id,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        job_path = os.path.join(self.base_dir, "pending", f"{job_id}.json")
        with open(job_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)
        
        return job_id

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """ジョブの状態を取得
        Args:
            job_id: ジョブID
        Returns:
            job_data: ジョブ情報（存在しない場合はNone）
        """
        for status in ["pending", "processing", "completed", "failed"]:
            job_path = os.path.join(self.base_dir, status, f"{job_id}.json")
            if os.path.exists(job_path):
                with open(job_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        return None

    def get_next_pending_job(self) -> Optional[Dict]:
        """次の待機中ジョブを取得"""
        pending_dir = os.path.join(self.base_dir, "pending")
        pending_jobs = sorted(os.listdir(pending_dir))
        
        for job_file in pending_jobs:
            if not job_file.endswith(".json"):
                continue
                
            job_path = os.path.join(pending_dir, job_file)
            with open(job_path, "r", encoding="utf-8") as f:
                return json.load(f)
        
        return None

    def update_job_status(self, job_id: str, new_status: str, error: Optional[str] = None) -> None:
        """ジョブの状態を更新
        Args:
            job_id: ジョブID
            new_status: 新しい状態（processing/completed/failed）
            error: エラーメッセージ（失敗時）
        """
        # 現在のジョブ情報を取得
        job_data = self.get_job_status(job_id)
        if not job_data:
            raise ValueError(f"Job not found: {job_id}")

        # 古いファイルを削除
        old_status = job_data["status"]
        old_path = os.path.join(self.base_dir, old_status, f"{job_id}.json")
        if os.path.exists(old_path):
            os.remove(old_path)

        # ジョブ情報を更新
        job_data["status"] = new_status
        job_data["updated_at"] = datetime.now().isoformat()
        if error:
            job_data["error"] = error

        # 新しいファイルを作成
        new_path = os.path.join(self.base_dir, new_status, f"{job_id}.json")
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, ensure_ascii=False, indent=2)

    def list_jobs(self, status: Optional[str] = None) -> List[Dict]:
        """ジョブ一覧を取得
        Args:
            status: 取得するジョブの状態（指定しない場合は全て）
        Returns:
            jobs: ジョブ情報のリスト
        """
        jobs = []
        statuses = [status] if status else ["pending", "processing", "completed", "failed"]
        
        for job_status in statuses:
            status_dir = os.path.join(self.base_dir, job_status)
            if not os.path.exists(status_dir):
                continue
                
            for job_file in os.listdir(status_dir):
                if not job_file.endswith(".json"):
                    continue
                    
                job_path = os.path.join(status_dir, job_file)
                with open(job_path, "r", encoding="utf-8") as f:
                    jobs.append(json.load(f))
        
        return sorted(jobs, key=lambda x: x["created_at"], reverse=True)
