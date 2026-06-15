from typing import TypedDict, Annotated, List, Dict, Any, Optional
from langgraph.graph import add_messages
from langchain_core.messages import BaseMessage
from datetime import datetime


class AgentState(TypedDict, total=False):
    """
    State chung cho toàn bộ Multi-Agent System (Đã sửa lỗi nuốt cờ hiệu)
    """
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Multi-Agent Control
    current_agent: Optional[str]                    # "business", "document", "vision", "general"
    intent_classification: Optional[Dict[str, Any]]
    
    # Business Agent specific
    pending_confirmation: Optional[Dict[str, Any]]
    confirmation_id: Optional[str]
    confirmation_timeout: Optional[datetime]
    
    # Document & Vision related
    active_document: Optional[str]                  # Tên file đang tương tác
    context_files: List[str]                        # Danh sách file liên quan trong session
    
    # 🔥 THÊM VÀO ĐỂ QUẢN LÝ TIẾN TRÌNH TÓM TẮT TÀI LIỆU (CHẶN LOOP)
    force_summary: Optional[bool]                   # Ép buộc tóm tắt (khi user gõ lệnh hệ thống)
    pending_summary: Optional[bool]                 # Đang chờ tóm tắt sau upload
    is_auto_summary: Optional[bool]                 # Cờ kích hoạt luồng tóm tắt tự động
    summary_lock: Optional[bool]                    # Khóa luồng khi đang thực thi tool
    
    # General tracking
    thread_id: Optional[str]
    error_count: Optional[int]                      # Chuẩn hóa lại kiểu dữ liệu của TypedDict
    last_error: Optional[str] 
    metadata: Optional[Dict[str, Any]]              # Dùng để mở rộng sau này