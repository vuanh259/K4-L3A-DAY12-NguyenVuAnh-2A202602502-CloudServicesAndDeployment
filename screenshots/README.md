# Minh chứng thực tế

- `dashboard.png`: Blueprint tạo Web Service và Key Value thành công.
- `health.png`: URL public `/health` trả status ok.
- `ready.png`: URL public `/ready` trả redis true.
- `cloud-probes.json`: HTTP thật trên Render, gồm auth, history và rate limit.
- `docker-probes.json`: cùng phép thử trên Docker Compose local với Redis thật.
- `scale-results.json`: history chia sẻ giữa ba container.
- `docker-runtime.txt`: trạng thái ba container và UID không phải root.
- `docker-cache.txt`: log build khi thay đổi source trong bản sao riêng.
- `image-sizes.json`: số byte và image ID của hai image đã build thật.
- `shutdown-results.json`: dừng container an toàn, exit code và log kết thúc.
- `dependency-failure.json`: health/readiness khi Redis thật bị dừng tạm thời.
- `pytest-results.txt`, `grade-summary.txt`: kết quả cuối, bao gồm bonus CI/CD đã đạt.
- `ci-results.json`: trạng thái ba job test/build/deploy từ GitHub Actions API.
- `local-python-probes.json`, `ask-log.jsonl`: phép thử Python với fake Redis ban đầu.

Ba ảnh PNG do học viên chụp; các file JSON/TXT là output thực tế của công cụ.
Không có API key trong các minh chứng này.
