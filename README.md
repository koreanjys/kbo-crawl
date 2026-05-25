# KBO Crawler

KBO 기록실 데이터를 수집해 MySQL에 저장하고, Vue3 화면에서 테이블로 조회하는 프로젝트입니다.

## Backend

```bash
uv sync --extra dev
```

`.env`에 DB 접속 정보를 설정합니다. 예시는 `.env.example`을 참고합니다.

DB 테이블 생성:

```bash
uv run kbo-crawl init-db
```

현재 시즌의 선수/팀 기록 샘플 수집:

```bash
uv run kbo-crawl crawl --season 2026
```

전체 연도 범위 수집:

```bash
uv run kbo-crawl crawl --all-seasons
```

API 서버 실행:

```bash
uv run kbo-api
```

## Frontend

```bash
cd frontend
npm install
npm run dev
```

운영 API 예시 주소는 `https://kbo-crawl.duckdns.org`입니다. 서버 내부에서 직접 확인할 때는 `http://localhost:8001`을 사용합니다.
변경이 필요하면 `frontend/.env`에 `VITE_API_BASE_URL`을 설정합니다.
