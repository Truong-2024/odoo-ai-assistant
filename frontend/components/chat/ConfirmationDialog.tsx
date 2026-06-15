'use client';
import { Button } from '@/components/ui/button';
import { useChat } from '@/hooks/useChat';

export default function ConfirmationDialog() {
  const { pendingConfirmation, sendMessage } = useChat();

  if (!pendingConfirmation) return null;

  return (
    <div className="p-6 border-t border-border bg-zinc-900">
      <div className="bg-amber-950 border border-amber-800 rounded-2xl p-6">
        <h3 className="font-semibold text-amber-400 mb-4 flex items-center gap-2">
          🟡 Xác nhận tạo đơn hàng
        </h3>

        <div className="space-y-3 text-sm">
          <div><strong>Khách hàng:</strong> {pendingConfirmation.preview?.customer?.name}</div>
          <div><strong>Tổng tiền:</strong> {pendingConfirmation.preview?.total_amount?.toLocaleString()} VND</div>
          {pendingConfirmation.preview?.order_lines?.length > 0 && (
            <div>
              <strong>Sản phẩm:</strong>
              <ul className="list-disc pl-5 mt-1 text-xs">
                {pendingConfirmation.preview.order_lines.map((line: any, i: number) => (
                  <li key={i}>{line.product_name} × {line.quantity}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex gap-3 mt-6">
          <Button 
            onClick={() => sendMessage("Xác nhận")} 
            className="flex-1 bg-emerald-600 hover:bg-emerald-700"
          >
            ✅ Xác nhận tạo đơn
          </Button>
          <Button 
            onClick={() => sendMessage("Hủy")} 
            variant="outline" 
            className="flex-1"
          >
            Hủy
          </Button>
        </div>
      </div>
    </div>
  );
}