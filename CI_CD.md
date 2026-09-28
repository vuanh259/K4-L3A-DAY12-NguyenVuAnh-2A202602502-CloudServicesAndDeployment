# CI/CD của bài lab

Workflow `.github/workflows/ci.yml` chạy khi push main, mở pull request hoặc
chạy thủ công từ tab Actions. Ba job chạy theo thứ tự:

1. `test`: cài requirements, chạy CP1–CP4 và test bổ sung không cần Docker.
2. `build`: sau test thành công, build image và kiểm tra UID cùng giới hạn 500 MB.
3. `deploy`: chỉ trên main và sau test/build thành công, gọi Render Deploy Hook
   với `ref` bằng đúng commit SHA đã kiểm tra.

Không chạy test CP5 hoặc test badge của chính workflow trong job test: các
test đó cần hệ thống bên ngoài và không phải điều kiện để build source.

## Secret cần cấu hình một lần

Lấy Deploy Hook từ Render → service → Settings. Lưu URL vào GitHub repository →
Settings → Secrets and variables → Actions, tên `RENDER_DEPLOY_HOOK_URL`.
Không lưu URL trong source, `.env`, ảnh chụp hoặc chat. Thiếu secret thì deploy
job báo lỗi; workflow không được ghi nhận hoàn tất trước khi deploy job thành công.

`render.yaml` đặt `autoDeployTrigger: 'off'` để Render không tự deploy trước khi
CI hoàn tất. Blueprint phải sync thay đổi này; có thể kiểm tra lại Auto-Deploy
trong Settings của service. Bản đang chạy vẫn phục vụ trong lúc CI chạy.

Deploy Hook trả thành công nghĩa là Render đã nhận yêu cầu triển khai. Sau đó
cần kiểm tra trạng thái Live trên Render và health/readiness của URL public.

Nguồn: [Render Deploy Hooks](https://render.com/docs/deploy-hooks),
[Render Blueprint](https://render.com/docs/blueprint-spec).
