# Hiểu bài lab qua một lượt hỏi

Tài liệu này giúp đọc hiểu code đang có trong repository. Nên đọc theo thứ tự:
luồng request → cấu hình → Docker → bảo vệ API → Redis → vòng đời → cloud/CI.
Các ví dụ giải thích không phải kết quả thí nghiệm mới; kết quả chạy thật được
liên kết ở cuối tài liệu.

**Sản phẩm của bài:** một HTTP API chạy trên Render, dùng mock LLM offline.
HTTP, container và Redis là thật; câu trả lời và chi phí LLM được giả lập.
API key trong bài dùng để bảo vệ `/ask`, không phải khóa của OpenAI.

Ví dụ bạn gửi `POST /ask` với câu hỏi “Docker là gì?”, kèm `X-API-Key` và
`X-User-Id: sv01`. Ứng dụng xử lý theo thứ tự:

```text
Client → kiểm tra key → quota 60 giây → ngân sách tháng
       → đọc history Redis → mock LLM → lưu history Redis
       → cộng chi phí → ghi log JSON → trả câu trả lời
```

Giả sử user chưa có lịch sử: request đầu đọc được 0 message, rồi lưu câu hỏi
và câu trả lời thành 2 message. Request tiếp theo đọc được 2 message trước đó.
Do vậy `history_length` là số message **trước lượt hỏi hiện tại**, không phải
số câu hỏi đã gửi và cũng không phải số message sau khi trả lời.

| Muốn hiểu phần nào | Đọc file |
|---|---|
| Cấu hình và mặc định | [app/config.py](app/config.py) |
| Thứ tự xử lý request và các endpoint | [app/main.py](app/main.py) |
| So sánh API key | [app/auth.py](app/auth.py) |
| Đếm quota 60 giây | [app/rate_limiter.py](app/rate_limiter.py) |
| Cộng chi phí theo tháng | [app/cost_guard.py](app/cost_guard.py) |
| Lưu/đọc lịch sử | [app/store.py](app/store.py) |
| Xử lý tín hiệu dừng | [app/lifecycle.py](app/lifecycle.py) |
| Tạo JSON log | [app/logging_utils.py](app/logging_utils.py) |
| Câu trả lời giả lập | [utils/mock_llm.py](utils/mock_llm.py) |

## 1. Config theo 12-Factor

Code mô tả cách ứng dụng hoạt động; biến môi trường mô tả nó chạy ở đâu và với
cấu hình nào. `app/config.py` đọc các biến như `REDIS_URL`, `AGENT_API_KEY`.
Cùng image có thể chạy trên laptop và Render chỉ bằng cách thay biến môi trường.
`.env` là cách tiện để nạp biến khi phát triển, không phải nơi công khai secret.
API key không có mặc định: quên cấu hình thì app dừng ngay lúc startup.

`Settings` kế thừa `BaseSettings`. Ví dụ trường `port` đọc biến `PORT`, chuyển
chuỗi thành số nguyên và kiểm tra khoảng 1–65535. Biến môi trường có ưu tiên
hơn giá trị trong `.env`. `get_settings()` cache cấu hình để không đọc lại ở
mỗi request; thay `.env` thì cần khởi động lại process để áp dụng.

| Biến | Ý nghĩa trong bài |
|---|---|
| `PORT` | Cổng HTTP; mặc định 8000, Render tự cấp khi chạy cloud |
| `AGENT_API_KEY` | Khóa cho client gọi `/ask`, bắt buộc và không được rỗng |
| `REDIS_URL` | Địa chỉ Redis mà process API kết nối tới |
| `RATE_LIMIT_PER_MINUTE` | Hạn mức request của mỗi user trong cửa sổ 60 giây |
| `MONTHLY_BUDGET_USD` | Ngân sách giả lập theo user/tháng |
| `LOG_LEVEL` | Trường cấu hình mức log; hàm `log_event` hiện chưa dùng nó để lọc log |

Hai biến phục vụ kiểm thử, không thuộc sáu trường `Settings`:

- `DEPLOY_API_KEY`: bản sao khóa của API cloud, dùng cho script/test trên máy.
- `LOCAL_FALLBACK`: chọn cách kiểm tra CP5. Bài đã có cloud nên giữ `false`.

`RENDER_DEPLOY_HOOK_URL` lại là secret riêng trong **GitHub Secrets**, dùng để
yêu cầu Render deploy. Nó không dùng để gọi `/ask` và không lưu trong `.env`.

| Nơi chạy API | `REDIS_URL` phù hợp |
|---|---|
| Python trực tiếp trên laptop, Redis được publish cổng 6379 | `redis://localhost:6379/0` |
| Agent trong Docker Compose | `redis://redis:6379/0` |
| Render | Địa chỉ nội bộ do Blueprint lấy từ Key Value |
| Thử một process không có Redis thật | `fake://` |

Trong container, `localhost` là chính container đó. Tên `redis` trong Compose
là hostname của service Redis, nên agent mới kết nối đúng container khác.

Tự kiểm tra: tại sao không viết API key cố định trong `config.py`?

## 2. Health và log JSON

`/health` trả trạng thái của process. Log JSON trong `app/logging_utils.py` có
event, level, timestamp và các trường như user_id, cost_usd. Một event trên một
dòng giúp hệ thống thu log tách sự kiện và tổng hợp số liệu. Không ghi API key.
Ví dụ có thể lọc event `ask_completed` và cộng cost_usd của một user trong ngày.

Tự kiểm tra: log “xong rồi” thiếu dữ liệu nào để tính tổng chi phí?

Trong code, `json.dumps(..., ensure_ascii=False)` chuyển dict thành JSON và giữ
được tiếng Việt. Không dùng `indent` để mỗi event chỉ chiếm một dòng.
`flush=True` đẩy log ra stdout ngay, giúp xem log container kịp thời. Log event
của ứng dụng là JSON; các dòng access log mặc định của Uvicorn có định dạng riêng.

## 3. Docker multi-stage và non-root

Builder cài thư viện. Runtime lấy thư viện đã cài và chỉ source cần chạy.
Base slim loại bớt công cụ không cần thiết. Copy requirements trước source giúp
sửa một dòng Python không phải cài lại dependency. `USER 10001:10001` giảm quyền
của process; một lỗi thực thi mã không lập tức có quyền root trong container.
Non-root không phải bảo đảm tuyệt đối chống thoát container.

`exec uvicorn ...` giúp Uvicorn nhận trực tiếp tín hiệu dừng. `0.0.0.0` cho phép
nhận kết nối vào container; `PORT` lấy theo giá trị cloud cấp.

**Image** là gói ứng dụng đã build; **container** là một instance đang chạy từ
image. Ba container có thể dùng chung một image nhưng có process và RAM riêng.
`.dockerignore` loại `.env`, `.git`, `.venv` khỏi build context. Dockerfile
còn chỉ COPY thư mục `app` và `utils` vào runtime, không COPY toàn bộ repository.

Số đo trong bài: single-stage 1695,83 MB, multi-stage 270,92 MB. Chênh lệch còn
do base image đầy đủ so với slim; không nên kết luận mọi multi-stage đều tự
động giảm 84% dung lượng. Xem [số đo thật](screenshots/image-sizes.json).

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

Đọc code theo ba bước:

1. `verify_api_key()` đọc header, dùng `secrets.compare_digest()` để so khóa;
   khóa sai trả 401. Khóa đúng nhưng không có user ID thì dùng `anonymous`.
2. `RateLimiter.check()` loại request cũ, đếm lượt còn lại, rồi ghi lượt mới nếu
   còn quota. WATCH phát hiện một instance khác đã sửa key; khi đó giao dịch
   phải kiểm tra lại thay vì dùng số đếm cũ.
3. `CostGuard.check()` so `spent + estimated_cost > budget`. `/ask` hiện gọi
   hàm này với `estimated_cost=0`, nên chưa ước lượng chi phí câu trả lời sắp tạo.
   Sau LLM, `record()` dùng INCRBYFLOAT để cộng số tiền vừa phát sinh.

Ngoài các mã trên, câu hỏi rỗng bị validation từ chối với 422, còn `/ask` đang
shutdown trả 503. **API key** chứng minh người gọi biết khóa chung; **user ID**
chỉ là nhãn trong lab, chưa phải tài khoản đã được xác minh độc lập.

## 5. Redis và scale ngang

Scale ngang là chạy nhiều instance API. Mỗi instance có RAM riêng. Nếu lưu
history bằng dict, câu đầu vào A và câu sau vào B có thể mất ngữ cảnh.
Cả A và B đọc cùng Redis thì đều thấy lịch sử đã lưu. Redis cũng dùng chung
quota và chi phí. History giữ tối đa 20 message, TTL 7 ngày để giới hạn bộ nhớ.
`fake://` chỉ dành cho phát triển: dữ liệu nằm trong một process nên không
chứng minh được khả năng chia sẻ state giữa các container.

| Dữ liệu | Kiểu Redis | Ví dụ key | Cách giới hạn |
|---|---|---|---|
| Lịch sử | List chứa message JSON | `history:sv01` | LTRIM 20 message, TTL 7 ngày |
| Lượt gọi | Sorted Set | `ratelimit:sv01` | Cửa sổ 60 giây; TTL 60 giây được gia hạn mỗi lần ghi nhận request hợp lệ |
| Chi phí | Chuỗi số, tăng bằng INCRBYFLOAT | `cost:sv01:2026-09` | Key theo tháng, TTL 40 ngày từ lần ghi gần nhất |

`RPUSH` thêm ở cuối, `LRANGE` đọc từ cũ tới mới. Sau khi thêm message,
`LTRIM(key, -20, -1)` giữ 20 message mới nhất. TTL giúp dữ liệu không được dùng
nữa tự hết hạn; TTL không có nghĩa là xóa dữ liệu ngay sau mỗi request.

Trong lần thử ba container, history tăng 0, 2, 4, 6, 8, 10 qua agent 1/2/3.
Đây là bằng chứng chia sẻ dữ liệu. Nó chưa chứng minh hai request đồng thời
của cùng user luôn được xử lý theo đúng thứ tự hội thoại.

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

`lifespan` là phần khởi động/kết thúc chung của FastAPI: kiểm tra settings,
đăng ký handler, ghi log bắt đầu; khi kết thúc thì bật cờ dừng, khôi phục handler
và ghi log kết thúc. `SIGINT` thường đến từ Ctrl+C, còn `SIGTERM` thường đến
từ Docker/nền tảng. Signal handler chỉ làm việc ngắn; không gọi Redis hay LLM.

Lần thử `docker stop` trong bài thoát mã 0 và có log `service_stopped` sau
khoảng 0,75 giây. Đây là quan sát của lần thử, không phải cam kết mọi request
ở mọi tình huống đều hoàn thành trong thời gian đó.

## 8. Render và URL công khai

Render build Dockerfile từ GitHub, chạy container và cung cấp HTTPS. Blueprint
tạo API và Key Value cùng khu vực, truyền URL Redis nội bộ, sinh API key.
`/ready` thành công chứng minh API chạm được Redis; `/ask` với key đúng kiểm tra
luồng chính. `/ask` không key phải bị chặn dù URL là công khai.
Key của ứng dụng không phải key OpenAI. Mock LLM chạy offline theo đề bài.
Render Free có thể ngủ và Key Value Free có thể mất dữ liệu sau restart.

## 9. CI/CD: kiểm tra trước khi deploy

[Workflow](.github/workflows/ci.yml) có ba job:

```text
push main / pull request → test → build image
                                      ↓
                  chỉ main → gọi Deploy Hook với commit đã test
```

`needs` buộc build chờ test và deploy chờ cả hai. Điều kiện `if` không cho pull
request deploy. Secret `RENDER_DEPLOY_HOOK_URL` nằm trong GitHub Secrets;
workflow chỉ tham chiếu tên, không chứa giá trị. `render.yaml` tắt auto-deploy
theo commit để tránh Render triển khai trước khi CI qua.

Gọi Deploy Hook thành công chỉ chứng minh Render nhận yêu cầu. Vẫn cần kiểm
tra deployment và API public sau đó. Trong bài, cả ba job đã success và CP5
được chạy lại thành công. Xem [CI_CD.md](CI_CD.md).

## 10. Tự kiểm tra trên máy

Chạy ở thư mục gốc repository bằng PowerShell. Các lệnh dùng môi trường đã tạo:

```powershell
# Chạy stack thật: cần Docker Desktop đang hoạt động và .env đã có key.
docker compose up -d --build
docker compose ps

# Hai probe không cần API key.
curl.exe -i http://localhost:8000/health
curl.exe -i http://localhost:8000/ready

# Script tự đọc key từ .env, không cần dán secret vào câu lệnh.
.\.venv\Scripts\python.exe scripts/check_service.py http://127.0.0.1:8000

# Cloud dùng DEPLOY_API_KEY trong .env.
.\.venv\Scripts\python.exe scripts/check_service.py https://day12-agent-nguyenvuanh.onrender.com

# Kiểm tra tất cả và chấm tự động.
.\.venv\Scripts\python.exe -m pytest tests/ -v
.\.venv\Scripts\python.exe grade.py
```

Script HTTP tạo user thử mới cho mỗi lần chạy, gửi 12 câu hỏi và kiểm tra
10 lượt thành công, 2 lượt bị rate limit. Kịch bản này giả định hạn mức vẫn
là 10/phút. Nếu đổi cấu hình, cần điều chỉnh kỳ vọng của kịch bản tương ứng.

Kết quả đã lưu: **94 test đạt, 4 test local fallback bỏ qua**, điểm tự động
100/100 và bonus 10/10 (tổng bị chặn ở 100). Xem [VALIDATION.md](VALIDATION.md).
Điểm tự động không thay thế đánh giá chất lượng phần phản ánh.

## 11. Câu hỏi ôn nhanh

| Câu hỏi | Ý chính cần tự giải thích |
|---|---|
| Vì sao thiếu API key phải dừng startup? | Không âm thầm phục vụ với khóa mẫu ai cũng biết |
| Vì sao không dùng localhost cho Redis trong agent container? | Localhost chỉ chính container agent |
| Vì sao có UUID trong member rate limit? | Hai request cùng timestamp vẫn phải được đếm riêng |
| Vì sao history tăng 2 mỗi lượt? | Lưu một message user và một message assistant |
| Redis chết có nên restart toàn bộ API ngay không? | Process có thể vẫn sống; phân biệt readiness với liveness |
| Vì sao gọi lại signal handler cũ? | Để Uvicorn tiếp tục quy trình dừng server |
| API key và Deploy Hook khác nhau thế nào? | Một khóa cho gọi API; một URL bí mật cho kích hoạt triển khai |
| Vì sao 100 điểm chưa đồng nghĩa production-ready? | User ID tự khai, ngân sách chưa reservation, Redis Free có thể mất state |

## Tự trình bày trong một phút

“Ứng dụng của em nhận cấu hình từ môi trường, chạy trong Docker bằng user thường.
Request phải có API key; Redis dùng chung để lưu history, đếm quota và chi phí.
Em kiểm tra quota và ngân sách trước khi gọi mock LLM. Health chỉ kiểm tra
process, ready kiểm tra cả Redis. Khi nhận tín hiệu dừng, ứng dụng ngừng nhận
việc mới và nhường Uvicorn xử lý nốt request. Em triển khai bằng Render và đã
kiểm tra API công khai cùng các mã lỗi xác thực, rate limit.”

Đây là gợi ý để hiểu và tự diễn đạt; cần đọc code để giải thích được từng bước.
