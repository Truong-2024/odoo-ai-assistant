# backend/app/tools/general/calculator.py
from langchain_core.tools import tool
from typing import Dict, Any
import logging
import math
import re

from app.tools.general.general_utils import format_general_response, create_general_error

logger = logging.getLogger(__name__)


@tool
def calculator_tool(expression: str) -> Dict[str, Any]:
    """
    Thực hiện tính toán toán học đơn giản và phức tạp
    Hỗ trợ: +, -, *, /, **, %, sqrt, sin, cos, tan, log, etc.
    """
    try:
        # Làm sạch expression
        expr = expression.strip()
        
        # An toàn: chỉ cho phép một số hàm toán học
        allowed_names = {
            "sqrt": math.sqrt,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
            "abs": abs,
            "round": round,
        }

        # Thay thế một số từ phổ biến
        expr = expr.replace("√", "sqrt").replace("^", "**")

        # Đánh giá an toàn
        result = eval(expr, {"__builtins__": {}}, allowed_names)

        return format_general_response(
            answer=f"Kết quả: **{result}**",
            source="calculator"
        )

    except Exception as e:
        logger.warning(f"Calculator error with expression '{expression}': {e}")
        return create_general_error(f"Không thể tính toán biểu thức: {expression}. Vui lòng kiểm tra lại.")