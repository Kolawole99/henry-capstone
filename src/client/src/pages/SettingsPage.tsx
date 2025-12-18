import { useState, useEffect } from 'react';
import { Plus, Upload, Trash2, FileText } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { api } from '../api/client';
import type { Agent, FileInfo } from '../api/client';

export function SettingsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [agentFiles, setAgentFiles] = useState<FileInfo[]>([]);
  const [newAgent, setNewAgent] = useState({ name: '', description: '', department: 'GENERAL' as const });
  const [loading, setLoading] = useState(false);

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
    if (!newAgent.name.trim()) return;
    setLoading(true);
    try {
      const created = await api.createAgent(newAgent);
      setNewAgent({ name: '', description: '', department: 'GENERAL' });
      await loadAgents();
      setSelectedAgent(created);
    } catch (error) {
      console.error('Error creating agent:', error);
    } finally {
      setLoading(false);
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
                  <div className="text-sm opacity-80">{agent.department}</div>
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
              <CardTitle>Create New Agent</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Input
                placeholder="Agent Name"
                value={newAgent.name}
                onChange={(e) => setNewAgent({ ...newAgent, name: e.target.value })}
              />
              <Input
                placeholder="Description"
                value={newAgent.description}
                onChange={(e) => setNewAgent({ ...newAgent, description: e.target.value })}
              />
              <select
                value={newAgent.department}
                onChange={(e) => setNewAgent({ ...newAgent, department: e.target.value as any })}
                className="w-full px-3 py-2 border rounded-md bg-background"
              >
                <option value="HR">HR</option>
                <option value="TECH">Tech</option>
                <option value="GENERAL">General</option>
              </select>
              <Button onClick={handleCreateAgent} disabled={loading} className="w-full">
                <Plus className="w-4 h-4 mr-2" />
                Create Agent
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
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle>{selectedAgent.name}</CardTitle>
                    <p className="text-sm text-muted-foreground mt-1">
                      {selectedAgent.description || 'No description'}
                    </p>
                  </div>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => handleDeleteAgent(selectedAgent.id)}
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete Agent
                  </Button>
                </CardHeader>
              </Card>

              {/* File Upload */}
              <Card>
                <CardHeader>
                  <CardTitle>Upload Knowledge Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <Input
                      type="file"
                      onChange={handleFileUpload}
                      accept=".txt,.pdf,.md"
                      disabled={loading}
                      className="flex-1"
                    />
                    <Upload className="w-5 h-5 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground mt-2">
                    Upload documents to give this agent context and knowledge
                  </p>
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
