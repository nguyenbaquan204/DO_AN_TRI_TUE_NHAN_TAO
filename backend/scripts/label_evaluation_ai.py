"""Apply a documented AI review of the frozen local pool, without using model scores."""
import sqlite3, json, hashlib
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PREFIX = '[AI đề xuất; chưa được người xác nhận] '
PARTIAL = {
 (1,17): 'Có thiết kế thương hiệu và ấn phẩm hỗ trợ nội dung marketing; chưa thấy SEO, Google Ads, Analytics và kinh nghiệm chiến dịch 2 năm.',
 (1,20): 'Có nội dung tăng nhận diện thương hiệu và thiết kế; bằng chứng bị cắt, chưa xác nhận SEO, Ads, Analytics hoặc 2 năm marketing.',
 (2,18): 'Có kế toán, lập báo cáo tài chính và học vấn kế toán; chưa thấy Excel, mô hình tài chính hay dự báo ngân sách. Các mốc 2050–2058 là tương lai, cần kiểm tra CV mẫu, không công nhận 4 năm như kinh nghiệm đã xác minh.',
 (4,20): 'Có English Teaching và hoạt động tình nguyện; chưa thấy soạn giáo án, quản lý lớp, chuyên ngành sư phạm hay một năm giảng dạy.',
 (8,17): 'Có thiết kế đồ họa, in ấn, minh họa, thương hiệu và học vấn mỹ thuật; mới khoảng 5 tháng, chưa xác nhận Photoshop, Illustrator và portfolio.',
 (8,19): 'Có cử nhân thiết kế, phù hợp nền tảng ngành; phần dự án bị lỗi OCR, chưa có kỹ năng công cụ hoặc portfolio kiểm chứng; 3 năm chưa rõ nội dung công việc.',
 (8,20): 'Có thiết kế đồ họa, in ấn, minh họa, thương hiệu; chưa có Photoshop, Illustrator, portfolio và một năm kinh nghiệm được xác nhận.'
}
EVIDENCE = {
 1:'CV chỉ nêu phát triển backend Java/Spring/MySQL/Docker',
 2:'CV chỉ nêu phát triển frontend React/TypeScript/Node.js',
 3:'CV có học vấn CNTT, backend Java và dự án API quản lý tồn kho',
 4:'CV có học vấn CNTT, backend Java và dự án API quản lý tồn kho',
 5:'CV có học vấn CNTT, backend Java và dự án API quản lý tồn kho',
 6:'Bản chụp chỉ còn danh sách kỹ năng backend, thiếu bằng chứng công việc',
 7:'Bản chụp chỉ còn danh sách kỹ năng frontend, thiếu bằng chứng công việc',
 8:'CV backend CNTT, dự án API tồn kho không chứng minh năng lực vận hành logistics',
 9:'CV frontend và dashboard thương mại điện tử, không chứng minh kinh nghiệm kinh doanh',
 10:'CV backend CNTT, dự án API tồn kho không chứng minh năng lực vận hành logistics',
 11:'CV frontend và dashboard thương mại điện tử, không chứng minh kinh nghiệm kinh doanh',
 13:'CV backend CNTT, dự án API tồn kho không chứng minh năng lực vận hành logistics',
 14:'CV CNTT, giao diện tìm kiếm AI bằng React/Python',
 17:'CV thiết kế đồ họa/mỹ thuật; English không chứng minh năng lực giảng dạy',
 18:'CV kế toán và báo cáo tài chính; mốc thời gian tương lai cần kiểm tra',
 19:'CV chỉ rõ cử nhân thiết kế và ngoại ngữ, nhiều đoạn lỗi OCR',
 20:'CV thiết kế và tình nguyện giảng dạy, nội dung bị cắt'
}
def main():
 db=sqlite3.connect(ROOT/'backend/app.db'); db.row_factory=sqlite3.Row
 rows=[dict(r) for r in db.execute('SELECT * FROM evaluation_pairs ORDER BY id')]
 backup=ROOT/'data/evaluation/backups'; backup.mkdir(parents=True,exist_ok=True)
 stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 with sqlite3.connect(backup/f'before-ai-labels-{stamp}.db') as dest: db.backup(dest)
 report=[]
 with db:
  for row in rows:
   if row['relevance'] is not None or (row['notes'] or '').strip(): continue
   inputs=json.loads(row['inputs']); jid,cid=row['job_id'],row['candidate_id']
   if not inputs['cv_text'].strip():
    relevance=None; reason='CHƯA ĐỦ THÔNG TIN: bản chụp CV rỗng. Cần sửa/trích xuất và tạo lại mẫu; không suy ra không phù hợp.'
   elif (jid,cid) in PARTIAL: relevance=1; reason=PARTIAL[(jid,cid)]
   else:
    if cid not in EVIDENCE: raise ValueError('Unreviewed candidate; stop')
    relevance=0; reason=EVIDENCE[cid]+'. Chưa có bằng chứng đáp ứng yêu cầu cốt lõi của '+row['job_title']+': '+', '.join(inputs['required_skills'])+'. Nhãn phản ánh thông tin trong bản chụp, không khẳng định ứng viên không có năng lực.'
   notes=PREFIX+reason
   db.execute('UPDATE evaluation_pairs SET relevance=?,notes=?,reviewer_id=NULL,reviewed_at=? WHERE id=? AND relevance IS NULL',(relevance,notes,datetime.now(timezone.utc).isoformat(),row['id']))
   report.append({'pair_id':row['id'],'job_id':jid,'candidate_id':cid,'relevance':relevance,'notes':notes,'source':'AI proposal','input_sha256':hashlib.sha256(row['inputs'].encode()).hexdigest()})
 output=ROOT/'data/evaluation/ai_review.json'
 output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'reviewed':len(report),'labels':{str(k):sum(r['relevance']==k for r in report) for k in [0,1,2,None]},'report':str(output)}))
 db.close()
if __name__=='__main__': main()
