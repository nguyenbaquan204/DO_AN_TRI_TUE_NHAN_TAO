import { useEffect, useState } from 'react';
import axios from 'axios';
const API = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000') + '/api/experiments';
export default function ExperimentsPage() {
  const [pairs, setPairs] = useState([]), [job, setJob] = useState(''), [selected, setSelected] = useState('');
  const [grade, setGrade] = useState(''), [notes, setNotes] = useState(''), [busy, setBusy] = useState(false);
  const [error, setError] = useState(''), [report, setReport] = useState(null);
  const config = () => ({ headers: { Authorization: `Bearer ${localStorage.getItem('token')}` } });
  const load = async () => { const r = await axios.get(API + '/pairs', config()); setPairs(r.data); };
  const action = async (fn) => { setBusy(true); setError(''); try { await fn(); } catch(e) { setError(typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Không thực hiện được. Hãy kiểm tra kết nối và đăng nhập.'); } finally { setBusy(false); } };
  useEffect(() => { action(load); }, []);
  const jobs = [...new Map(pairs.map(p => [p.job_id, p.job_title])).entries()];
  const rows = pairs.filter(p => String(p.job_id) === job);
  const pair = rows.find(p => String(p.id) === selected);
  const choose = (id) => { const p = rows.find(x => String(x.id) === id); setSelected(id); setGrade(p?.relevance == null ? '' : String(p.relevance)); setNotes(p?.notes || ''); };
  const download = () => { const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'})); const a=document.createElement('a'); a.href=url; a.download=`danh-gia-${job}.json`; a.click(); URL.revokeObjectURL(url); };
  return <div className="stack">
    <div className="page-heading"><div><h1>Đánh giá mô hình</h1><p>Đọc CV và mô tả công việc, gán nhãn trước khi xem thứ hạng máy tính.</p></div></div>
    <div className="card"><p>0: Thiếu yêu cầu cốt lõi · 1: Đáp ứng một phần · 2: Đáp ứng phần lớn yêu cầu thiết yếu.</p><p>Dữ liệu được chụp tại thời điểm tạo bộ đánh giá. Nhãn AI đề xuất chưa phải đánh giá độc lập của con người. Hồ sơ rỗng cần bổ sung trước khi gán nhãn.</p>
    {!pairs.length && <button disabled={busy} className="primary-button" onClick={() => action(async()=>{await axios.post(API+'/prepare',{},config()); await load();})}>Chuẩn bị bộ CV–vị trí</button>}
    <label>Vị trí đánh giá <select disabled={busy} value={job} onChange={e=>{setJob(e.target.value);setSelected('');setReport(null);}}><option value="">Chọn vị trí</option>{jobs.map(([id,title])=><option key={id} value={id}>{title}</option>)}</select></label>
    {job && <p>Đã gán nhãn {rows.filter(p=>p.relevance !== null).length}/{rows.length} hồ sơ.</p>}
    <label>Hồ sơ <select disabled={busy} value={selected} onChange={e=>choose(e.target.value)}><option value="">Chọn hồ sơ</option>{rows.map(p=><option key={p.id} value={p.id}>{p.candidate_name} — {p.relevance === null ? 'Chưa đánh giá' : (p.label_source === 'ai-proposed' ? 'AI đề xuất' : 'Đã đánh giá')}</option>)}</select></label>
    </div>
    {error && <div role="alert" className="error-box">{error}</div>}
    {busy && <p role="status">Đang xử lý… Lần chạy E5 đầu tiên có thể mất thời gian tải model.</p>}
    {pair && <div className="card"><h2>{pair.candidate_name} / {pair.job_title}</h2><div style={{display:'grid',gridTemplateColumns:'repeat(auto-fit,minmax(260px,1fr))',gap:24}}><div><h3>CV đã duyệt</h3><p style={{whiteSpace:'pre-wrap'}}>{pair.inputs.cv_text || 'Chưa có nội dung'}</p><p>Kỹ năng: {pair.inputs.candidate_skills.join(', ')}</p></div><div><h3>Mô tả công việc</h3><p style={{whiteSpace:'pre-wrap'}}>{pair.inputs.jd_text}</p><p>Kỹ năng bắt buộc: {pair.inputs.required_skills.join(', ')}</p><p>Kinh nghiệm: {pair.inputs.required_experience_years} năm · Học vấn: {pair.inputs.education_required || 'Không yêu cầu'}</p></div></div>
    <label>Mức phù hợp <select disabled={busy} value={grade} onChange={e=>setGrade(e.target.value)}><option value="">Chọn nhãn</option><option value="0">0 — Không phù hợp</option><option value="1">1 — Phù hợp một phần</option><option value="2">2 — Phù hợp cao</option></select></label>
    <label>Lý do đánh giá<textarea disabled={busy} value={notes} onChange={e=>setNotes(e.target.value)} maxLength={2000} rows={3}/></label>
    <button className="primary-button" disabled={busy || grade === '' || notes.trim().length < 3} onClick={()=>action(async()=>{await axios.put(API+'/pairs/'+pair.id,{relevance:Number(grade),notes},config());setReport(null);await load();})}>Lưu nhãn đánh giá</button></div>}
    {job && <button className="primary-button" disabled={busy || rows.length < 5 || rows.some(p=>p.relevance === null)} onClick={()=>action(async()=>{setReport(null);const r=await axios.post(API+'/run/'+job,{},config());setReport(r.data);})}>So sánh TF-IDF và E5</button>}
    {report && <div className="card"><h2>Kết quả trên bộ nhãn</h2>{!report.independent_human_benchmark && <p className="error-box">Có nhãn AI đề xuất: chỉ là so sánh thử nghiệm, không phải độ chính xác trên nhãn người độc lập.</p>}<p>NDCG@5 đo chất lượng thứ tự xếp hạng; MRR@5 đo vị trí hồ sơ đầu tiên có nhãn 1 hoặc 2. Giá trị càng gần 1 càng tốt.</p><p>TF-IDF: NDCG@5 {report.tfidf['ndcg@5']} · MRR@5 {report.tfidf['mrr@5']}</p>{report.hybrid ? <p>E5 + TF-IDF: NDCG@5 {report.hybrid['ndcg@5']} · MRR@5 {report.hybrid['mrr@5']}</p> : <p>E5 chưa khả dụng: chỉ có kết quả TF-IDF, chưa đủ điều kiện so sánh.</p>}
    <div style={{overflowX:'auto'}}><table><thead><tr><th>Ứng viên</th><th>Nhãn người</th><th>TF-IDF</th><th>E5 kết hợp</th><th>Kỹ năng còn thiếu</th></tr></thead><tbody>{report.details.map(r=><tr key={r.candidate_id}><td>{r.candidate_name}</td><td>{r.relevance}</td><td>{r.tfidf}</td><td>{report.semantic_comparison_valid ? r.hybrid : 'Chưa có'}</td><td>{r.missing_skills.join(', ') || 'Không'}</td></tr>)}</tbody></table></div><button className="ghost-button" onClick={download}>Tải báo cáo và dữ liệu đối chiếu</button><p>Tệp tải về chứa nội dung CV đã duyệt; chỉ chia sẻ với người được phép xem hồ sơ.</p></div>}
  </div>;
}
