# stockavenue

투자 리서치 웹앱. **단일 FastAPI 서버**(`main.py`)가 inline 프론트엔드(`index.html`)를 직접 서빙합니다. (별도 프론트 빌드/Node 없음)

## 기능
- **Screener** — 미국 대형주 상승/하락 Top (Finviz)
- **News** — `#키워드`별 뉴스 트래커 (Google News RSS)
- **수출데이터** — 미국/한국 무역 급증 품목 Top 20 (MoM·YoY ≥ +20%). 소스: US Census · 관세청(data.go.kr)
- **Watchlist** — 카테고리별 관심종목 + 시세/스파크라인/차트
- **Paper Maker** — 문서(PDF 등) 업로드 기반 분석 (Gemini)

## 실행
```bash
pip install -r requirements.txt
cp .env.example .env          # 복사 후 실제 API 키 입력
uvicorn main:app --reload --port 8000
```
→ http://localhost:8000

## 환경변수 (`.env`)
| 키 | 용도 |
|---|---|
| `ANTHROPIC_API_KEY` | 무역 품목명 한글 번역 |
| `GEMINI_API_KEY` | Paper Maker 문서 분석 / 헤드라인 번역 |
| `CENSUS_API_KEY` | 미국 무역통계 (api.data.gov) |
| `KCS_API_KEY` | 한국 관세청 무역통계 (data.go.kr) |

> 런타임 캐시(`*_cache.json`, `keyword_tracker.json`, `watchlist.json`)와 업로드(`uploads/`)는 자동 생성되며 저장소에서 제외됩니다.
