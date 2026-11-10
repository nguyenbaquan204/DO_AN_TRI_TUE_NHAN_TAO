# Đánh giá xếp hạng CV – mô tả công việc

`matches.json` là tệp cặp CV–vị trí có nhãn đang dùng trong dự án. Trước khi
dùng số đo cho báo cáo, hãy xác nhận từng nhãn là đánh giá độc lập của người;
nhãn minh họa hoặc nhãn do hệ thống tự sinh không phải dữ liệu kiểm chứng.

## Bổ sung nhãn

Mỗi dòng trong `matches.json` cần có:

```json
{"candidate_id": 1, "job_id": 1, "expected_relevance": "high", "labeler": "reviewer-1", "notes": "Đáp ứng yêu cầu Java và kinh nghiệm"}
```

Gán `high` khi hồ sơ đáp ứng phần lớn yêu cầu thiết yếu, `medium` khi chỉ đáp
ứng một phần và cần xem xét, `low` khi thiếu các yêu cầu cốt lõi. Hai người nên
đánh giá độc lập trước khi thống nhất các cặp có ý kiến khác nhau. Người đánh
giá cần xem CV và JD, không xem thứ hạng do mô hình tạo trước khi gán nhãn.

## Chạy so sánh

Trong môi trường Python của backend, chạy:

```powershell
python backend/scripts/evaluate_matching.py --data data/evaluation/matches.json --k 5
```

Lệnh chỉ đọc cơ sở dữ liệu và nhãn. Nó so sánh TF-IDF hiện tại làm mốc với điểm
kết hợp multilingual E5 + TF-IDF, rồi báo NDCG@5 và MRR@5 theo từng vị trí. Nếu
E5 chưa được cài/bật hoặc chưa tải được, kết quả sẽ ghi rõ việc dùng phương án
dự phòng TF-IDF. Các chỉ số chỉ đáng tin khi tập nhãn đủ lớn, đa dạng ngành nghề
và được người đánh giá xác nhận.
