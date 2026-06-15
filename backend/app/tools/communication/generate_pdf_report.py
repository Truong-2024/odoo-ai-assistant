# backend/app/tools/communication/generate_pdf_report.py
from langchain_core.tools import tool
from typing import Dict, Any, List
import logging
from datetime import datetime
from io import BytesIO

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

logger = logging.getLogger(__name__)


@tool
def generate_pdf_report_tool(
    title: str = "Báo cáo Odoo AI",
    content: str = "",
    data: List[Dict] = None
) -> Dict[str, Any]:
    """
    Tạo file PDF báo cáo từ dữ liệu
    """
    if not REPORTLAB_AVAILABLE:
        return {
            "status": "error",
            "message": "Thư viện reportlab chưa được cài đặt. Vui lòng cài: pip install reportlab"
        }

    try:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()

        elements = []

        # Header
        elements.append(Paragraph(f"<b>{title}</b>", styles['Heading1']))
        elements.append(Paragraph(f"Ngày tạo: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Nội dung text
        if content:
            elements.append(Paragraph(content, styles['Normal']))
            elements.append(Spacer(1, 20))

        # Table data nếu có
        if data and isinstance(data, list):
            table_data = [["STT", "Thông tin", "Giá trị"]]
            for i, item in enumerate(data[:20], 1):  # Giới hạn 20 dòng
                row = [str(i), str(item.get('name', '')), str(item.get('value', ''))]
                table_data.append(row)

            table = Table(table_data, colWidths=[40, 250, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

        doc.build(elements)
        buffer.seek(0)

        return {
            "status": "success",
            "pdf_content": buffer.getvalue(),
            "filename": f"{title.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf",
            "message": "✅ Đã tạo file PDF thành công"
        }

    except Exception as e:
        logger.error(f"Generate PDF Report Error: {e}")
        return {"status": "error", "message": str(e)}