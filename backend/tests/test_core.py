import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.cv_information_extractor import CVInformationExtractor
from app.services.jd_parser import JDParser
from app.services.skill_extractor import SkillExtractor


def test_cv_email_extraction():
    text = "John Doe\njohn.doe@example.com\n+1 555 010 2020"
    assert CVInformationExtractor.extract_email(text) == "john.doe@example.com"


def test_vietnamese_image_cv_information_extraction():
    text = r"""Thông tin liên hệ
+84 900 000 000
ungvien\@example.com
www.portfolio.example.com
Kỹ năng liên quan
* Thiết kế bản in về kỹ thuật số
* Vẽ minh hoạ
* Xây dựng thương hiệu
Công việc Tình nguyện và Sở thích
* Giáo viên Tiếng Anh tình nguyện
Minh Nguyễn __ NHÀ THIẾT KẾ ĐỒ HỌA
Kinh nghiệm làm việc
Thực tập sinh
Bảo tàng Nghệ thuật Đương đại
Tháng 1/2022 đến Tháng 6/2022 (5 tháng)
Học vấn
CỬ NHÂN
Đại học Nghệ Thuật, 2022
Bằng cấp
Học viện, Năm
* Liệt kê một thành tích
* Liệt kê một thành tích"""
    assert CVInformationExtractor.extract_name(text) == "Minh Nguyễn"
    assert CVInformationExtractor.extract_email(text) == "ungvien@example.com"
    assert CVInformationExtractor.extract_phone(text) == "+84 900 000 000"
    assert CVInformationExtractor.extract_links(text)["portfolio"] == "https://www.portfolio.example.com"
    assert CVInformationExtractor.extract_experience_years(text) == 5 / 12
    assert "Đại học Nghệ Thuật, 2022" in CVInformationExtractor.extract_education(text)["text"]
    assert CVInformationExtractor.extract_languages(text) == ["English"]
    assert CVInformationExtractor.extract_certificates(text) == []
    flattened = "Tổ chức Trẻ em Bình An Minh Nguyễn __ NHÀ THIẾT KẾ ĐỒ HỌA Kinh nghiệm làm việc Thực tập sinh Bảo tàng Nghệ thuật Đương đại Tháng 1/2022 đến Tháng 6/2022 (5 tháng)"
    assert CVInformationExtractor.extract_name(flattened) == "Minh Nguyễn"


def test_ocr_typos_still_extract_vietnamese_profile_fields():
    text = """Thông tin liên hệ\nungvien@example.com\nKỹ năng liên quan\nThiết kế ban in về kỹ thuột số\nVẽ minh hoạ\nXây dựng thương hiệu\nMinh Nguyễn __ NHÀ THIẾT KE ĐỒ HOA\nTháng 1/2022 đến Tháng 6/2022 (5 thang)\nHọc vấn\ncu CUNHAN\n=F DoihocMyThuot 2022\nBẰNG CẤP\nHoe viện, Nam\nLiét kê một thònh tích"""
    assert CVInformationExtractor.extract_name(text) == "Minh Nguyễn"
    assert abs(CVInformationExtractor.extract_experience_years(text) - 5 / 12) < 1e-9
    assert CVInformationExtractor.extract_education(text)["text"] == "Cử nhân\nĐại học Mỹ Thuật, 2022"
    assert CVInformationExtractor.extract_certificates(text) == []
    assert {"Thiết kế in ấn", "Vẽ minh họa", "Xây dựng thương hiệu"} <= set(SkillExtractor.extract(text))


def test_work_history_date_ranges_do_not_pollute_education_or_experience():
    text = """KINH NGHIỆM LÀM VIỆC
2055 - 2058 2054 - 2055
Công ty: Thynk Unlimited Công ty: Thynk Unlimited
Vị trí: Chuyên viên kế toán Vị trí: Chuyên viên kế toán
2054
Công ty: Thynk Unlimited
Vị trí: Thực tập sinh
TRÌNH ĐỘ HỌC VẤN
2050 - 2054
Đại Học Thynk Unlimited
Tốt nghiệp loại giỏi chuyên ngành Kế Toán
KỸ NĂNG
Tin học văn phòng"""
    assert CVInformationExtractor.extract_experience_years(text) == 4
    assert CVInformationExtractor.extract_education(text)["text"].startswith("2050 - 2054")
    experience = CVInformationExtractor.extract_work_experience(text)["text"]
    assert "2055 - 2058" in experience
    assert "2050 - 2054" not in experience


def test_name_on_first_cv_line_is_not_confused_with_employer_name():
    text = "Neil Tran\nNgày sinh: 02/05/2045\nKINH NGHIỆM LÀM VIỆC\nCông ty: Thynk Unlimited"
    assert CVInformationExtractor.extract_name(text) == "Neil Tran"


def test_skill_extraction_handles_aliases():
    text = "Worked with ReactJS, Spring Boot, and My SQL"
    skills = SkillExtractor.extract(text)
    assert "React" in skills
    assert "Spring Boot" in skills
    assert "MySQL" in skills


def test_skill_extraction_recognizes_vietnamese_design_skills():
    skills = SkillExtractor.extract("Thiết kế bản in về kỹ thuật số, vẽ minh hoạ và xây dựng thương hiệu")
    assert "Thiết kế in ấn" in skills
    assert "Vẽ minh họa" in skills
    assert "Xây dựng thương hiệu" in skills


def test_skill_extraction_uses_word_boundaries():
    skills = SkillExtractor.extract("The organization is available for a reactive JSON API.")
    assert "AI" not in skills
    assert "React" not in skills
    assert "JavaScript" not in skills


def test_jd_parser_extracts_required_skills():
    jd = "Backend Developer with Java, Spring Boot, MySQL, Git and Docker requirements. Need 2 years experience."
    parsed = JDParser.analyze(jd, job_title="Backend Developer")
    assert "Java" in parsed["required_skills"]
    assert "MySQL" in parsed["required_skills"]
    assert parsed["experience_years"] == 2.0



def test_matching_uses_evidence_and_handles_empty_text():
    from app.ai.matching_engine import MatchingEngine
    score = MatchingEngine().score_candidate("Bachelor\
2 years experience\
Built project", "", ["Python"], ["Python"], 3, "Bachelor")
    assert score["experience_score"] < 100
    assert score["education_score"] == 100
    assert score["project_score"] > 0
    assert score["experience_gap"] == 1
    assert score["semantic_score"] == 0
    assert score["embedding_status"] in {"sentence-transformer", "tfidf-fallback"}


def test_jd_parser_does_not_fabricate_sections():
    parsed = JDParser.analyze("Backend role. Required: Python. Preferred: Docker. Responsibilities: Build APIs.")
    assert parsed["responsibilities"] == ["Build APIs."]
    assert parsed["qualifications"] == []
    assert parsed["required_skills"] == ["Python"]
    assert parsed["preferred_skills"] == ["Docker"]
    assert parsed["education_required"] is None


def test_jd_parser_handles_preferred_qualifications_heading():
    parsed = JDParser.analyze("Required skills: Python. Preferred Qualifications: Docker. Responsibilities: Build APIs.")
    assert parsed["required_skills"] == ["Python"]
    assert parsed["preferred_skills"] == ["Docker"]
