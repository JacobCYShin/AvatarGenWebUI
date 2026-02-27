"""
가상인간 TTS 웹 데모 (분리형 아키텍처)
텍스트 → TTS API → 비디오 생성 API → 결과 반환
"""
import os
import json
import uuid
import subprocess
import aiofiles
import math
import shutil
import wave
import argparse
import datetime
from pathlib import Path
from typing import Optional

import requests

from fastapi import FastAPI, Request, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# ==================== 설정 ====================
app = FastAPI(title="하나금융융합기술원 AI 아바타")

BASE_DIR = Path(__file__).resolve().parent
OUTPUTS_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
PRESETS_DIR = BASE_DIR / "presets"

OUTPUTS_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
PRESETS_DIR.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# API 설정 (환경 변수로 유연하게 관리)
TTS_API_URL = os.getenv("TTS_API_URL", "http://localhost:7009/tts")
VIDEO_API_URL = os.getenv("VIDEO_API_URL", "http://localhost:8001/synthesize")

# Dev/mock mode settings
DEV_MODE = os.getenv("DEV_MODE", "0") == "1"
MOCK_TTS = os.getenv("MOCK_TTS", "0") == "1"
MOCK_VIDEO = os.getenv("MOCK_VIDEO", "0") == "1"
USE_MOCK_TTS = DEV_MODE or MOCK_TTS
USE_MOCK_VIDEO = DEV_MODE or MOCK_VIDEO
ASSET_DIR = BASE_DIR / "asset" / "sample_video"
SAMPLE_ORIG_PATH = ASSET_DIR / "sample_orig.mp4"
SAMPLE_ALPHA_PATH = ASSET_DIR / "sample_alpha.mp4"
MASK_VIDEO_PATH = Path(os.getenv("MASK_VIDEO_PATH", str(SAMPLE_ALPHA_PATH)))
FFMPEG_TIMEOUT_SEC = int(os.getenv("FFMPEG_TIMEOUT_SEC", "300"))

# 기본 설정
DEFAULT_AVATAR_ID = "PDS_blue_smooth5_margin10_bboxshift10_v2"

# 아바타 매핑 (사용자 친화적 이름 -> 실제 폴더명)
AVATAR_MAP = {
    "편다송 아나운서(전신/파란원피스)": "PDS_blue_smooth5_margin10_bboxshift10_v2",
    # 추가 아바타는 여기에 등록
}

# 역방향 매핑 (실제 폴더명 -> 사용자 친화적 이름)
AVATAR_MAP_REVERSE = {v: k for k, v in AVATAR_MAP.items()}

# ==================== Mock helpers ====================
def _write_dummy_wav(path: Path, duration_sec: float = 1.5, sr: int = 16000) -> None:
    """Generate a short dummy WAV for dev mode."""
    samples = int(duration_sec * sr)
    amplitude = 0.2
    freq = 440.0
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytearray()
        for i in range(samples):
            value = int(32767 * amplitude * math.sin(2 * math.pi * freq * i / sr))
            frames.extend(value.to_bytes(2, byteorder="little", signed=True))
        wf.writeframes(frames)

def _write_dummy_video(path: Path, duration_sec: float = 2.0) -> None:
    """Generate a short dummy MP4 for dev mode (requires ffmpeg)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found for mock video generation")
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", f"testsrc=size=640x360:rate=25:duration={duration_sec}",
        "-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=16000",
        "-shortest",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-movflags", "+faststart",
        str(path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)



def _compose_alpha_video(
    base_path: Path,
    mask_path: Path,
    output_path: Path,
    output_format: str,
    alpha_codec: str,
) -> None:
    """Create a video with alpha using a precomputed mask."""
    if not base_path.exists():
        raise FileNotFoundError(f"Base video not found: {base_path}")
    if not mask_path.exists():
        raise FileNotFoundError(f"Mask video not found: {mask_path}")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found for alpha composition")

    filter_graph = "[1:v][0:v]scale2ref[alpha][base];[base]format=rgba[base2];[alpha]format=gray[alpha2];[base2][alpha2]alphamerge[v]"

    if output_format == "mov":
        if alpha_codec == "prores_ks":
            codec_args = ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le"]
        elif alpha_codec == "png":
            codec_args = ["-c:v", "png", "-pix_fmt", "rgba"]
        else:
            codec_args = ["-c:v", "qtrle"]
        cmd = [
            ffmpeg, "-y",
            "-i", str(base_path),
            "-i", str(mask_path),
            "-filter_complex", filter_graph,
            "-map", "[v]",
            "-map", "0:a?",
            "-shortest",
            *codec_args,
            "-c:a", "aac",
            str(output_path),
        ]
    elif output_format == "webm":
        cmd = [
            ffmpeg, "-y",
            "-i", str(base_path),
            "-i", str(mask_path),
            "-filter_complex", filter_graph,
            "-map", "[v]",
            "-map", "0:a?",
            "-shortest",
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-auto-alt-ref", "0",
            "-deadline", "good",
            "-cpu-used", "4",
            "-b:v", "0",
            "-crf", "30",
            "-c:a", "libopus",
            str(output_path),
        ]
    else:
        raise ValueError(f"Unsupported alpha output format: {output_format}")

    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_SEC)

def _compose_alpha_preview(base_path: Path, mask_path: Path, output_path: Path) -> None:
    """Create a fast preview (webm with alpha)."""
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise RuntimeError("ffmpeg not found for alpha preview")

    filter_graph = "[1:v][0:v]scale2ref[alpha][base];[base]format=rgba[base2];[alpha]format=gray[alpha2];[base2][alpha2]alphamerge[v]"
    cmd = [
        ffmpeg, "-y",
        "-i", str(base_path),
        "-i", str(mask_path),
        "-filter_complex", filter_graph,
        "-map", "[v]",
        "-map", "0:a?",
        "-shortest",
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-auto-alt-ref", "0",
        "-deadline", "realtime",
        "-cpu-used", "8",
        "-b:v", "0",
        "-crf", "40",
        "-c:a", "libopus",
        str(output_path),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_SEC)

def _probe_video_size(path: Path) -> tuple[int, int]:
    """Read video dimensions via ffprobe."""
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found for video probing")
    cmd = [
        ffprobe,
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "json",
        str(path),
    ]
    result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_SEC)
    payload = json.loads(result.stdout or "{}")
    stream = (payload.get("streams") or [{}])[0]
    width = int(stream.get("width", 0))
    height = int(stream.get("height", 0))
    if width <= 0 or height <= 0:
        raise RuntimeError("Invalid video dimensions from ffprobe")
    return width, height

def _preset_path(preset_id: str) -> Path:
    return PRESETS_DIR / f"{preset_id}.json"

def _load_preset(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def _save_preset(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def _list_presets() -> list[dict]:
    presets: list[dict] = []
    for file in PRESETS_DIR.glob("*.json"):
        if file.name == "last_used.json":
            continue
        try:
            presets.append(_load_preset(file))
        except Exception:
            continue
    presets.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return presets

def _trim_presets(limit: int = 20) -> None:
    presets = _list_presets()
    if len(presets) <= limit:
        return
    for preset in presets[limit:]:
        preset_id = preset.get("id")
        if preset_id:
            path = _preset_path(preset_id)
            if path.exists():
                path.unlink()

def _apply_runtime_config(
    dev_mode: bool | None = None,
    mock_tts: bool | None = None,
    mock_video: bool | None = None,
    mask_video_path: str | None = None,
) -> None:
    """Update runtime config after startup (CLI args)."""
    global DEV_MODE, MOCK_TTS, MOCK_VIDEO, USE_MOCK_TTS, USE_MOCK_VIDEO, MASK_VIDEO_PATH

    if dev_mode is not None:
        DEV_MODE = dev_mode
    if mock_tts is not None:
        MOCK_TTS = mock_tts
    if mock_video is not None:
        MOCK_VIDEO = mock_video

    USE_MOCK_TTS = DEV_MODE or MOCK_TTS
    USE_MOCK_VIDEO = DEV_MODE or MOCK_VIDEO

    if mask_video_path:
        MASK_VIDEO_PATH = Path(mask_video_path)
# ==================== 요청 모델 ====================
class VideoRequest(BaseModel):
    text: str
    model: str = "pds_natural"
    audio_transition_frames: int = 4
    frame_transition_frames: int = 3
    interpolation_method: str = "cosine"

class CropRequest(BaseModel):
    source_url: str
    x: int
    y: int
    width: int
    height: int
    output_width: int
    output_height: int

class PresetCrop(BaseModel):
    x: float
    y: float
    w: float
    h: float

class PresetOutput(BaseModel):
    mode: str
    value: str
    w: int
    h: int
    scale: float

class CropPresetRequest(BaseModel):
    name: str | None = None
    ratio: str
    crop: PresetCrop
    output: PresetOutput

# ==================== API 엔드포인트 ====================
@app.on_event("startup")
async def startup_event():
    """서버 시작"""
    print("="*70)
    print("[STARTUP] 하나금융융합기술원 AI 아바타 서버 시작")
    print("="*70)
    print("[INFO] 웹 서버 준비 완료")
    print(f"[INFO] 웹 인터페이스: http://localhost:8000")
    print(f"")
    print(f"[CONFIG] API 서버 설정:")
    print(f"  - TTS 서버: {TTS_API_URL}")
    print(f"  - 비디오 생성 서버: {VIDEO_API_URL}")
    print(f"")
    print(f"[HEALTH CHECK] 외부 서버 연결 확인:")
    if USE_MOCK_TTS or USE_MOCK_VIDEO:
        print("[DEV MODE] Mock servers enabled; skipping external health checks.")
        print("="*70)
        return
    
    # 헬스 체크
    try:
        tts_check = requests.get(TTS_API_URL.replace("/tts", "/"), timeout=2)
        print(f"  [OK] TTS 서버 연결 성공")
    except:
        print(f"  [FAIL] TTS 서버 연결 실패")
    
    try:
        video_check = requests.get(VIDEO_API_URL.replace("/synthesize", "/health"), timeout=2)
        print(f"  [OK] 비디오 생성 서버 연결 성공")
    except:
        print(f"  [FAIL] 비디오 생성 서버 연결 실패")
    
    print("="*70)

@app.get("/", response_class=HTMLResponse)
@app.head("/")
async def index(request: Request):
    """메인 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/avatars")
async def get_avatars():
    """사용 가능한 아바타 목록 조회"""
    return JSONResponse({
        "avatars": list(AVATAR_MAP.keys()),
        "default": AVATAR_MAP_REVERSE.get(DEFAULT_AVATAR_ID, list(AVATAR_MAP.keys())[0])
    })

@app.post("/api/tts")
async def generate_tts(
    text: str = Form(...), 
    voice_model: str = Form("natural"),
    speed: float = Form(1.0),
    pre_post_silence_sec: float = Form(3.0),
    intermittent_silence_sec: float = Form(0.6)
):
    """음성 생성 API 호출 (테스트용)"""
    try:
        if USE_MOCK_TTS:
            audio_id = str(uuid.uuid4())
            audio_path = TEMP_DIR / f"audio_{audio_id}.wav"
            _write_dummy_wav(audio_path)
            return JSONResponse({
                "success": True,
                "audio_path": str(audio_path),
                "audio_id": audio_id
            })
        # 음성 모델 매핑
        voice_model_map = {
            "natural": "pds_natural",
            "announcer": "pds_announcer",
            "default": "pds_natural"
        }
        actual_model = voice_model_map.get(voice_model, "pds_natural")
        
        # 음성 생성 서버 호출
        tts_payload = {
            "text": text,
            "sr": 16000,
            "model": actual_model,
            "pre_post_silence_sec": pre_post_silence_sec,
            "intermittent_silence_sec": intermittent_silence_sec,
            "speed": speed
        }
        
        response = requests.post(
            TTS_API_URL,
            json=tts_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            error_detail = f"음성 생성 서버 오류 (코드: {response.status_code})"
            try:
                error_detail += f" - {response.json()}"
            except:
                error_detail += f" - {response.text[:200]}"
            print(f"[ERROR] TTS 서버 오류: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
        
        # 오디오 저장
        audio_id = str(uuid.uuid4())
        audio_path = TEMP_DIR / f"audio_{audio_id}.wav"
        
        with open(audio_path, 'wb') as f:
            f.write(response.content)
        
        return JSONResponse({
            "success": True,
            "audio_path": str(audio_path),
            "audio_id": audio_id
        })
    
    except requests.exceptions.ConnectionError:
        raise HTTPException(
            status_code=503, 
            detail=f"음성 생성 서버에 연결할 수 없습니다. {TTS_API_URL.replace('/tts', '')} 에서 서버가 실행 중인지 확인하세요."
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"음성 생성 실패: {str(e)}")

@app.post("/api/generate_video")
async def generate_video_api(
    text: str = Form(...),
    voice_model: str = Form("natural"),
    speed: float = Form(1.0),
    pre_post_silence_sec: float = Form(3.0),
    intermittent_silence_sec: float = Form(0.6),
    audio_transition_frames: int = Form(4),
    frame_transition_frames: int = Form(3),
    interpolation_method: str = Form("cosine"),
    pad_start_frames: int = Form(10),
    pad_end_frames: int = Form(10),
    avatar_name: str = Form("편다송 아나운서(전신/파란원피스)"),
    output_type: str = Form("video"),
    output_variant: str = Form("mp4"),
    alpha_format: str = Form("mov"),
    alpha_codec: str = Form("qtrle")
):
    """비디오/오디오 생성 API (TTS + 비디오 생성 서버 호출)"""
    try:
        output_variant = (output_variant or "mp4").lower()
        alpha_format = (alpha_format or "mov").lower()
        alpha_codec = (alpha_codec or "qtrle").lower()
        if output_variant not in ("mp4", "alpha"):
            output_variant = "mp4"
        if alpha_format not in ("mov", "webm"):
            alpha_format = "mov"
        if alpha_codec not in ("qtrle", "prores_ks", "png"):
            alpha_codec = "qtrle"

        if output_type == "audio" and USE_MOCK_TTS:
            audio_id = str(uuid.uuid4())
            audio_output_path = OUTPUTS_DIR / f"audio_{audio_id}.wav"
            _write_dummy_wav(audio_output_path)
            audio_size = audio_output_path.stat().st_size / 1024 / 1024
            return JSONResponse({
                "success": True,
                "output_type": "audio",
                "audio_url": f"/outputs/{audio_output_path.name}",
                "audio_id": audio_id,
                "audio_size": f"{audio_size:.2f} MB"
            })

        if output_type == "video" and USE_MOCK_VIDEO:
            video_id = str(uuid.uuid4())
            base_path = SAMPLE_ORIG_PATH
            preview_url = None
            if output_variant == "alpha":
                output_ext = alpha_format
                video_path = OUTPUTS_DIR / f"video_{video_id}.{output_ext}"
                try:
                    _compose_alpha_video(base_path, MASK_VIDEO_PATH, video_path, alpha_format, alpha_codec)
                except Exception as exc:
                    raise HTTPException(status_code=500, detail=f"Mock alpha video generation failed: {exc}")
                if alpha_format == "mov":
                    preview_path = OUTPUTS_DIR / f"video_{video_id}_preview.webm"
                    try:
                        _compose_alpha_preview(base_path, MASK_VIDEO_PATH, preview_path)
                        preview_url = f"/outputs/{preview_path.name}"
                    except Exception as exc:
                        print(f"[WARNING] Mock alpha preview failed: {exc}")
                        preview_fallback = OUTPUTS_DIR / f"video_{video_id}_preview.mp4"
                        try:
                            if base_path.exists():
                                shutil.copyfile(base_path, preview_fallback)
                                preview_url = f"/outputs/{preview_fallback.name}"
                        except Exception as fallback_exc:
                            print(f"[WARNING] Mock alpha preview fallback failed: {fallback_exc}")
            else:
                video_path = OUTPUTS_DIR / f"video_{video_id}.mp4"
                try:
                    if base_path.exists():
                        shutil.copyfile(base_path, video_path)
                    else:
                        _write_dummy_video(video_path)
                except Exception as exc:
                    raise HTTPException(status_code=500, detail=f"Mock video generation failed: {exc}")
            return JSONResponse({
                "success": True,
                "output_type": "video",
                "video_url": f"/outputs/{video_path.name}",
                "preview_url": preview_url,
                "video_id": video_id,
                "avatar_name": avatar_name
            })

        voice_model_map = {
            "natural": "pds_natural",
            "announcer": "pds_announcer",
            "default": "pds_natural"
        }
        actual_model = voice_model_map.get(voice_model, "pds_natural")
        
        # 아바타 이름 -> 실제 폴더명 매핑
        avatar_id = AVATAR_MAP.get(avatar_name, DEFAULT_AVATAR_ID)
        
        # 1. TTS 생성
        print(f"[REQUEST] 텍스트: {text[:50]}..." if len(text) > 50 else f"[REQUEST] 텍스트: {text}")
        print(f"[TTS] 음성 생성 시작 | 모델: {voice_model} | 속도: {speed}x | 출력: {output_type}")
        
        tts_payload = {
            "text": text,
            "sr": 16000,
            "model": actual_model,
            "pre_post_silence_sec": pre_post_silence_sec,
            "intermittent_silence_sec": intermittent_silence_sec,
            "speed": speed
        }
        print(f"[TTS] API 호출 파라미터: model={actual_model}, speed={speed}, silence={pre_post_silence_sec}/{intermittent_silence_sec}")
        
        tts_response = requests.post(
            TTS_API_URL,
            json=tts_payload,
            timeout=60
        )
        
        if tts_response.status_code != 200:
            error_detail = f"음성 생성 서버 오류 (코드: {tts_response.status_code})"
            try:
                error_detail += f" - {tts_response.json()}"
            except:
                error_detail += f" - {tts_response.text[:200]}"
            print(f"[ERROR] TTS 서버 오류: {error_detail}")
            raise HTTPException(status_code=500, detail=error_detail)
        
        # 오디오 임시 저장
        audio_id = str(uuid.uuid4())
        audio_path = TEMP_DIR / f"audio_{audio_id}.wav"
        with open(audio_path, 'wb') as f:
            f.write(tts_response.content)
        
        print(f"[SUCCESS] 음성 생성 완료")
        
        # 오디오만 생성하는 경우
        if output_type == "audio":
            # 오디오를 outputs 폴더로 이동
            audio_output_path = OUTPUTS_DIR / f"audio_{audio_id}.wav"
            audio_path.rename(audio_output_path)
            
            # 파일 크기 계산
            audio_size = audio_output_path.stat().st_size / 1024 / 1024  # MB
            
            print(f"[SUCCESS] 오디오 생성 완료: {audio_output_path.name}")
            print(f"[INFO] 파일 크기: {audio_size:.2f} MB")
            
            return JSONResponse({
                "success": True,
                "output_type": "audio",
                "audio_url": f"/outputs/{audio_output_path.name}",
                "audio_id": audio_id,
                "audio_size": f"{audio_size:.2f} MB"
            })
        
        # 2. 비디오 생성 API 호출
        print(f"[VIDEO] 비디오 생성 시작")
        print(f"[VIDEO] 아바타: {avatar_name} ({avatar_id})")
        print(f"[VIDEO] 파라미터: audio_trans={audio_transition_frames}, frame_trans={frame_transition_frames}, pad={pad_start_frames}/{pad_end_frames}")
        
        with open(audio_path, 'rb') as f:
            files = {'audio_file': (f'audio_{audio_id}.wav', f, 'audio/wav')}
            data = {
                'avatar_id': avatar_id,
                'audio_transition_frames': audio_transition_frames,
                'frame_transition_frames': frame_transition_frames,
                'interpolation_method': interpolation_method,
                'pad_start_frames': pad_start_frames,
                'pad_end_frames': pad_end_frames,
                'fps': 25,
                'batch_size': 8
            }
            
            video_response = requests.post(
                VIDEO_API_URL,
                files=files,
                data=data,
                timeout=300,  # 5분 타임아웃
                stream=True   # 스트리밍 모드로 받기
            )
        
        if video_response.status_code != 200:
            raise HTTPException(status_code=500, detail="비디오 생성 서버 오류")
        
        # 비디오 저장 (스트리밍으로 받기)
        video_id = str(uuid.uuid4())
        temp_video_path = TEMP_DIR / f"temp_{video_id}.mp4"
        video_path = OUTPUTS_DIR / f"video_{video_id}.mp4"
        
        bytes_written = 0
        with open(temp_video_path, 'wb') as f:
            for chunk in video_response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    bytes_written += len(chunk)
        
        print(f"[SUCCESS] 비디오 파일 저장 완료: {temp_video_path.name}")
        print(f"[INFO] 파일 크기: {bytes_written / 1024 / 1024:.2f} MB")
        
        # 파일 검증
        if not temp_video_path.exists():
            raise HTTPException(status_code=500, detail="비디오 파일이 생성되지 않았습니다")
        
        if temp_video_path.stat().st_size == 0:
            raise HTTPException(status_code=500, detail="비디오 파일이 비어있습니다")
        
        # 브라우저 호환 포맷으로 재인코딩 (H.264)
        print(f"[VIDEO] 브라우저 호환 포맷으로 변환 중 (H.264)...")
        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', str(temp_video_path),
                '-c:v', 'libx264',  # H.264 코덱
                '-preset', 'fast',  # 빠른 인코딩
                '-crf', '23',  # 품질 (18-28, 낮을수록 고품질)
                '-c:a', 'aac',  # AAC 오디오
                '-b:a', '128k',  # 오디오 비트레이트
                '-movflags', '+faststart',  # 웹 스트리밍 최적화
                str(video_path)
            ]
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"[SUCCESS] 비디오 변환 완료")
            
            # 임시 파일 삭제
            if temp_video_path.exists():
                temp_video_path.unlink()
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] 비디오 변환 실패, 원본 파일 사용: {e}")
            # 변환 실패 시 원본 파일 사용
            if temp_video_path.exists():
                temp_video_path.rename(video_path)
        
        # 임시 오디오 삭제
        if audio_path.exists():
            audio_path.unlink()
        
        print(f"[SUCCESS] 비디오 생성 완료: {video_path.name}")
        
        if output_variant == "alpha":
            alpha_ext = alpha_format
            alpha_path = OUTPUTS_DIR / f"video_{video_id}.{alpha_ext}"
            try:
                _compose_alpha_video(video_path, MASK_VIDEO_PATH, alpha_path, alpha_format, alpha_codec)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Alpha video generation failed: {exc}")
            preview_url = None
            if alpha_format == "mov":
                preview_path = OUTPUTS_DIR / f"video_{video_id}_preview.webm"
                try:
                    _compose_alpha_preview(video_path, MASK_VIDEO_PATH, preview_path)
                    preview_url = f"/outputs/{preview_path.name}"
                except Exception as exc:
                    print(f"[WARNING] Alpha preview failed: {exc}")
                    preview_fallback = OUTPUTS_DIR / f"video_{video_id}_preview.mp4"
                    try:
                        if video_path.exists():
                            shutil.copyfile(video_path, preview_fallback)
                            preview_url = f"/outputs/{preview_fallback.name}"
                    except Exception as fallback_exc:
                        print(f"[WARNING] Alpha preview fallback failed: {fallback_exc}")
            return JSONResponse({
                "success": True,
                "output_type": "video",
                "video_url": f"/outputs/{alpha_path.name}",
                "preview_url": preview_url,
                "video_id": video_id,
                "avatar_name": avatar_name
            })

        return JSONResponse({
            "success": True,
            "output_type": "video",
            "video_url": f"/outputs/{video_path.name}",
            "video_id": video_id,
            "avatar_name": avatar_name
        })
    
    except requests.exceptions.ConnectionError as e:
        error_msg = str(e)
        if "7009" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail=f"음성 생성 서버에 연결할 수 없습니다. {TTS_API_URL.replace('/tts', '')} 에서 서버가 실행 중인지 확인하세요."
            )
        elif "8001" in error_msg:
            raise HTTPException(
                status_code=503, 
                detail=f"비디오 생성 서버에 연결할 수 없습니다. {VIDEO_API_URL.replace('/synthesize', '')} 에서 서버가 실행 중인지 확인하세요."
            )
        else:
            raise HTTPException(status_code=503, detail=f"서버 연결 오류: {error_msg}")
    
    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="요청 시간 초과. 비디오 생성에 시간이 오래 걸리고 있습니다. 잠시 후 다시 시도해주세요.")
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"비디오 생성 실패: {str(e)}")

@app.post("/api/crop_video")
async def crop_video(req: CropRequest):
    """Crop and scale a generated video."""
    source_url = (req.source_url or "").split("?")[0]
    if not source_url.startswith("/outputs/"):
        raise HTTPException(status_code=400, detail="Invalid source_url")

    source_rel = source_url.replace("/outputs/", "", 1)
    source_path = OUTPUTS_DIR / source_rel
    if not source_path.exists():
        raise HTTPException(status_code=404, detail="Source video not found")

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        raise HTTPException(status_code=500, detail="ffmpeg not found")

    try:
        video_w, video_h = _probe_video_size(source_path)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Video probe failed: {exc}")

    def _even(value: int) -> int:
        return max(2, value - (value % 2))

    x = max(0, min(req.x, video_w - 2))
    y = max(0, min(req.y, video_h - 2))
    w = max(2, min(req.width, video_w - x))
    h = max(2, min(req.height, video_h - y))
    out_w = max(2, req.output_width)
    out_h = max(2, req.output_height)

    ext = source_path.suffix.lower().lstrip(".")
    if ext not in ("mp4", "webm", "mov"):
        ext = "mp4"

    if ext in ("mp4", "webm"):
        x, y, w, h = map(_even, [x, y, w, h])
        out_w, out_h = map(_even, [out_w, out_h])

    output_path = OUTPUTS_DIR / f"crop_{uuid.uuid4().hex}.{ext}"
    vf = f"crop={w}:{h}:{x}:{y},scale={out_w}:{out_h}"

    if ext == "webm":
        codec_args = [
            "-c:v", "libvpx-vp9",
            "-b:v", "0",
            "-crf", "32",
            "-pix_fmt", "yuv420p",
            "-c:a", "libopus",
        ]
    elif ext == "mov":
        vf = f"{vf},format=argb"
        codec_args = [
            "-c:v", "qtrle",
            "-pix_fmt", "argb",
            "-c:a", "aac",
            "-b:a", "192k",
        ]
    else:
        codec_args = [
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "20",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
        ]

    cmd = [
        ffmpeg, "-y",
        "-i", str(source_path),
        "-vf", vf,
        "-map", "0:v:0",
        "-map", "0:a?",
        *codec_args,
        str(output_path),
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=FFMPEG_TIMEOUT_SEC)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr or ""
        tail = "\n".join(stderr.splitlines()[-12:])
        raise HTTPException(status_code=500, detail=f"Crop failed: {tail or 'ffmpeg error'}")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Crop timed out")

    return JSONResponse({
        "success": True,
        "output_url": f"/outputs/{output_path.name}",
        "output_name": output_path.name,
    })

@app.get("/api/crop_presets")
async def list_crop_presets():
    return JSONResponse({"success": True, "presets": _list_presets()})

@app.get("/api/crop_presets/recent")
async def get_recent_preset():
    path = PRESETS_DIR / "last_used.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="No recent preset")
    return JSONResponse({"success": True, "preset": _load_preset(path)})

@app.post("/api/crop_presets")
async def save_crop_preset(req: CropPresetRequest):
    preset_id = uuid.uuid4().hex
    now = datetime.datetime.utcnow().isoformat() + "Z"
    name = req.name or f"프리셋 {now[:19].replace('T', ' ')}"
    payload = {
        "id": preset_id,
        "name": name,
        "ratio": req.ratio,
        "crop": req.crop.model_dump(),
        "output": req.output.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    _save_preset(_preset_path(preset_id), payload)
    _trim_presets()
    return JSONResponse({"success": True, "preset": payload})

@app.post("/api/crop_presets/recent")
async def save_recent_preset(req: CropPresetRequest):
    now = datetime.datetime.utcnow().isoformat() + "Z"
    payload = {
        "id": "last_used",
        "name": req.name or "최근 설정",
        "ratio": req.ratio,
        "crop": req.crop.model_dump(),
        "output": req.output.model_dump(),
        "created_at": now,
        "updated_at": now,
    }
    _save_preset(PRESETS_DIR / "last_used.json", payload)
    return JSONResponse({"success": True, "preset": payload})

@app.delete("/api/crop_presets/{preset_id}")
async def delete_crop_preset(preset_id: str):
    path = _preset_path(preset_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Preset not found")
    path.unlink()
    return JSONResponse({"success": True})

@app.get("/api/crop_presets/export")
async def export_crop_presets():
    return JSONResponse({"success": True, "presets": _list_presets()})

@app.post("/api/crop_presets/import")
async def import_crop_presets(file: UploadFile | None = File(None)):
    if file:
        content = await file.read()
        payload = json.loads(content.decode("utf-8"))
    else:
        raise HTTPException(status_code=400, detail="No import file provided")

    if isinstance(payload, dict):
        presets = payload.get("presets", [])
    elif isinstance(payload, list):
        presets = payload
    else:
        raise HTTPException(status_code=400, detail="Invalid import format")

    now = datetime.datetime.utcnow().isoformat() + "Z"
    for preset in presets:
        preset_id = preset.get("id") or uuid.uuid4().hex
        preset["id"] = preset_id
        preset["updated_at"] = preset.get("updated_at") or now
        preset["created_at"] = preset.get("created_at") or now
        _save_preset(_preset_path(preset_id), preset)
    _trim_presets()
    return JSONResponse({"success": True, "count": len(presets)})

@app.get("/health")
@app.head("/health")
async def health_check():
    """헬스 체크"""
    if USE_MOCK_TTS or USE_MOCK_VIDEO:
        return {
            "status": "healthy",
            "tts_server": "mock" if USE_MOCK_TTS else "unknown",
            "video_server": "mock" if USE_MOCK_VIDEO else "unknown"
        }
    # 외부 서버 상태 확인
    tts_status = "unknown"
    video_status = "unknown"
    
    try:
        tts_check = requests.get("http://localhost:7009/", timeout=2)
        tts_status = "healthy" if tts_check.status_code == 200 else "error"
    except:
        tts_status = "offline"
    
    try:
        video_check = requests.get("http://localhost:8001/health", timeout=2)
        video_status = "healthy" if video_check.status_code == 200 else "error"
    except:
        video_status = "offline"
    
    return {
        "status": "healthy",
        "tts_server": tts_status,
        "video_server": video_status
    }

if __name__ == "__main__":
    import uvicorn
    parser = argparse.ArgumentParser(description="Web studio server")
    parser.add_argument("--dev", action="store_true", help="Enable dev mode (mock servers)")
    parser.add_argument("--mock-tts", action="store_true", help="Mock TTS calls only")
    parser.add_argument("--mock-video", action="store_true", help="Mock video generation only")
    parser.add_argument("--mask-video", default=None, help="Override mask video path")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host")
    parser.add_argument("--port", type=int, default=8000, help="Bind port")
    args = parser.parse_args()

    _apply_runtime_config(
        dev_mode=args.dev,
        mock_tts=args.mock_tts,
        mock_video=args.mock_video,
        mask_video_path=args.mask_video,
    )

    uvicorn.run(app, host=args.host, port=args.port)

