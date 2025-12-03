from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from datetime import datetime

# =========================
# 기본 설정
# =========================
app = FastAPI()

# GitHub Pages / 로컬 허용
origins = [
    "https://rkawk123.github.io",
    "https://rkawk123.github.io/",
    "http://localhost:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# 경로 설정 (data/ 아래에 모으기)
# =========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UPLOAD_DIR = os.path.join(DATA_DIR, "uploads")
LOG_FILE = os.path.join(DATA_DIR, "feedback_logs.json")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 로그 파일 초기 생성
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)


# =========================
# 헬스 체크
# =========================
@app.get("/ping")
def ping():
    return {"status": "feedback-alive"}


# =========================
# 피드백 수신 API
# =========================
@app.post("/feedback")
async def receive_feedback(
    predicted: str = Form(...),
    corrected: str = Form(...),
    image: UploadFile = File(None),
):
    """
    사용자 정정 피드백 저장용 API
    - predicted: 모델이 예측한 라벨
    - corrected: 사용자가 정정한 라벨
    - image: 사용자가 업로드한 원본 이미지 (선택)
    """

    # 1. 이미지 저장
    image_path = None
    if image is not None:
        # 파일명에 타임스탬프 붙여서 중복 방지
        safe_name = image.filename.replace(" ", "_")
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_name}"
        image_path = os.path.join(UPLOAD_DIR, filename)

        with open(image_path, "wb") as f:
            f.write(await image.read())

    # 2. JSON 로그 한 건 생성
    feedback_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "predicted": predicted,
        "corrected": corrected,
        "image_path": image_path,
    }

    # 3. 기존 로그 불러와서 append
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            if not isinstance(logs, list):
                # 혹시 파일이 깨졌을 경우 대비
                logs = []
    except Exception:
        logs = []

    logs.append(feedback_entry)

    # 4. 다시 저장
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

    return {
        "status": "success",
        "message": "피드백이 저장되었습니다.",
        "data": feedback_entry,
    }


# =========================
# (옵션) 피드백 로그 조회용 – 개발/전시 디버깅용
# =========================
@app.get("/feedback_logs")
def get_feedback_logs():
    """
    저장된 피드백 로그를 전체 조회 (전시 중 확인용)
    ※ 공개 서버라면 인증을 거는 것이 안전하지만,
       지금은 소량 데이터 확인용이라 단순 조회만 둠.
    """
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            logs = json.load(f)
            if not isinstance(logs, list):
                logs = []
    except Exception:
        logs = []

    return {"count": len(logs), "logs": logs}


# =========================
# 루트
# =========================
@app.get("/")
def home():
    return {"message": "Feedback Server Running!"}


# =========================
# 로컬 실행용
# =========================
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
