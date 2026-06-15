'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import api from '@/lib/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const res = await api.post('/auth/login', { username, password });
      localStorage.setItem('access_token', res.data.access_token);
      router.push('/chat');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Sai tài khoản hoặc mật khẩu');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-[380px]">
        <CardHeader className="text-center pb-8">
          <CardTitle className="text-3xl">Odoo AI Assistant</CardTitle>
          <p className="text-muted-foreground mt-2">Trợ lý thông minh cho Odoo</p>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleLogin} className="space-y-5">
            <Input
              type="text"
              placeholder="Tên đăng nhập / Email"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="h-12"
              required
            />
            <Input
              type="password"
              placeholder="Mật khẩu"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-12"
              required
            />

            {error && <p className="text-destructive text-sm text-center">{error}</p>}

            <Button type="submit" className="w-full h-12 text-base" disabled={loading}>
              {loading ? "Đang đăng nhập..." : "Đăng nhập"}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}