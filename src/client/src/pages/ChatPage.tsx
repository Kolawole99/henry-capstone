import { useState } from 'react';
import { Send, Bot, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card } from '../components/ui/card';
import { api } from '../api/client';
import type { Message } from '../api/client';
import { validateMessage, MAX_MESSAGE_LENGTH } from '../utils/validators';

export function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => crypto.randomUUID());
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setInput(value);

    // Real-time validation
    if (value.trim()) {
      const result = validateMessage(value);
      setValidationError(result.isValid ? null : result.error || null);
    } else {
      setValidationError(null);
    }
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    // Validate before sending
    const validation = validateMessage(input);
    if (!validation.isValid) {
      setValidationError(validation.error || 'Invalid message');
      return;
    }

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setValidationError(null);
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

  const characterCount = input.length;
  const isValid = !validationError && input.trim().length > 0;

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

      <div className="space-y-2">
        <div className="flex gap-2">
          <div className="flex-1">
            <Input
              value={input}
              onChange={handleInputChange}
              onKeyDown={(e) => e.key === 'Enter' && isValid && !loading && handleSend()}
              placeholder="Ask me anything..."
              disabled={loading}
              className={validationError ? 'border-destructive' : ''}
            />
          </div>
          <Button onClick={handleSend} disabled={loading || !isValid}>
            <Send className="w-4 h-4" />
          </Button>
        </div>
        <div className="flex justify-between items-center text-xs">
          {validationError ? (
            <span className="text-destructive">{validationError}</span>
          ) : (
            <span className="text-muted-foreground">
              {characterCount > 0 && `${characterCount} / ${MAX_MESSAGE_LENGTH} characters`}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
