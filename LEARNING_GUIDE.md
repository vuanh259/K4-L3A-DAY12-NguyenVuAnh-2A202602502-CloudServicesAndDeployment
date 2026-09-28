# Hiểu bài lab qua một lượt hỏi

Ví dụ bạn gửi `POST /ask` với câu hỏi “Docker là gì?”, kèm `X-API-Key` và
`X-User-Id: sv01`. Ứng dụng xử lý theo thứ tự:

```text
Client → kiểm tra key → quota 60 giây → ngân sách tháng
       → đọc history Redis → mock LLM → lưu history Redis
       → cộng chi phí → ghi log JSON → trả câu trả lời
```

## 1. Config theo 12-Factor

Code mô tả cách ứng dụng hoạt động; biến môi trường mô tả nó chạy ở đâu và với
cấu hình nào. `app/config.py` đọc các biến như `REDIS_URL`, `AGENT_API_KEY`.
Cùng image có thể chạy trên laptop và Render chỉ bằng cách thay biến môi trường.
`.env` là cách tiện để nạp biến khi phát triển, không phải nơi công khai secret.
API key không có mặc định: quên cấu hình thì app dừng ngay lúc startup.

Tự kiểm tra: tại sao không viết API key cố định trong `config.py`?

## 2. Health và log JSON

`/health` trả trạng thái của process. Log JSON trong `app/logging_utils.py` có
event, level, timestamp và các trường như user_id, cost_usd. Một event trên một
dòng giúp hệ thống thu log tách sự kiện và tổng hợp số liệu. Không ghi API key.
Ví dụ có thể lọc event `ask_completed` và cộng cost_usd của một user trong ngày.

Tự kiểm tra: log “xong rồi” thiếu dữ liệu nào để tính tổng chi phí?

## 3. Docker multi-stage và non-root

Builder cài thư viện. Runtime lấy thư viện đã cài và chỉ source cần chạy.
Base slim loại bớt công cụ không cần thiết. Copy requirements trước source giúp
sửa một dòng Python không phải cài lại dependency. `USER 10001:10001` giảm quyền
của process; một lỗi thực thi mã không lập tức có quyền root trong container.
Non-root không phải bảo đảm tuyệt đối chống thoát container.

`exec uvicorn ...` giúp Uvicorn nhận trực tiếp tín hiệu dừng. `0.0.0.0` cho phép
nhận kết nối vào container; `PORT` lấy theo giá trị cloud cấp.

## 4. Ba lớp bảo vệ

| Lớp | Câu hỏi được trả lời | Mã lỗi |
|---|---|---|
| API key | Request có khóa đúng không? | 401 |
| Rate limit | User đã gọi quá nhiều trong 60 giây chưa? | 429 |
| Cost guard | Chi phí tháng đã vượt ngân sách chưa? | 402 |

Rate limiter dùng Sorted Set: timestamp là score, timestamp + UUID là member.
UUID ngăn hai request cùng thời điểm ghi đè nhau. WATCH/MULTI/EXEC giúp quota
không bị vượt do hai instance cùng đọc một số đếm cũ.
Cost guard dùng key `cost:sv01:2026-09`. Kiểm tra trước LLM mới có tác dụng ngăn
một lượt gọi đã biết vượt ngân sách; kiểm tra sau khi gọi thì tiền đã phát sinh.

Giới hạn lab: client tự khai user ID, và cost guard chưa đặt trước chi phí cho
request đồng thời. Không coi đây là hệ thống tính tiền production hoàn chỉnh.

## 5. Redis và scale ngang

Scale ngang là chạy nhiều instance API. Mỗi instance có RAM riêng. Nếu lưu
history bằng dict, câu đầu vào A và câu sau vào B có thể mất ngữ cảnh.
Cả A và B đọc cùng Redis thì đều thấy lịch sử đã lưu. Redis cũng dùng chung
quota và chi phí. History giữ tối đa 20 message, TTL 7 ngày để giới hạn bộ nhớ.
`fake://` chỉ dành cho phát triển: dữ liệu nằm trong một process nên không
chứng minh được khả năng chia sẻ state giữa các container.

## 6. Liveness khác readiness

| Trạng thái | `/health` | `/ready` |
|---|---|---|
| Process và Redis hoạt động | 200 | 200 |
| Process sống, Redis mất kết nối | 200 | 503 |
| Đang shutdown | 503 | 503 |

Liveness hỏi “process còn sống không?”. Readiness hỏi “có thể nhận việc mới
không?”. Redis lỗi không nên khiến mọi API bị restart theo. Docker HEALTHCHECK
chỉ đánh dấu health; hành động restart/định tuyến còn tùy nền tảng.

## 7. Graceful shutdown

Khi dừng hoặc redeploy, nền tảng gửi SIGTERM. `app/lifecycle.py` bật cờ
shutting_down, làm probes trả 503 và từ chối lượt hỏi mới. Handler gọi lại
handler cũ của Uvicorn để server xử lý nốt request đang chạy rồi thoát.
Chỉ bật cờ mà không chuyển tiếp tín hiệu có thể khiến server không thoát,
cuối cùng bị kill cưỡng bức sau thời gian chờ.

## 8. Render và URL công khai

Render build Dockerfile từ GitHub, chạy container và cung cấp HTTPS. Blueprint
tạo API và Key Value cùng khu vực, truyền URL Redis nội bộ, sinh API key.
`/ready` thành công chứng minh API chạm được Redis; `/ask` với key đúng kiểm tra
luồng chính. `/ask` không key phải bị chặn dù URL là công khai.
Key của ứng dụng không phải key OpenAI. Mock LLM chạy offline theo đề bài.
Render Free có thể ngủ và Key Value Free có thể mất dữ liệu sau restart.

## Tự trình bày trong một phút

“Ứng dụng của em nhận cấu hình từ môi trường, chạy trong Docker bằng user thường.
Request phải có API key; Redis dùng chung để lưu history, đếm quota và chi phí.
Em kiểm tra quota và ngân sách trước khi gọi mock LLM. Health chỉ kiểm tra
process, ready kiểm tra cả Redis. Khi nhận tín hiệu dừng, ứng dụng ngừng nhận
việc mới và nhường Uvicorn xử lý nốt request. Em triển khai bằng Render và đã
kiểm tra API công khai cùng các mã lỗi xác thực, rate limit.”

Đây là gợi ý để hiểu và tự diễn đạt; cần đọc code để giải thích được từng bước.
