# backend/app/tools/general/date_time.py
from langchain_core.tools import tool
from typing import Dict, Any
from datetime import datetime, timedelta
import logging

from app.tools.general.general_utils import format_general_response

logger = logging.getLogger(__name__)


@tool
def date_time_tool(query: str = "current_time") -> Dict[str, Any]:
    """
    Trả về thông tin thời gian hiện tại, ngày tháng, hoặc tính toán thời gian
    """
    now = datetime.now()

    if "ngày" in query.lower() or "date" in query.lower():
        result = f"Hôm nay là ngày **{now.strftime('%d/%m/%Y')}** ({now.strftime('%A')})"
    elif "giờ" in query.lower() or "time" in query.lower():
        result = f"Bây giờ là **{now.strftime('%H:%M:%S')}**"
    elif "tuần" in query.lower():
        result = f"Tuần thứ **{now.isocalendar()[1]}** năm {now.year}"
    elif "tháng" in query.lower():
        result = f"Tháng **{now.month}** năm {now.year}"
    else:
        result = f"""
**Thời gian hiện tại:**
- Ngày: {now.strftime('%d/%m/%Y')}
- Giờ: {now.strftime('%H:%M:%S')}
- Thứ: {now.strftime('%A')}
- Tuần: {now.isocalendar()[1]}
"""

    return format_general_response(answer=result, source="date_time")