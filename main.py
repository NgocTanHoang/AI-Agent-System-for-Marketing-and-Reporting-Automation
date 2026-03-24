import os
from dotenv import load_dotenv
from crewai import Crew, Process
from src.agents import MarketingAgents
from src.tasks import MarketingTasks

load_dotenv() # Tải các biến môi trường từ .env

def run_smartphone_intelligence_system():
    # 1. Khởi tạo
    agents_factory = MarketingAgents()
    tasks_factory = MarketingTasks()

    # 2. Tạo các Agents 
    search_analyst = agents_factory.search_analyst()
    content_strategist = agents_factory.content_strategist()
    business_reporter = agents_factory.business_reporter()

    # 3. Tạo các Tasks 
    research_task = tasks_factory.research_task(search_analyst, "Xu hướng smartphone 2026")
    content_task = tasks_factory.content_creation_task(content_strategist)
    report_task = tasks_factory.analytics_report_task(business_reporter)

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
            "Could not build Task (is CrewAI installed?): " + ", ".join(missing)
        )

    # 4. Thiết lập Quân đội (Crew)
    crew = Crew(
        agents=[search_analyst, content_strategist, business_reporter],
        tasks=[research_task, content_task, report_task],
        process=Process.sequential, 
        memory=False, # Tắt memory để không cần dùng Embedder (tránh lỗi ModuleNotfound)
        verbose=True
    )

    # 5. Khởi động chiến dịch
    print("\n--- Smartphone Intelligence System is starting... ---")
    result = crew.kickoff()

    print("\nMarket analysis run finished.")
    print("\n--- Done. ---")
    
    return result

if __name__ == "__main__":
    run_smartphone_intelligence_system()