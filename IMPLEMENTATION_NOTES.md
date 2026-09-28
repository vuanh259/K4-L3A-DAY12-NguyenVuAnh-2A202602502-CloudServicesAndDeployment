# Giải thích bài làm

## CP1

`Settings` nhận biến môi trường và `.env`; giá trị môi trường được ưu tiên.
API key không có mặc định và không được rỗng. Lifespan gọi `get_settings()`
trước khi phục vụ request, nên thiếu cấu hình sẽ làm startup thất bại.
`log_event` trả và in cùng một chuỗi JSON, timestamp UTC; không ghi API key.
`/health` không nhận dependency nên Redis mất kết nối không ảnh hưởng liveness.

## CP2

Builder cài dependency vào `/install`; runtime chỉ nhận dependency và `app/`,
`utils/`. Dependency được copy trước source để cache không mất khi sửa code.
UID/GID 10001 giảm quyền của process. `exec` thay shell bằng Uvicorn để SIGTERM
đến đúng server. `PORT` do cloud cấp được nội suy lúc container khởi động.
Compose dùng hostname `redis`, đợi Redis healthy rồi mới chạy agent.

## CP3

API key so bằng `secrets.compare_digest` trên bytes. Không có user ID thì dùng
`anonymous`. Sorted Set giữ request 60 giây, UUID phân biệt request cùng thời điểm.
WATCH/MULTI/EXEC kiểm tra quota và ghi lượt mới mà không bị race giữa instance.
Cost key tách theo user và tháng UTC; INCRBYFLOAT cộng dồn trên Redis.
Endpoint kiểm tra auth, rate limit và ngân sách trước LLM, sau đó lưu hai message,
ghi chi phí và log. 401 là lỗi xác thực, 429 hết quota, 402 vượt ngân sách.

## CP4

History là Redis List, giữ 20 message, TTL 7 ngày. RPUSH/LTRIM/EXPIRE chạy trong
một transaction. Redis timeout giới hạn 2 giây; ping lỗi thì `/ready` trả 503.
Khi shutdown, cả hai probe trả 503 và `/ask` từ chối request mới. Handler mới gọi
lại handler cũ để Uvicorn đợi request đang xử lý rồi kết thúc.

## Các giới hạn của mô hình lab

- `X-User-Id` do client tự khai báo, dùng chung một API key. Đây chưa phải cơ chế
  định danh user đáng tin cậy: người có key có thể đổi user ID để đổi quota/history.
- Kiểm tra ngân sách rồi ghi sau khi LLM trả về chưa đặt trước chi phí; có thể vượt
  ngân sách bởi một lượt gọi hoặc các lượt đồng thời. LLM thật cần reservation và
  đối soát chi phí, cùng giới hạn token.
- Hai lượt ghi history và cập nhật chi phí chưa phải một transaction xuyên toàn
  bộ request. Nhiều câu hỏi cùng một user có thể xen kẽ khi chạy đồng thời.
- `fake://` chỉ phục vụ phát triển/test một process. Scale và cloud phải dùng Redis thật.
- Mock LLM offline không phát sinh hóa đơn nhà cung cấp LLM.

## Tự giải thích trước khi nộp

Đọc code, chạy lại test từng CP, rồi diễn đạt lại `exercises.md` theo cách hiểu
của bản thân. Tài liệu và log do công cụ hỗ trợ không thay thế việc hiểu bài.
