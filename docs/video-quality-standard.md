# 영상 QA

CPU mock 경로: approved plan의 제목/본문/표를 동일 순서로 그린 preview → pan/zoom → H.264 MP4 assemble.
장면은 source_slide_id/source_refs/slide_version/scene_version을 보존한다. 이전 scene 파일이 유효하면 선택하지 않은 장면은 재사용한다.
fps/장면길이는 config, 규격은 templates/video-profile.json에 둔다.

ffprobe 성공, 단일 video stream, 1920×1080/H.264/yuv420p, fps, duration, 근거를 검사하고 ffmpeg로 모든 frame를 디코드한다.
자막은 mock preview에 본문으로 표현한다. 기관 로고·인트로·아웃트로와 실제 Comfy video workflow는 연결 전 검증되지 않았다.
