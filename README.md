# scoreforge-runpod-basic-pitch

Spotify의 Basic-Pitch 모델을 사용한 오디오→MIDI 변환 RunPod Serverless 워커

## 배포 방법

### RunPod GitHub 연동 (권장)

1. [RunPod Console](https://www.runpod.io/console/serverless) 접속
2. "New Endpoint" → "GitHub Repo" 선택
3. `modootoday/scoreforge-runpod-basic-pitch` 레포 연결
4. GPU 타입: **CPU** 선택 (GPU 불필요)
5. 배포 완료 후 Endpoint URL 복사

### Docker Hub 사용

```bash
docker build -t your-username/scoreforge-runpod-basic-pitch:latest .
docker push your-username/scoreforge-runpod-basic-pitch:latest
```

RunPod에서 이미지 URL 입력: `your-username/scoreforge-runpod-basic-pitch:latest`

## API

### 요청

```json
{
  "input": {
    "audio_url": "https://example.com/audio.mp3",
    "onset_threshold": 0.5,
    "frame_threshold": 0.3,
    "minimum_note_length": 58
  }
}
```

| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `audio_url` | string | (필수) | 오디오 파일 URL |
| `onset_threshold` | float | 0.5 | 음 시작 감지 임계값 (0.0-1.0) |
| `frame_threshold` | float | 0.3 | 프레임 감지 임계값 (0.0-1.0) |
| `minimum_note_length` | int | 58 | 최소 음 길이 (ms) |

### 응답

```json
{
  "notes": [
    {
      "pitch": 60,
      "startTime": 0.5,
      "duration": 0.25,
      "velocity": 80
    }
  ],
  "note_count": 150
}
```

## 로컬 테스트

```bash
pip install -r requirements.txt
python handler.py
```

## 라이선스

MIT License
