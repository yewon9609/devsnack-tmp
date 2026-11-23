# devsnack-tmp

@devsnack.kr 데일리 카드뉴스 자동화용 저장소.

- `tools/devsnack_render.py` — content.json → 카드 PNG/JPG + 장별 MP4 (모든 장 애니메이션)
- `tools/ig_publish.py` — 사전 점검(check) / 인스타 캐러셀 게시(publish)
- `fonts/` — IBM Plex Sans KR, JetBrains Mono (SIL OFL, 라이선스 동봉)
- `samples/` — content.json 예시 (deep / roundup)
- `posted/YYYYMMDD` — 게시 완료 표시 (같은 날 중복 게시 방지)
- `YYYYMMDD/` — 게시용 임시 파일. 게시 후 삭제됨.
