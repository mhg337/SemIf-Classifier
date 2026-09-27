import datetime

def create_report(pdf_filename, results_data, execution_time):
    """
    분류 결과를 받아 예쁜 포맷의 마크다운 보고서 텍스트를 생성하고 파일로 저장합니다.
    """
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 보고서 텍스트 뼈대 구성
    report_content = f"""# 📊 AI 문서 자동 분류 파이프라인 결과 보고서

## 1. 분석 개요
* **대상 문서**: `{pdf_filename}`
* **분석 일시**: {now}
* **소요 시간**: 약 {execution_time:.2f}초
* **사용 모델**: Qwen3.5-4B (SemIf 프레임워크)

## 2. 카테고리별 핵심 분류 결과
"""
    
    # 결과 데이터 포맷팅
    for key, data in results_data.items():
        category_name = {"policy": "정책(수단)", "industry": "산업분야", "tech": "기술분야"}.get(key, key)
        best_option = data['best_option']
        best_prob = data['best_prob']
        
        report_content += f"* ▶ **{category_name}**: **{best_option}** ({best_prob:.2f}%)\n"

    report_content += "\n---\n*본 보고서는 Docling 및 SemIf 모델을 활용하여 자동 생성되었습니다.*\n"
    
    # 3. 마크다운 파일로 저장
    report_filename = f"classification_report_{datetime.datetime.now().strftime('%Y%md_%H%M%S')}.md"
    with open(report_filename, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    return report_content, report_filename
