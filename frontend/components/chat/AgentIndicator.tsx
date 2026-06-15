'use client';
import { Bot, Building2, FileText, Image, MessageSquare } from 'lucide-react';

const agentConfig = {
  business: { 
    icon: Building2, 
    color: 'text-emerald-500', 
    bgColor: 'bg-emerald-500/10',
    label: 'Business Agent' 
  },
  document: { 
    icon: FileText, 
    color: 'text-blue-500', 
    bgColor: 'bg-blue-500/10',
    label: 'Document Agent' 
  },
  vision: { 
    icon: Image, 
    color: 'text-purple-500', 
    bgColor: 'bg-purple-500/10',
    label: 'Vision Agent' 
  },
  general: { 
    icon: MessageSquare, 
    color: 'text-muted-foreground', 
    bgColor: 'bg-muted',
    label: 'General Agent' 
  },
};

export default function AgentIndicator({ currentAgent = 'general' }: { currentAgent: string }) {
  const config = agentConfig[currentAgent as keyof typeof agentConfig] || agentConfig.general;
  const Icon = config.icon;

  return (
    <div className="px-6 py-3 border-b border-border bg-background flex items-center gap-3">
      <div className={`p-1.5 rounded-xl ${config.bgColor} ${config.color}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-sm font-medium text-foreground">{config.label}</p>
        <p className="text-xs text-muted-foreground">Đang hỗ trợ bạn</p>
      </div>
    </div>
  );
}