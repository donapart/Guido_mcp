/**
 * MCP Agent Workbench - VS Code Extension
 * 
 * Haupteinstiegspunkt der Extension.
 * Unterstützt OpenAI, Anthropic, Ollama, Azure und Google mit automatischem Server-Loading.
 */

import * as vscode from "vscode";
import * as path from "path";
import * as fs from "fs";
import { AgentBridge, type AgentContext } from "./bridge.js";
import { getWebviewContent } from "./webview/chatPanel.js";

let bridge: AgentBridge | null = null;
let currentPanel: vscode.WebviewPanel | null = null;
let chatHistory: Array<{ role: string; content: string; timestamp: Date }> = [];
let outputChannel: vscode.OutputChannel;

// Modell-Definitionen für QuickPick
const MODEL_DEFINITIONS = {
  openai: [
    { label: "$(beaker) GPT-4.5 Preview", value: "gpt-4.5-preview", description: "Neuestes OpenAI Modell" },
    { label: "$(sparkle) GPT-4o", value: "gpt-4o", description: "Schnellstes GPT-4 (empfohlen)" },
    { label: "$(zap) GPT-4o Mini", value: "gpt-4o-mini", description: "Günstig & schnell" },
    { label: "$(rocket) GPT-4 Turbo", value: "gpt-4-turbo", description: "128K Kontext" },
    { label: "$(symbol-class) GPT-4", value: "gpt-4", description: "Original GPT-4" },
    { label: "$(symbol-method) GPT-3.5 Turbo", value: "gpt-3.5-turbo", description: "Schnell & günstig" },
    { label: "$(lightbulb) o3", value: "o3", description: "Stärkstes Reasoning" },
    { label: "$(lightbulb) o3-mini", value: "o3-mini", description: "Kompaktes o3" },
    { label: "$(lightbulb) o1", value: "o1", description: "Advanced Reasoning" },
    { label: "$(star) o1-pro", value: "o1-pro", description: "Maximales Reasoning" },
    { label: "$(lightbulb) o1-preview", value: "o1-preview", description: "Reasoning Preview" },
    { label: "$(lightbulb) o1-mini", value: "o1-mini", description: "Kompaktes Reasoning" },
  ],
  anthropic: [
    { label: "$(sparkle) Claude Opus 4", value: "claude-opus-4-20250514", description: "Stärkstes Claude Modell" },
    { label: "$(star) Claude Sonnet 4", value: "claude-sonnet-4-20250514", description: "Neuestes Sonnet (empfohlen)" },
    { label: "$(lightbulb) Claude 3.7 Sonnet", value: "claude-3-7-sonnet-20250219", description: "Extended Thinking" },
    { label: "$(symbol-class) Claude 3.5 Sonnet", value: "claude-3-5-sonnet-20241022", description: "Ausgewogen" },
    { label: "$(zap) Claude 3.5 Haiku", value: "claude-3-5-haiku-20241022", description: "Schnell" },
    { label: "$(rocket) Claude 3 Opus", value: "claude-3-opus-20240229", description: "Leistungsstark" },
  ],
  google: [
    { label: "$(sparkle) Gemini 2.5 Pro", value: "gemini-2.5-pro", description: "Stärkstes Google Modell" },
    { label: "$(star) Gemini 2.0 Flash", value: "gemini-2.0-flash", description: "Neuestes Gemini" },
    { label: "$(lightbulb) Gemini 2.0 Thinking", value: "gemini-2.0-flash-thinking", description: "Mit Reasoning" },
    { label: "$(rocket) Gemini 1.5 Pro", value: "gemini-1.5-pro", description: "1M Kontext" },
    { label: "$(zap) Gemini 1.5 Flash", value: "gemini-1.5-flash", description: "Schnell" },
  ],
  ollama: [
    { label: "$(sparkle) Llama 3.3", value: "llama3.3", description: "Meta's neuestes (70B)" },
    { label: "$(symbol-class) Llama 3.2", value: "llama3.2", description: "Meta Llama" },
    { label: "$(symbol-class) Llama 3.1", value: "llama3.1", description: "Meta Llama 405B" },
    { label: "$(code) CodeLlama", value: "codellama", description: "Code-spezialisiert" },
    { label: "$(symbol-method) Mistral", value: "mistral", description: "Open Source" },
    { label: "$(symbol-interface) Mixtral", value: "mixtral", description: "MoE 8x7B" },
    { label: "$(code) Qwen 2.5 Coder", value: "qwen2.5-coder", description: "Alibaba Code-Modell" },
    { label: "$(star) Qwen 2.5", value: "qwen2.5", description: "Alibaba's bestes" },
    { label: "$(code) DeepSeek Coder V2", value: "deepseek-coder-v2", description: "Coding" },
    { label: "$(lightbulb) DeepSeek R1", value: "deepseek-r1", description: "Reasoning Modell" },
    { label: "$(beaker) Phi-4", value: "phi-4", description: "Microsoft's neuestes" },
    { label: "$(symbol-method) Gemma 2", value: "gemma2", description: "Google Open Source" },
    { label: "$(code) StarCoder 2", value: "starcoder2", description: "Code-Modell" },
  ],
  azure: [
    { label: "$(azure) Azure GPT-4o", value: "gpt-4o", description: "Azure Deployment" },
    { label: "$(azure) Azure GPT-4 Turbo", value: "gpt-4-turbo", description: "Azure Deployment" },
    { label: "$(azure) Azure GPT-4", value: "gpt-4", description: "Azure Deployment" },
  ],
};

/**
 * Extension aktivieren
 */
export async function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel("MCP Agent");
  log("Extension wird aktiviert...");

  // Commands registrieren
  context.subscriptions.push(
    vscode.commands.registerCommand("mcpAgent.startSession", () => startSession(context)),
    vscode.commands.registerCommand("mcpAgent.showStatus", showStatus),
    vscode.commands.registerCommand("mcpAgent.sendSelection", sendSelection),
    vscode.commands.registerCommand("mcpAgent.configureServers", configureServers),
    vscode.commands.registerCommand("mcpAgent.selectModel", selectModel),
    vscode.commands.registerCommand("mcpAgent.openSettings", openSettings),
    vscode.commands.registerCommand("mcpAgent.clearHistory", clearHistory),
    vscode.commands.registerCommand("mcpAgent.exportChat", exportChat),
    vscode.commands.registerCommand("mcpAgent.restartServers", restartServers)
  );

  // Status Bar Item
  const statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBarItem.command = "mcpAgent.showStatus";
  statusBarItem.text = "$(robot) MCP Agent";
  statusBarItem.tooltip = "MCP Agent Status anzeigen";
  statusBarItem.show();
  context.subscriptions.push(statusBarItem);

  // Config Change Listener
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("mcpAgent")) {
        log("Konfiguration geändert");
        updateStatusBar(statusBarItem);
      }
    })
  );

  updateStatusBar(statusBarItem);
  log("Extension aktiviert ✓");
  log("Drücke Ctrl+Shift+M um den Chat zu öffnen");
}

/**
 * Logging-Funktion
 */
function log(message: string) {
  const timestamp = new Date().toISOString().substring(11, 19);
  outputChannel.appendLine(`[${timestamp}] ${message}`);
  
  const config = vscode.workspace.getConfiguration("mcpAgent");
  if (config.get<boolean>("debug")) {
    console.log(`[MCP Agent] ${message}`);
  }
}

/**
 * Status Bar aktualisieren
 */
function updateStatusBar(statusBarItem: vscode.StatusBarItem) {
  const config = vscode.workspace.getConfiguration("mcpAgent");
  const provider = config.get<string>("provider") ?? "openai";
  const model = config.get<string>("model") ?? "gpt-4o";
  
  statusBarItem.text = `$(robot) ${provider}/${model.split("-")[0]}`;
  statusBarItem.tooltip = `MCP Agent: ${provider} - ${model}\nKlicken für Status`;
}

/**
 * Extension deaktivieren
 */
export async function deactivate() {
  log("Extension wird deaktiviert...");
  
  if (bridge) {
    await bridge.disconnectAll();
    bridge = null;
  }
  
  if (currentPanel) {
    currentPanel.dispose();
    currentPanel = null;
  }
}

/**
 * Neue Agent-Session starten
 */
async function startSession(context: vscode.ExtensionContext) {
  // Wenn Panel schon existiert, fokussieren
  if (currentPanel) {
    currentPanel.reveal(vscode.ViewColumn.Beside);
    return;
  }

  // Konfiguration laden
  const config = vscode.workspace.getConfiguration("mcpAgent");
  const provider = config.get<string>("provider") ?? "openai";
  const openaiApiKey = config.get<string>("openaiApiKey");
  const anthropicApiKey = config.get<string>("anthropicApiKey");
  const googleApiKey = config.get<string>("googleApiKey");
  const azureEndpoint = config.get<string>("azureEndpoint");
  const azureApiKey = config.get<string>("azureApiKey");
  const ollamaEndpoint = config.get<string>("ollamaEndpoint") ?? "http://localhost:11434";
  const model = config.get<string>("model");
  const activeServers = config.get<string[]>("activeServers") ?? ["demo", "filesystem"];
  const debug = config.get<boolean>("debug") ?? false;
  const serversConfigPath = config.get<string>("serversConfigPath");
  const temperature = config.get<number>("temperature") ?? 0.7;
  const maxTokens = config.get<number>("maxTokens") ?? 4096;
  const systemPrompt = config.get<string>("systemPrompt");

  // API Key prüfen (je nach Provider)
  let apiKey: string | undefined;
  let keySettingName = "";
  
  switch (provider) {
    case "openai":
      apiKey = openaiApiKey;
      keySettingName = "mcpAgent.openaiApiKey";
      break;
    case "anthropic":
      apiKey = anthropicApiKey;
      keySettingName = "mcpAgent.anthropicApiKey";
      break;
    case "google":
      apiKey = googleApiKey;
      keySettingName = "mcpAgent.googleApiKey";
      break;
    case "azure":
      apiKey = azureApiKey;
      keySettingName = "mcpAgent.azureApiKey";
      break;
    case "ollama":
      apiKey = "ollama-local"; // Ollama braucht keinen Key
      break;
  }

  if (!apiKey && provider !== "ollama") {
    const setKey = await vscode.window.showErrorMessage(
      `${provider} API Key nicht konfiguriert`,
      "Einstellungen öffnen",
      "Provider wechseln"
    );
    if (setKey === "Einstellungen öffnen") {
      vscode.commands.executeCommand("workbench.action.openSettings", keySettingName);
    } else if (setKey === "Provider wechseln") {
      selectModel();
    }
    return;
  }

  // Server-Config-Pfad ermitteln
  let configPath = serversConfigPath;
  if (!configPath) {
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
      const possiblePaths = [
        path.join(workspaceFolders[0].uri.fsPath, "agent", "mcp-servers.json"),
        path.join(workspaceFolders[0].uri.fsPath, "mcp-servers.json"),
      ];
      for (const p of possiblePaths) {
        try {
          await vscode.workspace.fs.stat(vscode.Uri.file(p));
          configPath = p;
          break;
        } catch {
          // Datei existiert nicht
        }
      }
    }
  }

  // Bridge initialisieren
  try {
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: "MCP Agent",
        cancellable: false,
      },
      async (progress) => {
        progress.report({ message: "Initialisiere..." });

        bridge = new AgentBridge({
          provider: provider as any,
          openaiApiKey,
          anthropicApiKey,
          googleApiKey,
          azureEndpoint,
          azureApiKey,
          ollamaEndpoint,
          model,
          activeServers,
          serversConfigPath: configPath,
          debug,
          temperature,
          maxTokens,
          systemPrompt,
        });

        await bridge.initialize();

        progress.report({ message: "Verbinde Server..." });
        await bridge.connectActiveServers();

        const status = bridge.getStatus();
        log(`Bridge initialisiert: ${status.servers.length} Server, ${status.totalTools} Tools`);
      }
    );

  } catch (error) {
    log(`Fehler: ${error}`);
    vscode.window.showErrorMessage(
      `Fehler beim Initialisieren: ${error instanceof Error ? error.message : error}`
    );
    return;
  }

  // Webview-Panel erstellen
  const fontSize = config.get<number>("fontSize") ?? 14;
  const showToolCalls = config.get<boolean>("showToolCalls") ?? true;
  
  currentPanel = vscode.window.createWebviewPanel(
    "mcpAgent",
    "🤖 MCP Agent",
    vscode.ViewColumn.Beside,
    {
      enableScripts: true,
      retainContextWhenHidden: true,
      localResourceRoots: [context.extensionUri],
    }
  );

  // HTML setzen
  currentPanel.webview.html = getWebviewContent(
    currentPanel.webview,
    context.extensionUri,
    { fontSize, showToolCalls, provider, model: model ?? "gpt-4o" }
  );

  // Message-Handler
  currentPanel.webview.onDidReceiveMessage(
    async (message) => {
      switch (message.type) {
        case "userPrompt":
          await handleUserPrompt(message.prompt);
          break;
        case "getStatus":
          sendStatus();
          break;
        case "selectModel":
          selectModel();
          break;
        case "openSettings":
          openSettings();
          break;
        case "clearHistory":
          clearHistory();
          break;
      }
    },
    undefined,
    context.subscriptions
  );

  // Cleanup bei Schließen
  currentPanel.onDidDispose(
    () => {
      currentPanel = null;
    },
    undefined,
    context.subscriptions
  );

  // Initial-Status senden
  setTimeout(() => {
    sendStatus();
    const status = bridge?.getStatus();
    if (status) {
      vscode.window.showInformationMessage(
        `MCP Agent bereit: ${status.provider} mit ${status.totalTools} Tools`
      );
    }
  }, 1000);
}

/**
 * Modell wählen (QuickPick)
 */
async function selectModel() {
  const config = vscode.workspace.getConfiguration("mcpAgent");
  const currentProvider = config.get<string>("provider") ?? "openai";
  const currentModel = config.get<string>("model") ?? "gpt-4o";

  // Erst Provider wählen
  const providers = [
    { label: "$(cloud) OpenAI", value: "openai", description: "GPT-4o, GPT-4, GPT-3.5" },
    { label: "$(hubot) Anthropic", value: "anthropic", description: "Claude 3.5, Claude 3" },
    { label: "$(server) Ollama", value: "ollama", description: "Lokale Modelle (kostenlos)" },
    { label: "$(azure) Azure OpenAI", value: "azure", description: "Enterprise Azure" },
    { label: "$(globe) Google AI", value: "google", description: "Gemini Pro, Flash" },
  ];

  const selectedProvider = await vscode.window.showQuickPick(
    providers.map(p => ({
      ...p,
      picked: p.value === currentProvider,
    })),
    {
      placeHolder: "Wähle einen KI-Provider",
      title: "🤖 MCP Agent - Provider wählen",
    }
  );

  if (!selectedProvider) return;

  // Dann Modell wählen
  const models = MODEL_DEFINITIONS[selectedProvider.value as keyof typeof MODEL_DEFINITIONS] ?? [];
  
  const selectedModel = await vscode.window.showQuickPick(
    models.map(m => ({
      ...m,
      picked: m.value === currentModel,
    })),
    {
      placeHolder: "Wähle ein Modell",
      title: `🤖 ${selectedProvider.label} - Modell wählen`,
    }
  );

  if (!selectedModel) return;

  // Konfiguration speichern
  await config.update("provider", selectedProvider.value, vscode.ConfigurationTarget.Global);
  await config.update("model", selectedModel.value, vscode.ConfigurationTarget.Global);

  log(`Provider: ${selectedProvider.value}, Modell: ${selectedModel.value}`);
  
  vscode.window.showInformationMessage(
    `Modell gewechselt: ${selectedModel.label}`,
    "Session neustarten"
  ).then((action) => {
    if (action === "Session neustarten") {
      restartServers();
    }
  });

  // Status aktualisieren
  if (currentPanel) {
    sendStatus();
  }
}

/**
 * Einstellungen öffnen
 */
function openSettings() {
  vscode.commands.executeCommand("workbench.action.openSettings", "mcpAgent");
}

/**
 * Chat-Verlauf löschen
 */
async function clearHistory() {
  const confirm = await vscode.window.showWarningMessage(
    "Chat-Verlauf wirklich löschen?",
    { modal: true },
    "Löschen"
  );

  if (confirm === "Löschen") {
    chatHistory = [];
    if (currentPanel) {
      currentPanel.webview.postMessage({ type: "clearHistory" });
    }
    log("Chat-Verlauf gelöscht");
    vscode.window.showInformationMessage("Chat-Verlauf gelöscht");
  }
}

/**
 * Chat exportieren
 */
async function exportChat() {
  if (chatHistory.length === 0) {
    vscode.window.showWarningMessage("Kein Chat-Verlauf zum Exportieren");
    return;
  }

  const format = await vscode.window.showQuickPick(
    [
      { label: "$(markdown) Markdown", value: "md" },
      { label: "$(json) JSON", value: "json" },
      { label: "$(file) Text", value: "txt" },
    ],
    { placeHolder: "Export-Format wählen" }
  );

  if (!format) return;

  let content = "";
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");

  switch (format.value) {
    case "md":
      content = `# MCP Agent Chat Export\n\n*Exportiert: ${new Date().toLocaleString()}*\n\n---\n\n`;
      for (const msg of chatHistory) {
        const role = msg.role === "user" ? "👤 **User**" : "🤖 **Agent**";
        content += `${role}\n\n${msg.content}\n\n---\n\n`;
      }
      break;
    case "json":
      content = JSON.stringify(chatHistory, null, 2);
      break;
    case "txt":
      for (const msg of chatHistory) {
        const role = msg.role === "user" ? "USER" : "AGENT";
        content += `[${role}]\n${msg.content}\n\n`;
      }
      break;
  }

  const uri = await vscode.window.showSaveDialog({
    defaultUri: vscode.Uri.file(`mcp-chat-${timestamp}.${format.value}`),
    filters: {
      [format.label]: [format.value],
    },
  });

  if (uri) {
    await vscode.workspace.fs.writeFile(uri, Buffer.from(content, "utf-8"));
    vscode.window.showInformationMessage(`Chat exportiert: ${uri.fsPath}`);
  }
}

/**
 * Server neustarten
 */
async function restartServers() {
  log("Server werden neugestartet...");
  
  if (bridge) {
    await bridge.disconnectAll();
    bridge = null;
  }
  
  if (currentPanel) {
    currentPanel.dispose();
    currentPanel = null;
  }

  // Kurz warten
  await new Promise(resolve => setTimeout(resolve, 500));
  
  // Neu starten
  vscode.commands.executeCommand("mcpAgent.startSession");
}

/**
 * User-Prompt verarbeiten
 */
async function handleUserPrompt(prompt: string) {
  if (!bridge || !currentPanel) return;

  // Zur Historie hinzufügen
  chatHistory.push({ role: "user", content: prompt, timestamp: new Date() });

  const ctx = getWorkspaceContext();
  const config = vscode.workspace.getConfiguration("mcpAgent");
  const showToolCalls = config.get<boolean>("showToolCalls") ?? true;

  try {
    const result = await bridge.runAgent(prompt, ctx, (progress) => {
      if (showToolCalls || !progress.includes("Tool:")) {
        currentPanel?.webview.postMessage({ type: "progress", text: progress });
      }
    });

    chatHistory.push({ role: "assistant", content: result, timestamp: new Date() });
    currentPanel.webview.postMessage({ type: "assistant", text: result });
    
    // Historie beschränken
    const maxHistory = config.get<number>("historySize") ?? 100;
    if (chatHistory.length > maxHistory) {
      chatHistory = chatHistory.slice(-maxHistory);
    }

  } catch (error) {
    const errorMsg = error instanceof Error ? error.message : String(error);
    log(`Fehler: ${errorMsg}`);
    currentPanel.webview.postMessage({
      type: "error",
      text: errorMsg,
    });
  }
}

/**
 * Workspace-Kontext sammeln
 */
function getWorkspaceContext(): AgentContext {
  const workspaceFolders = (vscode.workspace.workspaceFolders ?? []).map(
    (f) => f.uri.fsPath
  );

  const openFiles = vscode.workspace.textDocuments
    .filter((d) => d.uri.scheme === "file")
    .map((d) => d.uri.fsPath);

  const editor = vscode.window.activeTextEditor;
  const currentFile = editor?.document.uri.fsPath;
  const selection = editor?.selection.isEmpty
    ? undefined
    : editor?.document.getText(editor.selection);

  return {
    workspaceFolders,
    openFiles,
    currentFile,
    selection,
  };
}

/**
 * Status ans Webview senden
 */
function sendStatus() {
  if (!currentPanel) return;

  const config = vscode.workspace.getConfiguration("mcpAgent");

  if (bridge) {
    const status = bridge.getStatus();
    currentPanel.webview.postMessage({
      type: "status",
      connected: status.initialized,
      provider: status.provider,
      model: status.model,
      servers: status.servers.length,
      tools: status.totalTools,
      serverList: status.servers,
      settings: {
        temperature: config.get<number>("temperature"),
        maxTokens: config.get<number>("maxTokens"),
        showToolCalls: config.get<boolean>("showToolCalls"),
      },
    });
  } else {
    currentPanel.webview.postMessage({
      type: "status",
      connected: false,
      servers: 0,
      tools: 0,
    });
  }
}

/**
 * Server-Status anzeigen
 */
async function showStatus() {
  const config = vscode.workspace.getConfiguration("mcpAgent");
  
  if (!bridge) {
    const action = await vscode.window.showInformationMessage(
      "MCP Agent: Keine aktive Session",
      "Chat öffnen",
      "Modell wählen",
      "Einstellungen"
    );
    
    switch (action) {
      case "Chat öffnen":
        vscode.commands.executeCommand("mcpAgent.startSession");
        break;
      case "Modell wählen":
        selectModel();
        break;
      case "Einstellungen":
        openSettings();
        break;
    }
    return;
  }

  const status = bridge.getStatus();
  
  const serverInfo = status.servers.length > 0
    ? status.servers.map((s) => `• ${s.name}: ${s.tools} Tools`).join("\n")
    : "Keine Server verbunden";

  const message = [
    `# 🤖 MCP Agent Status\n`,
    `| Eigenschaft | Wert |`,
    `|-------------|------|`,
    `| Provider | ${status.provider} |`,
    `| Modell | ${status.model} |`,
    `| Server | ${status.servers.length} |`,
    `| Tools | ${status.totalTools} |`,
    `| Temperature | ${config.get("temperature")} |`,
    `| Max Tokens | ${config.get("maxTokens")} |`,
    ``,
    `## Server`,
    serverInfo,
  ].join("\n");

  const action = await vscode.window.showInformationMessage(
    `MCP Agent: ${status.provider}/${status.model} mit ${status.totalTools} Tools`,
    "Details",
    "Modell wechseln",
    "Server neustarten",
    "Einstellungen"
  );

  switch (action) {
    case "Details":
      const doc = await vscode.workspace.openTextDocument({
        content: message,
        language: "markdown",
      });
      vscode.window.showTextDocument(doc, { preview: true });
      break;
    case "Modell wechseln":
      selectModel();
      break;
    case "Server neustarten":
      restartServers();
      break;
    case "Einstellungen":
      openSettings();
      break;
  }
}

/**
 * Server konfigurieren
 */
async function configureServers() {
  const config = vscode.workspace.getConfiguration("mcpAgent");
  const currentServers = config.get<string[]>("activeServers") ?? [];

  const allServers = [
    { label: "$(beaker) demo", description: "Basis-Tools (Rechnen, Zeit)", picked: currentServers.includes("demo") },
    { label: "$(file) filesystem", description: "Dateien lesen/schreiben", picked: currentServers.includes("filesystem") },
    { label: "$(git-branch) git", description: "Git-Verwaltung", picked: currentServers.includes("git") },
    { label: "$(project) project-manager", description: "Projekt-Scanner", picked: currentServers.includes("project-manager") },
    { label: "$(device-mobile) flutter", description: "Flutter/Dart Build", picked: currentServers.includes("flutter") },
    { label: "$(hubot) ollama", description: "Lokale LLMs", picked: currentServers.includes("ollama") },
    { label: "$(symbol-namespace) docker", description: "Docker lokal", picked: currentServers.includes("docker") },
    { label: "$(remote) docker-remote", description: "Docker Remote", picked: currentServers.includes("docker-remote") },
    { label: "$(github) github", description: "GitHub API", picked: currentServers.includes("github") },
    { label: "$(database) database", description: "SQL-Datenbanken", picked: currentServers.includes("database") },
    { label: "$(search) web-search", description: "Web-Suche", picked: currentServers.includes("web-search") },
    { label: "$(globe) web-scraping", description: "Web-Extraktion", picked: currentServers.includes("web-scraping") },
    { label: "$(mail) email", description: "SMTP/IMAP", picked: currentServers.includes("email") },
    { label: "$(cloud) ionos", description: "IONOS Hosting", picked: currentServers.includes("ionos") },
    { label: "$(terminal) ssh", description: "Remote SSH", picked: currentServers.includes("ssh") },
  ];

  const selected = await vscode.window.showQuickPick(allServers, {
    canPickMany: true,
    placeHolder: "Wähle die aktiven MCP-Server",
    title: "🔧 MCP Server Konfiguration",
  });

  if (selected) {
    const newServers = selected.map((s) => s.label.replace(/\$\([^)]+\)\s*/, ""));
    await config.update("activeServers", newServers, vscode.ConfigurationTarget.Global);
    
    log(`Server aktualisiert: ${newServers.join(", ")}`);
    
    const action = await vscode.window.showInformationMessage(
      `MCP Server aktualisiert: ${newServers.length} Server ausgewählt`,
      "Session neustarten"
    );

    if (action === "Session neustarten") {
      restartServers();
    }
  }
}

/**
 * Aktuelle Selektion an Agent senden
 */
async function sendSelection() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.selection.isEmpty) {
    vscode.window.showWarningMessage("Keine Selektion vorhanden");
    return;
  }

  const selection = editor.document.getText(editor.selection);
  const fileName = path.basename(editor.document.fileName);
  const language = editor.document.languageId;

  // Aktion wählen
  const action = await vscode.window.showQuickPick([
    { label: "$(search) Analysieren", value: "analyze" },
    { label: "$(lightbulb) Erklären", value: "explain" },
    { label: "$(bug) Bugs finden", value: "bugs" },
    { label: "$(sparkle) Verbessern", value: "improve" },
    { label: "$(output) Tests generieren", value: "tests" },
    { label: "$(comment) Dokumentieren", value: "document" },
  ], {
    placeHolder: "Was soll ich mit der Selektion machen?",
    title: "🤖 MCP Agent - Code-Aktion",
  });

  if (!action) return;

  const prompts: Record<string, string> = {
    analyze: `Analysiere folgenden ${language}-Code aus ${fileName}:\n\n\`\`\`${language}\n${selection}\n\`\`\``,
    explain: `Erkläre folgenden ${language}-Code aus ${fileName} Schritt für Schritt:\n\n\`\`\`${language}\n${selection}\n\`\`\``,
    bugs: `Finde potentielle Bugs und Probleme in folgendem ${language}-Code aus ${fileName}:\n\n\`\`\`${language}\n${selection}\n\`\`\``,
    improve: `Verbessere folgenden ${language}-Code aus ${fileName} (Performance, Lesbarkeit, Best Practices):\n\n\`\`\`${language}\n${selection}\n\`\`\``,
    tests: `Generiere Unit-Tests für folgenden ${language}-Code aus ${fileName}:\n\n\`\`\`${language}\n${selection}\n\`\`\``,
    document: `Erstelle Dokumentation und Kommentare für folgenden ${language}-Code aus ${fileName}:\n\n\`\`\`${language}\n${selection}\n\`\`\``,
  };

  // Session starten falls nötig
  if (!currentPanel) {
    await vscode.commands.executeCommand("mcpAgent.startSession");
    await new Promise((resolve) => setTimeout(resolve, 2000));
  }

  if (currentPanel) {
    await handleUserPrompt(prompts[action.value]);
  }
}
