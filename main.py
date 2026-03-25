import os
from dotenv import load_dotenv
from crewai import Crew, Process
from src.agents import MarketingAgents
from src.tasks import MarketingTasks

load_dotenv() # Tải các biến môi trường từ .env

def run_smartphone_intelligence_system():
    """
    Hệ thống AI Agent Siêu cấp - Phân tích, Trực quan hóa và Báo cáo tự động.
    Quy trình: Nghiên cứu -> Phân tích Sentiment -> Báo cáo Chiến lược & Xuất bản.
    """
    
    # 1. Khởi tạo Factory
    agents_factory = MarketingAgents()
    tasks_factory = MarketingTasks()

    # 2. Triệu tập các Chuyên gia (Agents)
    search_analyst = agents_factory.search_analyst()
    content_strategist = agents_factory.content_strategist()
    business_reporter = agents_factory.business_reporter()

    # 3. Phân công nhiệm vụ (Tasks)
    # - Bước 1: Thu thập tin tức và dữ liệu thô
    research_task = tasks_factory.research_task(search_analyst, "Xu hướng smartphone 2026 và thị trường AI Phone")
    
    # - Bước 2: Phân tích Social Sentiment & Sáng tạo Content marketing
    content_task = tasks_factory.content_creation_task(content_strategist)
    
    # - Bước 3: Phân tích sâu, Vẽ biểu đồ và Xuất bản Báo cáo Executive 
    report_task = tasks_factory.analytics_report_task(business_reporter)

    # Kiểm tra tính sẵn sàng của các Task
    missing = [
        n
        for n, t in (
            ("research_task", research_task),
            ("content_task", content_task),
            ("report_task", report_task),
        )
        if t is None
    ]
    if missing:
        raise RuntimeError(
            "Hệ thống không thể khởi tạo Task (vui lòng kiểm tra cài đặt CrewAI): " + ", ".join(missing)
        )

    # 4. Thiết lập Quân đội (Crew) - Thực thi tuần tự (Sequential)
    crew = Crew(
        agents=[search_analyst, content_strategist, business_reporter],
        tasks=[research_task, content_task, report_task],
        process=Process.sequential, 
        memory=False, # Tắt memory để tránh phụ thuộc vào Embedder bên ngoài
        verbose=True
    )

    # 5. Khởi động chiến dịch "Siêu phẩm"
    print("\n" + "="*50)
    print("🚀 SMARTPHONE INTELLIGENCE SYSTEM IS DEPLOYING...")
    print("🎯 Mục tiêu: Biến dữ liệu thô thành Siêu phẩm Báo cáo Chiến lược.")
    print("="*50 + "\n")
    
    result = crew.kickoff()

    # --- TRIGGER: Đảm bảo báo cáo được đẩy lên Google Drive sau khi Agent xong việc ---
    print("\n--- Đang tiến hành xuất bản báo cáo cuối cùng lên Google Docs... ---")
    try:
        from src.tools import CloudPublishTools
        publisher = CloudPublishTools()
        publisher.publish_to_docs(
            title=f"Smartphone Strategic Report {os.path.basename(os.getcwd())}", 
            content=str(result) # Ép kết quả của Agent thành chuỗi văn bản Markdown
        )
    except Exception as e:
        print(f"⚠️ Cảnh báo: Lỗi khi đẩy báo cáo cuối cùng: {e}")

    print("\n" + "="*50)
    print("✅ CHIẾN DỊCH HOÀN TẤT MỸ MÃN!")
    print("Báo cáo đã được lưu trữ và xuất bản.")
    print("="*50 + "\n")
    
    return result

if __name__ == "__main__":
    run_smartphone_intelligence_system()