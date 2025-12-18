const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Agent {
  id: string;
  name: string;
  description: string;
  system_prompt: string;
}

export interface FileInfo {
  id: string;
  name: string;
  size: number;
  uploadedAt: string;
}

export const api = {
  async chat(message: string, sessionId: string, agentId?: string): Promise<string> {
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, session_id: sessionId, agent_id: agentId }),
    });
    const data = await response.json();
    return data.response;
  },

  async getAgents(): Promise<Agent[]> {
    const response = await fetch(`${API_BASE_URL}/agents`);
    return response.json();
  },

  async createAgent(agent: Omit<Agent, 'id' | 'system_prompt'>): Promise<Agent> {
    const response = await fetch(`${API_BASE_URL}/agents`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(agent),
    });
    return response.json();
  },

  async deleteAgent(id: string): Promise<void> {
    await fetch(`${API_BASE_URL}/agents/${id}`, { method: 'DELETE' });
  },

  async getAgentFiles(agentId: string): Promise<FileInfo[]> {
    const response = await fetch(`${API_BASE_URL}/agents/${agentId}/files`);
    return response.json();
  },

  async uploadFileToAgent(agentId: string, file: File): Promise<FileInfo> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch(`${API_BASE_URL}/agents/${agentId}/files`, {
      method: 'POST',
      body: formData,
    });
    return response.json();
  },

  async deleteAgentFile(agentId: string, fileId: string): Promise<void> {
    await fetch(`${API_BASE_URL}/agents/${agentId}/files/${fileId}`, {
      method: 'DELETE'
    });
  },
};
