# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)

## Trợ lý tuyển dụng ứng dụng trí tuệ nhân tạo

| Thuộc tính | Giá trị |
|---|---|
| Mã tài liệu | SRS-AIRA-01 |
| Phiên bản | 1.0 |
| Trạng thái | Bản nháp dựa trên mã nguồn hiện tại |
| Ngày lập | 29/09/2026 |
| Hệ thống | AI Recruitment Assistant |
| Nguồn xác minh | README, mã frontend/backend, cấu hình triển khai và dữ liệu huấn luyện trong repository |

> **Phạm vi tài liệu:** SRS này mô tả hành vi và giới hạn của phiên bản đang có trong repository. Mục “Khoảng trống và đề xuất” đánh dấu rõ những năng lực chưa được hiện thực; không xem chúng là chức năng đã hoàn thành.

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu xác định yêu cầu chức năng, yêu cầu giao diện, dữ liệu, bảo mật, ràng buộc và tiêu chí nghiệm thu của Trợ lý tuyển dụng. Tài liệu dành cho sinh viên/nhóm phát triển, giảng viên hướng dẫn, người kiểm thử và người dùng tuyển dụng khi xem xét phạm vi đồ án.

### 1.2 Phạm vi sản phẩm

Hệ thống cung cấp ứng dụng web cho nhà tuyển dụng để:

- tạo và quản lý vị trí tuyển dụng, tiêu chí và mô tả công việc;
- tải CV PDF/DOCX, trích xuất văn bản và một số trường hồ sơ;
- tải JD PDF/DOCX/TXT để phân tích và gợi ý tiêu chí;
- tính điểm so khớp ứng viên–vị trí, xếp hạng, lọc và xem chi tiết;
- xem số liệu tổng quan và trạng thái mô hình.

Sản phẩm là công cụ hỗ trợ rà soát hồ sơ. Kết quả phân tích hoặc nhãn `HIGH`, `MEDIUM`, `LOW` không tự đưa ra quyết định tuyển dụng hay loại ứng viên.

### 1.3 Thuật ngữ và viết tắt

| Thuật ngữ | Định nghĩa |
|---|---|
| CV | Hồ sơ/Sơ yếu lý lịch của ứng viên |
| JD | Mô tả công việc và yêu cầu tuyển dụng |
| Matching | Tính mức độ tương đồng/phù hợp giữa hồ sơ và vị trí |
| OCR | Nhận dạng ký tự từ trang tài liệu dạng ảnh |
| TF-IDF | Biểu diễn văn bản theo tần suất từ và độ hiếm trong tập văn bản |
| Embedding | Vector biểu diễn ngữ nghĩa của văn bản |
| SRS | Software Requirements Specification – Đặc tả yêu cầu phần mềm |
| PII | Thông tin có thể nhận diện cá nhân, gồm dữ liệu trong CV |

### 1.4 Tài liệu tham chiếu

- `README.md` – kiến trúc, hướng dẫn chạy, mô hình, dữ liệu và giới hạn.
- `backend/app/api/routes/` – hợp đồng API và quyền truy cập.
- `backend/app/models/` – cấu trúc thực thể lưu trữ.
- `backend/app/ai/matching_engine.py` – trọng số điểm matching.
- `backend/app/services/cv_parser.py` và `cv_information_extractor.py` – trích xuất CV.
- `data/training/evaluation_report.md` – kết quả và giới hạn đánh giá mô hình.
- `docker-compose.yml`, `.env.example` – cấu hình triển khai và môi trường.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh hệ thống

Ứng dụng theo mô hình frontend–backend. Trình duyệt sử dụng giao diện React/Vite, gọi REST API FastAPI qua HTTP. Backend dùng Pydantic để kiểm tra dữ liệu, SQLAlchemy để truy cập cơ sở dữ liệu và SQLite làm cấu hình phát triển. Tệp tải lên được lưu trong vùng uploads của backend. Docker Compose khởi chạy frontend ở cổng 5173 và backend ở cổng 8000.

### 2.2 Nhóm người dùng

| Vai trò | Mô tả và quyền hiện có |
|---|---|
| Nhà tuyển dụng (`recruiter`) | Tạo tài khoản công khai; đăng nhập; truy cập các nghiệp vụ được bảo vệ như vị trí, ứng viên, CV, matching và dashboard. |
| Quản trị viên (`admin`) | Có thể được tạo từ cấu hình tài khoản demo; hiện được chấp nhận ở các API yêu cầu `recruiter` hoặc `admin`. Chưa có nhóm màn hình/quy trình quản trị riêng trong giao diện. |
| Người tìm việc | Không phải người dùng trực tiếp của phiên bản hiện tại; không có cổng ứng viên để tự nộp hồ sơ. |

Các API nghiệp vụ dùng chung yêu cầu vai trò recruiter/admin. Mặc dù dữ liệu vị trí có trường `user_id`, API hiện tại chưa áp dụng lọc quyền sở hữu theo người dùng; phiên bản này nên được xem như một không gian dữ liệu dùng chung, không phải hệ thống đa tổ chức đã được cô lập.

### 2.3 Môi trường vận hành

- Trình duyệt desktop hiện đại có hỗ trợ JavaScript và giao thức HTTP.
- Frontend React/Vite, backend FastAPI/Python.
- SQLite dùng cho phát triển/demo; có thể cấu hình `DATABASE_URL` khác nhưng chưa đặc tả nghiệm thu trên hệ quản trị khác.
- Docker Compose là cách khởi chạy đóng gói được README hướng dẫn.
- OCR trang PDF scan cần Tesseract cùng gói ngôn ngữ tiếng Anh và tiếng Việt. Sentence Transformer là tùy chọn; mặc định matching dùng TF-IDF khi embedding không được bật/khả dụng.

### 2.4 Giả định và phụ thuộc

1. Backend, frontend và cơ sở dữ liệu đã chạy, mạng giữa trình duyệt và API thông suốt.
2. Người dùng có quyền xử lý các CV/JD được tải lên và chịu trách nhiệm về mục đích sử dụng dữ liệu cá nhân.
3. Tài liệu đầu vào là PDF hoặc DOCX cho CV; JD hỗ trợ PDF, DOCX hoặc TXT.
4. OCR chỉ hoạt động nếu binary Tesseract và dữ liệu ngôn ngữ có trong môi trường backend.
5. Chất lượng trích xuất phụ thuộc chất lượng tài liệu, bố cục, ngôn ngữ và khả năng OCR.
6. Dữ liệu/mô hình suitability hiện dùng cho thử nghiệm, không phải benchmark tuyển dụng được gán nhãn độc lập.

## 3. Yêu cầu giao diện ngoài

### 3.1 Giao diện người dùng

Các trang hiện có gồm đăng nhập, đăng ký, dashboard, danh sách/tạo/sửa vị trí, chi tiết vị trí, tải CV, danh sách ứng viên, chi tiết ứng viên, danh sách xếp hạng và chi tiết matching. Giao diện phải hiển thị trạng thái tải, kết quả, lỗi API và trạng thái xử lý từng tệp; điều hướng nghiệp vụ qua URL phía frontend.

### 3.2 Giao diện phần mềm

- Frontend gọi API JSON dưới prefix `/api`.
- Các yêu cầu được bảo vệ gửi header `Authorization: Bearer <access_token>`.
- Tải tệp dùng `multipart/form-data`.
- API cung cấp OpenAPI/Swagger tại `/docs`, ReDoc tại `/redoc`.
- Health check công khai tại `GET /health`.

### 3.3 Giao diện phần cứng và truyền thông

Không có phần cứng chuyên dụng. Trình duyệt giao tiếp với backend qua HTTP trong môi trường phát triển. Khi truy cập từ cùng máy, dùng `http://localhost:5173` cho frontend và `http://localhost:8000` cho API; `0.0.0.0` chỉ là địa chỉ bind của dịch vụ, không phải địa chỉ trình duyệt.

## 4. Yêu cầu chức năng

Mỗi yêu cầu có mã duy nhất. “Hiện có” mô tả trạng thái đối chiếu với mã nguồn tại ngày lập tài liệu; các yêu cầu này cần được kiểm thử nghiệm thu trước khi nộp.

### 4.1 Xác thực và phiên làm việc

| ID | Yêu cầu | Mức | Trạng thái |
|---|---|---:|---|
| FR-AUTH-01 | Hệ thống phải cho phép tạo tài khoản nhà tuyển dụng với họ tên, email hợp lệ và mật khẩu tối thiểu 8 ký tự. | Cao | Hiện có |
| FR-AUTH-02 | Email đăng ký phải được chuẩn hóa chữ thường và không được trùng; email đã có phải trả lỗi xung đột. | Cao | Hiện có |
| FR-AUTH-03 | Hệ thống phải xác thực email/mật khẩu và trả access token kiểu Bearer cùng thông tin người dùng khi thành công. | Cao | Hiện có |
| FR-AUTH-04 | Backend phải cung cấp thông tin người dùng hiện tại qua endpoint hồ sơ có xác thực. | Trung bình | API hiện có; chưa có trang hồ sơ riêng |
| FR-AUTH-05 | Người dùng phải có thể đăng xuất ở giao diện; thao tác hiện tại xóa token khỏi `localStorage` của trình duyệt. | Cao | Hiện có |
| FR-AUTH-06 | API nghiệp vụ phải từ chối request thiếu/sai/hết hạn token; vai trò ngoài `recruiter`/`admin` không được truy cập. | Cao | Hiện có |

### 4.2 Quản lý vị trí tuyển dụng

| ID | Yêu cầu | Mức | Trạng thái |
|---|---|---:|---|
| FR-JOB-01 | Người dùng đã đăng nhập phải có thể tạo vị trí có tiêu đề (2–255 ký tự) và mô tả (ít nhất 10 ký tự). | Cao | Hiện có |
| FR-JOB-02 | Vị trí phải lưu được phòng ban, địa điểm, loại hình, mức lương, trạng thái, yêu cầu học vấn/kinh nghiệm, chuyên ngành, kỹ năng, chứng chỉ và ngôn ngữ bắt buộc/ưu tiên. | Cao | Hiện có |
| FR-JOB-03 | Backend phải cung cấp danh sách vị trí theo phân trang; mặc định `skip=0`, `limit=20`, giới hạn `limit` từ 1 đến 100. | Cao | API hiện có; UI chưa có điều khiển chuyển trang |
| FR-JOB-04 | Hệ thống phải cho xem, cập nhật và xóa vị trí theo ID; ID không tồn tại phải trả lỗi không tìm thấy. | Cao | API có CRUD; UI chưa có thao tác xóa |
| FR-JOB-05 | Giao diện phải cho lọc trạng thái đang tuyển/đã đóng/tất cả vị trí trong danh sách đã tải. | Trung bình | Hiện có |
| FR-JOB-06 | Hệ thống phải phân tích JD đã nhập, trả gợi ý kỹ năng/yêu cầu và cho người dùng chủ động áp dụng đề xuất vào vị trí. | Cao | Hiện có |
| FR-JOB-07 | Hệ thống phải tiếp nhận JD PDF/DOCX/TXT tối đa 5 MB, trích xuất nội dung và trả lỗi phù hợp nếu sai định dạng, quá cỡ hoặc không đọc được văn bản. | Cao | Hiện có |

### 4.3 Tiếp nhận CV và hồ sơ ứng viên

| ID | Yêu cầu | Mức | Trạng thái |
|---|---|---:|---|
| FR-CV-01 | Người dùng phải có thể tải một CV PDF hoặc DOCX, giới hạn 5 MB mỗi tệp. | Cao | Hiện có |
| FR-CV-02 | Người dùng phải có thể tải CV theo luồng hàng loạt gắn với một vị trí; giao diện hiển thị hàng đợi, tiến độ, thành công/thất bại và cho thử lại tệp thất bại. | Cao | Hiện có |
| FR-CV-03 | Hệ thống phải trích xuất văn bản PDF/DOCX; trang PDF scan cần thử OCR khi điều kiện phát hiện scan phù hợp và OCR được cấu hình. | Cao | Hiện có |
| FR-CV-04 | Hệ thống phải tạo hồ sơ ứng viên gồm họ tên, email, điện thoại, địa điểm, liên kết, kỹ năng, số năm kinh nghiệm, học vấn, kinh nghiệm làm việc, dự án, chứng chỉ, ngôn ngữ và văn bản gốc khi phát hiện được. | Cao | Hiện có |
| FR-CV-05 | Hệ thống phải lưu tệp gốc, văn bản trích xuất, trạng thái phân tích và thông tin phiên bản phân tích liên kết với hồ sơ. | Cao | Hiện có |
| FR-CV-06 | Nếu tệp sai loại, vượt 5 MB, không trích xuất được hoặc OCR không sẵn sàng, hệ thống phải báo lỗi; không được báo phân tích hoàn tất khi nội dung văn bản rỗng. | Cao | Hiện có |
| FR-CV-07 | Giao diện phải cho xem danh sách ứng viên, tìm theo tên/email và xem chi tiết hồ sơ. | Cao | Hiện có |
| FR-CV-08 | Kết quả trích xuất chỉ là gợi ý máy tạo; giao diện/hướng dẫn sử dụng phải yêu cầu người tuyển dụng đối chiếu CV gốc. | Cao | Nguyên tắc sử dụng; cần thể hiện rõ hơn trong UI |

### 4.4 Matching, sàng lọc và xếp hạng

| ID | Yêu cầu | Mức | Trạng thái |
|---|---|---:|---|
| FR-MAT-01 | Hệ thống phải tính điểm ứng viên–vị trí từ kỹ năng, kinh nghiệm, học vấn, dự án và tương đồng nội dung. | Cao | Hiện có |
| FR-MAT-02 | Điểm kỹ năng/kinh nghiệm/học vấn/dự án có trọng số 40%/15%/15%/10%; 20% còn lại là tương đồng văn bản. Khi embedding bật, 20% được chia 10% TF-IDF và 10% semantic; nếu fallback, TF-IDF chiếm đủ 20%. | Cao | Hiện có |
| FR-MAT-03 | Hệ thống phải ghi kết quả matching cho một ứng viên và một vị trí, cập nhật kết quả cũ cho cùng cặp thay vì tạo bản trùng ở mỗi lần tính. | Cao | Hiện có |
| FR-MAT-04 | Hệ thống phải sàng lọc hàng loạt danh sách từ 1 đến 100 ID ứng viên cho một vị trí. | Cao | Hiện có |
| FR-MAT-05 | Hệ thống phải hiển thị danh sách xếp hạng cùng điểm tổng, lớp dự đoán nếu có, độ tin cậy nếu có và điểm kỹ năng. | Cao | Hiện có |
| FR-MAT-06 | Người dùng phải lọc danh sách theo nhãn suitability, ngưỡng độ tin cậy từ 0 đến 1 và tìm tên ứng viên. | Trung bình | Hiện có |
| FR-MAT-07 | Người dùng phải xem chi tiết một kết quả, gồm các thành phần điểm, kỹ năng phù hợp/thiếu/bổ sung và thông tin dự đoán được lưu. | Cao | Hiện có |
| FR-MAT-08 | Hệ thống phải phân biệt chế độ `trained-model` và `fallback`; không được tạo nhãn/độ tin cậy giả khi mô hình không khả dụng. | Cao | Hiện có |
| FR-MAT-09 | Nhãn và điểm suitability chỉ hỗ trợ rà soát, không tự động quyết định tuyển/loại ứng viên. | Cao | Quy tắc sử dụng/giới hạn hệ thống |

### 4.5 Dashboard và trạng thái mô hình

| ID | Yêu cầu | Mức | Trạng thái |
|---|---|---:|---|
| FR-DASH-01 | Dashboard phải cung cấp tổng vị trí, vị trí đang mở, tổng ứng viên, CV hoàn tất, tổng lượt matching và điểm matching trung bình. | Trung bình | Hiện có |
| FR-DASH-02 | Dashboard phải cung cấp phân bố nhãn suitability, số lượt matching theo vị trí và số CV theo trạng thái xử lý. | Trung bình | Hiện có |
| FR-MOD-01 | API trạng thái mô hình phải trả khả dụng hay không, loại mô hình, lớp, số đặc trưng, phiên bản và chế độ dự đoán khi có metadata. | Trung bình | Hiện có |

## 5. Quy tắc nghiệp vụ và thuật toán

1. Tài khoản đăng ký công khai luôn được gán vai trò `recruiter`; đăng ký không cho người dùng tự chọn quyền `admin`.
2. Email lưu ở dạng chữ thường sau khi loại khoảng trắng đầu/cuối.
3. CV chỉ chấp nhận phần mở rộng `.pdf` và `.docx`; giới hạn backend là 5 MB cho từng tệp.
4. JD chấp nhận `.pdf`, `.docx`, `.txt`; giới hạn backend là 5 MB.
5. Trường không nhận diện được có thể để rỗng/0; không suy diễn rằng trường rỗng là dữ liệu đã xác minh.
6. Điểm matching theo trọng số trong FR-MAT-02. Điểm dự án hiện là heuristic dựa trên một số cụm từ tiếng Anh; điểm kinh nghiệm dò mẫu năm/tháng; điểm học vấn dựa trên cấp bậc nhận diện. Đây không phải đánh giá ngữ nghĩa hoàn chỉnh.
7. Mô hình Random Forest dự đoán `HIGH`, `MEDIUM`, `LOW` khi artifact sẵn có; nếu không có artifact thì ứng dụng dùng luồng điểm dựa trên bằng chứng/TF-IDF và ghi `fallback`.
8. Embedding sentence-transformer là tùy chọn và mặc định tắt trong cấu hình môi trường; không tính điểm semantic nếu provider không sẵn sàng.
9. Batch screening có giới hạn 100 ID ứng viên; batch upload xử lý theo từng tệp và có thể trả kết quả hỗn hợp thành công/thất bại.

## 6. Dữ liệu và mô hình thông tin

### 6.1 Thực thể

| Thực thể | Dữ liệu chính | Quan hệ |
|---|---|---|
| User | ID, tên, email duy nhất, hash mật khẩu, vai trò, thời gian tạo/cập nhật | Có thể tạo/quản lý nhiều vị trí theo trường `user_id` (hiện chưa cưỡng chế lọc quyền sở hữu trong API). |
| Job | Tiêu đề/mô tả, trạng thái, phòng ban, địa điểm, yêu cầu kỹ năng/học vấn/kinh nghiệm/chứng chỉ/ngôn ngữ | Có nhiều Match. |
| Candidate | Thông tin liên hệ, raw text, kỹ năng, học vấn, kinh nghiệm, dự án, chứng chỉ, ngôn ngữ, trạng thái phân tích | Có nhiều Resume và Match. |
| Resume | Tệp gốc/đường dẫn, văn bản trích xuất, trạng thái, phiên bản phân tích | Thuộc một Candidate. |
| Match | Job, Candidate, điểm thành phần, nhãn/độ tin cậy, phiên bản/chế độ dự đoán, snapshot đặc trưng | Có nhiều MatchDetail. |
| MatchDetail | Tên kỹ năng, loại khớp, điểm, trạng thái, mô tả | Thuộc một Match. |
| Skill | Tên kỹ năng, nhóm, bí danh | Danh mục chuẩn hóa kỹ năng. |
| AnalysisLog | Loại entity, entity ID, hành động, trạng thái, thông điệp, thời gian | Ghi lại một số thao tác phân tích JD. |

### 6.2 Phân loại và xử lý dữ liệu cá nhân

CV có thể chứa PII và thông tin nghề nghiệp. Bản hiện tại lưu tệp gốc cùng văn bản đã trích xuất trong vùng uploads/cơ sở dữ liệu. Tài liệu dự án không xác định chính sách thời hạn lưu, xóa an toàn, mã hóa tệp khi lưu, phân quyền theo tổ chức hay quy trình yêu cầu xóa dữ liệu. Các nội dung này cần được thống nhất trước khi dùng dữ liệu thật ngoài môi trường demo.

## 7. Yêu cầu phi chức năng

### 7.1 Bảo mật

| ID | Yêu cầu |
|---|---|
| NFR-SEC-01 | Endpoint nghiệp vụ phải yêu cầu token Bearer hợp lệ; sai/hết hạn trả 401, sai vai trò trả 403. |
| NFR-SEC-02 | Mật khẩu phải lưu dạng hash; API không được trả hash mật khẩu trong dữ liệu UserOut. |
| NFR-SEC-03 | Access token hiện có thời hạn cấu hình mặc định 1.440 phút (24 giờ). |
| NFR-SEC-04 | Môi trường không demo phải thay JWT secret mặc định bằng secret ngẫu nhiên, riêng tư; không đưa secret thật vào mã nguồn hoặc tài liệu. |
| NFR-SEC-05 | Tệp tải lên phải tuân thủ whitelist phần mở rộng và giới hạn kích thước đã nêu; lỗi phải không để lại tệp phân tích thất bại trong vùng uploads. |
| NFR-SEC-06 | Vì frontend lưu token trong `localStorage`, triển khai thực tế cần xem xét biện pháp giảm rủi ro XSS, chính sách CSP và vòng đời phiên. |

### 7.2 Tính đúng và khả năng giải thích

- Điểm phải trả về các thành phần hiện có và danh sách kỹ năng khớp/thiếu/bổ sung để phục vụ rà soát.
- Khi model không tải được, hệ thống phải báo rõ fallback.
- Nội dung trích xuất, điểm và nhãn phải được coi là kết quả có thể sai; cần đối chiếu nguồn CV/JD.
- Không được tuyên bố mô hình đã được kiểm chứng tuyển dụng thực tế. Báo cáo đánh giá hiện có dùng dữ liệu tổng hợp/model-assisted.

### 7.3 Khả năng sử dụng và lỗi

- Mỗi luồng tải tệp phải cho biết trạng thái thành công/thất bại theo tên tệp.
- Lỗi đầu vào hoặc API phải được hiển thị bằng thông báo dễ hiểu, không để giao diện rơi vào trạng thái tải vô hạn.
- Form vị trí phải kiểm tra tối thiểu tiêu đề và mô tả; form đăng ký phải kiểm tra trường bắt buộc, email và độ dài mật khẩu.

### 7.4 Hiệu năng, sẵn sàng và khả năng mở rộng

Chưa có SLO/thời gian đáp ứng hoặc bài tải kiểm chứng trong repository. Do đó các giới hạn định lượng về p95, số người dùng đồng thời, thời gian lưu trữ và RPO/RTO được ghi là **TBD** và cần được chốt nếu triển khai vượt quá demo cục bộ. SQLite được định vị cho phát triển/demo, chưa được xác nhận cho tải sản xuất.

### 7.5 Tương thích và khả năng triển khai

- Backend phải chạy qua môi trường Python phụ thuộc theo requirements của dự án.
- Frontend phải build/chạy bằng Node/Vite theo cấu hình hiện hành.
- Docker Compose phải cung cấp dịch vụ frontend/backend và health check API.
- Cấu hình DB, JWT, CORS, upload directory, seed demo và model name phải lấy từ biến môi trường/cấu hình thay vì cố định theo máy cá nhân.

## 8. Tóm tắt API

Tất cả đường dẫn bên dưới tương đối với host backend. Ngoại trừ health/root và đăng ký/đăng nhập, các endpoint nghiệp vụ yêu cầu Bearer token.

| Nhóm | Phương thức và đường dẫn | Chức năng |
|---|---|---|
| Health | `GET /health`, `GET /` | Kiểm tra API và thông tin dịch vụ |
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me` | Đăng ký, đăng nhập, hồ sơ hiện tại |
| Jobs | `GET/POST /api/jobs`, `GET/PUT/DELETE /api/jobs/{job_id}` | Danh sách, tạo, xem, sửa, xóa vị trí |
| JD | `POST /api/jobs/{job_id}/analyze`, `GET /api/jobs/{job_id}/analysis`, `POST /api/jobs/{job_id}/upload-jd` | Phân tích JD và tải JD |
| CV | `POST /api/resumes/upload`, `POST /api/resumes/upload-batch` | Tải một/nhiều CV |
| Candidates | `GET /api/candidates`, `GET /api/candidates/{candidate_id}` | Tìm và xem hồ sơ ứng viên |
| Matching | `POST /api/matching/jobs/{job_id}/match/{candidate_id}`, `GET /api/matching/jobs/{job_id}/matches`, `POST /api/matching/jobs/{job_id}/screen-batch`, `GET /api/matching/matches/{match_id}`, `POST /api/matching/evaluate` | Matching, xếp hạng, sàng lọc batch, chi tiết/đánh giá |
| Model | `GET /api/model/status`, `GET /api/matching/model/status` | Trạng thái model |
| Dashboard | `GET /api/dashboard/overview` | Số liệu tổng quan |

Mã phản hồi thường gặp: `200`/`201` thành công, `400` đầu vào/tệp không hợp lệ, `401` chưa xác thực hoặc token không hợp lệ, `403` vai trò không được phép, `404` ID không tồn tại, `409` email đã đăng ký, `422` lỗi xác thực schema hoặc không đọc được nội dung tệp.

## 9. Luồng sử dụng chính

### UC-01: Tạo tài khoản và đăng nhập

- **Tác nhân:** Nhà tuyển dụng.
- **Điều kiện trước:** API và giao diện khả dụng; email chưa đăng ký.
- **Luồng chính:** Nhập tên/email/mật khẩu → frontend gửi đăng ký → backend chuẩn hóa email, băm mật khẩu, tạo tài khoản recruiter → backend trả token và user → frontend lưu token, chuyển sang dashboard.
- **Ngoại lệ:** Email đã tồn tại trả 409; email/mật khẩu không hợp lệ trả lỗi validation; đăng nhập sai trả 401.

### UC-02: Tạo vị trí và phân tích JD

- **Tác nhân:** Recruiter hoặc admin.
- **Luồng chính:** Tạo vị trí và nhập yêu cầu → lưu → tải JD tùy chọn → hệ thống trích xuất và phân tích → giao diện trình bày gợi ý → người dùng xem và chủ động áp dụng → hệ thống cập nhật vị trí.
- **Ngoại lệ:** Định dạng ngoài PDF/DOCX/TXT, tệp >5 MB, JD rỗng/không đọc được hoặc vị trí không tồn tại sẽ hiển thị lỗi.

### UC-03: Tải CV và sàng lọc

- **Tác nhân:** Recruiter hoặc admin.
- **Điều kiện trước:** Có vị trí nếu muốn sàng lọc gắn với công việc.
- **Luồng chính:** Chọn PDF/DOCX → backend lưu tệp tạm/thật, trích xuất nội dung, phân tích trường, tạo candidate/resume → giao diện hiện kết quả → người dùng chọn sàng lọc → backend tính matching và model/fallback → lưu kết quả → giao diện mở bảng xếp hạng.
- **Ngoại lệ:** Tệp không hợp lệ, quá cỡ, OCR thiếu hoặc nội dung không đọc được thì tệp đó thất bại; các tệp khác trong batch vẫn có thể hoàn tất.

### UC-04: Xem và lọc xếp hạng

- **Tác nhân:** Recruiter hoặc admin.
- **Luồng chính:** Mở danh sách kết quả theo vị trí → tìm ứng viên/lọc nhãn/độ tin cậy → xem điểm, mode → mở chi tiết để xem bằng chứng khớp.
- **Ngoại lệ:** Vị trí hoặc match không tồn tại trả 404; chưa có match thì giao diện hiển thị trạng thái rỗng.

## 10. Tiêu chí nghiệm thu mức hệ thống

1. Người dùng mới có thể đăng ký hợp lệ và đăng nhập; email trùng bị từ chối; endpoint nghiệp vụ từ chối token không hợp lệ.
2. Tạo/sửa/xem/xóa vị trí hợp lệ hoạt động qua giao diện/API; dữ liệu sau tải lại vẫn còn trong DB cấu hình.
3. PDF/DOCX tối đa 5 MB có văn bản đọc được tạo hồ sơ; TXT không được nhận làm CV; lỗi định dạng/quá cỡ/scan không đọc được được báo rõ.
4. JD PDF/DOCX/TXT được phân tích và gợi ý, nhưng chỉ cập nhật vị trí sau hành động áp dụng của người dùng.
5. Matching trả điểm trong khoảng 0–100 cùng các điểm thành phần; cùng ứng viên/vị trí chạy lại cập nhật bản match.
6. Sàng lọc 1–100 ứng viên trả được completed/failed tương ứng; xếp hạng hỗ trợ tìm kiếm, nhãn và ngưỡng confidence.
7. Khi classifier không khả dụng, API/giao diện thể hiện fallback; không hiển thị confidence giả.
8. Dashboard phản ánh số liệu được lưu; endpoint `/health` trả trạng thái `ok` khi backend sẵn sàng.
9. Kết quả kiểm thử phải được lưu bằng log; SRS không khẳng định các tiêu chí trên đã được chạy thành công cho tới khi có bằng chứng kiểm thử.

## 11. Giới hạn hiện tại và khoảng trống cần quyết định

| Mã | Khoảng trống/giới hạn hiện tại | Hướng xử lý đề xuất |
|---|---|---|
| GAP-01 | Không có chức năng sửa trực tiếp các trường candidate đã trích xuất trong giao diện hiện tại. | Bổ sung form rà soát/sửa và lưu, kèm trạng thái xác minh bởi người dùng. |
| GAP-02 | Không có xóa candidate/resume và chính sách retention/consent được đặc tả. | Định nghĩa quyền, thời hạn lưu, xóa tệp và xử lý yêu cầu xóa PII. |
| GAP-03 | Trường `user_id` của Job chưa được dùng để cô lập dữ liệu theo người tạo; các recruiter được xác thực có thể truy vấn không gian chung. | Xác nhận sản phẩm là shared workspace hay bổ sung tenant/ownership authorization. |
| GAP-04 | Chưa có email verification, quên/đổi mật khẩu, thu hồi token hoặc rate limiting đăng nhập. | Cân nhắc trước khi cho dùng ngoài demo. |
| GAP-05 | Kết quả trích xuất heuristic/OCR chưa có độ tin cậy theo trường; chưa có đánh giá precision/recall parser. | Gắn cờ trường chưa chắc chắn và tạo tập CV gán nhãn để đánh giá. |
| GAP-06 | Matching có heuristic cho kinh nghiệm, học vấn và dự án; chưa có hiệu chuẩn trọng số bằng người dùng tuyển dụng. | Thu thập tiêu chí có kiểm soát và đánh giá lỗi, độ công bằng. |
| GAP-07 | Bộ dữ liệu model có dữ liệu tổng hợp/model-assisted; không phải tập nhãn con người độc lập; model không phù hợp ra quyết định tự động. | Duy trì chế độ hỗ trợ, đánh giá trên dữ liệu có quyền sử dụng và nhãn độc lập. |
| GAP-08 | Chưa có ngưỡng hiệu năng, tải đồng thời, backup/restore hoặc mục tiêu availability được nghiệm thu. | Chốt theo môi trường triển khai trước khi mở rộng. |
| GAP-09 | Chưa xác nhận sanitizer/MIME sniffing/quét malware cho file upload. | Thêm kiểm tra nội dung file và biện pháp phòng chống file độc hại trước triển khai thật. |
| GAP-10 | Không có nhật ký đầy đủ cho mọi hành động xem/tải/sửa/xóa PII. | Bổ sung audit log và chính sách truy cập nếu cần tuân thủ nội bộ/pháp lý. |

## 12. Theo dõi trạng thái yêu cầu

| Trạng thái | Ý nghĩa |
|---|---|
| Hiện có | Đã thấy triển khai tương ứng trong mã nguồn; chưa đồng nghĩa đã pass kiểm thử nghiệm thu. |
| Cần kiểm thử | Hành vi có trong code nhưng cần chạy và lưu kết quả trên bản nộp. |
| Cần xác nhận | Cần chủ đồ án/giảng viên chốt phạm vi, ưu tiên hoặc mức chấp nhận. |
| Chưa triển khai | Khoảng trống; không trình bày như chức năng hoàn thành. |

---

**Lưu ý khi nộp:** điền người soạn/người duyệt theo biểu mẫu khoa; xác nhận phạm vi đa người dùng, quyền truy cập dữ liệu CV, các ngưỡng NFR và kết quả kiểm thử thực tế.
