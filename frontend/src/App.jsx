import React, { useState, useEffect, useRef } from 'react';
import { 
  Play, 
  Loader2, 
  FileText, 
  ListChecks, 
  Lightbulb, 
  HelpCircle, 
  Send, 
  MessageSquare,
  Bot,
  User
} from 'lucide-react';

// In development: points to local Flask on port 5001
// In production: reads VITE_API_BASE from frontend/.env.production
const API_BASE = import.meta.env.VITE_API_BASE ?? (import.meta.env.PROD ? "" : "http://localhost:5001");

// --- MAIN APP COMPONENT ---
export default function App() {
  // Input State
  const [source, setSource] = useState('');
  const [language, setLanguage] = useState('english');
  
  // Pipeline State
  const [isProcessing, setIsProcessing] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  
  // Layout State
  const [activeTab, setActiveTab] = useState('summary');
  
  // Chat State
  const [chatHistory, setChatHistory] = useState([
    { role: 'assistant', content: 'Hi! I am ready to answer questions about your video.' }
  ]);
  const [currentQuestion, setCurrentQuestion] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Loading Steps configuration
  const loadingSteps = [
    "Processing audio...",
    "Transcribing with AI...",
    "Generating title & summary...",
    "Extracting insights...",
    "Building RAG engine...",
    "Almost done..."
  ];

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory, isChatLoading]);

  // Handle Pipeline Submission
  const handleAnalyze = async (e) => {
    e.preventDefault();
    if (!source) return;

    setIsProcessing(true);
    setResult(null);
    setError('');
    setLoadingStep(0);
    setChatHistory([
      { role: 'assistant', content: 'Hi! I am ready to answer questions about your video.' }
    ]);
    
    // Cycle through loading steps while waiting for the API
    const stepInterval = setInterval(() => {
      setLoadingStep((prev) => {
        if (prev < loadingSteps.length - 1) return prev + 1;
        return prev;
      });
    }, 15000); // The real pipeline takes minutes, so cycle every 15s

    try {
      const response = await fetch(`${API_BASE}/api/pipeline`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: source.trim(), language }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Pipeline failed');
      }

      setResult(data);
    } catch (err) {
      setError(err.message || 'Something went wrong. Is the backend running?');
    } finally {
      clearInterval(stepInterval);
      setIsProcessing(false);
      setLoadingStep(0);
    }
  };

  // Handle Chat Submission
  const handleChat = async (e) => {
    e.preventDefault();
    if (!currentQuestion.trim() || !result?.session_id) return;

    const questionText = currentQuestion;
    setCurrentQuestion('');
    setChatHistory(prev => [...prev, { role: 'user', content: questionText }]);
    setIsChatLoading(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: result.session_id, question: questionText }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Chat request failed');
      }

      setChatHistory(prev => [...prev, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setChatHistory(prev => [...prev, { role: 'assistant', content: `Error: ${err.message}` }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 font-sans">
      {/* HEADER / INPUT PANEL */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between mb-4">
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-600 to-blue-500 flex items-center gap-2">
              <Play className="text-purple-600" fill="currentColor" />
              AI Video Assistant
            </h1>
          </div>
          
          <form onSubmit={handleAnalyze} className="flex flex-col sm:flex-row gap-4 items-end bg-gray-50 p-4 rounded-xl border border-gray-200 shadow-sm">
            <div className="flex-1 w-full">
              <label className="block text-sm font-medium text-gray-700 mb-1">Source (URL or File Path)</label>
              <input 
                type="text" 
                value={source}
                onChange={(e) => setSource(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none transition-all"
                disabled={isProcessing}
              />
            </div>
            <div className="w-full sm:w-48">
              <label className="block text-sm font-medium text-gray-700 mb-1">Language</label>
              <select 
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-2 rounded-lg border border-gray-300 focus:ring-2 focus:ring-purple-500 focus:border-purple-500 outline-none bg-white transition-all"
                disabled={isProcessing}
              >
                <option value="english">English</option>
                <option value="hinglish">Hinglish</option>
              </select>
            </div>
            <button 
              type="submit" 
              disabled={isProcessing || !source}
              className="w-full sm:w-auto px-6 py-2 bg-gray-900 hover:bg-gray-800 text-white font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 h-[42px]"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Analyzing...
                </>
              ) : (
                'Analyze Video'
              )}
            </button>
          </form>

          {/* ERROR MESSAGE */}
          {error && (
            <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              ❌ {error}
            </div>
          )}

          {/* LOADING INDICATOR */}
          {isProcessing && (
            <div className="mt-6 flex flex-col items-center justify-center py-12">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-gray-100"></div>
                <div className="absolute inset-0 rounded-full border-4 border-purple-500 border-t-transparent animate-spin"></div>
              </div>
              <p className="mt-4 text-sm font-medium text-purple-600 animate-pulse">
                {loadingSteps[loadingStep]}
              </p>
              <p className="mt-1 text-xs text-gray-400">This may take a few minutes for long videos...</p>
            </div>
          )}
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      {!isProcessing && result && (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex flex-col lg:flex-row gap-8">
          
          {/* LEFT COLUMN: Insights Explorer (60%) */}
          <div className="w-full lg:w-3/5 flex flex-col gap-4">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{result.title}</h2>
            
            {/* TABS */}
            <div className="flex border-b border-gray-200">
              <button 
                onClick={() => setActiveTab('summary')}
                className={`px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'summary' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                <FileText className="w-4 h-4" /> Summary
              </button>
              <button 
                onClick={() => setActiveTab('insights')}
                className={`px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'insights' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                <Lightbulb className="w-4 h-4" /> Insights
              </button>
              <button 
                onClick={() => setActiveTab('transcript')}
                className={`px-4 py-3 font-medium text-sm flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'transcript' ? 'border-purple-600 text-purple-600' : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                <MessageSquare className="w-4 h-4" /> Transcript
              </button>
            </div>

            {/* TAB CONTENT */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm min-h-[500px]">
              {activeTab === 'summary' && (
                <div className="prose prose-purple max-w-none">
                  <div className="whitespace-pre-wrap text-gray-700 leading-relaxed">
                    {result.summary}
                  </div>
                </div>
              )}
              
              {activeTab === 'insights' && (
                <div className="flex flex-col gap-6">
                  <div className="bg-green-50 border border-green-100 rounded-lg p-4">
                    <h3 className="font-semibold text-green-800 flex items-center gap-2 mb-2">
                      <ListChecks className="w-5 h-5" /> Action Items
                    </h3>
                    <div className="whitespace-pre-wrap text-green-700 text-sm">{result.action_items}</div>
                  </div>
                  <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
                    <h3 className="font-semibold text-blue-800 flex items-center gap-2 mb-2">
                      <Lightbulb className="w-5 h-5" /> Key Decisions
                    </h3>
                    <div className="whitespace-pre-wrap text-blue-700 text-sm">{result.key_decisions}</div>
                  </div>
                  <div className="bg-amber-50 border border-amber-100 rounded-lg p-4">
                    <h3 className="font-semibold text-amber-800 flex items-center gap-2 mb-2">
                      <HelpCircle className="w-5 h-5" /> Open Questions
                    </h3>
                    <div className="whitespace-pre-wrap text-amber-700 text-sm">{result.open_questions}</div>
                  </div>
                </div>
              )}

              {activeTab === 'transcript' && (
                <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 h-[450px] overflow-y-auto font-mono text-sm text-gray-600 leading-relaxed whitespace-pre-wrap">
                  {result.transcript}
                </div>
              )}
            </div>
          </div>

          {/* RIGHT COLUMN: Chat Interface (40%) */}
          <div className="w-full lg:w-2/5 h-[600px] flex flex-col bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden sticky top-32">
            {/* Chat Header */}
            <div className="bg-gray-900 px-4 py-3 text-white flex items-center gap-2">
              <Bot className="w-5 h-5 text-purple-400" />
              <h3 className="font-semibold">RAG Chat Assistant</h3>
            </div>
            
            {/* Chat Messages */}
            <div className="flex-1 p-4 overflow-y-auto bg-gray-50 flex flex-col gap-4">
              {chatHistory.map((msg, idx) => (
                <div key={idx} className={`flex gap-3 max-w-[85%] ${msg.role === 'user' ? 'self-end flex-row-reverse' : 'self-start'}`}>
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-purple-100 text-purple-700' : 'bg-gray-200 text-gray-700'}`}>
                    {msg.role === 'user' ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>
                  <div className={`px-4 py-2 rounded-2xl text-sm shadow-sm ${msg.role === 'user' ? 'bg-purple-600 text-white rounded-tr-none' : 'bg-white border border-gray-200 text-gray-800 rounded-tl-none'}`}>
                    {msg.content}
                  </div>
                </div>
              ))}
              
              {isChatLoading && (
                <div className="flex gap-3 max-w-[85%] self-start">
                  <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4 text-gray-700" />
                  </div>
                  <div className="px-4 py-3 rounded-2xl bg-white border border-gray-200 rounded-tl-none flex gap-1">
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                    <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* Chat Input */}
            <form onSubmit={handleChat} className="p-3 bg-white border-t border-gray-200">
              <div className="relative flex items-center">
                <input 
                  type="text" 
                  value={currentQuestion}
                  onChange={(e) => setCurrentQuestion(e.target.value)}
                  placeholder="Ask a question about the video..."
                  className="w-full pl-4 pr-12 py-2.5 bg-gray-100 border-transparent focus:bg-white focus:border-purple-500 focus:ring-2 focus:ring-purple-200 rounded-full text-sm outline-none transition-all"
                  disabled={isChatLoading}
                />
                <button 
                  type="submit"
                  disabled={!currentQuestion.trim() || isChatLoading}
                  className="absolute right-1.5 p-1.5 bg-purple-600 text-white rounded-full hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </form>
          </div>

        </main>
      )}

      {/* EMPTY STATE */}
      {!isProcessing && !result && !error && (
        <div className="max-w-3xl mx-auto mt-20 text-center px-4">
          <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Play className="w-8 h-8 text-gray-400 ml-1" />
          </div>
          <h2 className="text-2xl font-semibold text-gray-900 mb-2">Ready to Analyze</h2>
          <p className="text-gray-500 mb-8 max-w-md mx-auto">
            Paste a YouTube URL or path to a local audio/video file above. We'll generate a full transcript, extract key insights, and set up a chat session for you.
          </p>
        </div>
      )}
    </div>
  );
}
