//app/layout.tsx
import type { Metadata } from "next";
import { Geist } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "sonner";

const geist = Geist({
  subsets: ['latin'],
  variable: '--font-sans',
  weight: ['400', '500', '600', '700'],
});

export const metadata: Metadata = {
  title: "Odoo AI Assistant",
  description: "Trợ lý thông minh cho Odoo ERP",
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html 
      lang="vi" 
      suppressHydrationWarning 
      className={geist.variable}
    >
      <body 
        className={cn(
          "h-screen overflow-hidden bg-background text-foreground font-sans antialiased"
        )}
        suppressHydrationWarning
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem={false}
          disableTransitionOnChange
        >
          {children}
          <Toaster 
            position="top-center"
            richColors
            closeButton
            theme="system"
            toastOptions={{
              className: 'dark:bg-zinc-900 dark:border-zinc-700',
            }}
          />
        </ThemeProvider>
      </body>
    </html>
  );
}