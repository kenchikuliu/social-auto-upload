from __future__ import annotations

import asyncio
import shutil
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


ROOT_DIR = Path(__file__).parent.resolve()
CONF_FILE = ROOT_DIR / "conf.py"
CONF_EXAMPLE_FILE = ROOT_DIR / "conf.example.py"

if not CONF_FILE.exists() and CONF_EXAMPLE_FILE.exists():
    shutil.copyfile(CONF_EXAMPLE_FILE, CONF_FILE)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from conf import BASE_DIR
from sau_cli import (
    BilibiliVideoUploadRequest,
    DouyinVideoUploadRequest,
    KuaishouVideoUploadRequest,
    TencentVideoUploadRequest,
    XiaohongshuVideoUploadRequest,
    check_bilibili_account,
    check_douyin_account,
    check_kuaishou_account,
    check_tencent_account,
    check_xiaohongshu_account,
    login_bilibili_account,
    login_douyin_account,
    login_kuaishou_account,
    login_tencent_account,
    login_xiaohongshu_account,
    parse_schedule,
    parse_tags,
    upload_bilibili_video,
    upload_kuaishou_video,
    upload_tencent_video,
    upload_video as upload_douyin_video,
    upload_xiaohongshu_video,
)


app = Flask(__name__)
CORS(app)
app.config["MAX_CONTENT_LENGTH"] = 1024 * 1024 * 1024

RUNTIME_DIR = Path(BASE_DIR)
COOKIE_DIR = RUNTIME_DIR / "cookies"
VIDEO_DIR = RUNTIME_DIR / "videoFile"
THUMBNAIL_DIR = RUNTIME_DIR / "thumbnailFile"

for directory in (COOKIE_DIR, VIDEO_DIR, THUMBNAIL_DIR):
    directory.mkdir(parents=True, exist_ok=True)


PLATFORMS: dict[str, dict[str, Any]] = {
    "douyin": {
        "key": "douyin",
        "label": "抖音",
        "video": True,
        "note": True,
        "schedule": True,
        "web_login": True,
        "status": "stable",
    },
    "kuaishou": {
        "key": "kuaishou",
        "label": "快手",
        "video": True,
        "note": True,
        "schedule": True,
        "web_login": True,
        "status": "stable",
    },
    "xiaohongshu": {
        "key": "xiaohongshu",
        "label": "小红书",
        "video": True,
        "note": True,
        "schedule": True,
        "web_login": True,
        "status": "stable",
    },
    "tencent": {
        "key": "tencent",
        "label": "视频号",
        "video": True,
        "note": False,
        "schedule": True,
        "web_login": True,
        "status": "beta",
    },
    "bilibili": {
        "key": "bilibili",
        "label": "Bilibili",
        "video": True,
        "note": False,
        "schedule": True,
        "web_login": False,
        "status": "stable",
    },
}


@dataclass(slots=True)
class Job:
    id: str
    kind: str
    status: str = "queued"
    message: str = "已排队"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    steps: list[dict[str, Any]] = field(default_factory=list)
    result: dict[str, Any] | None = None
    error: str | None = None
    qrcode: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "steps": self.steps,
            "result": self.result,
            "error": self.error,
            "qrcode": self.qrcode,
        }


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, kind: str) -> Job:
        job = Job(id=uuid.uuid4().hex, kind=kind)
        with self._lock:
            self._jobs[job.id] = job
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)

    def list_recent(self, limit: int = 50) -> list[Job]:
        with self._lock:
            jobs = sorted(self._jobs.values(), key=lambda item: item.created_at, reverse=True)
        return jobs[:limit]

    def update(self, job_id: str, **values: Any) -> None:
        with self._lock:
            job = self._jobs[job_id]
            for key, value in values.items():
                setattr(job, key, value)
            job.updated_at = time.time()

    def add_step(self, job_id: str, platform: str, status: str, message: str) -> None:
        with self._lock:
            job = self._jobs[job_id]
            job.steps.append(
                {
                    "platform": platform,
                    "status": status,
                    "message": message,
                    "time": time.time(),
                }
            )
            job.updated_at = time.time()


jobs = JobStore()


def api_ok(data: Any = None, message: str = "success", status_code: int = 200):
    return jsonify({"code": 200, "success": True, "message": message, "msg": message, "data": data}), status_code


def api_error(message: str, status_code: int = 400):
    return jsonify({"code": status_code, "success": False, "message": message, "msg": message, "data": None}), status_code


def run_async(coro):
    return asyncio.run(coro)


def start_job(job: Job, target: Callable[[str], None]) -> None:
    thread = threading.Thread(target=target, args=(job.id,), daemon=True)
    thread.start()


def normalize_platform(platform: str | None) -> str:
    key = (platform or "").strip().lower()
    aliases = {
        "channels": "tencent",
        "shipinhao": "tencent",
        "视频号": "tencent",
        "抖音": "douyin",
        "快手": "kuaishou",
        "小红书": "xiaohongshu",
        "b站": "bilibili",
    }
    key = aliases.get(key, key)
    if key not in PLATFORMS:
        raise ValueError(f"不支持的平台: {platform}")
    return key


def resolve_account_file(platform: str, account_name: str) -> Path:
    return COOKIE_DIR / f"{platform}_{account_name}.json"


def serialize_account(platform: str, path: Path) -> dict[str, Any]:
    account_name = path.stem.removeprefix(f"{platform}_")
    return {
        "platform": platform,
        "platform_label": PLATFORMS.get(platform, {}).get("label", platform),
        "account_name": account_name,
        "account_file": str(path),
        "exists": path.exists(),
        "updated_at": path.stat().st_mtime if path.exists() else None,
    }


def list_accounts() -> list[dict[str, Any]]:
    accounts: list[dict[str, Any]] = []
    for path in sorted(COOKIE_DIR.glob("*.json")):
        for platform in PLATFORMS:
            if path.stem.startswith(f"{platform}_"):
                accounts.append(serialize_account(platform, path))
                break
    return accounts


def material_dir_for_kind(kind: str) -> Path:
    return THUMBNAIL_DIR if kind == "thumbnail" else VIDEO_DIR


def serialize_material(path: Path, kind: str | None = None) -> dict[str, Any]:
    resolved_kind = kind or ("thumbnail" if path.parent == THUMBNAIL_DIR else "video")
    return {
        "id": path.name,
        "filename": path.name,
        "original_name": path.name.split("_", 1)[1] if "_" in path.name else path.name,
        "kind": resolved_kind,
        "path": str(path),
        "size": path.stat().st_size,
        "size_mb": round(path.stat().st_size / 1024 / 1024, 2),
        "updated_at": path.stat().st_mtime,
        "url": f"/api/v1/materials/{resolved_kind}/{path.name}",
    }


def list_materials() -> list[dict[str, Any]]:
    materials = [serialize_material(path, "video") for path in sorted(VIDEO_DIR.iterdir()) if path.is_file()]
    materials += [serialize_material(path, "thumbnail") for path in sorted(THUMBNAIL_DIR.iterdir()) if path.is_file()]
    materials.sort(key=lambda item: item["updated_at"], reverse=True)
    return materials


def parse_publish_schedule(raw_schedule: str | None) -> datetime | int:
    if not raw_schedule:
        return 0
    return parse_schedule(raw_schedule)


def build_upload_request(platform: str, payload: dict[str, Any], target: dict[str, Any]):
    video_path = Path(payload["video_path"])
    thumbnail_path = Path(payload["thumbnail_path"]) if payload.get("thumbnail_path") else None
    account_name = target["account_name"]
    title = payload["title"]
    description = payload.get("description", "")
    tags = payload.get("tags") or parse_tags(payload.get("raw_tags", ""))
    publish_date = parse_publish_schedule(payload.get("schedule"))
    common = {
        "account_name": account_name,
        "video_file": video_path,
        "title": title,
        "description": description,
        "tags": tags,
        "publish_date": publish_date,
    }

    if platform == "douyin":
        settings = target.get("settings") or {}
        return DouyinVideoUploadRequest(
            **common,
            thumbnail_file=thumbnail_path,
            product_link=settings.get("product_link", ""),
            product_title=settings.get("product_title", ""),
            headless=payload.get("headless", True),
            debug=payload.get("debug", True),
        )

    if platform == "kuaishou":
        return KuaishouVideoUploadRequest(
            **common,
            thumbnail_file=thumbnail_path,
            headless=payload.get("headless", True),
            debug=payload.get("debug", True),
        )

    if platform == "xiaohongshu":
        return XiaohongshuVideoUploadRequest(
            **common,
            thumbnail_file=thumbnail_path,
            headless=payload.get("headless", True),
            debug=payload.get("debug", True),
        )

    if platform == "tencent":
        settings = target.get("settings") or {}
        return TencentVideoUploadRequest(
            **common,
            thumbnail_file=thumbnail_path,
            short_title=settings.get("short_title") or None,
            category=settings.get("category") or None,
            is_draft=bool(settings.get("draft")),
            headless=payload.get("headless", True),
            debug=payload.get("debug", True),
        )

    if platform == "bilibili":
        settings = target.get("settings") or {}
        tid = settings.get("tid")
        if not tid:
            raise ValueError("Bilibili 发布必须提供分区 tid")
        return BilibiliVideoUploadRequest(**common, tid=int(tid))

    raise ValueError(f"不支持的平台: {platform}")


async def upload_for_platform(platform: str, request_object) -> Path:
    if platform == "douyin":
        return await upload_douyin_video(request_object)
    if platform == "kuaishou":
        return await upload_kuaishou_video(request_object)
    if platform == "xiaohongshu":
        return await upload_xiaohongshu_video(request_object)
    if platform == "tencent":
        return await upload_tencent_video(request_object)
    if platform == "bilibili":
        return await upload_bilibili_video(request_object)
    raise ValueError(f"不支持的平台: {platform}")


async def check_for_platform(platform: str, account_name: str) -> bool:
    if platform == "douyin":
        return await check_douyin_account(account_name)
    if platform == "kuaishou":
        return await check_kuaishou_account(account_name)
    if platform == "xiaohongshu":
        return await check_xiaohongshu_account(account_name)
    if platform == "tencent":
        return await check_tencent_account(account_name)
    if platform == "bilibili":
        return await check_bilibili_account(account_name)
    raise ValueError(f"不支持的平台: {platform}")


async def login_for_platform(platform: str, account_name: str, headless: bool) -> dict:
    if platform == "douyin":
        return await login_douyin_account(account_name, headless=headless)
    if platform == "kuaishou":
        return await login_kuaishou_account(account_name, headless=headless)
    if platform == "xiaohongshu":
        return await login_xiaohongshu_account(account_name, headless=headless)
    if platform == "tencent":
        return await login_tencent_account(account_name, headless=headless)
    if platform == "bilibili":
        return await login_bilibili_account(account_name)
    raise ValueError(f"不支持的平台: {platform}")


@app.get("/api/v1/health")
def health():
    return api_ok({"status": "ok"})


@app.get("/api/v1/platforms")
def get_platforms():
    return api_ok(list(PLATFORMS.values()))


@app.get("/api/v1/accounts")
def get_accounts():
    return api_ok(list_accounts())


@app.post("/api/v1/accounts/check")
def check_account():
    payload = request.get_json(silent=True) or {}
    try:
        platform = normalize_platform(payload.get("platform"))
        account_name = str(payload.get("account_name") or "").strip()
        if not account_name:
            return api_error("account_name 不能为空")
    except ValueError as exc:
        return api_error(str(exc))

    job = jobs.create("account-check")

    def runner(job_id: str) -> None:
        try:
            jobs.update(job_id, status="running", message=f"正在检测 {PLATFORMS[platform]['label']} 账号")
            is_valid = run_async(check_for_platform(platform, account_name))
            jobs.update(
                job_id,
                status="success" if is_valid else "failed",
                message="账号 cookie 有效" if is_valid else "账号未登录或 cookie 已失效",
                result={"valid": is_valid, "platform": platform, "account_name": account_name},
            )
        except Exception as exc:
            jobs.update(job_id, status="failed", message=str(exc), error=str(exc))

    start_job(job, runner)
    return api_ok(job.to_dict(), "account check started", 202)


@app.post("/api/v1/accounts/login")
def login_account():
    payload = request.get_json(silent=True) or {}
    try:
        platform = normalize_platform(payload.get("platform"))
        account_name = str(payload.get("account_name") or "").strip()
        if not account_name:
            return api_error("account_name 不能为空")
    except ValueError as exc:
        return api_error(str(exc))

    if not PLATFORMS[platform]["web_login"]:
        return api_error(f"{PLATFORMS[platform]['label']} 暂不支持从 Web 登录，请使用 CLI 登录")

    headless = bool(payload.get("headless", True))
    job = jobs.create("account-login")

    def runner(job_id: str) -> None:
        try:
            jobs.update(job_id, status="running", message=f"正在登录 {PLATFORMS[platform]['label']} 账号")
            result = run_async(login_for_platform(platform, account_name, headless=headless))
            success = bool(result.get("success"))
            jobs.update(
                job_id,
                status="success" if success else "failed",
                message=result.get("message") or ("登录成功" if success else "登录失败"),
                result=result,
                error=None if success else result.get("message"),
            )
        except Exception as exc:
            jobs.update(job_id, status="failed", message=str(exc), error=str(exc))

    start_job(job, runner)
    return api_ok(job.to_dict(), "login started", 202)


@app.get("/api/v1/materials")
def get_materials():
    return api_ok(list_materials())


@app.post("/api/v1/materials")
def upload_material():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return api_error("未收到文件")

    kind = request.form.get("kind", "video").strip().lower()
    if kind not in {"video", "thumbnail"}:
        return api_error("kind 只能是 video 或 thumbnail")

    filename = secure_filename(uploaded.filename)
    if not filename:
        return api_error("文件名无效")

    target_dir = material_dir_for_kind(kind)
    target_path = target_dir / f"{uuid.uuid4().hex}_{filename}"
    uploaded.save(target_path)
    return api_ok(serialize_material(target_path, kind), "uploaded", 201)


@app.get("/api/v1/materials/<kind>/<filename>")
def get_material_file(kind: str, filename: str):
    if kind not in {"video", "thumbnail"}:
        return api_error("kind 只能是 video 或 thumbnail", 404)
    return send_from_directory(material_dir_for_kind(kind), filename)


@app.post("/api/v1/publish")
def create_publish_job():
    payload = request.get_json(silent=True) or {}
    try:
        video_path = Path(payload.get("video_path") or "")
        if not video_path.is_absolute():
            video_path = VIDEO_DIR / str(payload.get("video_path") or "")
        if not video_path.exists():
            return api_error("视频文件不存在")
        payload["video_path"] = str(video_path)

        thumbnail_value = payload.get("thumbnail_path")
        if thumbnail_value:
            thumbnail_path = Path(thumbnail_value)
            if not thumbnail_path.is_absolute():
                thumbnail_path = THUMBNAIL_DIR / str(thumbnail_value)
            if not thumbnail_path.exists():
                return api_error("封面文件不存在")
            payload["thumbnail_path"] = str(thumbnail_path)

        if not str(payload.get("title") or "").strip():
            return api_error("标题不能为空")

        targets = payload.get("targets") or []
        normalized_targets = []
        for target in targets:
            platform = normalize_platform(target.get("platform"))
            account_name = str(target.get("account_name") or "").strip()
            if not account_name:
                return api_error(f"{PLATFORMS[platform]['label']} 缺少账号名称")
            normalized_targets.append({**target, "platform": platform, "account_name": account_name})
        if not normalized_targets:
            return api_error("至少选择一个发布平台")
    except ValueError as exc:
        return api_error(str(exc))

    job = jobs.create("publish")

    def runner(job_id: str) -> None:
        jobs.update(job_id, status="running", message="发布任务运行中")
        success_count = 0
        failed_count = 0

        for target in normalized_targets:
            platform = target["platform"]
            platform_label = PLATFORMS[platform]["label"]
            try:
                jobs.add_step(job_id, platform, "running", f"{platform_label} 开始发布")
                request_object = build_upload_request(platform, payload, target)
                account_file = run_async(upload_for_platform(platform, request_object))
                success_count += 1
                jobs.add_step(job_id, platform, "success", f"{platform_label} 已提交，账号文件: {account_file}")
            except Exception as exc:
                failed_count += 1
                jobs.add_step(job_id, platform, "failed", f"{platform_label} 失败: {exc}")

        status = "success" if failed_count == 0 else "partial" if success_count else "failed"
        jobs.update(
            job_id,
            status=status,
            message=f"发布完成：成功 {success_count}，失败 {failed_count}",
            result={"success_count": success_count, "failed_count": failed_count},
        )

    start_job(job, runner)
    return api_ok(job.to_dict(), "publish started", 202)


@app.get("/api/v1/jobs")
def list_jobs():
    return api_ok([job.to_dict() for job in jobs.list_recent()])


@app.get("/api/v1/jobs/<job_id>")
def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return api_error("任务不存在", 404)
    return api_ok(job.to_dict())


def main() -> None:
    app.run(host="0.0.0.0", port=5409)


if __name__ == "__main__":
    main()
