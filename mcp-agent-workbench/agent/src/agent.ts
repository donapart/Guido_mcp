/**
 * Agent - LLM-gesteuerter Agent mit Tool-Execution
 * 
 * Der Kern des Systems: Nimmt User-Prompts, orchestriert Tool-Aufrufe
 * und liefert finale Antworten.
 * 
 * Unterstützt: Anthropic Claude und OpenAI GPT
 */

import Anthropic from "@anthropic-ai/sdk";
import OpenAI from "openai";
import type { McpClientManager } from "./client.js";
import type { ToolRegistry } from "./registry.js";

// Types für Anthropic Messages API
type MessageRole = "user" | "assistant";
type ContentBlock = Anthropic.Messages.ContentBlock;
type ToolUseBlock = Anthropic.Messages.ToolUseBlock;
type ToolResultBlockParam = Anthropic.Messages.ToolResultBlockParam;
type MessageParam = Anthropic.Messages.MessageParam;
type ToolParam = Anthropic.Messages.Tool;

// LLM Provider Type
type LLMProvider = "anthropic" | "openai";

export interface AgentConfig {
  model?: string;
  maxTokens?: number;
  maxIterations?: number;
  systemPrompt?: string;
  debug?: boolean;
  provider?: LLMProvider;
}

export interface AgentContext {
  workspaceFolders?: string[];
  openFiles?: string[];
  currentFile?: string;
  selection?: string;
  customContext?: Record<string, unknown>;
}

export interface AgentResult {
  success: boolean;
  answer: string;
  toolCalls: Array<{
    tool: string;
    args: Record<string, unknown>;
    result: unknown;
  }>;
  iterations: number;
  error?: string;
}

const DEFAULT_SYSTEM_PROMPT = `Du bist ein hilfreicher KI-Assistent mit Zugriff auf verschiedene Tools.

Deine Aufgaben:
1. Verstehe die Anfrage des Nutzers genau
2. Nutze die verfügbaren Tools, um Informationen zu sammeln oder Aktionen auszuführen
3. Erkläre dem Nutzer, was du tust
4. Gib eine klare, hilfreiche Antwort

Regeln:
- Nutze Tools nur wenn nötig
- Erkläre deine Schritte
- Bei Fehlern: Versuche es anders oder erkläre das Problem
- Sei präzise und hilfreich`;

/**
 * MCP Agent
 * 
 * Orchestriert LLM-Aufrufe und Tool-Execution in einem Loop.
 * Unterstützt Anthropic Claude und OpenAI GPT.
 */
export class McpAgent {
  private anthropic: Anthropic | null = null;
  private openai: OpenAI | null = null;
  private provider: LLMProvider;
  private mcpClient: McpClientManager;
  private registry: ToolRegistry;
  private config: Required<AgentConfig>;

  constructor(
    mcpClient: McpClientManager,
    registry: ToolRegistry,
    config: AgentConfig = {}
  ) {
    // Provider bestimmen basierend auf verfügbaren API Keys
    const hasAnthropic = !!process.env.ANTHROPIC_API_KEY;
    const hasOpenAI = !!process.env.OPENAI_API_KEY;
    
    // Expliziter Provider oder Auto-Detect
    this.provider = config.provider ?? (hasOpenAI ? "openai" : "anthropic");
    
    if (this.provider === "anthropic" && hasAnthropic) {
      this.anthropic = new Anthropic({
        apiKey: process.env.ANTHROPIC_API_KEY,
      });
    } else if (this.provider === "openai" && hasOpenAI) {
      this.openai = new OpenAI({
        apiKey: process.env.OPENAI_API_KEY,
      });
    } else {
      throw new Error(`Kein API Key für Provider '${this.provider}' gefunden`);
    }

    this.mcpClient = mcpClient;
    this.registry = registry;
    
    // Default-Modell je nach Provider
    const defaultModel = this.provider === "openai" ? "gpt-4o" : "claude-sonnet-4-20250514";
    
    this.config = {
      model: config.model ?? defaultModel,
      maxTokens: config.maxTokens ?? 4096,
      maxIterations: config.maxIterations ?? 10,
      systemPrompt: config.systemPrompt ?? DEFAULT_SYSTEM_PROMPT,
      debug: config.debug ?? false,
      provider: this.provider,
    };
    
    console.log(`🧠 LLM Provider: ${this.provider.toUpperCase()}`);
    console.log(`   Modell: ${this.config.model}`);
  }

  /**
   * Führt eine Agent-Session aus
   */
  async run(userPrompt: string, context?: AgentContext): Promise<AgentResult> {
    if (this.provider === "openai") {
      return this.runWithOpenAI(userPrompt, context);
    } else {
      return this.runWithAnthropic(userPrompt, context);
    }
  }

  /**
   * Agent-Loop mit OpenAI
   */
  private async runWithOpenAI(userPrompt: string, context?: AgentContext): Promise<AgentResult> {
    if (!this.openai) throw new Error("OpenAI nicht initialisiert");
    
    const toolCalls: AgentResult["toolCalls"] = [];
    let iterations = 0;

    // System-Prompt mit Kontext
    let systemPrompt = this.config.systemPrompt;
    if (context) {
      systemPrompt += this.buildContextSection(context);
    }

    // Tools für OpenAI vorbereiten
    const tools: OpenAI.Chat.Completions.ChatCompletionTool[] = this.registry.getForLLM().map((t) => ({
      type: "function" as const,
      function: {
        name: t.name,
        description: t.description,
        parameters: t.input_schema as Record<string, unknown>,
      },
    }));

    // Message History
    const messages: OpenAI.Chat.Completions.ChatCompletionMessageParam[] = [
      { role: "system", content: systemPrompt },
      { role: "user", content: userPrompt },
    ];

    // Agent Loop
    while (iterations < this.config.maxIterations) {
      iterations++;

      if (this.config.debug) {
        console.log(`\n--- Iteration ${iterations} ---`);
      }

      try {
        const response = await this.openai.chat.completions.create({
          model: this.config.model,
          max_tokens: this.config.maxTokens,
          messages,
          tools: tools.length > 0 ? tools : undefined,
        });

        const choice = response.choices[0];
        const message = choice.message;

        if (this.config.debug) {
          console.log(`   Finish reason: ${choice.finish_reason}`);
        }

        // Fertig?
        if (choice.finish_reason === "stop" || !message.tool_calls) {
          return {
            success: true,
            answer: message.content ?? "Keine Antwort generiert.",
            toolCalls,
            iterations,
          };
        }

        // Tool-Calls verarbeiten
        if (message.tool_calls && message.tool_calls.length > 0) {
          messages.push(message);

          for (const toolCall of message.tool_calls) {
            const toolName = toolCall.function.name;
            const args = JSON.parse(toolCall.function.arguments);

            if (this.config.debug) {
              console.log(`   🔧 Tool: ${toolName}`);
              console.log(`      Input: ${JSON.stringify(args).slice(0, 200)}`);
            }

            try {
              const result = await this.mcpClient.callToolByFullName(toolName, args);

              toolCalls.push({ tool: toolName, args, result });

              messages.push({
                role: "tool",
                tool_call_id: toolCall.id,
                content: JSON.stringify(result),
              });

              if (this.config.debug) {
                console.log(`      Result: ${JSON.stringify(result).slice(0, 200)}`);
              }
            } catch (error) {
              const errorMessage = error instanceof Error ? error.message : String(error);
              
              toolCalls.push({ tool: toolName, args, result: { error: errorMessage } });

              messages.push({
                role: "tool",
                tool_call_id: toolCall.id,
                content: JSON.stringify({ error: errorMessage }),
              });

              if (this.config.debug) {
                console.log(`      ❌ Error: ${errorMessage}`);
              }
            }
          }
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        return {
          success: false,
          answer: `Fehler: ${errorMessage}`,
          toolCalls,
          iterations,
          error: errorMessage,
        };
      }
    }

    return {
      success: false,
      answer: `Maximale Iterationen (${this.config.maxIterations}) erreicht.`,
      toolCalls,
      iterations,
      error: "Max iterations reached",
    };
  }

  /**
   * Agent-Loop mit Anthropic
   */
  private async runWithAnthropic(userPrompt: string, context?: AgentContext): Promise<AgentResult> {
    if (!this.anthropic) throw new Error("Anthropic nicht initialisiert");
    
    const toolCalls: AgentResult["toolCalls"] = [];
    let iterations = 0;

    // System-Prompt mit Kontext erweitern
    let systemPrompt = this.config.systemPrompt;
    if (context) {
      systemPrompt += this.buildContextSection(context);
    }

    // Tools für das LLM vorbereiten
    const tools = this.registry.getForLLM().map((t): ToolParam => ({
      name: t.name,
      description: t.description,
      input_schema: t.input_schema as ToolParam["input_schema"],
    }));

    if (this.config.debug) {
      console.log(`🤖 Agent startet mit ${tools.length} Tools`);
      console.log(`   Prompt: ${userPrompt.slice(0, 100)}...`);
    }

    // Message History initialisieren
    const messages: MessageParam[] = [
      { role: "user", content: userPrompt },
    ];

    // Agent Loop
    while (iterations < this.config.maxIterations) {
      iterations++;

      if (this.config.debug) {
        console.log(`\n--- Iteration ${iterations} ---`);
      }

      try {
        // LLM aufrufen
        const response = await this.anthropic.messages.create({
          model: this.config.model,
          max_tokens: this.config.maxTokens,
          system: systemPrompt,
          tools,
          messages,
        });

        if (this.config.debug) {
          console.log(`   Stop reason: ${response.stop_reason}`);
        }

        // Prüfen ob fertig (end_turn = keine weiteren Tool-Calls)
        if (response.stop_reason === "end_turn") {
          const textContent = response.content.find(
            (block): block is Anthropic.Messages.TextBlock => block.type === "text"
          );
          
          return {
            success: true,
            answer: textContent?.text ?? "Keine Antwort generiert.",
            toolCalls,
            iterations,
          };
        }

        // Tool-Calls verarbeiten
        if (response.stop_reason === "tool_use") {
          const toolUseBlocks = response.content.filter(
            (block): block is ToolUseBlock => block.type === "tool_use"
          );

          // Assistant-Message zur History hinzufügen
          messages.push({ role: "assistant", content: response.content });

          // Tool-Results sammeln
          const toolResults: ToolResultBlockParam[] = [];

          for (const toolUse of toolUseBlocks) {
            if (this.config.debug) {
              console.log(`   🔧 Tool: ${toolUse.name}`);
              console.log(`      Input: ${JSON.stringify(toolUse.input).slice(0, 200)}`);
            }

            try {
              // Tool ausführen
              const result = await this.mcpClient.callToolByFullName(
                toolUse.name,
                toolUse.input as Record<string, unknown>
              );

              // Ergebnis speichern
              toolCalls.push({
                tool: toolUse.name,
                args: toolUse.input as Record<string, unknown>,
                result,
              });

              toolResults.push({
                type: "tool_result",
                tool_use_id: toolUse.id,
                content: JSON.stringify(result),
              });

              if (this.config.debug) {
                console.log(`      Result: ${JSON.stringify(result).slice(0, 200)}`);
              }
            } catch (error) {
              const errorMessage = error instanceof Error ? error.message : String(error);
              
              toolCalls.push({
                tool: toolUse.name,
                args: toolUse.input as Record<string, unknown>,
                result: { error: errorMessage },
              });

              toolResults.push({
                type: "tool_result",
                tool_use_id: toolUse.id,
                content: JSON.stringify({ error: errorMessage }),
                is_error: true,
              });

              if (this.config.debug) {
                console.log(`      ❌ Error: ${errorMessage}`);
              }
            }
          }

          // Tool-Results zur History hinzufügen
          messages.push({ role: "user", content: toolResults });
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        
        return {
          success: false,
          answer: `Fehler während der Agent-Ausführung: ${errorMessage}`,
          toolCalls,
          iterations,
          error: errorMessage,
        };
      }
    }

    // Max Iterations erreicht
    return {
      success: false,
      answer: `Maximale Anzahl an Iterationen (${this.config.maxIterations}) erreicht.`,
      toolCalls,
      iterations,
      error: "Max iterations reached",
    };
  }

  /**
   * Baut den Kontext-Abschnitt für den System-Prompt
   */
  private buildContextSection(context: AgentContext): string {
    const parts: string[] = ["\n\n--- Aktueller Kontext ---"];

    if (context.workspaceFolders?.length) {
      parts.push(`Workspace: ${context.workspaceFolders.join(", ")}`);
    }

    if (context.openFiles?.length) {
      parts.push(`Offene Dateien: ${context.openFiles.join(", ")}`);
    }

    if (context.currentFile) {
      parts.push(`Aktuelle Datei: ${context.currentFile}`);
    }

    if (context.selection) {
      parts.push(`Selektion:\n\`\`\`\n${context.selection}\n\`\`\``);
    }

    if (context.customContext) {
      parts.push(`Zusätzlicher Kontext: ${JSON.stringify(context.customContext)}`);
    }

    return parts.join("\n");
  }

  /**
   * Einfacher Chat ohne Tools (für Tests)
   */
  async chat(message: string): Promise<string> {
    if (this.provider === "openai" && this.openai) {
      const response = await this.openai.chat.completions.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        messages: [{ role: "user", content: message }],
      });
      return response.choices[0]?.message?.content ?? "Keine Antwort.";
    } else if (this.anthropic) {
      const response = await this.anthropic.messages.create({
        model: this.config.model,
        max_tokens: this.config.maxTokens,
        messages: [{ role: "user", content: message }],
      });

      const textContent = response.content.find(
        (block): block is Anthropic.Messages.TextBlock => block.type === "text"
      );

      return textContent?.text ?? "Keine Antwort.";
    }
    throw new Error("Kein LLM Provider verfügbar");
  }
}
