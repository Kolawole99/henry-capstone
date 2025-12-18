import { useState } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { api } from '../api/client';
import type { Message } from '../api/client';

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await api.chat(input, sessionId);
      const assistantMessage: Message = { role: 'assistant', content: response };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error: any) {
      console.error('Chat error:', error);

      let errorMessage = 'Sorry, I encountered an error. Please try again.';
      if (error.message) {
        errorMessage = error.message;
      }

      try {
        const errorText = await error.text?.();
        if (errorText) {
          const errorData = JSON.parse(errorText);
          if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
              errorMessage = errorData.detail;
            } else if (errorData.detail.message) {
              errorMessage = errorData.detail.message;
            }
          }
        }
      } catch (parseError) {
        // Ignore parsing errors, use default message
      }

      const errorMessageObj: Message = {
        role: 'assistant',
        content: `❌ Error: ${errorMessage}`
      };
      setMessages(prev => [...prev, errorMessageObj]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col max-w-4xl mx-auto p-4" style={{ height: 'calc(100vh - 60px)' }}>
      <div className="mb-4">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Bot className="w-8 h-8" />
          Nexus-Mind
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          AI will automatically route your question to the best agent
        </p>
      </div>

      <Card className="flex-1 overflow-y-auto p-4 mb-4 space-y-4 min-h-0">
        {messages.length === 0 && (
          <div className="text-center text-muted-foreground py-12">
            <Bot className="w-16 h-16 mx-auto mb-4 opacity-50" />
            <p>Start a conversation with Nexus-Mind</p>
          </div>
        )}
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${msg.role === 'user'
                ? 'bg-primary text-primary-foreground'
                : 'bg-muted'
                }`}
            >
              {msg.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-muted rounded-lg px-4 py-3 max-w-[80%]">
              <div className="flex items-center gap-3">
                <Loader2 className="w-4 h-4 animate-spin text-primary" />
                <span className="text-sm text-muted-foreground">AI is thinking...</span>
              </div>
            </div>
          </div>
        )}
      </Card>

      <div className="flex gap-2">
        <Input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Ask me anything..."
          disabled={loading}
        />
        <Button onClick={handleSend} disabled={loading || !input.trim()}>
          <Send className="w-4 h-4" />
        </Button>
      </div>
    </div>
  );
}
