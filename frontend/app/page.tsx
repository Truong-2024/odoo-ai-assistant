// app/page.tsx
'use client';
import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Tự động chuyển hướng sang trang chat sau 1.5 giây
    const timer = setTimeout(() => {
      router.push('/chat');
    }, 1500);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-950">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-3xl text-center">Odoo AI Assistant</CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-6">
          <p className="text-zinc-400">
            Trợ lý thông minh tích hợp Odoo ERP
          </p>

          <Button 
            onClick={() => router.push('/chat')}
            size="lg"
            className="w-full text-lg py-6"
          >
            Bắt đầu trò chuyện
          </Button>

          <p className="text-xs text-zinc-500">
            Đang chuyển hướng tự động...
          </p>
        </CardContent>
      </Card>
    </div>
  );
}