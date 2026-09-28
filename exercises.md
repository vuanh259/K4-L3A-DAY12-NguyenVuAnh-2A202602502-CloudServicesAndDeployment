# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Nội dung được hỗ trợ biên soạn bằng AI, dựa trên các lần chạy thật của repository.
> Học viên cần đọc hiểu và điều chỉnh cách diễn đạt theo hiểu biết của bản thân.
> Phân biệt rõ kết quả đã quan sát với tình huống giả định dùng để giải thích.
>
> Họ và tên: Nguyễn Vũ Anh — Mã học viên: 2A202602502

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Ví dụ khi chuyển ứng dụng từ laptop lên một service cloud mới, người triển khai
quên tạo biến `AGENT_API_KEY`. Nếu dùng mặc định `changeme`, service vẫn chạy
nhưng ai biết khóa mẫu cũng có thể gọi API. Với cấu hình hiện tại, ứng dụng báo
lỗi validation và không nhận request cho tới khi có khóa hợp lệ. Lỗi cấu hình
được phát hiện trước khi dịch vụ bị sử dụng trái phép.

Đây là tình huống minh họa. Trong bài, test thiếu API key đã đạt; `lifespan`
gọi `get_settings()` trước khi startup hoàn tất nên việc kiểm tra diễn ra ngay
khi khởi động, không đợi tới request đầu tiên.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log thật từ service Python local dùng fake Redis, ngày 28/09/2026:

```json
{"user_id": "evidence-8bf83efb2c", "tokens_in": 3, "tokens_out": 42, "cost_usd": 2.565e-05, "event": "ask_completed", "level": "info", "timestamp": "2026-09-28T08:44:10.276076+00:00"}
```

Hai việc có thể làm với log này:

1. Lọc `user_id` và `timestamp` để tìm các lượt hỏi của một user trong một khoảng thời gian.
2. Cộng `cost_usd`, thống kê `tokens_in` và `tokens_out` để theo dõi mức sử dụng.

Chuỗi “đã trả lời xong” không chứa user, thời gian hay chi phí để máy xử lý.
JSON còn giữ cấu trúc key/value rõ ràng, không cần tách một câu văn bằng tay.
Log gốc: [ask-log.jsonl](screenshots/ask-log.jsonl). Chi phí này là số giả lập
của mock LLM, không phải hóa đơn OpenAI.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t day12-agent:prod .
docker image inspect agent:single day12-agent:prod --format '{{.RepoTags}} {{.Size}} bytes'
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (`agent:single`, từ `Dockerfile.single`) | 1695,83 MB |
| Multi-stage (`day12-agent:prod`) | 270,92 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Đo bằng `docker image inspect`: single-stage là 1.695.833.068 byte,
multi-stage là 270.915.050 byte; bảng dùng MB = 1.000.000 byte. Giảm khoảng
1424,92 MB, tương đương 84,02%. `docker images` làm tròn thành 1,7 GB và 271 MB.
Output gốc kèm image ID: [image-sizes.json](screenshots/image-sizes.json).

Chênh lệch chủ yếu đến từ base Python đầy đủ có thêm công cụ build, header và
thư viện hệ điều hành; bản slim lược bỏ nhiều thành phần đó. Multi-stage chỉ
đưa dependency đã cài và source cần chạy sang runtime, không đưa cả thư mục
builder sang. Cả hai Dockerfile đều dùng pip `--no-cache-dir`, nên không quy
toàn bộ chênh lệch cho pip cache. Đây là so sánh cả base image lẫn cách đóng gói,
không phải phép đo riêng tác động của multi-stage trên cùng một base.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

Đã thêm một comment vào bản sao `app/main.py` rồi build lại. Kết quả quan sát:

| Bước | Kết quả |
|---|---|
| COPY requirements, pip install | Dùng lại cache |
| Tạo user, COPY dependency từ builder | Dùng lại cache |
| COPY app, COPY utils | Chạy lại |

Docker dùng cache theo đầu vào và các layer trước đó. Đặt requirements trước
source giúp phần cài thư viện không bị ảnh hưởng khi chỉ sửa code. Nếu đưa
`COPY . .` lên trước pip install, thay đổi code sẽ làm mất cache ở bước COPY
và kéo theo việc chạy lại pip install.

Log thật: [docker-cache.txt](screenshots/docker-cache.txt). Thí nghiệm dùng
bản sao source để không làm thay đổi chức năng ứng dụng đang nộp.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

Ví dụ một lỗi cho phép thực thi mã từ input làm kẻ tấn công chạy lệnh dưới
quyền của process Python. Nếu process là root trong container, họ có thêm
khả năng sửa file và khai thác cấu hình mount/capability hoặc lỗ hổng kernel để
thoát container. Root trong container không tự động đồng nghĩa root trên host.
`USER 10001:10001` giảm quyền ngay ở bước thực thi mã trong container; nó là
một lớp phòng vệ, không thay thế vá lỗi hoặc cấu hình cách ly đúng.

Đã kiểm tra bằng `id -u` trong container và nhận `10001`:
[docker-runtime.txt](screenshots/docker-runtime.txt).

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Với bộ đếm reset theo phút, có thể gửi 10 request ở giây 59 của phút trước
và 10 request ở giây 00 của phút sau: tổng cộng 20 request trong khoảng hai giây.
Cụ thể, gửi 10 lượt lúc 10:00:59 rồi thêm 10 lượt lúc 10:01:00 sẽ qua được bộ
đếm theo phút. Cửa sổ trượt vẫn nhìn thấy 10 lượt vừa gửi ở phút trước nên sẽ
chặn lượt tiếp theo. Request cũ rời cửa sổ khi đủ 60 giây, lúc đó quota tương
ứng mới được dùng lại; không phải cứ sang phút mới là reset toàn bộ.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit đếm số lượt gọi trong 60 giây; cost guard theo dõi tiền của từng
user trong tháng UTC. Hai ví dụ minh họa:

| Tình huống | Rate limit | Cost guard |
|---|---|---|
| Mới gọi 1 lượt/phút nhưng đã tiêu 11 USD, ngân sách 10 USD | Cho qua | Chặn, trả 402 |
| Gọi lượt thứ 11 trong 60 giây, mới tiêu 0,001 USD | Chặn, trả 429 | Về ngân sách thì còn đủ |

Trong endpoint, rate limit chạy trước nên ở tình huống thứ hai cost guard
chưa được gọi. Test HTTP cho 402 và 429 đều đạt. Cost guard kiểm tra số đã chi
trước LLM và ghi chi phí sau LLM; nó chưa giữ trước ngân sách cho request đồng
thời, cũng chưa bảo đảm một lượt gọi mới không vượt số tiền còn lại.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

Redis mất kết nối, probe chung của cả ba container bắt đầu trả lỗi. Load
balancer có thể ngừng gửi traffic; nếu orchestrator dùng probe đó làm liveness
và đủ số lần lỗi, nó có thể restart cả ba container. Restart API không sửa được
Redis, nên các container mới tiếp tục lỗi và có thể tạo vòng restart. Thực tế
có restart hay không phụ thuộc chính sách orchestrator; Docker HEALTHCHECK
đơn thuần chỉ đánh dấu unhealthy. Tách probe thì `/health` vẫn 200, `/ready`
503 trong lúc Redis lỗi; test tình huống này đã đạt. Đã thử dừng Redis thật
trong stack local: `/health` trả 200 và `/ready` trả 503 với `redis: false`,
rồi khởi động lại Redis. Output: [dependency-failure.json](screenshots/dependency-failure.json).

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Đã chạy ba container bằng lệnh:

```powershell
docker compose -p day12-scale -f docker-compose.scale.yml up -d --no-build --scale agent=3 agent
```

Gửi HTTP trực tiếp với cùng user ID cho kết quả:

| Container nhận request | 1 | 2 | 3 | 1 | 2 | 3 |
|---|---|---|---|---|---|---|
| `history_length` | 0 | 2 | 4 | 6 | 8 | 10 |

Mỗi lượt hỏi thêm hai message: user và assistant. Instance sau thấy được dữ
liệu instance trước ghi vì cùng truy cập Redis. Nếu dùng dict riêng và ba
instance ban đầu đều rỗng, chuỗi trên sẽ là 0, 0, 0, 2, 2, 2.

Kết quả thật: [scale-results.json](screenshots/scale-results.json). Phép thử gọi
từng container trực tiếp, không đi qua Nginx, để xác định instance nhận request.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Trong lần triển khai này chưa ghi nhận lỗi build/runtime trên Render. Vì vậy,
chưa có một lỗi cloud đúng nghĩa để báo cáo theo câu hỏi. Sự cố thực tế gần
nhất xảy ra khi kiểm tra URL cloud từ môi trường công cụ:

- **Thông báo:** `WinError 10061` khi client HTTP kết nối qua proxy của sandbox.
- **Cách xác định:** traceback nằm ở bước kết nối proxy, chưa nhận được HTTP
  response từ API; chạy lại với quyền truy cập mạng được cấp thì endpoint hoạt động.
- **Cách xử lý:** dùng môi trường kiểm thử có quyền mạng phù hợp, giữ nguyên
  cấu hình bảo vệ API và không sửa service để né lỗi ở phía máy kiểm thử.
- **Kết quả:** `/health` và `/ready` trả 200, `/ask` thiếu key trả 401; CP5 đạt 9/9.

Đây là lỗi môi trường kiểm tra deployment, không phải lỗi bên trong Render.
Kết quả cloud được lưu tại [cloud-probes.json](screenshots/cloud-probes.json).
