// app/api/export/chat-pdf/route.ts
import puppeteer from 'puppeteer';
import { marked } from 'marked';
import { NextRequest } from 'next/server';

export async function POST(req: NextRequest) {
  try {
    const { messages, chatTitle = "Chat Export" } = await req.json();

    if (!messages || !Array.isArray(messages)) {
      return new Response(JSON.stringify({ error: "Messages is required" }), { 
        status: 400,
        headers: { 'Content-Type': 'application/json' }
      });
    }

    const html = generateHTML(messages, chatTitle);

    const browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    });

    const page = await browser.newPage();
    
    await page.setContent(html, { 
      waitUntil: 'domcontentloaded' 
    });

    // Chờ thêm để style và font load tốt hơn
    await new Promise(resolve => setTimeout(resolve, 1000));

    const pdf = await page.pdf({
      format: 'A4',
      printBackground: true,
      margin: { top: '40px', bottom: '40px', left: '30px', right: '30px' },
    });

    await browser.close();
    
    return new Response(Buffer.from(pdf), {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': 'attachment; filename="chat-export.pdf"'
      },
    });
  } catch (error: any) {
    console.error('PDF Export Error:', error);
    return new Response(JSON.stringify({ 
      error: 'Export PDF thất bại', 
      details: error.message 
    }), { 
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

function generateHTML(messages: any[], chatTitle: string): string {
  // ✅ Đã sửa: Ép kiểu 'as string' để TypeScript không bắt bẻ trường hợp Promise bất đồng bộ
  const safeContent = (content: string): string => {
    return marked.parse(content || '', { 
      breaks: true,
      gfm: true 
    }) as string;
  };

  return `
<!DOCTYPE html>
<html lang="vi">
<head>
  <meta charset="UTF-8">
  <title>${chatTitle}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
    
    body {
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      line-height: 1.6;
      color: #111827;
      background: #ffffff;
      padding: 40px 0;
      max-width: 800px;
      margin: 0 auto;
    }

    .header {
      text-align: center;
      margin-bottom: 40px;
      padding-bottom: 20px;
      border-bottom: 2px solid #e5e7eb;
    }

    .header h1 {
      font-size: 26px;
      font-weight: 600;
      color: #111827;
      margin: 0;
    }

    .message {
      margin-bottom: 32px;
      padding: 20px;
      border-radius: 16px;
      max-width: 85%;
    }

    .user {
      background: #dbeafe;
      border: 1px solid #bfdbfe;
      margin-left: auto;
      border-bottom-right-radius: 4px;
    }

    .assistant {
      background: #f3f4f6;
      border: 1px solid #e5e7eb;
      margin-right: auto;
      border-bottom-left-radius: 4px;
    }

    .role {
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin-bottom: 8px;
      opacity: 0.8;
    }

    .content {
      font-size: 15.5px;
      white-space: pre-wrap;
    }

    pre {
      background: #1f2937;
      color: #e5e7eb;
      padding: 16px;
      border-radius: 10px;
      overflow-x: auto;
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>📄 ${chatTitle}</h1>
    <p>Xuất từ Odoo AI Assistant • ${new Date().toLocaleDateString('vi-VN')}</p>
  </div>

  ${messages
    .filter(m => m.content || m.isFileCard)
    .map((m) => {
      const isUser = m.role === 'user';
      let contentHtml = '';

      if (m.isFileCard) {
        contentHtml = `<strong>📎 File: ${m.fileName || 'Không có tên'}</strong>`;
      } else {
        contentHtml = safeContent(m.content || '');
      }

      return `
        <div class="message ${isUser ? 'user' : 'assistant'}">
          <div class="role">${isUser ? 'Bạn' : 'AI Assistant'}</div>
          <div class="content">${contentHtml}</div>
        </div>
      `;
    })
    .join('')}
</body>
</html>`;
}