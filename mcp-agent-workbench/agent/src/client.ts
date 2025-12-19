/**
 * MCP Client Wrapper
 * 
 * Abstrahiert die Verbindung zu MCP-Servern und bietet eine einheitliche
 * Schnittstelle für Tool-Aufrufe.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { spawn, type ChildProcess } from "child_process";
import type { Tool, Resource } from "@modelcontextprotocol/sdk/types.js";

export interface ServerConfig {
  type: "stdio" | "http";
  command?: string;
  args?: string[];
  url?: string;
  description?: string;
}

export interface McpServerConnection {
  name: string;
  config: ServerConfig;
  client: Client;
  transport: StdioClientTransport;
  process?: ChildProcess;
  tools: Tool[];
  resources: Resource[];
}

/**
 * MCP Client Manager
 * 
 * Verwaltet mehrere MCP-Server-Verbindungen und bietet eine zentrale
 * Schnittstelle für Tool-Aufrufe.
 */
export class McpClientManager {
  private connections: Map<string, McpServerConnection> = new Map();

  /**
   * Verbindet zu einem MCP-Server via stdio
   */
  async connectStdio(name: string, config: ServerConfig): Promise<McpServerConnection> {
    if (!config.command) {
      throw new Error(`Server ${name}: 'command' ist erforderlich für stdio-Transport`);
    }

    console.log(`🔌 Verbinde zu Server: ${name}...`);

    // Transport erstellen
    const transport = new StdioClientTransport({
      command: config.command,
      args: config.args ?? [],
    });

    // Client erstellen
    const client = new Client(
      { name: "mcp-agent-host", version: "0.1.0" },
      { capabilities: {} }
    );

    // Verbinden
    await client.connect(transport);

    // Tools und Resources laden
    const toolsResult = await client.listTools();
    const resourcesResult = await client.listResources();

    const connection: McpServerConnection = {
      name,
      config,
      client,
      transport,
      tools: toolsResult.tools,
      resources: resourcesResult.resources,
    };

    this.connections.set(name, connection);

    console.log(`✅ Server ${name} verbunden:`);
    console.log(`   - ${connection.tools.length} Tools`);
    console.log(`   - ${connection.resources.length} Resources`);

    return connection;
  }

  /**
   * Verbindet zu mehreren Servern basierend auf Konfiguration
   */
  async connectFromConfig(servers: Record<string, ServerConfig>, activeServers?: string[]): Promise<void> {
    const toConnect = activeServers ?? Object.keys(servers);

    for (const serverName of toConnect) {
      const config = servers[serverName];
      if (!config) {
        console.warn(`⚠️ Server '${serverName}' nicht in Konfiguration gefunden`);
        continue;
      }

      try {
        if (config.type === "stdio") {
          await this.connectStdio(serverName, config);
        } else {
          console.warn(`⚠️ Transport-Typ '${config.type}' noch nicht implementiert`);
        }
      } catch (error) {
        console.error(`❌ Fehler beim Verbinden zu ${serverName}:`, error);
      }
    }
  }

  /**
   * Gibt alle verfügbaren Tools zurück (aggregiert von allen Servern)
   */
  getAllTools(): Array<Tool & { serverName: string }> {
    const allTools: Array<Tool & { serverName: string }> = [];

    for (const [serverName, connection] of this.connections) {
      for (const tool of connection.tools) {
        allTools.push({
          ...tool,
          serverName,
        });
      }
    }

    return allTools;
  }

  /**
   * Gibt Tools im Format zurück, das LLMs erwarten
   */
  getToolsForLLM(): Array<{
    name: string;
    description: string;
    input_schema: unknown;
  }> {
    return this.getAllTools().map((tool) => ({
      name: `${tool.serverName}__${tool.name}`,
      description: tool.description ?? `Tool: ${tool.name}`,
      input_schema: tool.inputSchema,
    }));
  }

  /**
   * Ruft ein Tool auf einem Server auf
   */
  async callTool(
    serverName: string,
    toolName: string,
    args: Record<string, unknown>
  ): Promise<unknown> {
    const connection = this.connections.get(serverName);
    if (!connection) {
      throw new Error(`Server '${serverName}' nicht verbunden`);
    }

    console.log(`🔧 Tool-Aufruf: ${serverName}/${toolName}`);
    console.log(`   Args:`, JSON.stringify(args, null, 2));

    const result = await connection.client.callTool({
      name: toolName,
      arguments: args,
    });

    console.log(`   Ergebnis:`, JSON.stringify(result, null, 2).slice(0, 200));

    return result;
  }

  /**
   * Ruft ein Tool auf (mit kombiniertem Namen "server__tool")
   */
  async callToolByFullName(
    fullName: string,
    args: Record<string, unknown>
  ): Promise<unknown> {
    const [serverName, toolName] = fullName.split("__");
    if (!serverName || !toolName) {
      throw new Error(`Ungültiger Tool-Name: ${fullName}. Erwartet: server__tool`);
    }
    return this.callTool(serverName, toolName, args);
  }

  /**
   * Liest eine Resource von einem Server
   */
  async readResource(serverName: string, uri: string): Promise<string> {
    const connection = this.connections.get(serverName);
    if (!connection) {
      throw new Error(`Server '${serverName}' nicht verbunden`);
    }

    const result = await connection.client.readResource({ uri });
    
    // Resource-Inhalte extrahieren
    const contents = result.contents
      .map((c) => {
        if ("text" in c) return c.text;
        if ("blob" in c) return `[Binary data: ${c.blob.length} bytes]`;
        return "[Unknown content type]";
      })
      .join("\n");

    return contents;
  }

  /**
   * Trennt die Verbindung zu einem Server
   */
  async disconnect(serverName: string): Promise<void> {
    const connection = this.connections.get(serverName);
    if (!connection) return;

    console.log(`🔌 Trenne Server: ${serverName}...`);
    
    await connection.client.close();
    this.connections.delete(serverName);
    
    console.log(`✅ Server ${serverName} getrennt`);
  }

  /**
   * Trennt alle Verbindungen
   */
  async disconnectAll(): Promise<void> {
    for (const serverName of this.connections.keys()) {
      await this.disconnect(serverName);
    }
  }

  /**
   * Gibt Verbindungsstatus zurück
   */
  getStatus(): Record<string, { connected: boolean; tools: number; resources: number }> {
    const status: Record<string, { connected: boolean; tools: number; resources: number }> = {};
    
    for (const [name, conn] of this.connections) {
      status[name] = {
        connected: true,
        tools: conn.tools.length,
        resources: conn.resources.length,
      };
    }
    
    return status;
  }
}
