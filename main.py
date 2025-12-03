from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import json
import os
from datetime import datetime

app = FastAPI()

# ✅ GitHub Pages 도메인만 허용 (추천)
origins = [
    "https://rkawk123.github.io",
    "http://localhost:5500",   # 로컬 테스트용 (필요시)
]

# CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 필요하면 도메인 제한 가능
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 업로드 폴더 생성
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

LOG_FILE = "feedback_logs.json"

# 로그 파일 초기 생성
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump([], f, ensure_ascii=False, indent=4)


@app.post("/feedback")
async def receive_feedback(
    predicted: str = Form(...),
    corrected: str = Form(...),
    image: UploadFile = File(None)
):
    """
    사용자 정정 피드백을 저장하는 API
    predicted: 모델이 예측한 라벨
    corrected: 사용자가 정정한 라벨
    image: 사용자가 업로드한 원본 이미지
    """

    # 1. 이미지 저장
    image_path = None
    if image:
        filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{image.filename}"
        image_path = os.path.join(UPLOAD_DIR, filename)

        with open(image_path, "wb") as f:
            f.write(await image.read())

    # 2. JSON 로그 저장
    feedback_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "predicted": predicted,
        "corrected": corrected,
        "image_path": image_path,
    }

    # 현재 로그 불러오기
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = json.load(f)

    logs.append(feedback_entry)

    # 저장
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=4)

    return {
        "status": "success",
        "message": "피드백이 저장되었습니다.",
        "data": feedback_entry
    }


@app.get("/")
def home():
    return {"message": "Feedback Server Running!"}
