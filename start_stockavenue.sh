#!/bin/bash
# stockavenue 자동 실행 스크립트 (macOS 로그인 시 LaunchAgent가 호출)
cd /Users/junseo_oh/stockavenue || exit 1

# 서버가 응답하면 브라우저를 띄우는 백그라운드 감시 (최대 60초 대기)
(
  for i in $(seq 1 60); do
    if curl -s -o /dev/null http://localhost:8000 2>/dev/null; then
      open http://localhost:8000
      break
    fi
    sleep 1
  done
) &

# uvicorn 서버를 포그라운드로 실행 (LaunchAgent가 이 프로세스를 관리)
exec /usr/bin/python3 -m uvicorn main:app --port 8000
