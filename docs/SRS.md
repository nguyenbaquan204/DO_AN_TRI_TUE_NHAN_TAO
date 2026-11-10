# TÀI LIỆU ĐẶC TẢ YÊU CẦU PHẦN MỀM (SRS)

## Trợ lý tuyển dụng ứng dụng trí tuệ nhân tạo

- **Mã tài liệu:** SRS-AIRA-01
- **Phiên bản:** 1.2
- **Trạng thái:** Bản dự thảo, mô tả theo phiên bản hiện có
- **Ngày lập:** 06/11/2026
- **Hệ thống:** AI Recruitment Assistant
- **Nguồn đối chiếu:** README, mã giao diện và máy chủ, cấu hình triển khai, dữ liệu huấn luyện

> **Cách đọc tài liệu:** SRS này ghi lại những gì ứng dụng hiện làm được và những phần còn thiếu. Các đề xuất ở cuối tài liệu chưa phải chức năng đã xây dựng.

## 1. Giới thiệu

### 1.1 Mục đích

Tài liệu giúp nhóm phát triển và giảng viên thống nhất ứng dụng cần làm gì, dữ liệu nào được xử lý và cách kiểm tra kết quả. Nội dung được đối chiếu với phiên bản đồ án hiện có.

### 1.2 Phạm vi sản phẩm

Ứng dụng web dành cho nhà tuyển dụng hiện hỗ trợ các việc sau:

- tạo và quản lý vị trí tuyển dụng, tiêu chí và mô tả công việc;
- tải CV PDF/DOCX, trích xuất văn bản và một số trường hồ sơ;
- tải JD PDF/DOCX/TXT để phân tích và gợi ý tiêu chí;
- tính điểm so khớp ứng viên–vị trí, xếp hạng, lọc và xem chi tiết;
- xem số liệu tổng quan và trạng thái mô hình.

Ứng dụng chỉ giúp nhà tuyển dụng sắp xếp và xem xét hồ sơ. Điểm phù hợp hay nhãn HIGH, MEDIUM, LOW có thể chưa chính xác, vì vậy không được dùng để tự động nhận hoặc loại ứng viên.

### 1.3 Thuật ngữ và viết tắt

- **CV:** Hồ sơ/Sơ yếu lý lịch của ứng viên
- **JD:** Mô tả công việc và yêu cầu tuyển dụng
- **So khớp (matching):** So sánh yêu cầu tuyển dụng với thông tin trong hồ sơ ứng viên
- **OCR:** Công nghệ nhận chữ từ tài liệu scan hoặc ảnh
- **TF-IDF:** Cách máy tính so sánh văn bản dựa trên các từ xuất hiện và mức độ đặc trưng của chúng
- **Embedding:** Dãy số giúp máy tính so sánh ý nghĩa của các đoạn văn bản
- **SRS:** Tài liệu mô tả ứng dụng cần làm gì và cách kiểm tra ứng dụng
- **PII:** Thông tin có thể nhận diện một người, chẳng hạn tên, email hoặc số điện thoại
- **API:** Cách giao diện gửi yêu cầu và nhận dữ liệu từ máy chủ

### 1.4 Tài liệu tham chiếu

- README.md – kiến trúc, hướng dẫn chạy, mô hình, dữ liệu và giới hạn.
- backend/app/api/routes/ – hợp đồng API và quyền truy cập.
- backend/app/models/ – cấu trúc thực thể lưu trữ.
- backend/app/ai/matching_engine.py – trọng số điểm so khớp.
- backend/app/services/cv_parser.py và cv_information_extractor.py – trích xuất CV.
- data/training/evaluation_report.md – kết quả và giới hạn đánh giá mô hình.
- docker-compose.yml, .env.example – cấu hình triển khai và môi trường.

## 2. Mô tả tổng quan

### 2.1 Bối cảnh hệ thống

Ứng dụng có hai phần: giao diện chạy trên trình duyệt và máy chủ xử lý dữ liệu. Giao diện được làm bằng React/Vite, máy chủ dùng FastAPI và SQLite trong cấu hình phát triển. Khi chạy bằng Docker Compose, giao diện dùng cổng 5173, máy chủ dùng cổng 8000. CV và mô tả công việc tải lên được lưu trên máy chủ.

### 2.2 Nhóm người dùng

- **Nhà tuyển dụng (recruiter)**
  - **Mô tả và quyền hiện có:** Tạo tài khoản công khai; đăng nhập; truy cập các nghiệp vụ được bảo vệ như vị trí, ứng viên, CV, so khớp và trang tổng quan.
- **Quản trị viên (admin)**
  - **Mô tả và quyền hiện có:** Có thể được tạo từ cấu hình tài khoản demo; hiện được chấp nhận ở các chức năng yêu cầu vai trò recruiter hoặc admin. Chưa có nhóm màn hình/quy trình quản trị riêng trong giao diện.
- **Người tìm việc**
  - **Mô tả và quyền hiện có:** Không phải người dùng trực tiếp của phiên bản hiện tại; không có trang để người tìm việc tự tạo hồ sơ hoặc nộp đơn.

Các chức năng nghiệp vụ yêu cầu đăng nhập bằng tài khoản nhà tuyển dụng hoặc quản trị viên. Tuy nhiên, hệ thống hiện chưa tách dữ liệu theo từng tài khoản. Vì vậy, đây là ứng dụng dùng chung cho mục đích đồ án, chưa phải hệ thống có vùng dữ liệu riêng cho từng công ty.

### 2.3 Môi trường vận hành

- Trình duyệt desktop hiện đại có hỗ trợ JavaScript và giao thức HTTP.
- Giao diện React/Vite, máy chủ FastAPI/Python.
- SQLite hiện dùng cho phát triển và trình diễn. Có thể kết nối cơ sở dữ liệu khác qua cấu hình, nhưng dự án chưa kiểm tra trường hợp này.
- Docker Compose là cách khởi chạy đóng gói được README hướng dẫn.
- Để đọc PDF scan, máy chủ cần cài Tesseract và dữ liệu nhận dạng tiếng Anh, tiếng Việt. Tính năng so sánh ý nghĩa câu chữ là tùy chọn; mặc định ứng dụng so sánh dựa trên các từ trong CV và mô tả công việc.

### 2.4 Giả định và phụ thuộc

1. Máy chủ, giao diện và cơ sở dữ liệu đã chạy, mạng giữa trình duyệt và API thông suốt.
2. Người dùng có quyền xử lý các CV/JD được tải lên và chịu trách nhiệm về mục đích sử dụng dữ liệu cá nhân.
3. Tài liệu đầu vào là PDF hoặc DOCX cho CV; JD hỗ trợ PDF, DOCX hoặc TXT.
4. Đọc PDF scan chỉ hoạt động khi máy chủ có cài Tesseract và dữ liệu ngôn ngữ tương ứng.
5. Chất lượng trích xuất phụ thuộc chất lượng tài liệu, bố cục, ngôn ngữ và khả năng OCR.
6. Dữ liệu và mô hình hiện chỉ dùng cho đồ án thử nghiệm; chưa được đánh giá độc lập trên hồ sơ tuyển dụng thực tế.

## 3. Yêu cầu giao diện ngoài

### 3.1 Giao diện người dùng

Các trang hiện có gồm đăng nhập, đăng ký, trang tổng quan, danh sách/tạo/sửa vị trí, chi tiết vị trí, tải CV, danh sách ứng viên, chi tiết ứng viên, danh sách xếp hạng và chi tiết so khớp. Giao diện phải hiển thị trạng thái tải, kết quả, lỗi API và trạng thái xử lý từng tệp; điều hướng nghiệp vụ qua URL phía giao diện.

### 3.2 Giao diện phần mềm

- Giao diện gọi API JSON dưới prefix /api.
- Các yêu cầu được bảo vệ gửi header Authorization: Bearer <access_token>.
- Tải tệp dùng multipart/form-data.
- API cung cấp OpenAPI/Swagger tại /docs, ReDoc tại /redoc.
- Health check công khai tại GET /health.

### 3.3 Giao diện phần cứng và truyền thông

Ứng dụng không cần thiết bị đặc biệt. Khi chạy trên máy cá nhân, mở giao diện tại http://localhost:5173; máy chủ nhận yêu cầu tại http://localhost:8000. Địa chỉ 0.0.0.0 dùng để máy chủ lắng nghe kết nối, không phải địa chỉ nhập vào trình duyệt.

## 4. Yêu cầu chức năng

Mỗi yêu cầu có một mã để tiện tra cứu. Trạng thái cho biết yêu cầu đã thấy trong mã nguồn hay giao diện; “đã có” chưa thay thế cho việc kiểm thử trước khi nộp.

### 4.1 Xác thực và phiên làm việc

- **FR-AUTH-01** — Người tuyển dụng có thể tạo tài khoản bằng họ tên, email hợp lệ và mật khẩu dài ít nhất 8 ký tự. _(Ưu tiên cao; Hiện có)_
- **FR-AUTH-02** — Email được chuyển về chữ thường trước khi lưu. Nếu email đã có tài khoản, ứng dụng báo email đã được sử dụng. _(Ưu tiên cao; Hiện có)_
- **FR-AUTH-03** — Khi email và mật khẩu đúng, ứng dụng đăng nhập và cấp mã đăng nhập cho các thao tác cần đăng nhập. _(Ưu tiên cao; Hiện có)_
- **FR-AUTH-04** — Máy chủ trả thông tin của tài khoản đang đăng nhập. Giao diện hiện chưa có trang hồ sơ riêng. _(Ưu tiên trung bình; API hiện có; chưa có trang hồ sơ riêng)_
- **FR-AUTH-05** — Người dùng có thể đăng xuất; ứng dụng xóa mã đăng nhập đã lưu trên trình duyệt. _(Ưu tiên cao; Hiện có)_
- **FR-AUTH-06** — Các chức năng cần đăng nhập sẽ từ chối yêu cầu không có mã đăng nhập hợp lệ hoặc tài khoản không đúng vai trò. _(Ưu tiên cao; Hiện có)_

### 4.2 Quản lý vị trí tuyển dụng

- **FR-JOB-01** — Người dùng đã đăng nhập có thể tạo vị trí với tiêu đề dài 2–255 ký tự và mô tả dài ít nhất 10 ký tự. _(Ưu tiên cao; Hiện có)_
- **FR-JOB-02** — Mỗi vị trí lưu được phòng ban, địa điểm, loại hình công việc, mức lương, trạng thái và yêu cầu về học vấn, kinh nghiệm, chuyên ngành, kỹ năng, chứng chỉ, ngôn ngữ. _(Ưu tiên cao; Hiện có)_
- **FR-JOB-03** — Máy chủ trả danh sách vị trí theo từng trang: mặc định 20 vị trí, có thể yêu cầu từ 1 đến 100. Giao diện chưa có nút chuyển trang. _(Ưu tiên cao; API hiện có; giao diện chưa có điều khiển chuyển trang)_
- **FR-JOB-04** — Người dùng xem và sửa được vị trí. Máy chủ có chức năng xóa nhưng giao diện chưa có thao tác này. Nếu không tìm thấy vị trí, máy chủ trả lỗi 404. _(Ưu tiên cao; Máy chủ hỗ trợ thêm, xem, sửa, xóa; giao diện chưa có nút xóa)_
- **FR-JOB-05** — Người dùng có thể lọc danh sách để xem vị trí đang tuyển, đã đóng hoặc tất cả vị trí đã tải. _(Ưu tiên trung bình; Hiện có)_
- **FR-JOB-06** — Người dùng có thể yêu cầu phân tích mô tả công việc để xem gợi ý về kỹ năng và yêu cầu. Gợi ý chỉ được lưu khi người dùng chủ động áp dụng. _(Ưu tiên cao; Hiện có)_
- **FR-JOB-07** — Có thể tải mô tả công việc dạng PDF, DOCX hoặc TXT, tối đa 5 MB. Ứng dụng báo lỗi nếu tệp sai loại, quá lớn hoặc không đọc được. _(Ưu tiên cao; Hiện có)_

### 4.3 Tiếp nhận CV và hồ sơ ứng viên

- **FR-CV-01** — Người dùng có thể tải lên một CV dạng PDF hoặc DOCX, tối đa 5 MB mỗi tệp. _(Ưu tiên cao; Hiện có)_
- **FR-CV-02** — Người dùng có thể tải hàng loạt CV cho một vị trí. Giao diện cho biết tiến độ và kết quả từng tệp, đồng thời cho thử lại tệp bị lỗi. _(Ưu tiên cao; Hiện có)_
- **FR-CV-03** — Ứng dụng đọc nội dung PDF hoặc DOCX. Với PDF scan, ứng dụng thử nhận dạng chữ nếu đã cài OCR. _(Ưu tiên cao; Hiện có)_
- **FR-CV-04** — Ứng dụng tạo hồ sơ từ những thông tin đọc được trong CV: tên, liên hệ, kỹ năng, kinh nghiệm, học vấn, dự án, chứng chỉ và ngôn ngữ. _(Ưu tiên cao; Hiện có)_
- **FR-CV-05** — Ứng dụng lưu CV gốc, nội dung đã đọc, trạng thái xử lý và phiên bản công cụ phân tích cùng hồ sơ ứng viên. _(Ưu tiên cao; Hiện có)_
- **FR-CV-06** — Nếu tệp sai loại, quá 5 MB hoặc không đọc được nội dung, ứng dụng báo lỗi. Không được báo thành công khi chưa trích xuất được văn bản. _(Ưu tiên cao; Hiện có)_
- **FR-CV-07** — Người dùng có thể xem danh sách ứng viên, tìm theo tên hoặc email và mở từng hồ sơ. _(Ưu tiên cao; Hiện có)_
- **FR-CV-08** — Thông tin máy đọc từ CV chỉ là gợi ý. Người tuyển dụng cần kiểm tra lại với CV gốc; giao diện hiện cần nhắc điều này rõ hơn. _(Ưu tiên cao; Nguyên tắc sử dụng; cần thể hiện rõ hơn trong giao diện)_

### 4.4 So khớp, sàng lọc và xếp hạng

- **FR-MAT-01** — Ứng dụng so sánh kỹ năng, kinh nghiệm, học vấn, dự án và nội dung CV với yêu cầu của vị trí. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-02** — Điểm gồm kỹ năng 40%, kinh nghiệm 15%, học vấn 15%, dự án 10% và nội dung văn bản 20%. Nếu bật so sánh ngữ nghĩa, phần cuối chia đều giữa TF-IDF và cách biểu diễn ngữ nghĩa; nếu không, TF-IDF chiếm 20%. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-03** — Khi tính lại điểm cho cùng ứng viên và vị trí, ứng dụng cập nhật kết quả cũ thay vì tạo bản trùng. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-04** — Người dùng có thể so khớp hàng loạt từ 1 đến 100 ứng viên cho một vị trí. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-05** — Danh sách xếp hạng hiển thị điểm tổng, điểm kỹ năng và nhãn dự đoán/độ tin cậy nếu có. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-06** — Người dùng có thể tìm theo tên và lọc theo nhãn dự đoán hoặc độ tin cậy từ 0 đến 1. _(Ưu tiên trung bình; Hiện có)_
- **FR-MAT-07** — Trang chi tiết cho biết từng phần điểm, kỹ năng phù hợp, kỹ năng còn thiếu và thông tin dự đoán đã lưu. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-08** — Ứng dụng cho biết đang dùng mô hình đã huấn luyện (mô hình đã huấn luyện) hay cách tính dự phòng (cách tính dự phòng). Nếu không có mô hình, ứng dụng không được tự tạo nhãn hoặc độ tin cậy. _(Ưu tiên cao; Hiện có)_
- **FR-MAT-09** — Điểm và nhãn chỉ giúp người tuyển dụng xem xét hồ sơ; ứng dụng không tự quyết định nhận hay loại ứng viên. _(Ưu tiên cao; Quy tắc sử dụng/giới hạn hệ thống)_

### 4.5 Trang tổng quan và trạng thái mô hình

- **FR-DASH-01** — Trang tổng quan hiển thị số vị trí, vị trí đang tuyển, số ứng viên, CV đã xử lý, lượt so khớp và điểm trung bình. _(Ưu tiên trung bình; Hiện có)_
- **FR-DASH-02** — Trang tổng quan hiển thị thêm số lượng theo nhãn dự đoán, lượt so khớp của từng vị trí và trạng thái xử lý CV. _(Ưu tiên trung bình; Hiện có)_
- **FR-MOD-01** — Trạng thái mô hình cho biết mô hình có sẵn hay không, loại mô hình, nhãn dự đoán và phiên bản nếu có. _(Ưu tiên trung bình; Hiện có)_

## 5. Quy tắc nghiệp vụ và thuật toán

1. Khi tự đăng ký, người dùng luôn nhận quyền nhà tuyển dụng. Họ không thể tự cấp cho mình quyền quản trị viên.
2. Trước khi lưu, ứng dụng bỏ khoảng trắng ở đầu/cuối email và chuyển email thành chữ thường.
3. CV chỉ chấp nhận phần mở rộng .pdf và .docx; giới hạn máy chủ là 5 MB cho từng tệp.
4. JD chấp nhận .pdf, .docx, .txt; giới hạn máy chủ là 5 MB.
5. Nếu ứng dụng không nhận diện được một thông tin, trường đó có thể để trống hoặc bằng 0. Không xem dữ liệu thiếu là thông tin đã được xác minh.
6. Điểm so khớp được tính theo tỷ trọng ở yêu cầu FR-MAT-02. Một số phần hiện chỉ dựa trên quy tắc đơn giản: tìm từ khóa trong dự án, nhận diện số năm/tháng kinh nghiệm và bậc học. Vì vậy, điểm số chưa thể hiểu đầy đủ ý nghĩa của hồ sơ.
7. Nếu tệp mô hình Random Forest có sẵn, ứng dụng có thể xếp kết quả vào nhóm HIGH, MEDIUM hoặc LOW. Nếu không, ứng dụng dùng cách tính dự phòng và ghi nhận rõ chế độ đó.
8. Tính năng so sánh ý nghĩa câu chữ bằng Sentence Transformer đang tắt theo mặc định. Nếu không được cấu hình, ứng dụng chỉ so sánh từ ngữ.
9. Mỗi lần sàng lọc nhận tối đa 100 hồ sơ. Khi tải hàng loạt CV, ứng dụng xử lý từng tệp riêng, nên có thể có tệp thành công và tệp báo lỗi trong cùng một lượt.

## 6. Dữ liệu và mô hình thông tin

### 6.1 Thông tin ứng dụng lưu

- **Tài khoản (User):** tên, email, mật khẩu đã mã hóa, quyền sử dụng và thời điểm tạo và cập nhật.
- **Vị trí tuyển dụng (Job):** tiêu đề, mô tả, trạng thái và các tiêu chí như kỹ năng, học vấn, kinh nghiệm, chứng chỉ, ngôn ngữ.
- **Ứng viên (Candidate):** thông tin liên hệ cùng nội dung CV đã đọc được, kinh nghiệm, học vấn, kỹ năng, dự án và trạng thái xử lý.
- **Tệp CV (Resume):** tệp gốc, nội dung trích xuất và tình trạng đọc CV.
- **Kết quả so khớp (Match):** vị trí và ứng viên được so sánh, điểm từng phần, nhãn dự đoán và thông tin về cách tính điểm.
- **Chi tiết kết quả (MatchDetail):** kỹ năng liên quan, trạng thái phù hợp và giải thích ngắn.
- **Danh mục kỹ năng (Skill):** tên kỹ năng và các cách gọi tương đương để chuẩn hóa dữ liệu.
- **Nhật ký phân tích (AnalysisLog):** ghi lại một số lần phân tích mô tả công việc.

Một tài khoản có thể gắn với nhiều vị trí và mỗi vị trí có thể có nhiều kết quả so khớp. Dù cơ sở dữ liệu lưu mã tài khoản tạo vị trí, ứng dụng hiện chưa giới hạn người dùng chỉ xem dữ liệu của mình.

### 6.2 Phân loại và xử lý dữ liệu cá nhân

CV có thể chứa thông tin nhận diện cá nhân như họ tên, email, số điện thoại và lịch sử công việc. Hiện ứng dụng lưu tệp gốc và nội dung đã đọc được. Đồ án chưa quy định thời hạn lưu, cách xóa an toàn, mã hóa tệp hay quy trình xử lý yêu cầu xóa dữ liệu. Cần thống nhất các nội dung này trước khi dùng CV thật.

## 7. Yêu cầu phi chức năng

### 7.1 Bảo mật

- **NFR-SEC-01:** Các chức năng nghiệp vụ chỉ dành cho tài khoản đã đăng nhập. Mã truy cập sai hoặc hết hạn phải bị từ chối; tài khoản không đủ quyền cũng không được tiếp tục.
- **NFR-SEC-02:** Mật khẩu không được lưu dưới dạng có thể đọc lại. Máy chủ chỉ lưu giá trị đã được biến đổi để xác minh mật khẩu.
- **NFR-SEC-03:** Mã truy cập hiện có hiệu lực mặc định trong 24 giờ.
- **NFR-SEC-04:** Trước khi dùng ngoài demo, cần thay khóa bảo mật mặc định bằng một khóa riêng, khó đoán. Không ghi khóa thật vào mã nguồn hay tài liệu.
- **NFR-SEC-05:** Chỉ nhận các loại tệp được cho phép và không vượt quá giới hạn dung lượng. Nếu xử lý thất bại, tệp lỗi không được để lại như thể đã được nhận thành công.
- **NFR-SEC-06:** Giao diện lưu mã đăng nhập trong bộ nhớ trình duyệt. Trước khi triển khai thực tế, cần giảm nguy cơ mã độc trên trang web đánh cắp mã này và quy định rõ thời hạn đăng nhập.

### 7.2 Tính đúng và khả năng giải thích

- Khi hiển thị điểm, ứng dụng cần cho biết điểm được tạo từ những phần nào và kỹ năng nào phù hợp, còn thiếu hoặc được gợi ý bổ sung.
- Nếu không tải được mô hình, ứng dụng phải báo rằng đang dùng cách tính dự phòng.
- Nội dung trích xuất, điểm và nhãn phải được coi là kết quả có thể sai; cần đối chiếu nguồn CV/JD.
- Kết quả hiện có chưa chứng minh mô hình hoạt động chính xác trong tuyển dụng thực tế. Báo cáo đánh giá sử dụng dữ liệu tổng hợp hoặc có sự hỗ trợ của mô hình.

### 7.3 Khả năng sử dụng và lỗi

- Khi tải nhiều tệp, ứng dụng phải cho biết tệp nào thành công và tệp nào thất bại.
- Nếu dữ liệu nhập vào có lỗi hoặc máy chủ không phản hồi, giao diện cần giải thích điều gì đã xảy ra và không được quay tải mãi.
- Form vị trí phải kiểm tra tối thiểu tiêu đề và mô tả; form đăng ký phải kiểm tra trường bắt buộc, email và độ dài mật khẩu.

### 7.4 Hiệu năng, sẵn sàng và khả năng mở rộng

Dự án chưa đo thời gian phản hồi, số người có thể truy cập cùng lúc hay khả năng khôi phục dữ liệu. Các mục tiêu này chưa được xác định và cần bổ sung nếu triển khai ngoài phạm vi demo. SQLite hiện chỉ dùng cho phát triển và trình diễn.

### 7.5 Tương thích và khả năng triển khai

- Máy chủ phải chạy qua môi trường Python phụ thuộc theo requirements của dự án.
- Giao diện phải build/chạy bằng Node/Vite theo cấu hình hiện hành.
- Docker Compose phải cung cấp dịch vụ giao diện/máy chủ và health check API.
- Thông tin kết nối cơ sở dữ liệu, khóa đăng nhập, địa chỉ giao diện được phép kết nối, thư mục lưu tệp và cấu hình mô hình phải được đặt trong cấu hình môi trường, không gắn cố định với máy của người phát triển.

## 8. Các đường dẫn API chính

API giúp giao diện gửi yêu cầu và nhận dữ liệu từ máy chủ. Các đường dẫn dưới đây thuộc máy chủ. Ngoại trừ kiểm tra tình trạng, đăng ký và đăng nhập, người dùng cần đăng nhập trước.

- **Kiểm tra dịch vụ:** GET /health và GET / — xem máy chủ có hoạt động không.
- **Tài khoản:** POST /api/auth/register, POST /api/auth/login, GET /api/auth/me — tạo tài khoản, đăng nhập và xem thông tin tài khoản hiện tại.
- **Vị trí tuyển dụng:** GET/POST /api/jobs và GET/PUT/DELETE /api/jobs/{job_id} — xem danh sách, tạo, xem chi tiết, sửa hoặc xóa vị trí.
- **Mô tả công việc:** POST /api/jobs/{job_id}/analyze, GET /api/jobs/{job_id}/analysis, POST /api/jobs/{job_id}/upload-jd — tải và phân tích mô tả công việc.
- **CV:** POST /api/resumes/upload và POST /api/resumes/upload-batch — tải một hoặc nhiều CV.
- **Ứng viên:** GET /api/candidates và GET /api/candidates/{candidate_id} — tìm và xem hồ sơ ứng viên.
- **So khớp:** POST /api/matching/jobs/{job_id}/match/{candidate_id}, GET /api/matching/jobs/{job_id}/matches, POST /api/matching/jobs/{job_id}/screen-batch, GET /api/matching/matches/{match_id}, POST /api/matching/evaluate — tính điểm, xem xếp hạng, xử lý nhiều hồ sơ và đánh giá.
- **Trạng thái mô hình:** GET /api/model/status và GET /api/matching/model/status — xem mô hình có sẵn hay không.
- **Trang tổng quan:** GET /api/dashboard/overview — lấy số liệu tổng hợp.

Các mã phản hồi thường gặp: 200 hoặc 201 là thành công; 400 là dữ liệu/tệp không hợp lệ; 401 là chưa đăng nhập hoặc thông tin đăng nhập không đúng; 403 là không đủ quyền; 404 là không tìm thấy dữ liệu; 409 là email đã được đăng ký; 422 là dữ liệu sai định dạng hoặc không đọc được nội dung.

## 9. Các tình huống sử dụng chính

### UC-01 Tạo tài khoản và đăng nhập

Nhà tuyển dụng mở trang đăng ký, nhập tên, email và mật khẩu. Ứng dụng kiểm tra dữ liệu, tạo tài khoản rồi chuyển người dùng vào trang tổng quan. Nếu email đã được dùng hoặc thông tin đăng nhập sai, ứng dụng báo lỗi và không tạo phiên đăng nhập.

### UC-02 Tạo vị trí và đọc mô tả công việc

Nhà tuyển dụng tạo vị trí và nhập các tiêu chí cần tìm. Sau khi lưu vị trí, họ có thể tải mô tả công việc để ứng dụng đọc và gợi ý kỹ năng, yêu cầu. Nhà tuyển dụng xem lại rồi tự chọn áp dụng gợi ý. Tệp sai loại, quá 5 MB hoặc không đọc được sẽ được báo lỗi.

### UC-03 Tải CV và sàng lọc hồ sơ

Nhà tuyển dụng chọn CV PDF hoặc DOCX để tải lên. Ứng dụng đọc nội dung và tạo hồ sơ ứng viên. Sau đó, người dùng chọn vị trí và yêu cầu so khớp. Ứng dụng lưu điểm và mở danh sách xếp hạng. Nếu tải nhiều CV, mỗi tệp có kết quả riêng; một tệp lỗi không nhất thiết làm hỏng các tệp còn lại.

### UC-04 Xem kết quả và tìm ứng viên

Nhà tuyển dụng mở kết quả của một vị trí, tìm theo tên, lọc theo nhãn hoặc độ tin cậy rồi chọn một ứng viên để xem các điểm thành phần và kỹ năng phù hợp/chưa phù hợp. Nếu chưa có kết quả hoặc vị trí không tồn tại, ứng dụng hiển thị trạng thái tương ứng.

## 10. Những việc cần kiểm tra khi nghiệm thu

1. Người dùng mới đăng ký và đăng nhập được; email đã dùng bị từ chối; các chức năng riêng tư từ chối yêu cầu không có mã đăng nhập hợp lệ.
2. Tạo/sửa/xem/xóa vị trí hợp lệ hoạt động qua giao diện/API; dữ liệu sau tải lại vẫn còn trong DB cấu hình.
3. PDF/DOCX tối đa 5 MB có văn bản đọc được tạo hồ sơ; TXT không được nhận làm CV; lỗi định dạng/quá cỡ/scan không đọc được được báo rõ.
4. JD PDF/DOCX/TXT được phân tích và gợi ý, nhưng chỉ cập nhật vị trí sau hành động áp dụng của người dùng.
5. Kết quả so khớp nằm trong khoảng 0–100 và có các điểm thành phần; chạy lại cùng một hồ sơ cho cùng vị trí sẽ cập nhật kết quả cũ.
6. Sàng lọc 1–100 ứng viên trả được completed/failed tương ứng; xếp hạng hỗ trợ tìm kiếm, nhãn và ngưỡng độ tin cậy.
7. Khi classifier không khả dụng, API/giao diện thể hiện cách tính dự phòng; không hiển thị độ tin cậy giả.
8. Trang tổng quan hiển thị số liệu đã lưu; đường dẫn /health báo máy chủ sẵn sàng.
9. Lưu lại kết quả kiểm thử. Tài liệu này không khẳng định các tiêu chí trên đã đạt cho tới khi có bằng chứng chạy thử.

## 11. Phần còn thiếu và việc cần thống nhất

- **GAP-01 — Chưa sửa được thông tin hồ sơ trên giao diện.** Nên cho phép người tuyển dụng kiểm tra và sửa thông tin ứng dụng đọc từ CV.
- **GAP-02 — Chưa có quy định xóa CV và hồ sơ.** Cần thống nhất ai được xóa, lưu hồ sơ trong bao lâu và xử lý yêu cầu xóa thông tin cá nhân như thế nào.
- **GAP-03 — Dữ liệu chưa tách theo tài khoản.** Cần quyết định đồ án dùng chung dữ liệu hay mỗi nhà tuyển dụng chỉ được xem hồ sơ và vị trí của mình.
- **GAP-04 — Thiếu một số chức năng tài khoản.** Chưa có xác minh email, quên/đổi mật khẩu, đăng xuất khỏi mọi thiết bị hay giới hạn số lần đăng nhập sai.
- **GAP-05 — Chưa biết mức chính xác khi đọc CV.** Ứng dụng chưa cho biết trường nào đọc chưa chắc và chưa được đánh giá bằng bộ CV đã kiểm tra thủ công.
- **GAP-06 — Cách tính điểm chưa được xác nhận bởi nhà tuyển dụng.** Một số điểm dựa trên quy tắc đơn giản; cần xem lại trọng số và kiểm tra khả năng gây bất lợi cho nhóm ứng viên nào đó.
- **GAP-07 — Dữ liệu huấn luyện chưa đại diện cho tuyển dụng thật.** Một phần dữ liệu được tạo tổng hợp hoặc có hỗ trợ từ mô hình, chưa có nhãn đánh giá độc lập của con người.
- **GAP-08 — Chưa có mục tiêu vận hành.** Chưa đo số người dùng đồng thời, tốc độ phản hồi, sao lưu hoặc thời gian khôi phục khi xảy ra sự cố.
- **GAP-09 — Chưa xác nhận biện pháp bảo vệ tệp tải lên.** Cần kiểm tra loại tệp thực tế và cân nhắc quét phần mềm độc hại trước khi dùng dữ liệu thật.
- **GAP-10 — Chưa ghi lại đầy đủ thao tác với hồ sơ cá nhân.** Nếu cần truy vết, cần lưu ai đã xem, tải xuống, sửa hoặc xóa hồ sơ.

## 12. Cách hiểu trạng thái

- **Đã có trong mã nguồn**
  - **Ý nghĩa:** Đã tìm thấy phần triển khai trong dự án. Điều này chưa khẳng định chức năng đã vượt qua kiểm thử.
- **Cần kiểm thử**
  - **Ý nghĩa:** Cần chạy thử và lưu lại kết quả trước khi nộp.
- **Cần xác nhận**
  - **Ý nghĩa:** Sinh viên và giảng viên cần thống nhất phạm vi hoặc cách làm.
- **Chưa triển khai**
  - **Ý nghĩa:** Chức năng chưa được xây dựng, không nên mô tả là đã hoàn thành.

---

**Trước khi nộp:** bổ sung tên người soạn và người duyệt theo mẫu của khoa; trao đổi với giảng viên về phạm vi sử dụng, quyền xem CV, các mục tiêu vận hành còn bỏ ngỏ và kết quả kiểm thử.
