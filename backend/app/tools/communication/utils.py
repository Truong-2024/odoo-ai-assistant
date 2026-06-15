# backend/app/tools/communication/utils.py
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


def format_report_summary(report_data: Dict) -> str:
    """Định dạng báo cáo tóm tắt đẹp"""
    return f"""
📊 **BÁO CÁO TÓM TẮT**

**Kỳ:** {report_data.get('period', 'N/A')}
**Tổng đơn hàng:** {report_data.get('total_orders', 0)}
**Doanh thu tổng:** {report_data.get('total_amount', 0):,.0f} VND
**Đơn đã xác nhận:** {report_data.get('confirmed_orders', 0)}
**Doanh thu đã xác nhận:** {report_data.get('confirmed_amount', 0):,.0f} VND
**Ngày tạo:** {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""


def validate_email(email: str) -> bool:
    """Kiểm tra email hợp lệ cơ bản"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None