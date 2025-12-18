import { useState, useEffect } from 'react';
import { Plus, Upload, Trash2 } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { api } from '../api/client';
import type { Agent, FileInfo } from '../api/client';

export function SettingsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [files, setFiles] = useState<FileInfo[]>([]);
  const [newAgent, setNewAgent] = useState({ name: '', description: '', department: 'GENERAL' as const });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [agentsData, filesData] = await Promise.all([
        api.getAgents(),
        api.getFiles()
      ]);
      setAgents(agentsData);
      setFiles(filesData);
    } catch (error) {
      console.error('Error loading data:', error);
    }
  };

  const handleCreateAgent = async () => {
    if (!newAgent.name.trim()) return;
    setLoading(true);
    try {
      await api.createAgent(newAgent);
      setNewAgent({ name: '', description: '', department: 'GENERAL' });
      await loadData();
    } catch (error) {
      console.error('Error creating agent:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAgent = async (id: string) => {
    try {
      await api.deleteAgent(id);
      await loadData();
    } catch (error) {
      console.error('Error deleting agent:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setLoading(true);
    try {
      await api.uploadFile(file);
      await loadData();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFile = async (id: string) => {
    try {
      await api.deleteFile(id);
      await loadData();
    } catch (error) {
      console.error('Error deleting file:', error);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      <h1 className="text-3xl font-bold">Settings</h1>

      <Card>
        <CardHeader>
          <CardTitle>Create New Agent</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
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
            className="w-full px-4 py-2 border rounded-md bg-background"
          >
            <option value="HR">HR</option>
            <option value="TECH">Tech</option>
            <option value="GENERAL">General</option>
          </select>
          <Button onClick={handleCreateAgent} disabled={loading}>
            <Plus className="w-4 h-4 mr-2" />
            Create Agent
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Upload Files</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <Input
              type="file"
              onChange={handleFileUpload}
              accept=".txt,.pdf,.md"
              disabled={loading}
            />
            <Upload className="w-5 h-5 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      <div className="grid md:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Agents ({agents.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {agents.map(agent => (
                <div key={agent.id} className="flex items-center justify-between p-3 border rounded-md">
                  <div>
                    <div className="font-medium">{agent.name}</div>
                    <div className="text-sm text-muted-foreground">{agent.department}</div>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => handleDeleteAgent(agent.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              ))}
              {agents.length === 0 && (
                <p className="text-center text-muted-foreground py-4">No agents yet</p>
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Files ({files.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {files.map(file => (
                <div key={file.id} className="flex items-center justify-between p-3 border rounded-md">
                  <div>
                    <div className="font-medium">{file.name}</div>
                    <div className="text-sm text-muted-foreground">
                      {(file.size / 1024).toFixed(2)} KB
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
              {files.length === 0 && (
                <p className="text-center text-muted-foreground py-4">No files uploaded</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
