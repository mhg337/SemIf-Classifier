import json
import os
import time
import subprocess
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

import report_generator

def main():
    start_time = time.time()
    pdf_path = "sample.pdf"
    
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_table_structure = True
    pipeline_options.accelerator_options.device = "auto"

    converter = DocumentConverter(
        allowed_formats=[InputFormat.PDF],
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )

    result = converter.convert(pdf_path)
    safe_state_text = result.document.export_to_markdown().strip()[:4000]

    options_policy = [{"id": "실증·테스트베드", "description": "실제 환경 테스트"}, {"id": "금융/세제지원", "description": "자금 혜택"}]
    options_industry = [{"id": "반도체", "description": "메모리 시스템"}, {"id": "소재·부품·장비", "description": "기초 소재"}]
    options_tech = [{"id": "첨단소재", "description": "신소재"}, {"id": "AI/데이터", "description": "빅데이터"}]

    tasks = [
        {"id": "policy", "state": safe_state_text, "question": "핵심 정책(수단)?", "options": options_policy},
        {"id": "industry", "state": safe_state_text, "question": "주된 산업분야?", "options": options_industry},
        {"id": "tech", "state": safe_state_text, "question": "핵심 기술분야?", "options": options_tech}
    ]

    temp_input = "temp_input.jsonl"
    temp_output = "temp_results.jsonl"
    
    with open(temp_input, "w", encoding="utf-8") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")

    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = "0"
    
    cmd = [
        "semif-score", "--mode", "shared", "--backend", "llamacpp",
        "--gguf", "./models/Qwen_Qwen3.5-4B-Q4_K_M.gguf",
        "--model", "Qwen/Qwen3.5-4B", "--revision", "851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a",
        "--input", temp_input, "--output", temp_output
    ]
    subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    results_data = {}
    with open(temp_output, "r", encoding="utf-8") as f:
        for line in f:
            res = json.loads(line)
            probs = res["probabilities"]
            max_idx = probs.index(max(probs))
            
            results_data[res["id"]] = {
                "best_option": res["option_ids"][max_idx],
                "best_prob": probs[max_idx] * 100
            }

    execution_time = time.time() - start_time
    report_text, saved_file = report_generator.create_report(pdf_path, results_data, execution_time)
    
    print(report_text)

    os.remove(temp_input)
    os.remove(temp_output)

if __name__ == "__main__":
    main()
