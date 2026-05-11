# demo-day-2 — 별빛탐구 (Starlight Explorer)

위치·시간 기반 밤하늘 관측 학습 LangGraph 에이전트.

## 전체 흐름

```mermaid
flowchart LR
    START([START]) --> check_weather --> evaluate_observation --> list_visible_objects --> generate_learning_content --> generate_quiz --> build_final_answer --> save_learning_log --> END([END])
```

## 실행

```bash
uv sync
cp .env.example .env  # API 키 선택 설정
# 날짜·시간 생략 → 관측지(위경도) 타임존 기준 현재 시각으로 천체 위치 계산
uv run python main.py --lat 37.5665 --lon 126.9780
# 특정 밤을 지정하려면 (예: 저녁 9시)
uv run python main.py --date 2026-05-11 --time 21:00 --lat 37.5665 --lon 126.9780
```

`--date` / `--time` 규칙: 둘 다 생략하면 **지금**; `--date`만 주면 그날 **21:00** 로컬; `--time`만 주면 **오늘** 그 시각.

환경 변수: **`OPENAI_API_KEY` 필수**(학습 콘텐츠·퀴즈), **`OPENWEATHER_API_KEY` 권장**(OpenWeather Current — **호출 시점의 현재** 날씨; 무료 티어는 과거 시각 조회 없음). 키가 없거나 API 실패 시 날씨 분기는 생략되고 천체 목록은 기본 추천으로 진행되며 `pipeline_error`에 메시지가 쌓입니다.

### 가시 천체 데이터 소스

| 구분 | 소스 |
|------|------|
| 달·행성 | **AstronomyAPI** (`ASTRONOMY_API_APPLICATION_ID` / `SECRET` 설정 시, HTTPS). 미설정 시 **Skyfield + NASA DE421**으로 동일 역할을 로컬 계산. |
| 별자리(대표 별) | **VizieR Hipparcos** (`I/239/hip_main`) — `astroquery`로 HIP만 조회해 RA/Dec를 가져옴. 코드에 좌표를 박지 않음. |
| 지평선·방위 | **Skyfield**로 관측지 기준 alt/az 계산(별 데이터는 VizieR, 역학 파일은 DE421). |

첫 실행 시 DE421 등 데이터 파일이 내려받아질 수 있습니다. 입력 `date`/`time`은 **관측 지 근처 타임존**(`timezonefinder`) 기준 지방시로 해석합니다.
