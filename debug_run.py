import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Process
from src.agents import MarketingAgents
from src.tasks import MarketingTasks

# Đảm bảo output được flush liên tục trên Windows
import sys
def print_flush(text):
    print(text, flush=True)

load_dotenv()

def step_callback(step):
    print_flush(f"\n[DEBUG] Agent đang thực hiện bước: {step}")

def run_debug_system():
    print_flush("\n" + "="*50)
    print_flush("🚀 KHỞI ĐỘNG HỆ THỐNG DEBUG...")
    print_flush("="*50)
    
    # 1. Khởi tạo Factory
    try:
        print_flush("--- Đang khởi tạo Agents & Tasks... ---")
        agents_factory = MarketingAgents()
        tasks_factory = MarketingTasks()
    except Exception as e:
        print_flush(f"❌ Lỗi khởi tạo Factory: {e}")
        return

    # 2. Triệu tập các Chuyên gia
    search_analyst = agents_factory.search_analyst()
    content_strategist = agents_factory.content_strategist()
    business_reporter = agents_factory.business_reporter()

    # 3. Phân công nhiệm vụ
    research_task = tasks_factory.research_task(search_analyst, "Báo cáo thị trường smartphone 2026")
    content_task = tasks_factory.content_creation_task(content_strategist)
    report_task = tasks_factory.analytics_report_task(business_reporter)

    # 4. Thiết lập Crew
    print_flush("--- Đang chuẩn bị Quân đội (Crew)... ---")
    crew = Crew(
        agents=[search_analyst, content_strategist, business_reporter],
        tasks=[research_task, content_task, report_task],
        process=Process.sequential,
        verbose=True,
        step_callback=step_callback # Theo dõi từng bước
    )

    # 5. Khởi động
    print_flush("\n--- BẮT ĐẦU THỰC THI (KICKOFF) ---")
    try:
        result = crew.kickoff()
        print_flush("\n--- KICKOFF HOÀN TẤT ---")
        
        # Thử đẩy lên Drive thủ công nếu Agent chưa làm
        try:
            from src.tools import CloudPublishTools
            print_flush("--- Đang ép đẩy lên Google Docs... ---")
            CloudPublishTools.publish_to_docs(
                title=f"DEBUG Final Report {datetime.now().strftime('%H%M')}",
                content=str(result)
            )
        except Exception as e:
            print_flush(f"⚠️ Không thể đẩy lên Drive: {e}")
            
    except Exception as e:
        print_flush(f"❌ Lỗi nghiêm trọng khi chạy Crew: {e}")

if __name__ == "__main__":
    from datetime import datetime
    run_debug_system()
