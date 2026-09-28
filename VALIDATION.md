# Kiểm tra thực tế — 28/09/2026

## Đã đạt

Lệnh:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cp1.py tests/test_cp2.py tests/test_cp3.py tests/test_cp4.py tests/test_reliability_extra.py -m "not docker" -q -p no:cacheprovider
```

Kết quả: **70 passed, 2 deselected**. Phân bố: CP1 13, CP2 static 14, CP3 22,
CP4 19, kiểm tra bổ sung 2. Có cảnh báo deprecation từ Starlette TestClient/httpx.

Chạy server thật bằng Python ở cổng 8001 và `scripts/check_service.py` cũng đã
đạt auth, history và rate limit. Backend lần chạy này là fake Redis.
Xem `screenshots/local-python-probes.json` và `screenshots/ask-log.jsonl`.

## Chưa xác nhận

- Hai test Docker build/kích thước: đang bị chặn bởi tải image chậm/lỗi EOF.
- Stack Docker thực tế, thí nghiệm scale ba container, cache và kích thước hai image.
- Public HTTPS trên Render, ảnh dashboard và probes cloud.
- Câu phản ánh 3, 4, 9, 10 còn thiếu thí nghiệm tương ứng; đã ghi rõ trong bản nháp.
- Bonus CI/CD chưa thực hiện.

## Chấm tự động tạm thời

Đã chạy `grade.py` với `PYTEST_ADDOPTS='-m "not docker"'` để tránh lặp lại build
đang bị kẹt mạng. Output tính 92,5/100, **không phải điểm hoàn thành được xác nhận**:
grader phân bổ lại điểm CP2 khi bỏ test Docker và chỉ đếm câu phản ánh có chữ,
không kiểm chứng thí nghiệm. CP5 mới đạt bốn test tài liệu, chưa đạt public deployment.
Không dùng kết quả này để khẳng định bài đã xong hoặc đạt chuẩn production.

Cần chạy lại `pytest tests/ -v` và `python grade.py` không loại Docker sau khi
Docker và cloud sẵn sàng, rồi cập nhật tài liệu này bằng kết quả cuối.
