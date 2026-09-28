# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Bản nháp có hỗ trợ AI, dựa trên kết quả kiểm tra được lưu trong repository.
> Học viên cần đọc, kiểm chứng và diễn đạt lại theo hiểu biết của bản thân trước khi nộp.
> Những thí nghiệm chưa hoàn thành được ghi rõ, không coi là minh chứng đã đạt.
>
> Họ và tên: Nguyễn Vũ Anh — Mã học viên: 2A202602502

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

Khi tạo service cloud mới nhưng quên khai báo AGENT_API_KEY, ứng dụng dừng ở
startup với lỗi validation. Điều này buộc người triển khai sửa cấu hình trước
khi nhận request. Nếu mặc định là `changeme`, endpoint vẫn chạy và người biết
khóa mẫu có thể gọi được. Test thiếu API key trong CP1 đã đạt; trong lifespan
có gọi `get_settings()` để kiểm tra thực sự diễn ra lúc startup.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

Dòng log thật từ service Python local dùng fake Redis, ngày 28/09/2026:

```json
{"user_id": "evidence-8bf83efb2c", "tokens_in": 3, "tokens_out": 42, "cost_usd": 2.565e-05, "event": "ask_completed", "level": "info", "timestamp": "2026-09-28T08:44:10.276076+00:00"}
```

Có thể lọc theo user và khoảng thời gian để truy vết một lượt hỏi; cũng có thể
cộng `cost_usd` hoặc thống kê token để phát hiện mức dùng tăng bất thường.
Một câu in “đã trả lời xong” không cung cấp các trường này cho máy tổng hợp.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f Dockerfile.single -t agent:single .
docker build -t day12-agent:prod .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (`agent:single`, từ `Dockerfile.single`) | 1695,83 MB |
| Multi-stage (`day12-agent:prod`) | 270,92 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

Đo bằng `docker image inspect`: single-stage là 1.695.833.068 byte,
multi-stage là 270.915.050 byte; bảng dùng MB = 1.000.000 byte. Giảm khoảng
1424,92 MB, tương đương 84,02%. `docker images` làm tròn thành 1,7 GB và 271 MB.
Output gốc kèm image ID nằm ở `screenshots/image-sizes.json`.

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

Theo thứ tự Dockerfile, sửa `app/main.py` giữ được cache của bước copy
requirements, pip install, tạo user và copy dependency từ builder. Layer
`COPY app ./app` và các layer đứng sau bị xây dựng lại. Nếu copy toàn bộ code
trước pip install thì sửa source sẽ làm mất cache của bước cài dependency.
Đã chạy thí nghiệm thêm một comment vào bản sao `app/main.py`, rồi build lại.
Log `screenshots/docker-cache.txt` xác nhận COPY requirements, pip install,
tạo user và COPY dependency đều `CACHED`; COPY app và COPY utils chạy lại.
Bản sao được dùng để giữ nguyên source chính trong khi kiểm tra cache.

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

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

Với bộ đếm reset theo phút, có thể gửi 10 request ở giây 59 của phút trước
và 10 request ở giây 00 của phút sau: tổng cộng 20 request trong khoảng hai giây.
Cửa sổ trượt đếm lại 60 giây gần nhất nên các request ở phút trước vẫn nằm
trong cửa sổ và request thứ 11 bị chặn. Test CP3 cũng xác nhận hết 60 giây
thì quota được dùng lại.

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

Rate limit giới hạn tần suất, cost guard giới hạn số tiền theo tháng.
Ví dụ user chỉ gửi một request trong phút nhưng đã tiêu 11 USD với ngân sách
10 USD: rate limit cho qua, cost guard trả 402. Ngược lại, user gửi request
thứ 11 trong 60 giây dù tổng chi phí mới 0,001 USD: rate limit trả 429.
Test HTTP 402 và 429 đều đạt. Cost guard của lab kiểm tra rồi mới ghi chi phí,
nên chưa bảo đảm trần tuyệt đối khi các request đồng thời hoặc một lượt tốn quá nhiều.

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
rồi khởi động lại Redis. Output nằm ở `screenshots/dependency-failure.json`.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

Đã chạy ba container bằng `docker compose -p day12-scale -f docker-compose.scale.yml
up -d --no-build --scale agent=3 agent`. Gửi HTTP trực tiếp lần lượt tới agent
1, 2, 3, 1, 2, 3 với cùng user ID, quan sát history_length là 0, 2, 4, 6, 8, 10.
Kết quả gốc nằm trong `screenshots/scale-results.json`. Phép thử này không dùng
Nginx: gọi từng container giúp biết chắc request đã đi qua ba process khác nhau.
Nếu dùng dict riêng, ba lượt đầu sẽ đều thấy 0 và các lượt sau chỉ thấy lịch sử
của từng instance, thay vì lịch sử chung tăng liên tục.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

Deploy Render đã thành công; test CP5 đạt 9/9 và API HTTPS có Redis hoạt động.
Trong lần triển khai này chưa ghi nhận lỗi build hoặc runtime trên Render,
nên không bịa một lỗi cloud để điền câu trả lời.
Lỗi môi trường đã gặp là Docker báo không tìm thấy named pipe `docker_engine`;
nguyên nhân Docker Desktop chưa chạy. Sau khi khởi động Docker Desktop và cấp
quyền truy cập Engine, `docker info` trả phiên bản 29.8.0. Đây là lỗi local,
không thay thế yêu cầu phản ánh một lỗi deploy cloud. Một lỗi khi kiểm tra URL
từ môi trường công cụ là WinError 10061 ở kết nối proxy của sandbox; chạy lại
với quyền truy cập mạng được cấp thì các endpoint trả 200/401 đúng kỳ vọng,
cho thấy lỗi đó thuộc môi trường kiểm thử chứ không phải service Render.
