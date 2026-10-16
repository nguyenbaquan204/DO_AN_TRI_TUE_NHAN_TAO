# Bản báo cáo XeLaTeX theo mẫu AIP202

## Biên dịch trên Overleaf

1. Tải lên `bao_cao_overleaf.zip` bằng **New Project → Upload Project**.
2. Chọn compiler **XeLaTeX** và main document `do-an.tex` nếu Overleaf chưa tự nhận.
3. Bấm **Recompile**.

Nếu chạy trên máy đã cài TeX Live/MiKTeX và latexmk, mở terminal tại thư mục này và chạy:

```bash
latexmk -xelatex do-an.tex
```

## Trước khi nộp

- Điền họ tên, mã sinh viên, lớp, giảng viên hướng dẫn và năm học trong `do-an.tex`.
- Đọc và xác nhận lời cam đoan; cá nhân hóa lời cảm ơn.
- Chạy lại pipeline/test và cập nhật tình trạng thực tế vào Chương 4, số liệu vào Chương 5.
- Ảnh `hinh/cv-review.png` là giao diện CV mẫu; thay nếu cần ảnh chụp từ bản chạy cuối.
- Xem lại tài liệu tham khảo, nội dung mẫu, danh mục hình/bảng và toàn bộ PDF sau biên dịch.

Cấu trúc chương giữ theo mẫu của giảng viên. Các tệp style và logo gốc nằm trong `styles/` và `assets/`.
