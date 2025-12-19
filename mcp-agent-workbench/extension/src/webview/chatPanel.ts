/**
 * Webview Provider für den Chat-Panel
 * Mit erweiterter UI: Model-Dropdown, Settings, Export, etc.
 */

import * as vscode from "vscode";

interface ChatPanelOptions {
  fontSize?: number;
  showToolCalls?: boolean;
  provider?: string;
  model?: string;
}

export function getWebviewContent(
  webview: vscode.Webview,
  extensionUri: vscode.Uri,
  options: ChatPanelOptions = {}
): string {
  const { fontSize = 14, showToolCalls = true, provider = "openai", model = "gpt-4o" } = options;
  
  // Nonce für Content Security Policy
  const nonce = getNonce();

  return /* html */ `
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource} 'unsafe-inline'; script-src 'nonce-${nonce}';">
  <title>MCP Agent</title>
  <style>
    :root {
      --chat-font-size: ${fontSize}px;
    }
    
    * {
      box-sizing: border-box;
    }
    
    body {
      font-family: var(--vscode-font-family);
      font-size: var(--chat-font-size);
      color: var(--vscode-foreground);
      background-color: var(--vscode-editor-background);
      margin: 0;
      padding: 0;
      height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    /* Header mit Toolbar */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background-color: var(--vscode-sideBar-background);
      border-bottom: 1px solid var(--vscode-panel-border);
      gap: 8px;
      flex-wrap: wrap;
    }
    
    .header-left {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    .header h2 {
      margin: 0;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    
    .model-badge {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px 8px;
      background-color: var(--vscode-badge-background);
      color: var(--vscode-badge-foreground);
      border-radius: 10px;
      font-size: 11px;
      font-weight: 500;
      cursor: pointer;
      transition: background-color 0.15s;
    }
    
    .model-badge:hover {
      background-color: var(--vscode-button-hoverBackground);
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .icon-btn {
      display: flex;
      align-items: center;
      justify-content: center;
      width: 26px;
      height: 26px;
      background: transparent;
      border: none;
      border-radius: 4px;
      color: var(--vscode-foreground);
      cursor: pointer;
      opacity: 0.7;
      transition: all 0.15s;
    }
    
    .icon-btn:hover {
      background-color: var(--vscode-toolbar-hoverBackground);
      opacity: 1;
    }
    
    .icon-btn svg {
      width: 16px;
      height: 16px;
    }
    
    .status {
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .status-dot {
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--vscode-testing-iconFailed);
    }
    
    .status.connected .status-dot {
      background-color: var(--vscode-testing-iconPassed);
    }
    
    /* Chat Container */
    .chat-container {
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      scroll-behavior: smooth;
    }
    
    .message {
      margin-bottom: 12px;
      padding: 10px 12px;
      border-radius: 8px;
      max-width: 88%;
      animation: fadeIn 0.2s ease;
    }
    
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    .message.user {
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      margin-left: auto;
      border-radius: 8px 8px 2px 8px;
    }
    
    .message.assistant {
      background-color: var(--vscode-editor-inactiveSelectionBackground);
      margin-right: auto;
      border-radius: 8px 8px 8px 2px;
    }
    
    .message.system {
      background-color: transparent;
      font-size: 11px;
      color: var(--vscode-descriptionForeground);
      text-align: center;
      max-width: 100%;
      padding: 6px;
    }
    
    .message.error {
      background-color: var(--vscode-inputValidation-errorBackground);
      border: 1px solid var(--vscode-inputValidation-errorBorder);
    }
    
    .message-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }
    
    .message-role {
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      color: var(--vscode-descriptionForeground);
      opacity: 0.8;
    }
    
    .message.user .message-role {
      color: var(--vscode-button-foreground);
      opacity: 0.7;
    }
    
    .message-time {
      font-size: 9px;
      color: var(--vscode-descriptionForeground);
      opacity: 0.6;
    }
    
    .message-content {
      white-space: pre-wrap;
      word-break: break-word;
      line-height: 1.5;
    }
    
    .message-content code {
      background-color: var(--vscode-textCodeBlock-background);
      padding: 1px 4px;
      border-radius: 3px;
      font-family: var(--vscode-editor-font-family);
      font-size: calc(var(--chat-font-size) - 1px);
    }
    
    .message-content pre {
      background-color: var(--vscode-textCodeBlock-background);
      padding: 10px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 8px 0;
      border: 1px solid var(--vscode-panel-border);
    }
    
    .message-content pre code {
      padding: 0;
      background: none;
    }
    
    /* Tool Calls */
    .tool-call {
      background-color: var(--vscode-editorWidget-background);
      border: 1px solid var(--vscode-editorWidget-border);
      border-radius: 6px;
      padding: 8px 10px;
      margin: 6px 0;
      font-size: 11px;
    }
    
    .tool-call-header {
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 500;
      color: var(--vscode-symbolIcon-functionForeground);
    }
    
    .tool-call-args {
      font-family: var(--vscode-editor-font-family);
      font-size: 10px;
      color: var(--vscode-descriptionForeground);
      margin-top: 4px;
      padding-left: 18px;
    }
    
    /* Input Area */
    .input-area {
      padding: 10px 12px;
      background-color: var(--vscode-sideBar-background);
      border-top: 1px solid var(--vscode-panel-border);
    }
    
    .input-container {
      display: flex;
      gap: 8px;
      align-items: flex-end;
    }
    
    .input-wrapper {
      flex: 1;
      display: flex;
      flex-direction: column;
      background-color: var(--vscode-input-background);
      border: 1px solid var(--vscode-input-border);
      border-radius: 6px;
      overflow: hidden;
    }
    
    .input-wrapper:focus-within {
      border-color: var(--vscode-focusBorder);
    }
    
    .input-container textarea {
      width: 100%;
      min-height: 40px;
      max-height: 150px;
      resize: none;
      padding: 8px 10px;
      border: none;
      background: transparent;
      color: var(--vscode-input-foreground);
      font-family: var(--vscode-font-family);
      font-size: var(--chat-font-size);
      line-height: 1.4;
    }
    
    .input-container textarea:focus {
      outline: none;
    }
    
    .input-container textarea::placeholder {
      color: var(--vscode-input-placeholderForeground);
    }
    
    .input-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 4px 6px;
      border-top: 1px solid var(--vscode-panel-border);
      background-color: var(--vscode-editor-background);
    }
    
    .input-hint {
      font-size: 10px;
      color: var(--vscode-descriptionForeground);
      opacity: 0.7;
    }
    
    .send-btn {
      display: flex;
      align-items: center;
      gap: 4px;
      padding: 5px 12px;
      background-color: var(--vscode-button-background);
      color: var(--vscode-button-foreground);
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: all 0.15s;
    }
    
    .send-btn:hover:not(:disabled) {
      background-color: var(--vscode-button-hoverBackground);
    }
    
    .send-btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    
    .send-btn svg {
      width: 14px;
      height: 14px;
    }
    
    /* Loading */
    .loading {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      color: var(--vscode-descriptionForeground);
      font-size: 12px;
      padding: 12px;
    }
    
    .loading-spinner {
      width: 16px;
      height: 16px;
      border: 2px solid var(--vscode-progressBar-background);
      border-top-color: transparent;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
    }
    
    @keyframes spin {
      to { transform: rotate(360deg); }
    }
    
    .loading-text {
      max-width: 300px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    
    /* Welcome Screen */
    .welcome {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 30px;
      text-align: center;
      color: var(--vscode-descriptionForeground);
    }
    
    .welcome-icon {
      font-size: 48px;
      margin-bottom: 16px;
    }
    
    .welcome h3 {
      margin: 0 0 8px 0;
      color: var(--vscode-foreground);
      font-weight: 600;
    }
    
    .welcome p {
      margin: 0 0 16px 0;
      font-size: 12px;
      line-height: 1.5;
    }
    
    .quick-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      justify-content: center;
      margin-top: 12px;
    }
    
    .quick-action {
      padding: 6px 12px;
      background-color: var(--vscode-button-secondaryBackground);
      color: var(--vscode-button-secondaryForeground);
      border: none;
      border-radius: 14px;
      font-size: 11px;
      cursor: pointer;
      transition: all 0.15s;
    }
    
    .quick-action:hover {
      background-color: var(--vscode-button-secondaryHoverBackground);
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
    }
    
    ::-webkit-scrollbar-track {
      background: transparent;
    }
    
    ::-webkit-scrollbar-thumb {
      background-color: var(--vscode-scrollbarSlider-background);
      border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
      background-color: var(--vscode-scrollbarSlider-hoverBackground);
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="header-left">
      <h2>🤖 MCP Agent</h2>
      <span class="model-badge" onclick="selectModel()" title="Modell wechseln">
        <span id="providerIcon">⚡</span>
        <span id="modelName">${model}</span>
        <span>▼</span>
      </span>
    </div>
    <div class="header-right">
      <div id="status" class="status">
        <span class="status-dot"></span>
        <span class="status-text">Verbinde...</span>
      </div>
      <button class="icon-btn" onclick="clearHistory()" title="Chat löschen">
        <svg viewBox="0 0 16 16" fill="currentColor">
          <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
          <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4L4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
        </svg>
      </button>
      <button class="icon-btn" onclick="openSettings()" title="Einstellungen">
        <svg viewBox="0 0 16 16" fill="currentColor">
          <path fill-rule="evenodd" d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
          <path fill-rule="evenodd" d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319zm-2.633.283c.246-.835 1.428-.835 1.674 0l.094.319a1.873 1.873 0 0 0 2.693 1.115l.291-.16c.764-.415 1.6.42 1.184 1.185l-.159.292a1.873 1.873 0 0 0 1.116 2.692l.318.094c.835.246.835 1.428 0 1.674l-.319.094a1.873 1.873 0 0 0-1.115 2.693l.16.291c.415.764-.42 1.6-1.185 1.184l-.291-.159a1.873 1.873 0 0 0-2.693 1.116l-.094.318c-.246.835-1.428.835-1.674 0l-.094-.319a1.873 1.873 0 0 0-2.692-1.115l-.292.16c-.764.415-1.6-.42-1.184-1.185l.159-.291A1.873 1.873 0 0 0 1.945 8.93l-.319-.094c-.835-.246-.835-1.428 0-1.674l.319-.094A1.873 1.873 0 0 0 3.06 4.377l-.16-.292c-.415-.764.42-1.6 1.185-1.184l.292.159a1.873 1.873 0 0 0 2.692-1.115l.094-.319z"/>
        </svg>
      </button>
    </div>
  </div>
  
  <div id="chat" class="chat-container">
    <div class="welcome">
      <div class="welcome-icon">🤖</div>
      <h3>MCP Agent Workbench</h3>
      <p>Ich habe Zugriff auf ${showToolCalls ? "mehrere" : "verschiedene"} MCP-Server und Tools.<br>Stelle eine Frage oder wähle eine Schnellaktion:</p>
      <div class="quick-actions">
        <button class="quick-action" onclick="quickAction('Was kannst du?')">💡 Was kannst du?</button>
        <button class="quick-action" onclick="quickAction('Liste alle Tools')">🔧 Verfügbare Tools</button>
        <button class="quick-action" onclick="quickAction('Analysiere dieses Projekt')">📁 Projekt analysieren</button>
        <button class="quick-action" onclick="quickAction('Git Status')">📊 Git Status</button>
      </div>
    </div>
  </div>
  
  <div class="input-area">
    <div class="input-container">
      <div class="input-wrapper">
        <textarea 
          id="input" 
          placeholder="Nachricht eingeben..."
          rows="1"
        ></textarea>
        <div class="input-actions">
          <span class="input-hint">Enter = Senden · Shift+Enter = Neue Zeile</span>
          <button id="send" class="send-btn" onclick="sendMessage()">
            <svg viewBox="0 0 16 16" fill="currentColor">
              <path d="M15.854.146a.5.5 0 0 1 .11.54l-5.819 14.547a.75.75 0 0 1-1.329.124l-3.178-4.995L.643 7.184a.75.75 0 0 1 .124-1.33L15.314.037a.5.5 0 0 1 .54.11ZM6.636 10.07l2.761 4.338L14.13 2.576 6.636 10.07Zm6.787-8.201L1.591 6.602l4.339 2.76 7.494-7.493Z"/>
            </svg>
            Senden
          </button>
        </div>
      </div>
    </div>
  </div>

  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const chat = document.getElementById('chat');
    const input = document.getElementById('input');
    const sendBtn = document.getElementById('send');
    const status = document.getElementById('status');
    const modelName = document.getElementById('modelName');
    const providerIcon = document.getElementById('providerIcon');
    
    let isLoading = false;
    let hasMessages = false;
    const showToolCalls = ${showToolCalls};
    
    const providerIcons = {
      openai: '⚡',
      anthropic: '🤖',
      ollama: '🦙',
      azure: '☁️',
      google: '🔮'
    };
    
    // Quick Action
    function quickAction(text) {
      input.value = text;
      sendMessage();
    }
    
    // Nachricht senden
    function sendMessage() {
      const text = input.value.trim();
      if (!text || isLoading) return;
      
      // Welcome entfernen beim ersten Nachricht
      if (!hasMessages) {
        const welcome = chat.querySelector('.welcome');
        if (welcome) welcome.remove();
        hasMessages = true;
      }
      
      addMessage('user', text);
      input.value = '';
      autoResize();
      
      setLoading(true);
      vscode.postMessage({ type: 'userPrompt', prompt: text });
    }
    
    // Modell wechseln
    function selectModel() {
      vscode.postMessage({ type: 'selectModel' });
    }
    
    // Einstellungen öffnen
    function openSettings() {
      vscode.postMessage({ type: 'openSettings' });
    }
    
    // Chat löschen
    function clearHistory() {
      vscode.postMessage({ type: 'clearHistory' });
    }
    
    // Auto-Resize Textarea
    function autoResize() {
      input.style.height = 'auto';
      input.style.height = Math.min(input.scrollHeight, 150) + 'px';
    }
    
    input.addEventListener('input', autoResize);
    
    // Enter zum Senden
    input.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
    
    // Timestamp formatieren
    function formatTime(date) {
      return date.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' });
    }
    
    // Nachricht zum Chat hinzufügen
    function addMessage(role, content, isHtml = false) {
      const div = document.createElement('div');
      div.className = 'message ' + role;
      
      const roleLabel = {
        user: 'Du',
        assistant: 'Agent',
        system: 'System',
        error: 'Fehler'
      }[role] || role;
      
      const time = formatTime(new Date());
      
      div.innerHTML = \`
        <div class="message-header">
          <span class="message-role">\${roleLabel}</span>
          <span class="message-time">\${time}</span>
        </div>
        <div class="message-content">\${isHtml ? content : formatContent(content)}</div>
      \`;
      
      chat.appendChild(div);
      chat.scrollTop = chat.scrollHeight;
    }
    
    // Content formatieren (Code-Blöcke, Links, etc.)
    function formatContent(text) {
      // Escape HTML
      text = escapeHtml(text);
      
      // Code-Blöcke
      text = text.replace(/\\\`\\\`\\\`([\\s\\S]*?)\\\`\\\`\\\`/g, '<pre><code>$1</code></pre>');
      
      // Inline Code
      text = text.replace(/\\\`([^\\\`]+)\\\`/g, '<code>$1</code>');
      
      // Bold
      text = text.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
      
      return text;
    }
    
    // Loading-State
    function setLoading(loading) {
      isLoading = loading;
      sendBtn.disabled = loading;
      
      const existingLoader = document.getElementById('loader');
      if (loading && !existingLoader) {
        const loader = document.createElement('div');
        loader.id = 'loader';
        loader.className = 'loading';
        loader.innerHTML = '<div class="loading-spinner"></div><span class="loading-text">Agent arbeitet...</span>';
        chat.appendChild(loader);
        chat.scrollTop = chat.scrollHeight;
      } else if (!loading && existingLoader) {
        existingLoader.remove();
      }
    }
    
    // HTML escapen
    function escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    }
    
    // Nachrichten empfangen
    window.addEventListener('message', (event) => {
      const msg = event.data;
      
      switch (msg.type) {
        case 'assistant':
          setLoading(false);
          addMessage('assistant', msg.text);
          break;
          
        case 'error':
          setLoading(false);
          addMessage('error', msg.text);
          break;
          
        case 'progress':
          const loader = document.getElementById('loader');
          if (loader) {
            const loadingText = loader.querySelector('.loading-text');
            if (loadingText) {
              loadingText.textContent = msg.text;
            }
          }
          break;
          
        case 'status':
          const statusEl = document.getElementById('status');
          const statusText = statusEl.querySelector('.status-text');
          
          if (msg.connected) {
            statusEl.classList.add('connected');
            statusText.textContent = \`\${msg.servers} Server · \${msg.tools} Tools\`;
          } else {
            statusEl.classList.remove('connected');
            statusText.textContent = 'Nicht verbunden';
          }
          
          if (msg.model) {
            modelName.textContent = msg.model;
          }
          if (msg.provider && providerIcons[msg.provider]) {
            providerIcon.textContent = providerIcons[msg.provider];
          }
          break;
          
        case 'toolCall':
          if (showToolCalls) {
            const toolDiv = document.createElement('div');
            toolDiv.className = 'message system';
            toolDiv.innerHTML = \`
              <div class="tool-call">
                <div class="tool-call-header">🔧 \${escapeHtml(msg.tool)}</div>
                \${msg.args ? '<div class="tool-call-args">' + escapeHtml(JSON.stringify(msg.args)) + '</div>' : ''}
              </div>
            \`;
            chat.appendChild(toolDiv);
            chat.scrollTop = chat.scrollHeight;
          }
          break;
          
        case 'clearHistory':
          // Chat zurücksetzen
          chat.innerHTML = \`
            <div class="welcome">
              <div class="welcome-icon">🤖</div>
              <h3>MCP Agent Workbench</h3>
              <p>Chat-Verlauf gelöscht. Stelle eine neue Frage:</p>
              <div class="quick-actions">
                <button class="quick-action" onclick="quickAction('Was kannst du?')">💡 Was kannst du?</button>
                <button class="quick-action" onclick="quickAction('Liste alle Tools')">🔧 Verfügbare Tools</button>
              </div>
            </div>
          \`;
          hasMessages = false;
          break;
      }
    });
    
    // Initial-Status anfragen
    vscode.postMessage({ type: 'getStatus' });
    
    // Input fokussieren
    input.focus();
  </script>
</body>
</html>
`;
}

function getNonce(): string {
  let text = "";
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
