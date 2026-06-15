# backend/tests/e2e/test_full_system.py
import pytest
import time
from langchain_core.messages import HumanMessage
from app.agents.supervisor import app

@pytest.mark.e2e
class TestFullSystem:

    def test_full_flow(self):
        thread_id = f"test_full_{int(time.time())}"
        config = {"configurable": {"thread_id": thread_id}}

        # Test 1: Business Agent
        result1 = app.invoke(
            {"messages": [HumanMessage(content="Tạo đơn hàng cho khách Gemini Furniture mua 2 cái Acoustic Bloc Screens giá 150000")]},
            config=config
        )
        assert "XÁC NHẬN" in result1["messages"][-1].content or "pending_confirmation" in str(result1)

        # Test 2: General Agent
        result2 = app.invoke(
            {"messages": [HumanMessage(content="Bây giờ là mấy giờ?")]},
            config=config
        )
        assert "giờ" in result2["messages"][-1].content.lower()

        # Test 3: Document / Vision simulation
        result3 = app.invoke(
            {"messages": [HumanMessage(content="Tóm tắt file hóa đơn gần nhất")]},
            config=config
        )

        print("✅ Full System Test Passed!")
        print(f"Current Agent: {result3.get('current_agent', 'unknown')}")