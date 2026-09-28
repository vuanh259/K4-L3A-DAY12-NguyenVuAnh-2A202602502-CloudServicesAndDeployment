# Triển khai miễn phí trên Render

Repo đã có `render.yaml`: API dùng Docker, Key Value tương thích Redis, cả hai
đều `plan: free` ở Singapore. API key do Render tự sinh; Redis dùng mạng riêng.

1. Đăng nhập https://dashboard.render.com bằng GitHub.
2. Chọn **New → Blueprint**, kết nối đúng repository
   `vuanh259/K4-L3A-DAY12-NguyenVuAnh-2A202602502-CloudServicesAndDeployment`.
   Nếu GitHub yêu cầu cấp quyền, chỉ chọn repository bài lab này.
3. Chọn nhánh `main`, đường dẫn `render.yaml`. Kiểm tra cả hai service là **Free**
   trước khi tạo Blueprint. Không chọn gói trả phí.
4. Đợi Key Value và web service deploy xong. Web service dùng `/ready` làm
   health check nên phải kết nối được Redis mới được đánh dấu sẵn sàng.
5. Sao chép URL HTTPS của web service vào `DEPLOYMENT.md` và gửi URL đó để kiểm tra.
6. Muốn kiểm tra `/ask` có xác thực: trong Environment của web service, sao chép
   giá trị `AGENT_API_KEY` vào `DEPLOY_API_KEY` của file `.env` trên máy.
   Không đưa giá trị vào chat, ảnh chụp, Git hoặc dòng lệnh.
7. Chạy:

   ```powershell
   .\.venv\Scripts\python.exe scripts/check_service.py https://TEN-SERVICE.onrender.com
   .\.venv\Scripts\python.exe -m pytest tests/test_cp5.py -v
   ```

8. Chụp dashboard thể hiện deploy thành công và trang `/health`, `/ready`.
   Lưu ảnh thật vào `screenshots/`; tránh chụp trang đang hiện secret.

## Giới hạn cần hiểu

- Web Free ngủ sau 15 phút không nhận traffic; request đầu tiên có thể cần
  khoảng một phút để đánh thức service. Mở `/health` trước khi chạy test.
- Key Value Free chỉ lưu trong RAM: restart có thể xóa history, quota và chi phí.
  Phù hợp lab, không dùng như sổ ngân sách bền vững cho LLM có tính tiền.
- Free không có nghĩa là mọi tùy chọn đều miễn phí. Giữ nguyên Free cho cả
  web và Key Value, không bật tính năng trả phí.

Nguồn: [Render Free](https://render.com/docs/free),
[Blueprint](https://render.com/docs/blueprint-spec),
[Key Value](https://render.com/docs/key-value).
