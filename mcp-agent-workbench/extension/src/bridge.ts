/**
 * MCP Agent Bridge
 * 
 * Verbindet die VS Code Extension mit dem MCP Agent Host.
 * Unterstützt OpenAI und Anthropic als LLM-Provider.
 */

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import type { Tool } from "@modelcontextprotocol/sdk/types.js";
import * as fs from "fs";
import * as path from "path";

export interface BridgeConfig {
  provider: "openai" | "anthropic" | "ollama" | "azure" | "google";
  openaiApiKey?: string;
  anthropicApiKey?: string;
  googleApiKey?: string;
  azureEndpoint?: string;
  azureApiKey?: string;
  ollamaEndpoint?: string;
  model?: string;
  serversConfigPath?: string;
  activeServers?: string[];
  debug?: boolean;
  temperature?: number;
  maxTokens?: number;
  systemPrompt?: string;
}

export interface AgentContext {
  workspaceFolders: string[];
  openFiles: string[];
  currentFile?: string;
  selection?: string;
}

interface ServerConfig {
  type: "stdio" | "http";
  command?: string;
  args?: string[];
  description?: string;
}

interface ServersJson {
  servers: Record<string, ServerConfig>;
  defaults?: {
    activeServers?: string[];
  };
}

interface McpConnection {
  name: string;
  client: Client;
  transport: StdioClientTransport;
  tools: Tool[];
}

/**
 * Agent Bridge - Läuft im Extension-Host
 */
export class AgentBridge {
  private anthropic: Anthropic | null = null;
  private openai: OpenAI | null = null;
  private connections: Map<string, McpConnection> = new Map();
  private config: BridgeConfig;
  private allTools: Array<Tool & { serverName: string }> = [];
  private serversConfig: ServersJson | null = null;

  constructor(config: BridgeConfig) {
    this.config = config;
  }

  /**
   * Initialisiert den Bridge
   */
  async initialize(): Promise<void> {
    // LLM Client erstellen basierend auf Provider
    if (this.config.provider === "openai") {
      if (!this.config.openaiApiKey) {
        throw new Error("OpenAI API Key nicht konfiguriert");
      }
      this.openai = new OpenAI({
        apiKey: this.config.openaiApiKey,
      });
      console.log("[AgentBridge] OpenAI Client initialisiert");
    } else {
      if (!this.config.anthropicApiKey) {
        throw new Error("Anthropic API Key nicht konfiguriert");
      }
      this.anthropic = new Anthropic({
        apiKey: this.config.anthropicApiKey,
      });
      console.log("[AgentBridge] Anthropic Client initialisiert");
    }

    // Server-Konfiguration laden
    await this.loadServersConfig();

    console.log("[AgentBridge] Initialisiert");
  }

  /**
   * Lädt die Server-Konfiguration aus mcp-servers.json
   */
  private async loadServersConfig(): Promise<void> {
    const configPaths = [
      this.config.serversConfigPath,
      path.join(process.cwd(), "mcp-servers.json"),
      path.join(process.cwd(), "agent", "mcp-servers.json"),
      path.join(__dirname, "..", "..", "agent", "mcp-servers.json"),
    ].filter(Boolean) as string[];

    for (const configPath of configPaths) {
      try {
        if (fs.existsSync(configPath)) {
          const content = fs.readFileSync(configPath, "utf-8");
          this.serversConfig = JSON.parse(content);
          console.log(`[AgentBridge] Server-Config geladen: ${configPath}`);
          return;
        }
      } catch (e) {
        console.log(`[AgentBridge] Config nicht lesbar: ${configPath}`);
      }
    }

    console.log("[AgentBridge] Keine Server-Konfiguration gefunden");
  }

  /**
   * Verbindet zu allen konfigurierten aktiven Servern
   */
  async connectActiveServers(): Promise<void> {
    if (!this.serversConfig) {
      console.log("[AgentBridge] Keine Server-Konfiguration vorhanden");
      return;
    }

    const activeServers = this.config.activeServers ?? 
      this.serversConfig.defaults?.activeServers ?? 
      ["demo", "filesystem"];

    for (const serverName of activeServers) {
      const serverConfig = this.serversConfig.servers[serverName];
      if (serverConfig) {
        try {
          await this.connectServer(serverName, serverConfig);
        } catch (e) {
          console.error(`[AgentBridge] Fehler bei ${serverName}:`, e);
        }
      } else {
        console.log(`[AgentBridge] Server nicht gefunden: ${serverName}`);
      }
    }
  }

  /**
   * Gibt verfügbare Server zurück
   */
  getAvailableServers(): Array<{ name: string; description?: string }> {
    if (!this.serversConfig) return [];
    return Object.entries(this.serversConfig.servers).map(([name, config]) => ({
      name,
      description: config.description,
    }));
  }

  /**
   * Verbindet zu einem MCP Server
   */
  async connectServer(name: string, config: ServerConfig): Promise<void> {
    if (!config.command) {
      throw new Error(`Server ${name}: 'command' ist erforderlich`);
    }

    // Bereits verbunden?
    if (this.connections.has(name)) {
      console.log(`[AgentBridge] ${name} bereits verbunden`);
      return;
    }

    console.log(`[AgentBridge] Verbinde zu ${name}...`);

    const transport = new StdioClientTransport({
      command: config.command,
      args: config.args ?? [],
    });

    const client = new Client(
      { name: "mcp-agent-vscode", version: "0.1.0" },
      { capabilities: {} }
    );

    await client.connect(transport);

    const toolsResult = await client.listTools();

    const connection: McpConnection = {
      name,
      client,
      transport,
      tools: toolsResult.tools,
    };

    this.connections.set(name, connection);

    // Tools zur Gesamtliste hinzufügen
    for (const tool of toolsResult.tools) {
      this.allTools.push({ ...tool, serverName: name });
    }

    console.log(`[AgentBridge] ${name} verbunden mit ${toolsResult.tools.length} Tools`);
  }

  /**
   * Trennt alle Server-Verbindungen
   */
  async disconnectAll(): Promise<void> {
    for (const [name, conn] of this.connections) {
      console.log(`[AgentBridge] Trenne ${name}...`);
      try {
        await conn.client.close();
      } catch (e) {
        console.error(`[AgentBridge] Fehler beim Trennen von ${name}:`, e);
      }
    }
    this.connections.clear();
    this.allTools = [];
  }

  /**
   * Führt eine Agent-Session aus
   */
  async runAgent(
    prompt: string,
    context: AgentContext,
    onProgress?: (message: string) => void
  ): Promise<string> {
    const report = (msg: string) => {
      if (onProgress) onProgress(msg);
      if (this.config.debug) console.log(`[AgentBridge] ${msg}`);
    };

    report(`Starte Agent mit ${this.allTools.length} Tools...`);

    if (this.config.provider === "openai" && this.openai) {
      return this.runWithOpenAI(prompt, context, report);
    } else if (this.anthropic) {
      return this.runWithAnthropic(prompt, context, report);
    } else {
      throw new Error("Kein LLM-Provider initialisiert");
    }
  }

  /**
   * Agent mit OpenAI ausführen
   */
  private async runWithOpenAI(
    prompt: string,
    context: AgentContext,
    report: (msg: string) => void
  ): Promise<string> {
    const systemPrompt = this.buildSystemPrompt(context);

    // Tools für OpenAI vorbereiten
    const tools: OpenAI.Chat.Completions.ChatCompletionTool[] = this.allTools.map((t) => ({
      type: "function" as const,
      function: {
        name: `${t.serverName}__${t.name}`,
        description: t.description ?? t.name,
        parameters: t.inputSchema as Record<string, unknown>,
      },
    }));

    const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
      { role: "system", content: systemPrompt },
      { role: "user", content: prompt },
    ];

    let iterations = 0;
    const maxIterations = 10;

    while (iterations < maxIterations) {
      iterations++;
      report(`Iteration ${iterations}...`);

      const response = await this.openai!.chat.completions.create({
        model: this.config.model ?? "gpt-4o",
        messages,
        tools: tools.length > 0 ? tools : undefined,
        tool_choice: tools.length > 0 ? "auto" : undefined,
      });

      const choice = response.choices[0];
      const message = choice.message;

      // Keine Tool-Calls mehr?
      if (choice.finish_reason === "stop" || !message.tool_calls?.length) {
        return message.content ?? "Keine Antwort generiert.";
      }

      // Tool-Calls verarbeiten
      messages.push(message);

      for (const toolCall of message.tool_calls) {
        const toolName = toolCall.function.name;
        report(`Tool: ${toolName}`);

        try {
          const args = JSON.parse(toolCall.function.arguments || "{}");
          const result = await this.callTool(toolName, args);

          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            content: JSON.stringify(result),
          });
        } catch (error) {
          const errMsg = error instanceof Error ? error.message : String(error);
          report(`Tool-Fehler: ${errMsg}`);

          messages.push({
            role: "tool",
            tool_call_id: toolCall.id,
            content: JSON.stringify({ error: errMsg }),
          });
        }
      }
    }

    return "Maximale Iterationen erreicht.";
  }

  /**
   * Agent mit Anthropic ausführen
   */
  private async runWithAnthropic(
    prompt: string,
    context: AgentContext,
    report: (msg: string) => void
  ): Promise<string> {
    const systemPrompt = this.buildSystemPrompt(context);

    // Tools für Anthropic vorbereiten
    const tools: Anthropic.Messages.Tool[] = this.allTools.map((t) => ({
      name: `${t.serverName}__${t.name}`,
      description: t.description ?? t.name,
      input_schema: t.inputSchema as Anthropic.Messages.Tool["input_schema"],
    }));

    const messages: Anthropic.Messages.MessageParam[] = [
      { role: "user", content: prompt },
    ];

    let iterations = 0;
    const maxIterations = 10;

    while (iterations < maxIterations) {
      iterations++;
      report(`Iteration ${iterations}...`);

      const response = await this.anthropic!.messages.create({
        model: this.config.model ?? "claude-sonnet-4-20250514",
        max_tokens: 4096,
        system: systemPrompt,
        tools: tools.length > 0 ? tools : undefined,
        messages,
      });

      // Fertig?
      if (response.stop_reason === "end_turn") {
        const textBlock = response.content.find(
          (b): b is Anthropic.Messages.TextBlock => b.type === "text"
        );
        return textBlock?.text ?? "Keine Antwort generiert.";
      }

      // Tool-Calls verarbeiten
      if (response.stop_reason === "tool_use") {
        const toolUses = response.content.filter(
          (b): b is Anthropic.Messages.ToolUseBlock => b.type === "tool_use"
        );

        messages.push({ role: "assistant", content: response.content });

        const toolResults: Anthropic.Messages.ToolResultBlockParam[] = [];

        for (const toolUse of toolUses) {
          report(`Tool: ${toolUse.name}`);

          try {
            const result = await this.callTool(
              toolUse.name,
              toolUse.input as Record<string, unknown>
            );

            toolResults.push({
              type: "tool_result",
              tool_use_id: toolUse.id,
              content: JSON.stringify(result),
            });
          } catch (error) {
            const errMsg = error instanceof Error ? error.message : String(error);
            report(`Tool-Fehler: ${errMsg}`);

            toolResults.push({
              type: "tool_result",
              tool_use_id: toolUse.id,
              content: JSON.stringify({ error: errMsg }),
              is_error: true,
            });
          }
        }

        messages.push({ role: "user", content: toolResults });
      }
    }

    return "Maximale Iterationen erreicht.";
  }

  /**
   * Ruft ein Tool auf
   */
  private async callTool(
    fullName: string,
    args: Record<string, unknown>
  ): Promise<unknown> {
    const [serverName, toolName] = fullName.split("__");
    if (!serverName || !toolName) {
      throw new Error(`Ungültiger Tool-Name: ${fullName}`);
    }

    const connection = this.connections.get(serverName);
    if (!connection) {
      throw new Error(`Server '${serverName}' nicht verbunden`);
    }

    const result = await connection.client.callTool({
      name: toolName,
      arguments: args,
    });

    return result;
  }

  /**
   * Baut den System-Prompt
   */
  private buildSystemPrompt(context: AgentContext): string {
    const parts = [
      "Du bist ein hilfreicher KI-Assistent in VS Code.",
      "Du hast Zugriff auf MCP-Tools um Aufgaben auszuführen.",
      "Antworte auf Deutsch, kurz und präzise.",
      "",
      "--- Aktueller Kontext ---",
    ];

    if (context.workspaceFolders.length > 0) {
      parts.push(`Workspace: ${context.workspaceFolders.join(", ")}`);
    }

    if (context.openFiles.length > 0) {
      parts.push(`Offene Dateien: ${context.openFiles.slice(0, 5).join(", ")}`);
    }

    if (context.currentFile) {
      parts.push(`Aktuelle Datei: ${context.currentFile}`);
    }

    if (context.selection) {
      parts.push(`\nSelektion:\n\`\`\`\n${context.selection}\n\`\`\``);
    }

    parts.push("");
    parts.push(`Verfügbare Server: ${Array.from(this.connections.keys()).join(", ")}`);
    parts.push(`Verfügbare Tools: ${this.allTools.length}`);

    return parts.join("\n");
  }

  /**
   * Gibt Status-Informationen zurück
   */
  getStatus(): {
    initialized: boolean;
    provider: string;
    model: string;
    servers: Array<{ name: string; tools: number }>;
    totalTools: number;
  } {
    const servers = Array.from(this.connections.entries()).map(([name, conn]) => ({
      name,
      tools: conn.tools.length,
    }));

    return {
      initialized: this.openai !== null || this.anthropic !== null,
      provider: this.config.provider,
      model: this.config.model ?? (this.config.provider === "openai" ? "gpt-4o" : "claude-sonnet-4-20250514"),
      servers,
      totalTools: this.allTools.length,
    };
  }
}
