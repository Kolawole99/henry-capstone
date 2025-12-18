import { useState, useEffect } from 'react';
import { Plus, Upload, Trash2, FileText, Sparkles, Loader2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { api } from '../api/client';
import type { Agent, FileInfo } from '../api/client';

export function SettingsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentFiles, setAgentFiles] = useState<FileInfo[]>([]);
  const [newAgent, setNewAgent] = useState({ name: '', description: '' });
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    loadAgents();
  }, []);

  useEffect(() => {
    if (selectedAgent) {
      loadAgentFiles(selectedAgent.id);
    }
  }, [selectedAgent]);

  const loadAgents = async () => {
    try {
      const agentsData = await api.getAgents();
      setAgents(agentsData);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  const loadAgentFiles = async (agentId: string) => {
    try {
      const filesData = await api.getAgentFiles(agentId);
      setAgentFiles(filesData);
    } catch (error) {
      console.error('Error loading files:', error);
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgent.name.trim() || !newAgent.description.trim()) return;
    setCreating(true);
    try {
      const created = await api.createAgent(newAgent);
      setNewAgent({ name: '', description: '' });
      await loadAgents();
      setSelectedAgent(created);
    } catch (error) {
      console.error('Error creating agent:', error);
      alert('Failed to create agent. Please try again.');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteAgent = async (id: string) => {
    if (!confirm('Delete this agent and all its files?')) return;
    try {
      await api.deleteAgent(id);
      if (selectedAgent?.id === id) {
        setSelectedAgent(null);
        setAgentFiles([]);
      }
      await loadAgents();
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!selectedAgent) return;
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    try {
      await api.uploadFileToAgent(selectedAgent.id, file);
      await loadAgentFiles(selectedAgent.id);
      e.target.value = '';
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (fileId: string) => {
    if (!selectedAgent) return;
    try {
      await api.deleteAgentFile(selectedAgent.id, fileId);
      await loadAgentFiles(selectedAgent.id);
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Agent Management</h1>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Left Panel - Agent List */}
        <div className="md:col-span-1">
          <Card>
            <CardHeader>
              <CardTitle>Agents ({agents.length})</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {agents.map(agent => (
                <div
                  key={agent.id}
                  onClick={() => setSelectedAgent(agent)}
                  className={`p-3 border rounded-md cursor-pointer transition-colors ${selectedAgent?.id === agent.id
                    ? 'bg-primary text-primary-foreground'
                    : 'hover:bg-accent'
                    }`}
                >
                  <div className="font-medium">{agent.name}</div>
                  <div className="text-sm opacity-80 line-clamp-2">{agent.description}</div>
                </div>
              ))}
              {agents.length === 0 && (
                <p className="text-center text-muted-foreground py-4">No agents yet</p>
              )}
            </CardContent>
          </Card>

          {/* Create Agent Form */}
          <Card className="mt-4">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="w-5 h-5" />
                Create AI Agent
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <label className="text-sm font-medium mb-1 block">Agent Name</label>
                <Input
                  placeholder="e.g., Finance Specialist"
                  value={newAgent.name}
                  onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
                />
              </div>
              <div>
                <label className="text-sm font-medium mb-1 block">What should this agent do?</label>
                <textarea
                  placeholder="Describe the agent's role and responsibilities..."
                  value={newAgent.description}
                  onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-md bg-background min-h-[100px] resize-none"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  AI will generate a specialized system prompt based on your description
                </p>
              </div>
              <Button
                onClick={handleCreateAgent}
                disabled={creating || !newAgent.name.trim() || !newAgent.description.trim()}
                className="w-full"
              >
                {creating ? (
                  <>
                    <Sparkles className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Create Agent
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right Panel - Agent Details & Files */}
        <div className="md:col-span-2">
          {selectedAgent ? (
            <div className="space-y-4">
              {/* Agent Details */}
              <Card>
                <CardHeader className="flex flex-row items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="mb-2">{selectedAgent.name}</CardTitle>
                    <p className="text-sm text-muted-foreground mb-3">
                      {selectedAgent.description}
                    </p>
                    <details className="text-sm">
                      <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
                        View System Prompt
                      </summary>
                      <pre className="mt-2 p-3 bg-muted rounded-md text-xs whitespace-pre-wrap">
                        {selectedAgent.system_prompt}
                      </pre>
                    </details>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteAgent(selectedAgent.id)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </Button>
                </CardHeader>
              </Card>

              {/* File Upload */}
              <Card>
                <CardHeader>
                  <CardTitle>Upload Knowledge Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-4">
                      <Input
                        type="file"
                        onChange={handleFileUpload}
                        accept=".txt,.pdf,.md,.docx,.doc"
                        disabled={loading}
                        className="flex-1"
                      />
                      {loading ? (
                        <Loader2 className="w-5 h-5 text-primary animate-spin" />
                      ) : (
                        <Upload className="w-5 h-5 text-muted-foreground" />
                      )}
                    </div>
                    {loading && (
                      <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span>Uploading and processing file...</span>
                      </div>
                    )}
                    <p className="text-sm text-muted-foreground">
                      Upload documents to give this agent context and knowledge
                    </p>
                  </div>
                </CardContent>
              </Card>

              {/* Files List */}
              <Card>
                <CardHeader>
                  <CardTitle>Knowledge Base ({agentFiles.length} files)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {agentFiles.map(file => (
                      <div key={file.id} className="flex items-center justify-between p-3 border rounded-md">
                        <div className="flex items-center gap-3">
                          <FileText className="w-5 h-5 text-muted-foreground" />
                          <div>
                            <div className="font-medium">{file.name}</div>
                            <div className="text-sm text-muted-foreground">
                              {(file.size / 1024).toFixed(2)} KB
                            </div>
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDeleteFile(file.id)}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    ))}
                    {agentFiles.length === 0 && (
                      <p className="text-center text-muted-foreground py-8">
                        No files uploaded yet. Upload documents to give this agent knowledge.
                      </p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center text-muted-foreground">
                <p>Select an agent to view and manage its knowledge base</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
}
