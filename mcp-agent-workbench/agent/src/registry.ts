/**
 * Tool Registry
 * 
 * Verwaltet die Registrierung und Suche von Tools über mehrere Server hinweg.
 * Ermöglicht dynamische Tool-Auswahl basierend auf Kontext.
 */

import type { Tool } from "@modelcontextprotocol/sdk/types.js";

export interface RegisteredTool extends Tool {
  serverName: string;
  category?: string;
  tags?: string[];
  priority?: number;
}

export interface ToolSearchOptions {
  category?: string;
  tags?: string[];
  namePattern?: RegExp;
  servers?: string[];
  maxResults?: number;
}

/**
 * Tool Registry für dynamische Tool-Verwaltung
 */
export class ToolRegistry {
  private tools: Map<string, RegisteredTool> = new Map();
  private categoryIndex: Map<string, Set<string>> = new Map();
  private tagIndex: Map<string, Set<string>> = new Map();

  /**
   * Registriert ein Tool
   */
  register(tool: RegisteredTool): void {
    const fullName = `${tool.serverName}__${tool.name}`;
    this.tools.set(fullName, tool);

    // Category-Index aktualisieren
    if (tool.category) {
      if (!this.categoryIndex.has(tool.category)) {
        this.categoryIndex.set(tool.category, new Set());
      }
      this.categoryIndex.get(tool.category)!.add(fullName);
    }

    // Tag-Index aktualisieren
    if (tool.tags) {
      for (const tag of tool.tags) {
        if (!this.tagIndex.has(tag)) {
          this.tagIndex.set(tag, new Set());
        }
        this.tagIndex.get(tag)!.add(fullName);
      }
    }
  }

  /**
   * Registriert mehrere Tools von einem Server
   */
  registerFromServer(
    serverName: string,
    tools: Tool[],
    options?: { category?: string; tags?: string[] }
  ): void {
    for (const tool of tools) {
      this.register({
        ...tool,
        serverName,
        category: options?.category,
        tags: options?.tags,
      });
    }
  }

  /**
   * Entfernt alle Tools eines Servers
   */
  unregisterServer(serverName: string): void {
    const toRemove: string[] = [];
    
    for (const [fullName, tool] of this.tools) {
      if (tool.serverName === serverName) {
        toRemove.push(fullName);
      }
    }

    for (const fullName of toRemove) {
      const tool = this.tools.get(fullName);
      if (tool) {
        // Aus Indizes entfernen
        if (tool.category) {
          this.categoryIndex.get(tool.category)?.delete(fullName);
        }
        if (tool.tags) {
          for (const tag of tool.tags) {
            this.tagIndex.get(tag)?.delete(fullName);
          }
        }
        this.tools.delete(fullName);
      }
    }
  }

  /**
   * Holt ein Tool nach vollständigem Namen
   */
  get(fullName: string): RegisteredTool | undefined {
    return this.tools.get(fullName);
  }

  /**
   * Sucht Tools nach Kriterien
   */
  search(options: ToolSearchOptions = {}): RegisteredTool[] {
    let candidates = new Set<string>(this.tools.keys());

    // Nach Kategorie filtern
    if (options.category) {
      const categoryTools = this.categoryIndex.get(options.category);
      if (categoryTools) {
        candidates = new Set([...candidates].filter((t) => categoryTools.has(t)));
      } else {
        candidates = new Set();
      }
    }

    // Nach Tags filtern (AND-Verknüpfung)
    if (options.tags && options.tags.length > 0) {
      for (const tag of options.tags) {
        const tagTools = this.tagIndex.get(tag);
        if (tagTools) {
          candidates = new Set([...candidates].filter((t) => tagTools.has(t)));
        } else {
          candidates = new Set();
          break;
        }
      }
    }

    // Nach Server filtern
    if (options.servers && options.servers.length > 0) {
      candidates = new Set(
        [...candidates].filter((fullName) => {
          const tool = this.tools.get(fullName);
          return tool && options.servers!.includes(tool.serverName);
        })
      );
    }

    // Nach Name-Pattern filtern
    if (options.namePattern) {
      candidates = new Set(
        [...candidates].filter((fullName) => options.namePattern!.test(fullName))
      );
    }

    // Tools sammeln und sortieren
    let results: RegisteredTool[] = [];
    for (const fullName of candidates) {
      const tool = this.tools.get(fullName);
      if (tool) results.push(tool);
    }

    // Nach Priorität sortieren (höhere Priorität zuerst)
    results.sort((a, b) => (b.priority ?? 0) - (a.priority ?? 0));

    // Limit anwenden
    if (options.maxResults && results.length > options.maxResults) {
      results = results.slice(0, options.maxResults);
    }

    return results;
  }

  /**
   * Gibt alle Tools zurück
   */
  getAll(): RegisteredTool[] {
    return Array.from(this.tools.values());
  }

  /**
   * Gibt Tools im LLM-Format zurück
   */
  getForLLM(options?: ToolSearchOptions): Array<{
    name: string;
    description: string;
    input_schema: unknown;
  }> {
    const tools = options ? this.search(options) : this.getAll();
    
    return tools.map((tool) => ({
      name: `${tool.serverName}__${tool.name}`,
      description: tool.description ?? `Tool: ${tool.name}`,
      input_schema: tool.inputSchema,
    }));
  }

  /**
   * Gibt Statistiken zurück
   */
  getStats(): {
    totalTools: number;
    byServer: Record<string, number>;
    byCategory: Record<string, number>;
    topTags: Array<{ tag: string; count: number }>;
  } {
    const byServer: Record<string, number> = {};
    const byCategory: Record<string, number> = {};

    for (const tool of this.tools.values()) {
      byServer[tool.serverName] = (byServer[tool.serverName] ?? 0) + 1;
      if (tool.category) {
        byCategory[tool.category] = (byCategory[tool.category] ?? 0) + 1;
      }
    }

    const topTags = Array.from(this.tagIndex.entries())
      .map(([tag, tools]) => ({ tag, count: tools.size }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10);

    return {
      totalTools: this.tools.size,
      byServer,
      byCategory,
      topTags,
    };
  }
}
