# Trợ lý tuyển dụng ứng dụng trí tuệ nhân tạo

Đồ án hỗ trợ nhà tuyển dụng quản lý vị trí, đọc hồ sơ CV, xếp hạng ứng viên và theo dõi quá trình xử lý hồ sơ. Giao diện sử dụng React/Vite; máy chủ sử dụng FastAPI, SQLAlchemy và SQLite.

## Chức năng

- Đăng nhập, đăng ký; hỗ trợ vai trò quản trị viên và nhà tuyển dụng.
- Tạo, sửa, xóa vị trí tuyển dụng; nhập mô tả công việc từ văn bản, PDF, DOCX, TXT hoặc đường dẫn công khai được hỗ trợ.
- Nhập tin tuyển dụng qua Greenhouse, Lever và phân tích HTML khi trang cho phép. Có thể dán nội dung hoặc tải tệp nếu trang chặn truy cập tự động.
- Đọc CV PDF/DOCX; OCR tiếng Việt và tiếng Anh cho PDF dạng ảnh khi có Tesseract.
- Xem và chỉnh thông tin trích xuất trước khi lưu ứng viên.
- Chấm điểm, xếp hạng và xem kỹ năng đáp ứng hoặc còn thiếu.
- Theo dõi trạng thái riêng cho từng cặp ứng viên–vị trí, ghi chú và lịch sử xử lý. Chấm lại không làm mất trạng thái.
- So sánh 2–3 ứng viên; xuất danh sách đã chọn sang CSV.
- Chuẩn bị bộ cặp CV–JD, gán nhãn, so sánh phương pháp xếp hạng và xuất báo cáo JSON.

## Chạy bằng Docker

Cài và khởi động Docker Desktop. Tại thư mục dự án:

```powershell
Copy-Item .env.example .env
# Chỉnh .env phù hợp trước khi chạy
docker compose up --build -d
```

Chỉ sao chép `.env.example` khi chưa có `.env`, tránh ghi đè cấu hình đang dùng.

- Giao diện: http://127.0.0.1:5173
- Tài liệu API: http://127.0.0.1:8000/docs
- Kiểm tra máy chủ: http://127.0.0.1:8000/health

`0.0.0.0` là địa chỉ lắng nghe của máy chủ, không phải đường dẫn mở trên trình duyệt.

```powershell
docker compose logs --tail 50 backend frontend
docker compose stop
```

Docker cài Tesseract cùng dữ liệu ngôn ngữ Việt/Anh và PyTorch CPU. E5 tải trọng số ở lần dùng đầu, lưu trong volume `embedding-cache`; lần đầu sàng lọc có thể chậm.

## Tài khoản demo

| Vai trò | Email | Mật khẩu |
|---|---|---|
| Quản trị viên | admin@example.com | admin123 |
| Nhà tuyển dụng | recruiter@example.com | password123 |

Đây là tài khoản minh họa. Khi triển khai ra ngoài, thay `JWT_SECRET`, tắt tạo dữ liệu demo và xử lý tài khoản demo đã tồn tại. Compose hiện đặt `SEED_DEMO_DATA: "true"` trực tiếp; cần sửa cấu hình này nếu không muốn tạo dữ liệu demo. Có thể cấu hình tài khoản quản trị qua `DEMO_ADMIN_EMAIL`, `DEMO_ADMIN_PASSWORD` khi chạy cục bộ.

## Chạy trực tiếp trên Windows

Chuẩn bị Python 3.12, Node.js và Tesseract có ngôn ngữ `vie`, `eng` nếu cần đọc PDF scan.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
pip install -r requirements-embeddings.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Mở cửa sổ terminal thứ hai:

```powershell
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Để bật E5 khi chạy trực tiếp, đặt biến môi trường `ENABLE_SENTENCE_TRANSFORMERS=true` trong terminal backend trước khi khởi động. Đặt `false` để dùng TF-IDF. Cấu hình khác tham khảo `.env.example`: `DATABASE_URL`, `UPLOAD_DIR`, `MODEL_NAME`, `CORS_ORIGINS`.

## Mô hình và cách chấm điểm

Hệ thống dùng `intfloat/multilingual-e5-small`, một mô hình embedding đa ngôn ngữ đã được huấn luyện sẵn, để so sánh ý nghĩa CV và mô tả công việc. Dự án chưa fine-tune E5 trên dữ liệu riêng.

Điểm xếp hạng kết hợp:

| Tiêu chí | Trọng số |
|---|---:|
| Kỹ năng bắt buộc | 40% |
| Nội dung văn bản | 20% |
| Kinh nghiệm | 15% |
| Học vấn | 15% |
| Dự án | 10% |

Khi E5 hoạt động, phần văn bản gồm 10% TF-IDF và 10% E5. Khi E5 không khả dụng, cả 20% dùng TF-IDF và kết quả ghi rõ phương án dự phòng. Điểm là tín hiệu xếp hạng, không phải xác suất được tuyển.

Phiên bản `reviewed-profile-v2` ưu tiên dữ liệu CV đã duyệt, bao gồm kỹ năng đã xóa và kinh nghiệm 0 năm. Văn bản gốc phục vụ hồ sơ cũ chưa có dữ liệu cấu trúc. Kết quả đã lưu từ phiên bản cũ cần sàng lọc lại.

Random Forest dự đoán HIGH/MEDIUM/LOW là tín hiệu tham khảo riêng, không quyết định thứ tự chính. Mô hình hiện có được huấn luyện khi đặc trưng ngữ nghĩa bằng 0; luồng ứng dụng giữ quy ước đó. Trạng thái mô hình: `GET /api/model/status` (cần đăng nhập).

## Dữ liệu và huấn luyện

Nguồn huấn luyện: [resume-job-fit-merged-v1 trên Hugging Face](https://huggingface.co/datasets/med2425/resume-job-fit-merged-v1), gồm 93.733 bản ghi, 643 hồ sơ và 351 JD. Dữ liệu có thành phần tổng hợp và nhãn hỗ trợ bằng mô hình.

Các tệp Parquet lớn không đưa lên Git. Tải ba tệp vào `data/training/resume-job-fit-merged-v1/data/`, sau đó chạy từ thư mục gốc:

```powershell
python backend/training/train_model.py
python backend/training/evaluate_model.py
```

Mô hình lưu ở `backend/models/candidate_job_suitability_model.joblib`, metadata ở `backend/models/model_metadata.json`. Tập train/validation/test được tách theo hồ sơ; JD vẫn có thể lặp giữa các tập.

Báo cáo hiện có ghi accuracy 0,7128 và macro F1 0,5645; mốc luôn đoán lớp phổ biến có accuracy 0,7434 và macro F1 0,2843. Các số này thuộc Random Forest trên bộ dữ liệu đó, không phải bằng chứng E5 cải thiện tuyển dụng thực tế.

## Đánh giá xếp hạng

Mở mục **Đánh giá mô hình** tại `/experiments`. Hệ thống tạo tối đa 200 cặp từ 10 vị trí đang mở và 20 ứng viên hiện có, lưu bản chụp nội dung. Đây không phải 200 CV mới.

Nhãn: 0 — chưa đáp ứng yêu cầu cốt lõi; 1 — phù hợp một phần; 2 — phù hợp cao. Hồ sơ rỗng cần bổ sung, không tự coi là không phù hợp. Nguồn nhãn, người đánh giá và lý do được lưu; nhãn AI đề xuất không phải nhãn người độc lập.

Mỗi vị trí cần ít nhất 5 cặp, toàn bộ có nhãn và có ít nhất một cặp phù hợp để chạy so sánh. Kết quả gồm NDCG@5 và MRR@5; MRR coi nhãn 1 và 2 là phù hợp. Báo cáo xuất có dữ liệu CV, chỉ chia sẻ với người được phép xem.

Có thể chạy công cụ dòng lệnh:

```powershell
python backend/scripts/evaluate_matching.py --data data/evaluation/matches.json --k 5
```

Công cụ này dùng tệp nhãn JSON, khác với bảng nhãn trên giao diện. Nó dùng chung cách chuẩn bị đầu vào với API, kiểm tra cặp trùng/thiếu và ghi phiên bản chấm điểm cùng mã kiểm tra dữ liệu. Khi E5 không hoạt động, kết quả hybrid để trống, không trình bày TF-IDF dự phòng như E5.

Cần bộ nhãn người độc lập, đa dạng và tách khỏi quá trình chỉnh trọng số trước khi kết luận chất lượng. Giao diện hiện lưu một nhãn cuối cho mỗi cặp, chưa tính độ đồng thuận giữa nhiều người đánh giá.

## Lưu trữ và sao lưu

- Database: `backend/app.db`.
- CV gốc: `backend/uploads/`.
- Nhãn: bảng `evaluation_pairs`.
- Trạng thái tuyển dụng: `applications`; lịch sử: `application_events`.
- Docker gắn thư mục backend vào container, giữ database và CV trên máy.

Dừng backend rồi sao chép database và thư mục uploads cùng nhau vào thư mục sao lưu có ngày tháng. Khôi phục cả hai khi backend đang dừng. Không xóa volume Docker để reset demo. Database, CV tải lên, `.env`, bản sao lưu và kết quả gán nhãn cục bộ không được đẩy lên GitHub.

## Kiểm thử

```powershell
cd backend
pip install -r requirements-dev.txt
python -m pytest -q
```

Kiểm thử workflow và hồ sơ đã duyệt có thể chạy riêng bằng `unittest` trong môi trường backend:

```powershell
python -m unittest discover -s tests -p test_pipeline.py -v
python -m unittest discover -s tests -p test_reviewed_matching.py -v
python -m unittest discover -s tests -p test_experiments.py -v
```

Các kiểm thử huấn luyện cần dataset và model có sẵn. Kiểm tra build frontend bằng `npm run build` trong thư mục frontend.

## Luồng demo

Tạo/nhập JD → kiểm tra yêu cầu → tải CV → sửa thông tin trích xuất → lưu → sàng lọc → xem giải thích → so sánh ứng viên → ghi chú và chuyển trạng thái → xuất danh sách. Phần đánh giá mô hình dùng để thử nghiệm riêng.

## Giới hạn hiện tại

OCR và trích xuất theo luật có thể sai với CV nhiều cột hoặc chất lượng thấp. Điểm dự án vẫn là tín hiệu đơn giản. Môi trường demo dùng SQLite và không gian dữ liệu chung giữa admin/recruiter; chưa tách dữ liệu theo doanh nghiệp. Bộ mẫu lệch ngành hoặc nhãn AI không đủ chứng minh độ chính xác thực tế. Hệ thống hỗ trợ người tuyển dụng xem xét, không tự quyết định tuyển hoặc loại ứng viên.
