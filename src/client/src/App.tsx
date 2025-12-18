import { BrowserRouter, Routes, Route, Link } from 'react-router-dom';
import { MessageSquare, Settings } from 'lucide-react';
import { ChatPage } from './pages/ChatPage';
import { SettingsPage } from './pages/SettingsPage';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-background">
        <nav className="border-b">
          <div className="max-w-7xl mx-auto px-4 py-3 flex items-center gap-6">
            <Link to="/" className="flex items-center gap-2 hover:text-primary transition-colors">
              <MessageSquare className="w-5 h-5" />
              <span className="font-semibold">Chat</span>
            </Link>
            <Link to="/settings" className="flex items-center gap-2 hover:text-primary transition-colors">
              <Settings className="w-5 h-5" />
              <span className="font-semibold">Settings</span>
            </Link>
          </div>
        </nav>

        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;
