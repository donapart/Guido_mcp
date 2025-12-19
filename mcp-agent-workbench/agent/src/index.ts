/**
 * MCP Agent Host - Entry Point
 * 
 * Startet den Agent und führt eine Demo-Session aus.
 */

import "dotenv/config";
import { readFile } from "fs/promises";
import { McpClientManager } from "./client.js";
import { ToolRegistry } from "./registry.js";
import { McpAgent } from "./agent.js";

interface ServerConfig {
  type: "stdio" | "http";
  command?: string;
  args?: string[];
  url?: string;
  description?: string;
}

interface McpConfig {
  servers: Record<string, ServerConfig>;
  defaults?: {
    activeServers?: string[];
    timeout?: number;
    maxRetries?: number;
  };
}

async function loadConfig(configPath: string): Promise<McpConfig> {
  const content = await readFile(configPath, "utf-8");
  return JSON.parse(content) as McpConfig;
}

async function main() {
  console.log("🚀 MCP Agent Host startet...\n");

  // Konfiguration laden
  const configPath = process.env.MCP_CONFIG_PATH ?? "./mcp-servers.json";
  let config: McpConfig;
  
  try {
    config = await loadConfig(configPath);
    console.log(`📋 Konfiguration geladen: ${configPath}`);
    console.log(`   Server definiert: ${Object.keys(config.servers).join(", ")}`);
  } catch (error) {
    console.error(`❌ Fehler beim Laden der Konfiguration:`, error);
    process.exit(1);
  }

  // MCP Client Manager erstellen und Server verbinden
  const mcpClient = new McpClientManager();
  
  try {
    const activeServers = config.defaults?.activeServers ?? Object.keys(config.servers);
    console.log(`\n🔌 Verbinde zu Servern: ${activeServers.join(", ")}...\n`);
    
    await mcpClient.connectFromConfig(config.servers, activeServers);
  } catch (error) {
    console.error("❌ Fehler beim Verbinden zu Servern:", error);
    await mcpClient.disconnectAll();
    process.exit(1);
  }

  // Tool Registry aufbauen
  const registry = new ToolRegistry();
  
  for (const tool of mcpClient.getAllTools()) {
    registry.register({
      ...tool,
      serverName: tool.serverName,
    });
  }

  const stats = registry.getStats();
  console.log(`\n📊 Tool Registry:`);
  console.log(`   Total: ${stats.totalTools} Tools`);
  console.log(`   By Server:`, stats.byServer);

  // Agent erstellen
  const agent = new McpAgent(mcpClient, registry, {
    debug: process.env.DEBUG === "true",
    model: process.env.LLM_MODEL ?? "claude-sonnet-4-20250514",
  });

  // Demo: Agent ausführen
  console.log("\n" + "=".repeat(60));
  console.log("🤖 Agent Demo");
  console.log("=".repeat(60) + "\n");

  const demoPrompt = process.argv[2] ?? "Berechne 17 + 25 und erkläre mir welches Tool du dafür verwendet hast.";
  
  console.log(`📝 User: ${demoPrompt}\n`);

  try {
    const result = await agent.run(demoPrompt);

    console.log("\n" + "-".repeat(60));
    console.log(`✅ Erfolg: ${result.success}`);
    console.log(`📊 Iterationen: ${result.iterations}`);
    console.log(`🔧 Tool-Aufrufe: ${result.toolCalls.length}`);
    
    if (result.toolCalls.length > 0) {
      console.log("\n   Tool-Historie:");
      for (const call of result.toolCalls) {
        console.log(`   - ${call.tool}: ${JSON.stringify(call.args)} → ${JSON.stringify(call.result).slice(0, 100)}`);
      }
    }

    console.log("\n" + "-".repeat(60));
    console.log("🤖 Agent:", result.answer);
    
  } catch (error) {
    console.error("❌ Agent-Fehler:", error);
  }

  // Cleanup
  console.log("\n🔌 Trenne Server-Verbindungen...");
  await mcpClient.disconnectAll();
  console.log("👋 Bye!");
}

// Graceful Shutdown
process.on("SIGINT", () => {
  console.log("\n\n⚠️ SIGINT empfangen, beende...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\n\n⚠️ SIGTERM empfangen, beende...");
  process.exit(0);
});

// Start
main().catch((error) => {
  console.error("❌ Unerwarteter Fehler:", error);
  process.exit(1);
});
