import json
import os
import subprocess
import glob
import time
import re
import datetime

def main():
    txt_folder = "txts"
    if not os.path.exists(txt_folder):
        os.makedirs(txt_folder)
        return

    txt_files = glob.glob(os.path.join(txt_folder, "*.txt"))
    if not txt_files:
        print("처리할 TXT 파일이 없습니다.")
        return


    options_policy = [{"id": "실증·테스트베드", "description": "실제 환경 테스트"}, {"id": "금융/세제지원", "description": "자금 혜택"}]
    options_industry = [{"id": "반도체", "description": "메모리 시스템"}, {"id": "소재·부품·장비", "description": "기초 소재"}]
    options_tech = [{"id": "첨단소재", "description": "신소재"}, {"id": "AI/데이터", "description": "빅데이터"}]

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_content = f"# AI 자동 분류 마스터 보고서\n\n"
    report_content += f"* **분석 일시**: {now}\n\n---\n\n"

    global_doc_count = 1
    start_time_total = time.time()

    for txt_path in txt_files:
        filename = os.path.basename(txt_path)
        
        with open(txt_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        pattern = r"\[문서 제목:\s*(.*?)\](.*?)(?=\[문서 제목:|\Z)"
        documents = re.findall(pattern, full_text, re.DOTALL)

        if not documents:
            documents = [(filename, full_text)]

        for doc_title, doc_content in documents:
            clean_title = doc_title.strip()
            safe_state_text = f"[문서 제목: {clean_title}]\n{doc_content.strip()}"[:4000]

            print(f"[{global_doc_count}] '{clean_title}' 분석 중...")

            temp_input, temp_output = "temp_input.jsonl", "temp_results.jsonl"
            if os.path.exists(temp_input): os.remove(temp_input)
            if os.path.exists(temp_output): os.remove(temp_output)

            tasks = [
                {"id": "policy", "state": safe_state_text, "question": "핵심 정책(수단)?", "options": options_policy},
                {"id": "industry", "state": safe_state_text, "question": "주된 산업분야?", "options": options_industry},
                {"id": "tech", "state": safe_state_text, "question": "핵심 기술분야?", "options": options_tech}
            ]
            
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
            
            try:
                subprocess.run(cmd, env=env, check=True, stdout=subprocess.DEVNULL)
            except subprocess.CalledProcessError:
                print(f"   에러 발생 건너뜁니다.")
                report_content += f"## {global_doc_count}. 📄 {clean_title}\n*  분석 중 오류 발생\n\n---\n\n"
                global_doc_count += 1
                continue

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

            report_content += f"## {global_doc_count}. 📄 {clean_title}\n"
            for key, data in results_data.items():
                category_name = {"policy": "정책(수단)", "industry": "산업분야", "tech": "기술분야"}.get(key, key)
                best_option = data['best_option']
                best_prob = data['best_prob']
                report_content += f"* ▶ **{category_name}**: **{best_option}** ({best_prob:.2f}%)\n"
            report_content += "\n---\n\n"

            if os.path.exists(temp_input): os.remove(temp_input)
            if os.path.exists(temp_output): os.remove(temp_output)
            
            global_doc_count += 1

    total_time = time.time() - start_time_total
    report_content += f"\n*본 보고서는 SemIf 프레임워크를 활용하여 자동 생성되었습니다. (총 소요 시간: 약 {total_time:.2f}초)*\n"

    combined_report_name = "final_master_report.md"
    with open(combined_report_name, "w", encoding="utf-8") as f:
        f.write(report_content)
        

if __name__ == "__main__":
    main()
