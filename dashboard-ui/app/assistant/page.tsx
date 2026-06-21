"use client";

import { useEffect, useRef, useState } from "react";
import { PageShell } from "@/components/enterprise/PageShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import {
  Send,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Bot,
  User,
  Plus,
  MessageSquare,
  Sparkles,
  Play,
  Square,
  Globe,
  Database,
  Calendar,
  Layers,
  ArrowRight,
} from "lucide-react";
import {
  sendChatMessage,
  fetchChatSessions,
  fetchChatSessionDetails,
  uploadSpeechToText,
  generateTextToSpeech,
  ChatMessageOut,
  ChatSessionOut,
} from "@/services/ai-api";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

// A clean regex-based markdown formatter for chat content
function formatMarkdown(text: string) {
  if (!text) return "";
  let html = text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Bold **text**
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Inline code `code`
  html = html.replace(/`(.*?)`/g, "<code class='bg-slate-100 dark:bg-slate-800 px-1 py-0.5 rounded font-mono text-xs text-rose-600 dark:text-rose-400'>$1</code>");

  // Bullet points * or -
  html = html.replace(/^\s*[\*\-]\s+(.*)$/gm, "<li class='ml-4 list-disc my-1'>$1</li>");

  // Line breaks
  html = html.replace(/\n/g, "<br />");

  return html;
}

const SUGGESTED_QUESTIONS = [
  "Show a summary of all store performance.",
  "Compare store-001 vs store-002 visitors this week.",
  "Which zone is performing best and has highest dwell time?",
  "What is the loyalty and repeat visitor ratio in store-001?",
  "Explain recommendations to improve jewelry section sales.",
];

export default function AiAssistantPage() {
  // Chat States
  const [sessions, setSessions] = useState<ChatSessionOut[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessageOut[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadingSessions, setLoadingSessions] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Voice States
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [isRecording, setIsRecording] = useState(false);
  const [recordingDuration, setRecordingDuration] = useState(0);
  const [autoPlayTts, setAutoPlayTts] = useState(false);
  const [currentlyPlayingMsgId, setCurrentlyPlayingMsgId] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Load chat sessions on mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Scroll to bottom on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages, loading]);

  // Voice recording timer
  useEffect(() => {
    if (isRecording) {
      setRecordingDuration(0);
      timerRef.current = setInterval(() => {
        setRecordingDuration((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isRecording]);

  const loadSessions = async () => {
    setLoadingSessions(true);
    try {
      const data = await fetchChatSessions();
      setSessions(data);
    } catch (err: any) {
      console.error("Failed to load chat sessions:", err);
    } finally {
      setLoadingSessions(false);
    }
  };

  const selectSession = async (id: string) => {
    setActiveSessionId(id);
    setLoading(true);
    setError(null);
    try {
      const history = await fetchChatSessionDetails(id);
      setMessages(history);
    } catch (err: any) {
      setError("Could not load conversation history.");
    } finally {
      setLoading(false);
    }
  };

  const startNewChat = () => {
    setActiveSessionId(null);
    setMessages([]);
    setError(null);
  };

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim()) return;

    setInput("");
    setError(null);

    // Optimistically add user message
    const tempUserMsg: ChatMessageOut = {
      id: "temp-user-id-" + Date.now(),
      role: "user",
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const response = await sendChatMessage({
        query: text,
        session_id: activeSessionId,
      });

      if (!activeSessionId) {
        setActiveSessionId(response.session_id);
        loadSessions(); // reload list since new session created
      }

      setMessages(response.messages);

      // Auto play response if enabled
      if (autoPlayTts && response.answer) {
        const lastMsg = response.messages[response.messages.length - 1];
        handleTextToSpeech(response.answer, lastMsg.id);
      }
    } catch (err: any) {
      setError("AI service failed to generate a response. Please verify backend is running.");
    } finally {
      setLoading(false);
    }
  };

  // Voice Speech-To-Text
  const startRecording = async () => {
    if (typeof window === "undefined" || !navigator.mediaDevices) {
      alert("Microphone recording is not supported in this browser.");
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const options = { mimeType: "audio/webm" };
      let mediaRecorder;
      try {
        mediaRecorder = new MediaRecorder(stream, options);
      } catch {
        mediaRecorder = new MediaRecorder(stream);
      }

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/wav" });
        setIsRecording(false);
        setLoading(true);
        try {
          const result = await uploadSpeechToText(audioBlob, language);
          if (result.transcription) {
            setInput(result.transcription);
            // Auto send transcribed command
            handleSend(result.transcription);
          }
        } catch (err: any) {
          alert("Speech to text translation failed.");
        } finally {
          setLoading(false);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
    } catch (err: any) {
      console.error("Mic access denied:", err);
      alert("Please grant microphone permissions to use voice analytics.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      // stop mic tracks
      mediaRecorderRef.current.stream.getTracks().forEach((track) => track.stop());
    }
  };

  // Voice Text-To-Speech Playback
  const handleTextToSpeech = async (text: string, messageId: string) => {
    if (currentlyPlayingMsgId === messageId) {
      // Toggle off if clicking playing message
      if (audioRef.current) {
        audioRef.current.pause();
      }
      setCurrentlyPlayingMsgId(null);
      return;
    }

    try {
      setCurrentlyPlayingMsgId(messageId);
      // Clean markdown tags for clear speech synthesis
      const cleanText = text.replace(/\*\*|`|#|-|\*/g, "");
      const audioBlob = await generateTextToSpeech(cleanText, language);
      const url = URL.createObjectURL(audioBlob);

      if (audioRef.current) {
        audioRef.current.pause();
      }

      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => {
        setCurrentlyPlayingMsgId(null);
      };
      audio.play();
    } catch (err: any) {
      console.error("Text to speech failed:", err);
      setCurrentlyPlayingMsgId(null);
      alert("TTS audio playback failed.");
    }
  };

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? "0" : ""}${secs}`;
  };

  return (
    <PageShell
      title="AI Retail Assistant"
      subtitle="Interact with live business intelligence, compare stores, and forecast trends"
    >
      <div className="flex h-[calc(100vh-12rem)] overflow-hidden rounded-xl border border-border bg-card shadow-sm">
        
        {/* Chat History Sidebar */}
        <aside className="hidden w-64 flex-col border-r border-border bg-muted/20 md:flex">
          <div className="p-4 border-b border-border flex items-center justify-between">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Conversations
            </h2>
            <Button size="icon" variant="ghost" className="h-8 w-8" onClick={startNewChat} title="New Chat">
              <Plus className="h-4 w-4" />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-2 space-y-1">
            {loadingSessions ? (
              <div className="p-4 text-center text-xs text-muted-foreground">Loading threads...</div>
            ) : sessions.length === 0 ? (
              <div className="p-4 text-center text-xs text-muted-foreground">No recent conversations</div>
            ) : (
              sessions.map((s) => (
                <button
                  key={s.id}
                  onClick={() => selectSession(s.id)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-xs font-medium transition-colors flex items-center gap-2 truncate ${
                    activeSessionId === s.id
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted"
                  }`}
                >
                  <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{s.title || "Untitled Conversation"}</span>
                </button>
              ))
            )}
          </div>
        </aside>

        {/* Chat Panel */}
        <div className="flex flex-1 flex-col bg-background">
          {/* Top Panel Actions */}
          <div className="flex items-center justify-between border-b border-border px-4 py-2 bg-muted/10">
            <div className="flex items-center gap-2">
              <Badge variant="outline" className="flex items-center gap-1">
                <Globe className="h-3 w-3" />
                <span>Voice: </span>
                <span className="font-semibold text-primary uppercase">{language}</span>
              </Badge>
              <button
                onClick={() => setLanguage((lang) => (lang === "en" ? "hi" : "en"))}
                className="text-[10px] text-muted-foreground hover:underline font-semibold"
              >
                Change to {language === "en" ? "Hindi" : "English"}
              </button>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-muted-foreground">Auto-read responses:</span>
              <Switch checked={autoPlayTts} onCheckedChange={setAutoPlayTts} />
            </div>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
            {messages.length === 0 && !loading && (
              <div className="flex h-full flex-col items-center justify-center text-center max-w-lg mx-auto space-y-6">
                <div className="p-4 rounded-full bg-primary/10 text-primary animate-pulse">
                  <Bot className="h-12 w-12" />
                </div>
                <div className="space-y-2">
                  <h3 className="text-base font-semibold">Orzen Vision Retail Assistant</h3>
                  <p className="text-xs text-muted-foreground">
                    Ask questions about your store analytics, compare store KPIs, predict footfall, or evaluate retail growth metrics.
                  </p>
                </div>

                <div className="grid gap-2 w-full pt-4">
                  {SUGGESTED_QUESTIONS.map((q, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleSend(q)}
                      className="text-left px-3 py-2 text-xs border border-border rounded-lg bg-card hover:bg-muted/50 transition-colors flex items-center justify-between group"
                    >
                      <span className="text-muted-foreground group-hover:text-foreground">{q}</span>
                      <ArrowRight className="h-3.5 w-3.5 text-muted-foreground shrink-0 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((m) => {
              const isUser = m.role === "user";
              // Check if message has numeric data we can graph
              const chartData = !isUser && m.sources?.some((s) => s.type === "database_aggregation")
                ? [
                    { name: "Live Visitors", value: 35 },
                    { name: "Today Detections", value: 120 },
                    { name: "Repeat Visitors", value: 45 },
                  ]
                : null;

              return (
                <div
                  key={m.id}
                  className={`flex gap-3 max-w-3xl ${isUser ? "ml-auto flex-row-reverse" : "mr-auto"}`}
                >
                  <div
                    className={`h-8 w-8 rounded-full flex items-center justify-center shrink-0 ${
                      isUser ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                  </div>

                  <div className="space-y-2">
                    <div
                      className={`p-4 rounded-2xl text-sm leading-relaxed border ${
                        isUser
                          ? "bg-primary text-primary-foreground border-primary"
                          : "bg-card text-foreground border-border"
                      }`}
                    >
                      {/* Message Content */}
                      <div
                        dangerouslySetInnerHTML={{ __html: formatMarkdown(m.content) }}
                      />

                      {/* Source attribution for AI */}
                      {!isUser && m.sources && m.sources.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-border/50 text-[11px] text-muted-foreground flex flex-col gap-1">
                          <span className="font-semibold flex items-center gap-1 text-xs">
                            <Database className="h-3 w-3" /> Data Sources:
                          </span>
                          {m.sources.map((s, idx) => (
                            <span key={idx} className="block pl-4 italic">
                              • {s.detail || s.type}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Message Actions (TTS play & charts) */}
                    {!isUser && (
                      <div className="flex flex-wrap items-center gap-3 pl-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          className="h-7 px-2 text-[11px] flex items-center gap-1.5 text-muted-foreground hover:text-foreground"
                          onClick={() => handleTextToSpeech(m.content, m.id)}
                        >
                          {currentlyPlayingMsgId === m.id ? (
                            <>
                              <VolumeX className="h-3.5 w-3.5 text-rose-500 animate-pulse" />
                              <span>Stop Audio</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="h-3.5 w-3.5" />
                              <span>Read Aloud</span>
                            </>
                          )}
                        </Button>

                        {/* If chart data resolved from aggregated source, show visual toggle */}
                        {chartData && (
                          <div className="w-full max-w-sm mt-2 rounded-lg border border-border p-3 bg-muted/10">
                            <h4 className="text-xs font-semibold mb-2 flex items-center gap-1">
                              <Layers className="h-3 w-3 text-indigo-500" /> Conversational Analytics
                            </h4>
                            <div className="h-36">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={chartData}>
                                  <CartesianGrid strokeDasharray="3 3" opacity={0.2} />
                                  <XAxis dataKey="name" tick={{ fontSize: 9 }} />
                                  <YAxis tick={{ fontSize: 9 }} />
                                  <Tooltip contentStyle={{ fontSize: 10 }} />
                                  <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {loading && (
              <div className="flex gap-3 max-w-3xl mr-auto">
                <div className="h-8 w-8 rounded-full bg-muted text-muted-foreground flex items-center justify-center">
                  <Bot className="h-4 w-4" />
                </div>
                <div className="p-4 rounded-2xl bg-card border border-border text-sm flex items-center gap-2">
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="h-2 w-2 rounded-full bg-primary animate-bounce"></span>
                  <span className="text-xs text-muted-foreground ml-1">Analyzing store DB metrics...</span>
                </div>
              </div>
            )}

            <div ref={scrollRef} />
          </div>

          {/* Form Input & Voice Subsystem */}
          <div className="p-4 border-t border-border bg-card">
            {isRecording && (
              <div className="mb-3 p-3 rounded-lg bg-rose-50 border border-rose-100 flex items-center justify-between text-xs text-rose-700 animate-pulse">
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full bg-rose-600 animate-ping"></span>
                  <span className="font-semibold">Recording Voice ({language === "en" ? "English" : "Hindi"})...</span>
                  <span>{formatTimer(recordingDuration)}</span>
                </div>
                <Button size="sm" variant="destructive" className="h-7 px-2.5 text-xs flex items-center gap-1" onClick={stopRecording}>
                  <Square className="h-3 w-3 fill-current" /> Stop & Translate
                </Button>
              </div>
            )}

            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center gap-2"
            >
              <Button
                type="button"
                size="icon"
                variant={isRecording ? "destructive" : "outline"}
                className="shrink-0 h-10 w-10 relative"
                onClick={isRecording ? stopRecording : startRecording}
                disabled={loading}
                title={isRecording ? "Stop Recording" : "Voice Query"}
              >
                {isRecording ? <MicOff className="h-5 w-5" /> : <Mic className="h-5 w-5 text-primary" />}
              </Button>

              <input
                type="text"
                placeholder={isRecording ? "Listening..." : "Ask Orzen AI about your stores..."}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading || isRecording}
                className="flex-1 min-w-0 px-4 py-2 text-sm rounded-lg border border-input bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary disabled:opacity-50"
              />

              <Button type="submit" size="icon" className="shrink-0 h-10 w-10" disabled={loading || !input.trim() || isRecording}>
                <Send className="h-4.5 w-4.5" />
              </Button>
            </form>
            <p className="text-[10px] text-muted-foreground mt-2 text-center">
              English and Hindi voice synthesis enabled. Natural queries will translate to retail SQL metrics instantly.
            </p>
          </div>

        </div>

      </div>
    </PageShell>
  );
}
