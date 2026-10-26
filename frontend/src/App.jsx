import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  BookOpen,
  BrainCircuit,
  Plus,
  Search,
  PanelLeftClose,
  PanelLeftOpen,
  MessageSquare,
  LibraryBig,
  CalendarDays,
  Settings2,
  Sparkles,
  ArrowUp,
  Paperclip,
  ChevronDown,
  MoreHorizontal,
  GraduationCap,
  CircleHelp,
  Menu,
  AlertCircle,
  LoaderCircle,
} from "lucide-react";
const API_BASE_URL = "http://127.0.0.1:8000";
const suggestions = [
  {
    icon: GraduationCap,
    title: "Teach me a concept",
    text: "Explain a difficult topic step by step",
    prompt: "Teach me a concept step by step",
  },
  {
    icon: BrainCircuit,
    title: "Quiz me",
    text: "Test my understanding with questions",
    prompt: "Quiz me on a topic",
  },
  {
    icon: CalendarDays,
    title: "Build a study plan",
    text: "Make a realistic plan for my goals",
    prompt: "Build a study plan for me",
  },
];
function formatConversation(conversation) {
  return {
    id: conversation.id,
    title: conversation.title || "New conversation",
    category: "Your conversations",
    messages: [],
  };
}
function formatMessage(message) {
  return {
    id: message.id,
    role: message.role,
    content: message.content,
    intent: message.intent,
    document_id: message.document_id,
    created_at: message.created_at,
  };
}
function MessageContent({ content }) {
  const paragraphs = String(content || "").split("\n\n");
  return (
    <div className="message-copy">
      {paragraphs.map((paragraph, paragraphIndex) => (
        <p key={paragraphIndex}>
          {paragraph.split("\n").map((line, lineIndex) => (
            <React.Fragment key={lineIndex}>
              {lineIndex > 0 && <br />}
              {line.split(/(`[^`]+`|\*\*[^*]+\*\*)/g).map(
                (part, partIndex) => {
                  if (part.startsWith("`") && part.endsWith("`")) {
                    return (
                      <code key={partIndex}>
                        {part.slice(1, -1)}
                      </code>
                    );
                  }
                  if (part.startsWith("**") && part.endsWith("**")) {
                    return (
                      <strong key={partIndex}>
                        {part.slice(2, -2)}
                      </strong>
                    );
                  }
                  return part;
                }
              )}
            </React.Fragment>
          ))}
        </p>
      ))}
    </div>
  );
}
export default function App() {
  const [chats, setChats] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [loadingChats, setLoadingChats] = useState(true);
  const [chatError, setChatError] = useState("");
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [messageError, setMessageError] = useState("");
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [collapsed, setCollapsed] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [sending, setSending] = useState(false);
  const [sendError, setSendError] = useState("");
  const [creatingChat, setCreatingChat] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [selectedDocumentId, setSelectedDocumentId] = useState(null);
  const [uploadError, setUploadError] = useState("");
  const [uploadSuccess, setUploadSuccess] = useState("");
  const activeChat =
    chats.find((chat) => chat.id === activeId) || null;
  const hasMessages = Boolean(activeChat?.messages?.length);
  const filteredChats = useMemo(
    () =>
      chats.filter((chat) =>
        chat.title.toLowerCase().includes(query.toLowerCase())
      ),
    [chats, query]
  );
  // Load all conversations from FastAPI.
  const loadConversations = useCallback(async () => {
    setLoadingChats(true);
    setChatError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations`
      );
      if (!response.ok) {
        throw new Error(
          `Could not load conversations (HTTP ${response.status})`
        );
      }
      const data = await response.json();
      const conversations = Array.isArray(data.conversations)
        ? data.conversations.map(formatConversation)
        : [];
      setChats((previousChats) =>
        conversations.map((conversation) => {
          const existing = previousChats.find(
            (chat) => chat.id === conversation.id
          );
          return existing
            ? {
                ...conversation,
                messages: existing.messages || [],
              }
            : conversation;
        })
      );
      setActiveId((previousId) => {
        if (
          previousId &&
          conversations.some((chat) => chat.id === previousId)
        ) {
          return previousId;
        }
        return conversations[0]?.id || null;
      });
    } catch (error) {
      console.error("Error loading conversations:", error);
      setChatError(
        "Couldn't load conversations. Check that FastAPI is running and CORS is configured."
      );
    } finally {
      setLoadingChats(false);
    }
  }, []);
  useEffect(() => {
    loadConversations();
  }, [loadConversations]);
  // Load messages whenever the selected conversation changes.
  useEffect(() => {
    if (!activeId) {
      setLoadingMessages(false);
      return;
    }
    let cancelled = false;
    async function loadMessages() {
      setLoadingMessages(true);
      setMessageError("");
      try {
        const response = await fetch(
          `${API_BASE_URL}/conversations/${encodeURIComponent(
            activeId
          )}/messages`
        );
        if (!response.ok) {
          throw new Error(
            `Could not load messages (HTTP ${response.status})`
          );
        }
        const data = await response.json();
        const messages = Array.isArray(data.messages)
          ? data.messages.map(formatMessage)
          : [];
        if (!cancelled) {
          setChats((previousChats) =>
            previousChats.map((chat) =>
              chat.id === activeId
                ? { ...chat, messages }
                : chat
            )
          );
        }
      } catch (error) {
        console.error("Error loading messages:", error);
        if (!cancelled) {
          setMessageError(
            "Couldn't load this conversation's messages. Please try again."
          );
        }
      } finally {
        if (!cancelled) {
          setLoadingMessages(false);
        }
      }
    }
    loadMessages();
    return () => {
      cancelled = true;
    };
  }, [activeId]);
  function selectChat(id) {
    setActiveId(id);
    setMessageError("");
    setSendError("");
    setMobileMenu(false);
  }
  // Create a real conversation in MySQL through FastAPI.
  async function newChat() {
    if (creatingChat) return;
    setCreatingChat(true);
    setSendError("");
    setChatError("");
    try {
      const response = await fetch(
        `${API_BASE_URL}/conversations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            title: "New Chat",
          }),
        }
      );
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          data.detail ||
            `Could not create conversation (HTTP ${response.status})`
        );
      }
      const conversation = formatConversation(data);
      setChats((previousChats) => [
        conversation,
        ...previousChats.filter(
          (chat) => chat.id !== conversation.id
        ),
      ]);
      setActiveId(conversation.id);
      setInput("");
      setQuery("");
      setMobileMenu(false);
    } catch (error) {
      console.error("Error creating conversation:", error);
      setSendError(
        error.message || "Couldn't create a new conversation."
      );
    } finally {
      setCreatingChat(false);
    }
  }
  // Send the user's question to LangGraph through FastAPI.
  async function sendMessage(text = input) {
    const question = text.trim();
    if (!question || !activeId || sending) return;
    const conversationId = activeId;
    setSending(true);
    setSendError("");
    setMessageError("");
    setInput("");
    const temporaryUserMessage = {
      role: "user",
      content: question,
      localPending: true,
    };
    setChats((previousChats) =>
      previousChats.map((chat) =>
        chat.id === conversationId
          ? {
              ...chat,
              messages: [
                ...(chat.messages || []),
                temporaryUserMessage,
              ],
            }
          : chat
      )
    );
    try {
      const response = await fetch(`${API_BASE_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          conversation_id: conversationId,
          question: question,
          document_id: selectedDocumentId,
}),
      });
      const result = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(
          result.detail ||
            `Chat request failed (HTTP ${response.status})`
        );
      }
      const assistantMessage = {
        id: result.assistant_message_id,
        role: "assistant",
        content:
          result.answer || "The assistant returned an empty response.",
        intent: result.intent,
      };
const currentChat = chats.find(
  (chat) => chat.id === conversationId
);
if (currentChat?.title === "New Chat") {
  const newTitle =
    question.length > 50
      ? question.slice(0, 47) + "..."
      : question;
  const titleResponse = await fetch(
    `${API_BASE_URL}/conversations/${encodeURIComponent(
      conversationId
    )}/title`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title: newTitle,
      }),
    }
  );
  if (!titleResponse.ok) {
    console.error("Could not save conversation title");
  }
}
      setChats((previousChats) =>
        previousChats.map((chat) =>
          chat.id === conversationId
            ? {
                ...chat,
                title:
                  chat.title === "New Chat"
                    ? question.slice(0, 48) +
                      (question.length > 48 ? "…" : "")
                    : chat.title,
                messages: [
                  ...(chat.messages || []).filter(
                    (message) => !message.localPending
                  ),
                  assistantMessage,
                ],
              }
            : chat
        )
      );
      // Refresh saved history so database message IDs and content are current.
      const historyResponse = await fetch(
        `${API_BASE_URL}/conversations/${encodeURIComponent(
          conversationId
        )}/messages`
      );
      if (historyResponse.ok) {
        const historyData = await historyResponse.json();
        setChats((previousChats) =>
          previousChats.map((chat) =>
            chat.id === conversationId
              ? {
                  ...chat,
                  messages: (historyData.messages || []).map(
                    formatMessage
                  ),
                }
              : chat
          )
        );
      }
      // Refresh conversation titles/order from the backend.
      await loadConversations();
    } catch (error) {
      console.error("Error sending chat message:", error);
      // Remove the temporary user message. If FastAPI saved the user
      // message before LangGraph failed, it remains in the database.
      setChats((previousChats) =>
        previousChats.map((chat) =>
          chat.id === conversationId
            ? {
                ...chat,
                messages: (chat.messages || []).filter(
                  (message) => !message.localPending
                ),
              }
            : chat
        )
      );
      setInput(question);
      setSendError(
        error.message ||
          "Couldn't send your message. Please try again."
      );
    } finally {
      setSending(false);
    }
  }
  async function loadDocuments() {
    try {
      const response = await fetch(`${API_BASE_URL}/documents`);
      if (!response.ok) throw new Error("Could not load documents.");
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error("Error loading documents:", error);
    }
  }

  useEffect(() => {
    loadDocuments();
  }, []);

  async function uploadDocument(file) {
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setUploadError("Please select a PDF file.");
      setUploadSuccess("");
      return;
    }

    setUploading(true);
    setUploadError("");
    setUploadSuccess("");
    setSendError("");

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(`${API_BASE_URL}/documents/upload`, {
        method: "POST",
        body: formData,
      });
      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(result.detail || "PDF upload failed.");
      }

      setUploadSuccess(`${result.filename} uploaded successfully.`);
      setSelectedDocumentId(result.document_id);
      await loadDocuments();
    } catch (error) {
      console.error("Error uploading PDF:", error);
      setUploadError(error.message || "Could not upload the PDF.");
    } finally {
      setUploading(false);
    }
  }

  function choosePrompt(prompt) {
    setInput(prompt);
    document.querySelector(".composer textarea")?.focus();
  }
  return (
    <div
      className={`app-shell ${
        collapsed ? "sidebar-collapsed" : ""
      }`}
    >
      {mobileMenu && (
        <button
          className="mobile-scrim"
          aria-label="Close menu"
          onClick={() => setMobileMenu(false)}
        />
      )}
      <aside
        className={`sidebar ${
          mobileMenu ? "mobile-open" : ""
        } ${collapsed ? "is-collapsed" : ""}`}
      >
        <div className="brand-row">
          <div className="brand-mark">
            <BrainCircuit size={21} strokeWidth={2.2} />
          </div>
          {!collapsed && (
            <div className="brand-name">
              StudyMind <span>AI</span>
            </div>
          )}
          <button
            className="icon-button sidebar-toggle"
            onClick={() => setCollapsed((value) => !value)}
            title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {collapsed ? (
              <PanelLeftOpen size={18} />
            ) : (
              <PanelLeftClose size={18} />
            )}
          </button>
        </div>
        <button
          className="new-chat-button"
          onClick={newChat}
          disabled={creatingChat}
          title="New chat"
        >
          {creatingChat ? (
            <LoaderCircle size={18} className="spin" />
          ) : (
            <Plus size={18} strokeWidth={2.4} />
          )}
          {!collapsed && (
            <>
              <span>New chat</span>
              <kbd>⌘ K</kbd>
            </>
          )}
        </button>
        {!collapsed && (
          <div className="search-box">
            <Search size={16} />
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search conversations"
              aria-label="Search conversations"
            />
          </div>
        )}
        <div className="sidebar-section">
          {!collapsed && (
            <div className="section-label">WORKSPACE</div>
          )}
          <button
            className="nav-item active"
            onClick={() => setMobileMenu(false)}
          >
            <MessageSquare size={17} />
            <span>Chats</span>
          </button>
          <button
            className="nav-item"
            onClick={() =>
              setSendError(
                "Document upload is not connected yet."
              )
            }
          >
            <LibraryBig size={17} />
            <span>My documents</span>
            <span className="soon-dot" />
          </button>
          <button
            className="nav-item"
            onClick={() =>
              setSendError(
                "For now, ask the StudyMind AI chat to build a study plan."
              )
            }
          >
            <CalendarDays size={17} />
            <span>Study planner</span>
          </button>
        </div>
        <div className="chat-list-section">
          {!collapsed && (
            <div className="list-heading">
              <span>RECENT CHATS</span>
              <button
                className="tiny-icon"
                title="Refresh conversations"
                onClick={() => loadConversations()}
              >
                <MoreHorizontal size={16} />
              </button>
            </div>
          )}
          <div className="chat-list">
            {loadingChats && !chats.length && !collapsed && (
              <div className="empty-search">
                <LoaderCircle size={14} className="spin" />
                Loading conversations…
              </div>
            )}
            {!loadingChats && chatError && !collapsed && (
              <div className="sidebar-error">
                <AlertCircle size={14} />
                {chatError}
              </div>
            )}
            {!loadingChats &&
              !chatError &&
              filteredChats.map((chat) => (
                <button
                  key={chat.id}
                  className={`chat-list-item ${
                    activeId === chat.id ? "selected" : ""
                  }`}
                  onClick={() => selectChat(chat.id)}
                  title={chat.title}
                >
                  <MessageSquare size={15} />
                  <span>{chat.title}</span>
                </button>
              ))}
            {!loadingChats &&
              !chatError &&
              filteredChats.length === 0 &&
              !collapsed && (
                <div className="empty-search">
                  No conversations found
                </div>
              )}
          </div>
        </div>
        <div className="sidebar-bottom">
          <div className="usage-card">
            <div className="usage-icon">
              <Sparkles size={16} />
            </div>
            {!collapsed && (
              <div>
                <strong>Your learning space</strong>
                <p>Small steps. Real progress.</p>
              </div>
            )}
          </div>
          <button
            className="nav-item settings-item"
            onClick={() =>
              setSendError("Settings will be added as the app grows.")
            }
          >
            <Settings2 size={17} />
            <span>Settings</span>
          </button>
          <div className="profile-row">
            <div className="avatar user-avatar">H</div>
            {!collapsed && (
              <div className="profile-copy">
                <strong>My workspace</strong>
                <span>Personal account</span>
              </div>
            )}
            {!collapsed && (
              <MoreHorizontal size={17} className="profile-more" />
            )}
          </div>
        </div>
      </aside>
      <main className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button mobile-menu-button"
              onClick={() => setMobileMenu(true)}
              aria-label="Open menu"
            >
              <Menu size={19} />
            </button>
            <div className="breadcrumb">
              <span>Workspace</span>
              <span className="crumb-slash">/</span>
              <strong>
                {activeChat?.title ||
                  (loadingChats ? "Loading…" : "New conversation")}
              </strong>
            </div>
          </div>
          <div className="topbar-right">
            <div className="status-pill">
              <span className="status-dot" />
              Connected UI
            </div>
            <button className="icon-button help-button" title="Help">
              <CircleHelp size={18} />
            </button>
          </div>
        </header>
        <section
          className={`conversation-area ${
            hasMessages ? "has-messages" : ""
          }`}
        >
          {loadingChats && !chats.length ? (
            <div className="center-state">
              <LoaderCircle size={22} className="spin" />
              <span>Connecting to StudyMind AI…</span>
            </div>
          ) : chatError ? (
            <div className="center-state error-state">
              <AlertCircle size={22} />
              <span>{chatError}</span>
              <button onClick={() => loadConversations()}>
                Try again
              </button>
            </div>
          ) : !activeId ? (
            <div className="welcome-screen">
              <div className="welcome-eyebrow">
                <span className="eyebrow-sparkle">
                  <Sparkles size={14} />
                </span>
                YOUR PERSONAL LEARNING SPACE
              </div>
              <div className="welcome-logo">
                <BrainCircuit size={28} />
              </div>
              <h1>
                Learn something
                <br />
                <span>meaningful today.</span>
              </h1>
              <p className="welcome-subtitle">
                Your study partner for understanding concepts,
                practicing questions, and building consistent
                learning habits.
              </p>
              <div className="welcome-actions">
                <button className="primary-action" onClick={newChat}>
                  <Plus size={17} />
                  Start a conversation
                </button>
              </div>
            </div>
          ) : loadingMessages ? (
            <div className="center-state">
              <LoaderCircle size={22} className="spin" />
              <span>Loading conversation…</span>
            </div>
          ) : messageError ? (
            <div className="center-state error-state">
              <AlertCircle size={22} />
              <span>{messageError}</span>
              <button onClick={() => selectChat(activeId)}>
                Try again
              </button>
            </div>
          ) : !hasMessages ? (
            <div className="welcome-screen">
              <div className="welcome-eyebrow">
                <span className="eyebrow-sparkle">
                  <Sparkles size={14} />
                </span>
                YOUR PERSONAL LEARNING SPACE
              </div>
              <div className="welcome-logo">
                <BrainCircuit size={28} />
              </div>
              <h1>
                Learn something
                <br />
                <span>meaningful today.</span>
              </h1>
              <p className="welcome-subtitle">
                Your study partner for understanding concepts,
                practicing questions, and building consistent
                learning habits.
              </p>
              <div className="suggestion-grid">
                {suggestions.map(
                  ({ icon: Icon, title, text, prompt }) => (
                    <button
                      key={title}
                      className="suggestion-card"
                      onClick={() => choosePrompt(prompt)}
                    >
                      <div className="suggestion-icon">
                        <Icon size={19} />
                      </div>
                      <div className="suggestion-text">
                        <strong>{title}</strong>
                        <span>{text}</span>
                      </div>
                      <span className="suggestion-arrow">↗</span>
                    </button>
                  )
                )}
              </div>
              <div className="welcome-footnote">
                <span className="footnote-line" />
                A calmer way to make progress
                <span className="footnote-line" />
              </div>
            </div>
          ) : (
            <div className="messages-wrap">
              <div className="thread-heading">
                <div className="thread-icon">
                  <BookOpen size={17} />
                </div>
                <div>
                  <h2>{activeChat?.title}</h2>
                  <span>Your learning conversation</span>
                </div>
                <button
                  className="icon-button thread-more"
                  title="Conversation options"
                >
                  <MoreHorizontal size={19} />
                </button>
              </div>
              {activeChat?.messages.map((message, index) => (
                <div
                  key={message.id ?? `${activeId}-${index}`}
                  className={`message-row ${message.role}`}
                >
                  {message.role === "assistant" ? (
                    <div className="message-avatar ai-avatar">
                      <BrainCircuit size={17} />
                    </div>
                  ) : (
                    <div className="message-avatar user-avatar">H</div>
                  )}
                  <div className="message-content">
                    <div className="message-meta">
                      <strong>
                        {message.role === "assistant"
                          ? "StudyMind AI"
                          : "You"}
                      </strong>
                      <span>
                        {message.role === "assistant"
                          ? "Learning assistant"
                          : "You"}
                      </span>
                    </div>
                    <MessageContent content={message.content} />
                  </div>
                </div>
              ))}
              {sending && (
                <div className="message-row assistant">
                  <div className="message-avatar ai-avatar">
                    <BrainCircuit size={17} />
                  </div>
                  <div className="typing-bubble">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              )}
              {sendError && (
                <div className="inline-error">
                  <AlertCircle size={15} />
                  <span>{sendError}</span>
                </div>
              )}
            </div>
          )}
        </section>
        <div className="composer-zone">
          {uploadError && (
            <div className="inline-error composer-error">
              <AlertCircle size={15} />
              <span>{uploadError}</span>
            </div>
          )}

          {uploadSuccess && (
            <div className="upload-success" role="status">
              {uploadSuccess}
            </div>
          )}

          {sendError && !hasMessages && (
            <div className="inline-error composer-error">
              <AlertCircle size={15} />
              <span>{sendError}</span>
            </div>
          )}
          <div className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (
                  event.key === "Enter" &&
                  !event.shiftKey
                ) {
                  event.preventDefault();
                  sendMessage();
                }
              }}
              placeholder={
                activeId
                  ? "Ask anything, or tell me what you're learning..."
                  : "Create a conversation to get started…"
              }
              rows={2}
              aria-label="Message StudyMind AI"
              disabled={!activeId || sending}
            />
            <div className="composer-bottom">
              <div className="composer-tools">
                <input
                  id="pdf-upload"
                  type="file"
                  accept=".pdf,application/pdf"
                  hidden
                  disabled={uploading}
                  onChange={(event) => {
                    const file = event.target.files?.[0];
                    if (file) uploadDocument(file);
                    event.target.value = "";
                  }}
                />
                <button
                  className="tool-button"
                  title="Upload a PDF"
                  disabled={uploading}
                  onClick={() => document.getElementById("pdf-upload")?.click()}
                >
                  {uploading ? (
                    <LoaderCircle size={16} className="spin" />
                  ) : (
                    <Paperclip size={16} />
                  )}
                  <span>{uploading ? "Uploading..." : "Attach PDF"}</span>
                </button>
                <span className="tool-divider" />
                <button className="tool-button mode-button" title="Learning mode">
                  <Sparkles size={15} />
                  <span>Learning mode</span>
                  <ChevronDown size={14} />
                </button>
              </div>
              <div className="composer-actions">
                <span className="enter-hint">↵ to send</span>
                <button
                  className="send-button"
                  onClick={() => sendMessage()}
                  disabled={!input.trim() || !activeId || sending}
                  title="Send message"
                >
                  {sending ? (
                    <LoaderCircle size={18} className="spin" />
                  ) : (
                    <ArrowUp size={19} />
                  )}
                </button>
              </div>
            </div>
          </div>
          <div className="disclaimer">
            StudyMind AI can make mistakes. Check important information
            and keep learning curious.
          </div>
        </div>
      </main>
    </div>
  );
}
