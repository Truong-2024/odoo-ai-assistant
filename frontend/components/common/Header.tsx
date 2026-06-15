'use client';

import { Button } from '@/components/ui/button';
import { Moon, Sun, User } from 'lucide-react';
import { useTheme } from 'next-themes';
import { useEffect, useState } from 'react';
import { useChat } from '@/hooks/useChat';
import PDFReportButton from '@/components/chat/PDFReportButton';

export default function Header() {
  const { messages } = useChat();
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) return null;

  return (
    <header className="h-14 border-b border-border bg-background px-6 flex items-center justify-between">
      <div className="font-semibold">
        Odoo AI Assistant
      </div>

      <div className="flex items-center gap-3">

        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
        >
          {theme === 'dark' ? (
            <Sun className="w-5 h-5" />
          ) : (
            <Moon className="w-5 h-5" />
          )}
        </Button>

        <Button variant="ghost" size="icon">
          <User className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}