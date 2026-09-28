# Kiểm tra bản nộp — 28/09/2026

Đã chạy đủ `python -m pytest tests/ -v` và `python grade.py`, không loại test Docker.

| Nhóm | Kết quả |
|---|---|
| CP1 — Config, health, log | 13/13 đạt |
| CP2 — Docker, gồm build thật và dung lượng | 16/16 đạt |
| CP3 — Authentication, rate limit, cost guard | 22/22 đạt |
| CP4 — Redis, readiness, shutdown | 19/19 đạt |
| CP5 — Render HTTPS, gồm key thật | 9/9 đạt |
| Test bổ sung đồng thời và lifespan | 2/2 đạt |
| Local fallback | 4 test bỏ qua vì dùng cloud |
| Bonus CI/CD | 13/13 đạt; test, build và deploy trên GitHub đều success |

Tổng `pytest tests/ -v`: **94 passed, 4 skipped**, không có fail/error.
Bốn test bỏ qua dành riêng cho local fallback. Có một cảnh báo deprecation
từ Starlette TestClient/httpx; không ảnh hưởng kết quả kiểm tra.

`grade.py`: **100/100 phần bắt buộc, bonus 10/10; tổng bị giới hạn ở 100/100**.
Điểm exercises chỉ đếm số câu;
giảng viên vẫn đánh giá nội dung và khả năng giải thích. Không coi điểm này là
chứng nhận ứng dụng đủ an toàn cho LLM trả phí ngoài phạm vi lab.

## Bằng chứng

- [Output pytest](screenshots/pytest-results.txt)
- [Bảng điểm](screenshots/grade-summary.txt)
- [Kết quả CI/CD](screenshots/ci-results.json): ba job thành công cho commit
  `e1baf5b4031f4c115ef014dab0e6aec77033acb0`.
- [Cloud HTTP](screenshots/cloud-probes.json): hai probe 200, auth 401, 10 lượt hỏi
  200, sau đó 429, history tăng 0, 2, ..., 18.
- [Docker HTTP](screenshots/docker-probes.json): cùng luồng với Redis thật trên máy.
- [Ba container](screenshots/scale-results.json): gọi luân phiên agent 1/2/3,
  history tăng 0, 2, 4, 6, 8, 10.
- [Non-root và container](screenshots/docker-runtime.txt): UID 10001.
- [Cache](screenshots/docker-cache.txt): pip install CACHED khi chỉ thay source.
- [Shutdown thật](screenshots/shutdown-results.json): Docker stop, exit code 0,
  có log service_stopped, hoàn thành khoảng 0,75 giây.
- [Redis mất kết nối](screenshots/dependency-failure.json): health 200, ready 503;
  Redis được khởi động lại sau phép thử.
- [Dashboard](screenshots/dashboard.png), [health](screenshots/health.png),
  [ready](screenshots/ready.png): ảnh thật đã được mở và kiểm tra.

## Lưu ý trước khi nộp

`exercises.md` có hỗ trợ AI. Học viên cần đọc, kiểm chứng và diễn đạt theo cách
hiểu của mình. Câu 10 nói rõ không gặp lỗi runtime/build trên Render; các lỗi
đã gặp ở Docker local và môi trường kiểm thử được phân biệt với lỗi cloud.
Không tạo sự cố cloud giả để viết báo cáo.

Hai image đã build và đo bằng `docker image inspect`:
single-stage 1695,83 MB, multi-stage 270,92 MB, giảm 84,02%.
Số byte chính xác và image ID: [image-sizes.json](screenshots/image-sizes.json).
Số ước lượng cũ trong câu 3 đã được thay bằng kết quả này.
