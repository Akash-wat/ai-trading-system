"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  Activity,
  DollarSign,
  RefreshCw,
  AlertCircle,
  History,
  BarChart2,
  BookOpen,
  Shield,
  Zap,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api";

export default function Dashboard() {
  const [marketContext, setMarketContext] = useState<any>(null);
  const [portfolio, setPortfolio] = useState<any>(null);
  const [signals, setSignals] = useState<any[]>([]);
  const [signalHistory, setSignalHistory] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  const [backtestRunning, setBacktestRunning] = useState(false);
  const [backtestProgress, setBacktestProgress] = useState(0);
  const [backtestStatus, setBacktestStatus] = useState("");
    const [currentStock, setCurrentStock] = useState("");
  const [selectedSignal, setSelectedSignal] = useState<any>(null);
  const [aiAnalysis, setAiAnalysis] = useState<string>("");
  const [aiLoading, setAiLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("scanner");
  const [loading, setLoading] = useState(false);
  const [regime, setRegime] = useState<any>(null);
  const [strategies, setStrategies] = useState<any[]>([]);
  const [morningBriefing, setMorningBriefing] = useState<any>(null);
  const [globalMarkets, setGlobalMarkets] = useState<any>(null);
  const [fleetStatus, setFleetStatus] = useState<any>(null);
  const [loadingFleet, setLoadingFleet] = useState(false);
  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [agentControlLoading, setAgentControlLoading] = useState(false);

  // Phase 5 Additive State Variables
  const [autonomousScan, setAutonomousScan] = useState<any>(null);
  const [scanningAutonomous, setScanningAutonomous] = useState(false);
  const [aiStrategies, setAiStrategies] = useState<any[]>([]);
  const [generatingStrategies, setGeneratingStrategies] = useState(false);
  const [sentimentCache, setSentimentCache] = useState<{ [key: string]: any }>({});
  const [loadingSentiment, setLoadingSentiment] = useState<string | null>(null);
  const [performanceAnalysis, setPerformanceAnalysis] = useState<any>(null);
  const [loadingPerformance, setLoadingPerformance] = useState(false);
  const [researchData, setResearchData] = useState<any>(null);
  const [loadingResearch, setLoadingResearch] = useState(false);
  const [monitorResult, setMonitorResult] = useState<any>(null);

  const fetchMarketContext = async () => {
    const res = await fetch(`${API_BASE}/market-context`);
    const data = await res.json();
    setMarketContext(data);
  };
  const fetchAgentLogs = async () => {
  try {
    const res = await fetch(`${API_BASE}/agent/logs`);
    const data = await res.json();
    setAgentLogs(data.logs || []);
  } catch (err) {
    console.error("Fetch agent logs failed:", err);
  }
};

  const fetchFleetStatus = async () => {
  setLoadingFleet(true);
  try {
    const res = await fetch(`${API_BASE}/fleet/status`);
    const data = await res.json();
    setFleetStatus(data);
  } catch (err) {
    console.error("Fleet status fetch failed:", err);
  }
  setLoadingFleet(false);
};

const startAutonomousAgent = async () => {
  setAgentControlLoading(true);
  try {
    const res = await fetch(`${API_BASE}/agent/start`, { method: "POST" });
    const data = await res.json();
    alert(data.message || "Autonomous agent started");
    fetchFleetStatus();
  } catch (err) {
    console.error("Start agent failed:", err);
    alert("Failed to start agent");
  }
  setAgentControlLoading(false);
};

const stopAutonomousAgent = async () => {
  setAgentControlLoading(true);
  try {
    const res = await fetch(`${API_BASE}/agent/stop`, { method: "POST" });
    const data = await res.json();
    alert(data.message || "Autonomous agent stopped");
    fetchFleetStatus();
  } catch (err) {
    console.error("Stop agent failed:", err);
    alert("Failed to stop agent");
  }
  setAgentControlLoading(false);
};
  const fetchPortfolio = async () => {
    const res = await fetch(`${API_BASE}/portfolio`);
    const data = await res.json();
    setPortfolio(data);
  };

  const fetchSignalHistory = async () => {
    const res = await fetch(`${API_BASE}/signals/history`);
    const data = await res.json();
    setSignalHistory(data.signals || []);
  };

  const fetchRegime = async () => {
    const res = await fetch(`${API_BASE}/market/regime`);
    const data = await res.json();
    setRegime(data);
  };

  const fetchStrategies = async () => {
    const res = await fetch(`${API_BASE}/backtest/strategies`);
    const data = await res.json();
    setStrategies(data.strategies || []);
  };

  // Phase 5 Fetch Engine Methods
  const fetchAutonomousScan = async () => {
    setScanningAutonomous(true);
    try {
      const res = await fetch(`${API_BASE}/market/autonomous-scan`, { signal: AbortSignal.timeout(60000) });
      const data = await res.json();
      setAutonomousScan(data);
    } catch (err) {
      console.error("Autonomous scan fetch failed:", err);
    }
    setScanningAutonomous(false);
  };
  const pollBacktestProgress = async () => {
  const interval = setInterval(async () => {
    try {
      const res = await fetch(`${API_BASE}/backtest/progress`);
      const data = await res.json();
      setBacktestProgress(data.percent || 0);
      setCurrentStock(data.current_stock || "");
      setBacktestStatus(`${data.completed || 0} of ${data.total || 500} stocks processed`);
      
      if (data.percent >= 100) {
        clearInterval(interval);
        setBacktestRunning(false);
        setTimeout(() => {
          setBacktestProgress(0);
          setBacktestStatus("");
          setCurrentStock("");
        }, 3000);
      }
    } catch (err) {
      console.error("Progress poll failed:", err);
    }
  }, 2000);
  return interval;
};

  const fetchAiStrategies = async () => {
    try {
      const res = await fetch(`${API_BASE}/strategies/ai-generated`);
      const data = await res.json();
      setAiStrategies(data.strategies || []);
    } catch (err) {
      console.error("AI strategies fetch failed:", err);
    }
  };

  const generateNewAiStrategies = async () => {
    setGeneratingStrategies(true);
    try {
      await fetch(`${API_BASE}/strategies/generate`, { signal: AbortSignal.timeout(180000) });
      await fetchAiStrategies();
    } catch (err) {
      console.error("Strategy generation failed:", err);
    }
    setGeneratingStrategies(false);
  };

  const fetchPerformanceAnalysis = async () => {
    setLoadingPerformance(true);
    try {
      const res = await fetch(`${API_BASE}/performance/analysis`, { signal: AbortSignal.timeout(30000) });
      const data = await res.json();
      setPerformanceAnalysis(data);
    } catch (err) {
      console.error("Performance analysis failed:", err);
    }
    setLoadingPerformance(false);
  };

  const fetchStockResearch = async (symbol: string) => {
    setLoadingResearch(true);
    try {
      const res = await fetch(`${API_BASE}/research/${symbol}`);
      const data = await res.json();
      setResearchData(data);
    } catch (err) {
      console.error("Research failed:", err);
    }
    setLoadingResearch(false);
  };

  const monitorPositions = async () => {
    try {
      const res = await fetch(`${API_BASE}/monitor/positions`);
      const data = await res.json();
      setMonitorResult(data);
    } catch (err) {
      console.error("Monitor failed:", err);
    }
  };
  const fetchMorningBriefing = async () => {
  try {
    const res = await fetch(`${API_BASE}/market-intel/briefing`);
    const data = await res.json();
    setMorningBriefing(data);
  } catch (err) {
    console.error("Morning briefing failed:", err);
  }
};

const fetchGlobalMarkets = async () => {
  try {
    const res = await fetch(`${API_BASE}/market-intel/global`);
    const data = await res.json();
    setGlobalMarkets(data);
  } catch (err) {
    console.error("Global markets failed:", err);
  }
};

  const fetchStockSentiment = async (symbol: string) => {
    if (sentimentCache[symbol]) return;
    setLoadingSentiment(symbol);
    try {
      // Stripping potential duplicate .NS extensions if present natively
      const cleanSymbol = symbol.replace(".NS", "");
      const res = await fetch(`${API_BASE}/sentiment/${cleanSymbol}`);
      const data = await res.json();
      setSentimentCache(prev => ({ ...prev, [symbol]: data }));
    } catch (err) {
      console.error("Sentiment lookup failed:", err);
    }
    setLoadingSentiment(null);
  };

  const scanMarket = async () => {
    setScanning(true);
    const res = await fetch(`${API_BASE}/scan/market/top`);
    const data = await res.json();
    setSignals(data.signals || []);
    setScanning(false);
    fetchSignalHistory();
  };

  const getAiAnalysis = async (symbol: string) => {
    setAiLoading(true);
    setAiAnalysis("");
    const res = await fetch(`${API_BASE}/scan/${symbol}/ai`);
    const data = await res.json();
    setAiAnalysis(data.ai_analysis || "No analysis available");
    setAiLoading(false);
  };

  const buyStock = async (signal: any) => {
    const res = await fetch(`${API_BASE}/trade/buy`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        symbol: signal.symbol,
        price: signal.price,
        quantity: 10,
        target: signal.target,
        stop_loss: signal.stop_loss,
      }),
    });
    const data = await res.json();
    alert(data.message || data.error);
    fetchPortfolio();
  };

  useEffect(() => {
  Promise.all([
    fetchMarketContext(), 
    fetchAgentLogs(),
    fetchPortfolio(), 
    fetchSignalHistory(), 
    fetchRegime(), 
    fetchStrategies(),
    fetchAiStrategies(),
    fetchMorningBriefing(),
    fetchGlobalMarkets(),
    fetchFleetStatus()
  ]);
  const interval = setInterval(fetchMarketContext, 60000);
  return () => clearInterval(interval);
}, []);

  const getMoodColor = (mood: string) => {
    if (mood === "BULLISH") return "text-green-400";
    if (mood === "BEARISH") return "text-red-400";
    return "text-yellow-400";
  };

  const getSignalColor = (signal: string) => {
    if (signal === "STRONG BUY") return "bg-green-500 text-black";
    if (signal === "BUY") return "bg-green-400 text-black";
    if (signal === "WEAK BUY") return "bg-yellow-400 text-black";
    return "bg-red-400 text-black";
  };

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">

      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-white">
            🤖 AI Trading System
          </h1>
          <p className="text-gray-400 text-sm mt-1">
            NSE/BSE Adaptive Market Scanner — Paper Trading Mode
          </p>
        </div>
        <button
  onClick={() => { 
    fetchMarketContext(); 
    fetchPortfolio(); 
    fetchFleetStatus(); 
    fetchAgentLogs(); 
  }}
  className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm"
>
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      {/* Market Context */}
      {marketContext && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">NIFTY 50</p>
            <p className="text-2xl font-bold">{marketContext.nifty?.price?.toLocaleString()}</p>
            <p className={`text-sm ${marketContext.nifty?.change_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
              {marketContext.nifty?.change_pct >= 0 ? "▲" : "▼"} {Math.abs(marketContext.nifty?.change_pct)}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">BANKNIFTY</p>
            <p className="text-2xl font-bold">{marketContext.banknifty?.price?.toLocaleString()}</p>
            <p className={`text-sm ${marketContext.banknifty?.change_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
              {marketContext.banknifty?.change_pct >= 0 ? "▲" : "▼"} {Math.abs(marketContext.banknifty?.change_pct)}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">INDIA VIX</p>
            <p className="text-2xl font-bold">{marketContext.india_vix}</p>
            <p className={`text-sm ${marketContext.volatility === "HIGH" ? "text-red-400" : marketContext.volatility === "MEDIUM" ? "text-yellow-400" : "text-green-400"}`}>
              {marketContext.volatility}
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">MARKET MOOD</p>
            <p className={`text-2xl font-bold ${getMoodColor(marketContext.market_mood)}`}>
              {marketContext.market_mood}
            </p>
            <p className="text-gray-500 text-xs">{marketContext.timestamp}</p>
          </div>
        </div>
      )}

      {/* Portfolio Summary */}
      {portfolio && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">CASH</p>
            <p className="text-xl font-bold text-green-400">₹{portfolio.cash?.toLocaleString()}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">INVESTED</p>
            <p className="text-xl font-bold">₹{portfolio.total_invested?.toLocaleString()}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">CURRENT VALUE</p>
            <p className="text-xl font-bold">₹{portfolio.total_current_value?.toLocaleString()}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-4 border border-gray-800">
            <p className="text-gray-400 text-xs mb-1">OVERALL P&L</p>
            <p className={`text-xl font-bold ${portfolio.overall_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ₹{portfolio.overall_pnl?.toLocaleString()}
            </p>
          </div>
        </div>
      )}
            {/* Agent Control Tab */}
      {activeTab === "agent-control" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <Shield size={20} className="text-blue-400" />
            Agent Control Panel
          </h2>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <button
              onClick={async () => {
                await fetch(`${API_BASE}/control/pause`, { method: "POST" });
                alert("Agent paused");
              }}
              className="bg-yellow-600 hover:bg-yellow-500 px-4 py-3 rounded-lg text-sm font-medium"
            >
              ⏸️ Pause Agent
            </button>
            <button
              onClick={async () => {
                await fetch(`${API_BASE}/control/resume`, { method: "POST" });
                alert("Agent resumed");
              }}
              className="bg-green-600 hover:bg-green-500 px-4 py-3 rounded-lg text-sm font-medium"
            >
              ▶️ Resume Agent
            </button>
            <button
              onClick={async () => {
                await fetch(`${API_BASE}/control/stop`, { method: "POST" });
                alert("Agent stopped");
              }}
              className="bg-red-600 hover:bg-red-500 px-4 py-3 rounded-lg text-sm font-medium"
            >
              🛑 Stop Agent
            </button>
            <button
              onClick={async () => {
                const symbol = prompt("Enter stock symbol to blacklist:");
                if (symbol) {
                  await fetch(`${API_BASE}/control/blacklist/${symbol}`, { method: "POST" });
                  alert(`${symbol} blacklisted`);
                }
              }}
              className="bg-gray-700 hover:bg-gray-600 px-4 py-3 rounded-lg text-sm font-medium"
            >
              ⛔ Blacklist Stock
            </button>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs mb-2">RISK MODE</p>
              <select
                onChange={async (e) => {
                  await fetch(`${API_BASE}/control/risk/${e.target.value}`, { method: "POST" });
                  alert(`Risk mode changed to ${e.target.value}`);
                }}
                className="bg-gray-700 text-white px-3 py-2 rounded-lg text-sm w-full"
              >
                <option value="CONSERVATIVE">Conservative</option>
                <option value="MODERATE" selected>Moderate</option>
                <option value="AGGRESSIVE">Aggressive</option>
              </select>
            </div>
            <div className="bg-gray-800 rounded-xl p-4">
              <p className="text-gray-400 text-xs mb-2">FORCE BUY</p>
              <button
                onClick={async () => {
                  const symbol = prompt("Enter stock symbol:");
                  const price = prompt("Enter price:");
                  if (symbol && price) {
                    await fetch(`${API_BASE}/control/force-buy?symbol=${symbol}&price=${price}`, { method: "POST" });
                    alert(`Force buy ${symbol} at ₹${price}`);
                  }
                }}
                className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-lg text-sm w-full"
              >
                💪 Force Buy
              </button>
            </div>
          </div>
        </div>
      )}

            {/* Market Intelligence Tab */}
      {activeTab === "market-intel" && (
        <div className="space-y-6">
          {/* Morning Briefing */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <TrendingUp size={20} className="text-blue-400" />
                Morning Briefing
              </h2>
              <button
                onClick={async () => {
                  const res = await fetch(`${API_BASE}/market-intel/briefing`);
                  const data = await res.json();
                  setMorningBriefing(data);
                }}
                className="flex items-center gap-2 bg-blue-700 hover:bg-blue-600 px-4 py-2 rounded-lg text-sm"
              >
                <RefreshCw size={14} />
                Refresh
              </button>
            </div>

            {morningBriefing ? (
              <div className="space-y-4">
                {/* Recommendation */}
                <div className={`rounded-lg p-4 ${
                  morningBriefing.recommendation?.includes("BULLISH") ? "bg-green-900/30 border border-green-800" :
                  morningBriefing.recommendation?.includes("BEARISH") ? "bg-red-900/30 border border-red-800" :
                  "bg-yellow-900/30 border border-yellow-800"
                }`}>
                  <p className="text-xs text-gray-400 mb-1">TRADING RECOMMENDATION</p>
                  <p className="text-lg font-bold">{morningBriefing.recommendation}</p>
                </div>

                {/* AI Summary */}
                <div className="bg-gray-800 rounded-lg p-4">
                  <p className="text-xs text-gray-400 mb-2">AI MARKET SUMMARY</p>
                  <p className="text-sm text-gray-300 leading-relaxed">{morningBriefing.ai_summary}</p>
                </div>

                {/* Pre-market */}
                {morningBriefing.pre_market && (
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-xs text-gray-400">SGX NIFTY</p>
                      <p className="text-xl font-bold">₹{morningBriefing.pre_market.sgx_nifty}</p>
                      <p className={`text-sm ${
                        morningBriefing.pre_market.gap_pct >= 0 ? "text-green-400" : "text-red-400"
                      }`}>
                        Gap: {morningBriefing.pre_market.gap_pct}%
                      </p>
                    </div>
                    <div className="bg-gray-800 rounded-lg p-4">
                      <p className="text-xs text-gray-400">EXPECTED OPEN</p>
                      <p className={`text-xl font-bold ${
                        morningBriefing.pre_market.expected_open === "BULLISH" ? "text-green-400" :
                        morningBriefing.pre_market.expected_open === "BEARISH" ? "text-red-400" : "text-yellow-400"
                      }`}>
                        {morningBriefing.pre_market.expected_open}
                      </p>
                    </div>
                  </div>
                )}

                {/* News Analysis */}
                {morningBriefing.news_analysis && (
                  <div className="bg-gray-800 rounded-lg p-4">
                    <p className="text-xs text-gray-400 mb-2">NEWS IMPACT</p>
                    <div className="flex items-center gap-4 mb-2">
                      <span className={`text-sm font-bold ${
                        morningBriefing.news_analysis.sentiment === "BULLISH" ? "text-green-400" :
                        morningBriefing.news_analysis.sentiment === "BEARISH" ? "text-red-400" : "text-yellow-400"
                      }`}>
                        {morningBriefing.news_analysis.sentiment}
                      </span>
                      <span className="text-sm text-gray-400">Impact: {morningBriefing.news_analysis.impact}</span>
                    </div>
                    <p className="text-sm text-gray-300">{morningBriefing.news_analysis.summary}</p>
                    {morningBriefing.news_analysis.affected_sectors?.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {morningBriefing.news_analysis.affected_sectors.map((sector: string, i: number) => (
                          <span key={i} className="text-xs bg-gray-700 px-2 py-1 rounded-full">{sector}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <TrendingUp size={40} className="mx-auto mb-3 opacity-30" />
                <p>Click Refresh to load morning briefing</p>
              </div>
            )}
          </div>

          {/* Global Markets */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
              🌍 Global Markets
            </h2>
            {globalMarkets && Object.keys(globalMarkets).length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(globalMarkets).map(([name, data]: [string, any]) => (
                  <div key={name} className="bg-gray-800 rounded-lg p-3">
                    <p className="text-xs text-gray-400">{name}</p>
                    <p className="text-sm font-bold">{data.price?.toLocaleString()}</p>
                    <p className={`text-xs ${data.change_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
                      {data.change_pct >= 0 ? "▲" : "▼"} {Math.abs(data.change_pct)}%
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                <p>Loading global markets...</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { id: "scanner", label: "Scanner", icon: <Activity size={16} /> },
          { id: "history", label: "Signal History", icon: <History size={16} /> },
          { id: "positions", label: "Positions", icon: <DollarSign size={16} /> },
          { id: "analysis", label: "AI Analysis", icon: <AlertCircle size={16} /> },
          { id: "regime", label: "Market Regime", icon: <BarChart2 size={16} /> },
          { id: "autonomous", label: "Autonomous AI Scan", icon: <TrendingUp size={16} /> },
          { id: "ai-strategies", label: "AI Strategy Lab", icon: <RefreshCw size={16} /> },
          { id: "performance", label: "Performance", icon: <BookOpen size={16} /> },
          { id: "monitor", label: "Auto Monitor", icon: <Shield size={16} /> },
          { id: "market-intel", label: "Market Intel", icon: <TrendingUp size={16} /> },
          { id: "agent-control", label: "Agent Control", icon: <Shield size={16} /> },
            { id: "agent-fleet", label: "Agent Fleet", icon: <Shield size={16} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => {
              setActiveTab(tab.id);
              if (tab.id === "autonomous" && !autonomousScan) fetchAutonomousScan();
              if (tab.id === "performance") fetchPerformanceAnalysis();
              if (tab.id === "monitor") monitorPositions();
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Scanner Tab */}
      {activeTab === "scanner" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <Activity size={20} className="text-blue-400" />
              Market Scanner
            </h2>
            <button
              onClick={scanMarket}
              disabled={scanning}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium"
            >
              {scanning ? (
                <><RefreshCw size={16} className="animate-spin" /> Scanning...</>
              ) : (
                <><Activity size={16} /> Scan Market</>
              )}
            </button>
          </div>

          {signals.length === 0 && !scanning && (
            <div className="text-center py-12 text-gray-500">
              <Activity size={40} className="mx-auto mb-3 opacity-30" />
              <p>Click Scan Market to find trading opportunities</p>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {signals.map((signal, i) => (
              <div key={i} className="bg-gray-800 rounded-xl p-4 border border-gray-700 hover:border-blue-500 transition-all">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-bold text-lg">{signal.symbol}</h3>
                  <span className={`${getSignalColor(signal.signal)} text-xs font-bold px-2 py-1 rounded-full`}>
                    {signal.signal}
                  </span>
                </div>
                <div className="grid grid-cols-3 gap-2 text-sm mb-3">
                  <div>
                    <p className="text-gray-400 text-xs">Price</p>
                    <p className="font-medium">₹{signal.price}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Target</p>
                    <p className="font-medium text-green-400">₹{signal.target}</p>
                  </div>
                  <div>
                    <p className="text-gray-400 text-xs">Stop Loss</p>
                    <p className="font-medium text-red-400">₹{signal.stop_loss}</p>
                  </div>
                </div>
                <div className="mb-3">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="bg-gray-700 rounded-full h-2 flex-1">
                      <div className="bg-blue-500 h-2 rounded-full" style={{ width: `${Math.min(signal.score, 100)}%` }} />
                    </div>
                    <span className="text-xs text-gray-400">{signal.score}/100</span>
                  </div>
                </div>
                <div className="text-xs text-gray-400 mb-3">
                  {signal.reasons?.slice(0, 2).map((r: string, j: number) => (
                    <p key={j}>• {r}</p>
                  ))}
                </div>
                {/* SMC + Timeframe badges */}
                <div className="flex flex-wrap gap-1 mb-3">
                  {signal.smc_analysis?.near_order_block && (
                    <span className="text-xs bg-purple-900 text-purple-300 px-2 py-0.5 rounded-full">📦 Order Block</span>
                  )}
                  {signal.smc_analysis?.near_fvg && (
                    <span className="text-xs bg-blue-900 text-blue-300 px-2 py-0.5 rounded-full">⚡ FVG Zone</span>
                  )}
                  {signal.smc_analysis?.zone && (
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      signal.smc_analysis.zone === "DISCOUNT" ? "bg-green-900 text-green-300" :
                      signal.smc_analysis.zone === "PREMIUM" ? "bg-red-900 text-red-300" :
                      "bg-gray-700 text-gray-300"
                    }`}>{signal.smc_analysis.zone}</span>
                  )}
                  {signal.strategy_used && (
                    <span className="text-xs bg-yellow-900 text-yellow-300 px-2 py-0.5 rounded-full">
                      🎯 {signal.strategy_used} {signal.strategy_win_rate ? `(${signal.strategy_win_rate}% WR)` : ""}
                    </span>
                  )}
                </div>
                {/* Timeframe alignment */}
                {signal.timeframe_analysis && (
                  <div className="flex gap-1 mb-3">
                    {Object.entries(signal.timeframe_analysis).map(([tf, analysis]: [string, any]) => (
                      analysis && (
                        <span key={tf} className={`text-xs px-2 py-0.5 rounded ${
                          analysis.trend === "BULLISH" ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"
                        }`}>{tf}</span>
                      )
                    ))}
                  </div>
                )}
                {/* Fundamental score */}
                {signal.fundamental_score && (
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs text-gray-400">Fundamentals:</span>
                    <div className="bg-gray-700 rounded-full h-1.5 flex-1">
                      <div className={`h-1.5 rounded-full ${
                        signal.fundamental_score >= 70 ? "bg-green-500" :
                        signal.fundamental_score >= 50 ? "bg-yellow-500" : "bg-red-500"
                      }`} style={{ width: `${signal.fundamental_score}%` }} />
                    </div>
                    <span className="text-xs text-white">{signal.fundamental_score}/100</span>
                  </div>
                )}
                {/* Red flags */}
                {signal.red_flags?.length > 0 && (
                  <div className="mb-3">
                    {signal.red_flags.map((flag: string, fi: number) => (
                      <p key={fi} className="text-xs text-red-400">🚩 {flag}</p>
                    ))}
                  </div>
                )}
                <div className="flex gap-2">
                  <button
                    onClick={() => { setSelectedSignal(signal); setActiveTab("analysis"); getAiAnalysis(signal.symbol); }}
                    className="flex-1 text-xs bg-purple-700 hover:bg-purple-600 px-2 py-2 rounded-lg"
                  >
                    🤖 AI Analysis
                  </button>
                  <button
                    onClick={() => { setSelectedSignal(signal); fetchStockResearch(signal.symbol); setActiveTab("analysis"); }}
                    className="flex-1 text-xs bg-blue-800 hover:bg-blue-700 px-2 py-2 rounded-lg"
                  >
                    🔬 Research
                  </button>
                  <button
                    onClick={() => buyStock(signal)}
                    className="flex-1 text-xs bg-green-700 hover:bg-green-600 px-2 py-2 rounded-lg"
                  >
                    📈 Paper Buy
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Signal History Tab */}
      {activeTab === "history" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold flex items-center gap-2">
              <History size={20} className="text-yellow-400" />
              Signal History
            </h2>
            <button onClick={fetchSignalHistory} className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-3 py-2 rounded-lg text-sm">
              <RefreshCw size={14} /> Refresh
            </button>
          </div>

          {signalHistory.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <History size={40} className="mx-auto mb-3 opacity-30" />
              <p>No signals saved yet. Run a market scan first.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-800">
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-left py-2">Signal</th>
                    <th className="text-right py-2">Price</th>
                    <th className="text-right py-2">Target</th>
                    <th className="text-right py-2">SL</th>
                    <th className="text-right py-2">Score</th>
                    <th className="text-left py-2">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {signalHistory.map((s: any, i: number) => (
                    <tr key={i} className="border-b border-gray-800 hover:bg-gray-800">
                      <td className="py-3 font-bold">{s.symbol}</td>
                      <td className="py-3">
                        <span className={`${getSignalColor(s.signal_type)} text-xs px-2 py-1 rounded-full`}>
                          {s.signal_type}
                        </span>
                      </td>
                      <td className="text-right">₹{s.price}</td>
                      <td className="text-right text-green-400">₹{s.target}</td>
                      <td className="text-right text-red-400">₹{s.stop_loss}</td>
                      <td className="text-right">{s.score}</td>
                      <td className="text-left text-gray-400 text-xs">
                        {new Date(s.created_at).toLocaleString("en-IN")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Positions Tab */}
      {activeTab === "positions" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <DollarSign size={20} className="text-green-400" />
            Open Positions
          </h2>
          {!portfolio?.positions?.length ? (
            <div className="text-center py-12 text-gray-500">
              <DollarSign size={40} className="mx-auto mb-3 opacity-30" />
              <p>No open positions. Paper buy a stock from the scanner.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-400 border-b border-gray-800">
                    <th className="text-left py-2">Symbol</th>
                    <th className="text-right py-2">Buy Price</th>
                    <th className="text-right py-2">Current</th>
                    <th className="text-right py-2">Qty</th>
                    <th className="text-right py-2">P&L</th>
                    <th className="text-right py-2">Target</th>
                    <th className="text-right py-2">SL</th>
                  </tr>
                </thead>
                <tbody>
                  {portfolio.positions.map((pos: any, i: number) => (
                    <tr key={i} className="border-b border-gray-800 hover:bg-gray-800">
                      <td className="py-3 font-bold">{pos.symbol}</td>
                      <td className="text-right">₹{pos.buy_price}</td>
                      <td className="text-right">₹{pos.current_price}</td>
                      <td className="text-right">{pos.quantity}</td>
                      <td className={`text-right font-medium ${pos.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                        ₹{pos.pnl} ({pos.pnl_pct}%)
                      </td>
                      <td className="text-right text-green-400">₹{pos.target}</td>
                      <td className="text-right text-red-400">₹{pos.stop_loss}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Market Regime Tab */}
      {activeTab === "regime" && (
        <div className="space-y-6">
          {regime && (
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                <BarChart2 size={20} className="text-blue-400" />
                Market Regime Detection
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-gray-800 rounded-xl p-4">
                  <p className="text-gray-400 text-xs mb-1">REGIME</p>
                  <p className={`text-lg font-bold ${
                    regime.regime === "TRENDING_BULLISH" ? "text-green-400" :
                    regime.regime === "TRENDING_BEARISH" ? "text-red-400" :
                    regime.regime === "VOLATILE" ? "text-orange-400" :
                    "text-yellow-400"
                  }`}>
                    {regime.regime}
                  </p>
                </div>
                <div className="bg-gray-800 rounded-xl p-4">
                  <p className="text-gray-400 text-xs mb-1">CONFIDENCE</p>
                  <p className="text-lg font-bold">{regime.confidence}%</p>
                </div>
                <div className="bg-gray-800 rounded-xl p-4">
                  <p className="text-gray-400 text-xs mb-1">ADX</p>
                  <p className="text-lg font-bold">{regime.adx}</p>
                </div>
                <div className="bg-gray-800 rounded-xl p-4">
                  <p className="text-gray-400 text-xs mb-1">VOLATILITY</p>
                  <p className="text-lg font-bold">{regime.volatility_pct}%</p>
                </div>
              </div>
              <div className="bg-gray-800 rounded-xl p-4 mb-4">
                <p className="text-gray-400 text-xs mb-2">DESCRIPTION</p>
                <p className="text-white">{regime.description}</p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-green-900 bg-opacity-30 rounded-xl p-4 border border-green-800">
                  <p className="text-green-400 text-xs font-bold mb-2">✅ ACTIVE STRATEGIES</p>
                  {regime.active_strategies?.map((s: string, i: number) => (
                    <p key={i} className="text-white text-sm">• {s}</p>
                  ))}
                </div>
                <div className="bg-red-900 bg-opacity-30 rounded-xl p-4 border border-red-800">
                  <p className="text-red-400 text-xs font-bold mb-2">❌ AVOID STRATEGIES</p>
                  {regime.avoid_strategies?.map((s: string, i: number) => (
                    <p key={i} className="text-white text-sm">• {s}</p>
                  ))}
                </div>
              </div>
            </div>
          )}

                    {/* Strategy Performance */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <TrendingUp size={20} className="text-green-400" />
                Strategy Performance (1 Year Backtest)
              </h2>
              <button
                onClick={async () => {
                  setBacktestRunning(true);
                  setBacktestProgress(0);
                  setBacktestStatus("Starting...");
                  
                  const interval = await pollBacktestProgress();
                  
                  try {
                    const res = await fetch(`${API_BASE}/backtest/run-all`, {
                      signal: AbortSignal.timeout(3600000)
                    });
                    const data = await res.json();
                    clearInterval(interval);
                    alert(`Backtest complete! ${data.total_stocks} stocks analyzed.`);
                    fetchStrategies();
                  } catch (err) {
                    clearInterval(interval);
                    setBacktestRunning(false);
                    alert("Backtest failed");
                  }
                }}
                disabled={backtestRunning}
                className="bg-purple-600 hover:bg-purple-500 disabled:bg-gray-600 px-4 py-2 rounded-lg text-sm"
              >
                {backtestRunning ? "⏳ Running..." : "🔄 Run Backtest on All Stocks"}
              </button>
            </div>

            {backtestRunning && (
              <div className="mb-4 p-4 bg-gray-800 rounded-lg">
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-purple-400">{backtestProgress}%</span>
                </div>
                <div className="bg-gray-700 rounded-full h-3 w-full">
                  <div 
                    className="bg-purple-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${backtestProgress}%` }}
                  />
                </div>
                <div className="flex justify-between text-xs text-gray-400 mt-2">
                  <span>Current: {currentStock || "Starting..."}</span>
                  <span>{backtestStatus}</span>
                </div>
              </div>
            )}

                        {strategies.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <p>No backtest data yet. Run a backtest first.</p>
                <button
                  onClick={async () => {
                    await fetch(`${API_BASE}/backtest/run`, { signal: AbortSignal.timeout(180000) });
                    fetchStrategies();
                  }}
                  className="mt-4 bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg text-sm text-white"
                >
                  Run Backtest
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {strategies.map((s: any, i: number) => (
                  <div key={i} className="bg-gray-800 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <p className="font-bold">{s.strategy_name}</p>
                        <p className="text-gray-400 text-xs">
                          Win Rate: {s.win_rate}% | Sharpe: {s.sharpe_ratio}
                        </p>
                        {s.best_stock && (
                          <p className="text-green-400 text-xs mt-1">
                            🏆 Best on: {s.best_stock} ({s.best_win_rate}% win rate)
                          </p>
                        )}
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right">
                          <p className="text-xs text-gray-400">Score</p>
                          <p className="font-bold text-lg">{s.score}</p>
                        </div>
                        <div className="bg-gray-700 rounded-full h-2 w-24">
                          <div
                            className={`h-2 rounded-full ${s.is_active ? "bg-green-500" : "bg-red-500"}`}
                            style={{ width: `${Math.min(s.score, 100)}%` }}
                          />
                        </div>
                        <span className={`text-xs font-bold px-2 py-1 rounded-full ${s.is_active ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"}`}>
                          {s.is_active ? "ACTIVE" : "INACTIVE"}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* AI Analysis Tab */}
      {activeTab === "analysis" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-purple-800">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <AlertCircle size={20} className="text-purple-400" />
            AI Analysis {selectedSignal && `— ${selectedSignal.symbol}`}
          </h2>

          {/* Integrated Sentiment Verification Component Context Block */}
          {selectedSignal && (
            <div className="mb-6 bg-gray-950 p-4 rounded-xl border border-gray-800">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-purple-400">News Sentiment Submodule</span>
                <button
                  onClick={() => fetchStockSentiment(selectedSignal.symbol)}
                  disabled={loadingSentiment === selectedSignal.symbol}
                  className="bg-gray-800 hover:bg-gray-700 disabled:bg-gray-900 text-xs px-3 py-1.5 rounded-lg font-medium flex items-center gap-2 transition-all"
                >
                  {loadingSentiment === selectedSignal.symbol ? <RefreshCw size={12} className="animate-spin" /> : "📰"}
                  {loadingSentiment === selectedSignal.symbol ? "Extracting..." : "Scan Financial News"}
                </button>
              </div>
              
              {sentimentCache[selectedSignal.symbol] ? (
                <div className="grid grid-cols-2 gap-4 mt-3 pt-3 border-t border-gray-900">
                  <div>
                    <p className="text-gray-500 text-[10px] uppercase">Sentiment Mood</p>
                    <p className={`font-bold text-sm ${
                      sentimentCache[selectedSignal.symbol]?.sentiment?.sentiment === 'BULLISH' ? 'text-green-400' : 
                      sentimentCache[selectedSignal.symbol]?.sentiment?.sentiment === 'BEARISH' ? 'text-red-400' : 'text-yellow-400'
                    }`}>
                      {sentimentCache[selectedSignal.symbol]?.sentiment?.sentiment || "NEUTRAL"}
                    </p>
                  </div>
                  <div>
                    <p className="text-gray-500 text-[10px] uppercase">Sentiment Score</p>
                    <p className="font-bold text-sm text-white">{sentimentCache[selectedSignal.symbol]?.sentiment?.score || "50"}/100</p>
                  </div>
                  <div className="col-span-2 bg-gray-900/40 p-2.5 rounded border border-gray-900 text-xs text-gray-300 leading-relaxed italic">
                    {sentimentCache[selectedSignal.symbol]?.sentiment?.summary || "No clear sentiment summary available."}
                  </div>
                </div>
              ) : (
                <p className="text-gray-500 text-xs italic mt-1">No historical news sequence analyzed for this symbol today. Click Scan to run.</p>
              )}
            </div>
          )}

          {/* Research Panel */}
          {loadingResearch && (
            <div className="flex items-center gap-3 text-gray-400 py-4 mb-4">
              <RefreshCw size={16} className="animate-spin" />
              Running deep stock research...
            </div>
          )}
          {researchData && !loadingResearch && (
            <div className="mb-6 bg-gray-950 rounded-xl p-4 border border-blue-900">
              <p className="text-blue-400 text-xs font-bold uppercase tracking-wider mb-3">🔬 Deep Research — {researchData.symbol}</p>
              <div className="grid grid-cols-2 gap-3 mb-3">
                <div>
                  <p className="text-gray-500 text-xs">Analyst Rating</p>
                  <p className={`font-bold text-sm ${
                    researchData.analyst_rating?.includes("BUY") ? "text-green-400" :
                    researchData.analyst_rating?.includes("SELL") ? "text-red-400" : "text-yellow-400"
                  }`}>{researchData.analyst_rating}</p>
                </div>
                <div>
                  <p className="text-gray-500 text-xs">Price Outlook</p>
                  <p className="font-bold text-sm text-white capitalize">{researchData.price_outlook}</p>
                </div>
              </div>
              <div className="bg-gray-900 rounded-lg p-3 mb-3">
                <p className="text-gray-400 text-xs mb-1">Investment Thesis</p>
                <p className="text-gray-200 text-xs leading-relaxed">{researchData.investment_thesis}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <p className="text-green-400 text-xs font-bold mb-1">Key Catalysts</p>
                  {researchData.key_catalysts?.map((c: string, i: number) => (
                    <p key={i} className="text-xs text-gray-300">• {c}</p>
                  ))}
                </div>
                <div>
                  <p className="text-red-400 text-xs font-bold mb-1">Key Risks</p>
                  {researchData.key_risks?.map((r: string, i: number) => (
                    <p key={i} className="text-xs text-gray-300">• {r}</p>
                  ))}
                </div>
              </div>
              <div className="mt-3 bg-purple-950/30 rounded-lg p-3 border border-purple-900">
                <p className="text-purple-400 text-xs font-bold mb-1">Institutional View</p>
                <p className="text-gray-300 text-xs">{researchData.institutional_view}</p>
              </div>
            </div>
          )}

          {aiLoading ? (
            <div className="flex items-center gap-3 text-gray-400 py-8">
              <RefreshCw size={16} className="animate-spin" />
              AI is analyzing the signal...
            </div>
          ) : aiAnalysis ? (
            <div className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
              {aiAnalysis}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <AlertCircle size={40} className="mx-auto mb-3 opacity-30" />
              <p>Click AI Analysis on any signal from the Scanner tab</p>
            </div>
          )}
        </div>
      )}

      {/* Autonomous AI Scan Tab Add-on */}
      {activeTab === "autonomous" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                🤖 Autonomous Market Intelligence
              </h2>
              <p className="text-gray-400 text-xs mt-1">Cross-sector macro regime evaluation and allocation directives</p>
            </div>
            <button
              onClick={fetchAutonomousScan}
              disabled={scanningAutonomous}
              className="bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all"
            >
              {scanningAutonomous ? <RefreshCw size={14} className="animate-spin" /> : <TrendingUp size={14} />}
              {scanningAutonomous ? "Scanning Models..." : "Execute Market Scan"}
            </button>
          </div>

          {scanningAutonomous ? (
            <div className="text-center py-12 text-gray-500 animate-pulse">
              <RefreshCw size={32} className="animate-spin mx-auto mb-3 text-blue-500" />
              <p>LLM agents are auditing indices, sector volume weights, and market structure alignments...</p>
            </div>
          ) : autonomousScan ? (
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-blue-400 text-xs font-bold uppercase tracking-wider mb-2">Market Outlook Summary</p>
                <p className="text-sm text-gray-200 leading-relaxed">{autonomousScan.market_summary || "Market regime processing complete."}</p>
              </div>
              <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                <p className="text-purple-400 text-xs font-bold uppercase tracking-wider mb-2">Strategic Tactical Plan</p>
                <p className="text-sm text-gray-200 leading-relaxed">{autonomousScan.trading_plan || "No distinct plan metrics returned."}</p>
              </div>
              {autonomousScan.best_sectors && (
                <div className="bg-gray-800 rounded-xl p-4 border border-gray-700">
                  <p className="text-green-400 text-xs font-bold uppercase tracking-wider mb-2">Outperforming Target Sectors</p>
                  <div className="flex flex-wrap gap-2">
                    {Array.isArray(autonomousScan.best_sectors) ? (
                      autonomousScan.best_sectors.map((sector: string, idx: number) => (
                        <span key={idx} className="bg-green-950/40 text-green-400 border border-green-900/60 text-xs px-2.5 py-1 rounded-md font-medium">
                          {sector}
                        </span>
                      ))
                    ) : (
                      <span className="text-sm text-white">{autonomousScan.best_sectors}</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <p>No active scan cached. Click Execute Market Scan above to extract agent research data.</p>
            </div>
          )}
        </div>
      )}

      {/* AI Strategy Lab Tab Add-on */}
      {activeTab === "ai-strategies" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                🏆 AI Strategy Generation Lab
              </h2>
              <p className="text-gray-400 text-xs mt-1">Algorithmic alphas generated, backtested, and verified by LLM reasoning architectures</p>
            </div>
            <button
              onClick={generateNewAiStrategies}
              disabled={generatingStrategies}
              className="bg-purple-700 hover:bg-purple-600 disabled:bg-gray-800 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2 transition-all"
            >
              {generatingStrategies ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              {generatingStrategies ? "Evaluating Optimization Vectors..." : "Run Optimization Cycle"}
            </button>
          </div>

          {generatingStrategies ? (
            <div className="text-center py-12 text-gray-500 animate-pulse">
              <RefreshCw size={32} className="animate-spin mx-auto mb-3 text-purple-500" />
              <p>Testing novel SMC Liquidity Sweeps, multi-timeframe FVGs, and Volume Profile Reversals...</p>
            </div>
          ) : aiStrategies.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <p>No active LLM generated strategy variants loaded. Click Run Optimization Cycle above to prompt the generator.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {aiStrategies.map((strat: any, idx: number) => {
                const winRateNum = parseFloat(strat.win_rate);
                const isKeeper = strat.status === "KEEPER" || (!strat.status && winRateNum >= 50.0);
                
                return (
                  <div key={idx} className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <h3 className="font-bold text-base text-purple-400">{strat.strategy_name || strat.name || "Custom Strategy Proposal"}</h3>
                        <p className="text-xs text-gray-400 mt-0.5">
                          Win Rate: <span className="text-white font-semibold">{strat.win_rate}%</span> | Fitness Score: <span className="text-white font-semibold">{strat.score || "N/A"}</span>
                        </p>
                      </div>
                      <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${
                        isKeeper 
                          ? 'bg-green-950/60 text-green-400 border-green-800/80' 
                          : 'bg-red-950/60 text-red-400 border-red-900/80'
                      }`}>
                        {strat.status || (isKeeper ? "KEEPER" : "DISCARDED")}
                      </span>
                    </div>
                    
                    {/* Setup Trigger Conditions Mapping Block */}
                    {(strat.entry_conditions || strat.entry) && (
                      <div className="text-xs text-gray-300 space-y-1 bg-gray-950/40 p-3 rounded-lg border border-gray-900">
                        <p className="text-gray-400 font-medium mb-1">Execution Rule Triggers:</p>
                        {Array.isArray(strat.entry_conditions || strat.entry) ? (
                          (strat.entry_conditions || strat.entry).map((cond: string, cIdx: number) => (
                            <p key={cIdx} className="pl-2 text-gray-400">• <span className="text-gray-200">{cond}</span></p>
                          ))
                        ) : (
                          <p className="pl-2 text-gray-200">{strat.entry_conditions || strat.entry}</p>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
      {/* Performance Analysis Tab */}
      {activeTab === "performance" && (
        <div className="space-y-6">
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BookOpen size={20} className="text-yellow-400" />
                Trading Performance Analysis
              </h2>
              <button
                onClick={fetchPerformanceAnalysis}
                disabled={loadingPerformance}
                className="flex items-center gap-2 bg-yellow-700 hover:bg-yellow-600 disabled:bg-gray-700 px-4 py-2 rounded-lg text-sm"
              >
                {loadingPerformance ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
                Refresh Analysis
              </button>
            </div>

            {loadingPerformance ? (
              <div className="text-center py-12 text-gray-500">
                <RefreshCw size={32} className="animate-spin mx-auto mb-3 text-yellow-500" />
                <p>AI analyzing your trading performance...</p>
              </div>
            ) : performanceAnalysis?.message ? (
              <div className="text-center py-12 text-gray-500">
                <BookOpen size={40} className="mx-auto mb-3 opacity-30" />
                <p>{performanceAnalysis.message}</p>
                <p className="text-xs mt-2">Complete some paper trades first then come back.</p>
              </div>
            ) : performanceAnalysis ? (
              <div className="space-y-4">
                {/* Grade + Stats */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="bg-gray-800 rounded-xl p-4 col-span-1 flex flex-col items-center justify-center">
                    <p className="text-gray-400 text-xs mb-1">GRADE</p>
                    <p className={`text-4xl font-bold ${
                      performanceAnalysis.performance_grade === "A" ? "text-green-400" :
                      performanceAnalysis.performance_grade === "B" ? "text-blue-400" :
                      performanceAnalysis.performance_grade === "C" ? "text-yellow-400" : "text-red-400"
                    }`}>{performanceAnalysis.performance_grade}</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4">
                    <p className="text-gray-400 text-xs">Total Trades</p>
                    <p className="text-xl font-bold">{performanceAnalysis.stats?.total_trades}</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4">
                    <p className="text-gray-400 text-xs">Win Rate</p>
                    <p className="text-xl font-bold text-green-400">{performanceAnalysis.stats?.win_rate}%</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4">
                    <p className="text-gray-400 text-xs">Total P&L</p>
                    <p className={`text-xl font-bold ${performanceAnalysis.stats?.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      ₹{performanceAnalysis.stats?.total_pnl}
                    </p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4">
                    <p className="text-gray-400 text-xs">Risk Score</p>
                    <p className="text-xl font-bold">{performanceAnalysis.risk_management_score}/10</p>
                  </div>
                </div>

                <div className="bg-gray-800 rounded-xl p-4">
                  <p className="text-gray-400 text-xs mb-2">OVERALL ASSESSMENT</p>
                  <p className="text-white text-sm leading-relaxed">{performanceAnalysis.overall_assessment}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-green-900 bg-opacity-20 rounded-xl p-4 border border-green-900">
                    <p className="text-green-400 text-xs font-bold mb-2">✅ STRENGTHS</p>
                    {performanceAnalysis.strengths?.map((s: string, i: number) => (
                      <p key={i} className="text-sm text-gray-300 mb-1">• {s}</p>
                    ))}
                  </div>
                  <div className="bg-red-900 bg-opacity-20 rounded-xl p-4 border border-red-900">
                    <p className="text-red-400 text-xs font-bold mb-2">⚠️ WEAKNESSES</p>
                    {performanceAnalysis.weaknesses?.map((w: string, i: number) => (
                      <p key={i} className="text-sm text-gray-300 mb-1">• {w}</p>
                    ))}
                  </div>
                </div>

                <div className="bg-blue-900 bg-opacity-20 rounded-xl p-4 border border-blue-900">
                  <p className="text-blue-400 text-xs font-bold mb-2">🎯 TOP RECOMMENDATIONS</p>
                  {performanceAnalysis.top_recommendations?.map((r: string, i: number) => (
                    <p key={i} className="text-sm text-gray-300 mb-1">• {r}</p>
                  ))}
                </div>

                <div className="bg-purple-900 bg-opacity-20 rounded-xl p-4 border border-purple-900">
                  <p className="text-purple-400 text-xs font-bold mb-2">📈 PROJECTED IMPROVEMENT</p>
                  <p className="text-sm text-gray-300">{performanceAnalysis.projected_improvement}</p>
                </div>
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <p>Click Refresh Analysis to load your performance data.</p>
              </div>
            )}
          </div>
        </div>
      )}

            {/* Agent Fleet Tab */}
      {activeTab === "agent-fleet" && (
        <div className="space-y-6">
          {/* Control Panel */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Shield size={20} className="text-blue-400" />
                Agent Control Center
              </h2>
              <div className="flex gap-3">
                <button
                  onClick={startAutonomousAgent}
                  disabled={agentControlLoading}
                  className="bg-green-600 hover:bg-green-500 disabled:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
                >
                  {agentControlLoading ? <RefreshCw size={14} className="animate-spin" /> : "▶️"}
                  Start Trading
                </button>
                <button
                  onClick={stopAutonomousAgent}
                  disabled={agentControlLoading}
                  className="bg-red-600 hover:bg-red-500 disabled:bg-gray-700 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
                >
                  ⏹️ Stop Trading
                </button>
                <button
                  onClick={fetchFleetStatus}
                  className="bg-gray-700 hover:bg-gray-600 px-4 py-2 rounded-lg text-sm flex items-center gap-2"
                >
                  <RefreshCw size={14} />
                  Refresh
                </button>
              </div>
            </div>
                      {/* Agent Activity Log */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Activity size={20} className="text-purple-400" />
                Agent Activity Log
              </h2>
              <button
                onClick={fetchAgentLogs}
                className="bg-gray-700 hover:bg-gray-600 px-3 py-1.5 rounded-lg text-xs flex items-center gap-1"
              >
                <RefreshCw size={12} />
                Refresh
              </button>
            </div>

            {agentLogs.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Activity size={32} className="mx-auto mb-2 opacity-30" />
                <p className="text-sm">No agent activity yet.</p>
              </div>
            ) : (
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {agentLogs.map((log, idx) => (
                  <div key={idx} className="bg-gray-800 rounded-lg p-3 border border-gray-700">
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          log.agent === "main_agent" ? "bg-blue-900 text-blue-300" :
                          log.agent === "swing_agent" ? "bg-green-900 text-green-300" :
                          "bg-yellow-900 text-yellow-300"
                        }`}>
                          {log.agent?.replace("_agent", "").toUpperCase()}
                        </span>
                        <span className={`text-xs font-medium ${
                          log.action === "BUY" ? "text-green-400" :
                          log.action === "SELL" ? "text-red-400" :
                          log.action === "SKIP" ? "text-yellow-400" : "text-gray-400"
                        }`}>
                          {log.action || "INFO"}
                        </span>
                      </div>
                      <span className="text-xs text-gray-500">{log.timestamp}</span>
                    </div>
                    <p className="text-sm text-gray-300">{log.message}</p>
                    {log.details && (
                      <p className="text-xs text-gray-500 mt-1">{log.details}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

            {loadingFleet ? (
              <div className="text-center py-12 text-gray-500">
                <RefreshCw size={32} className="animate-spin mx-auto mb-3" />
                <p>Loading fleet status...</p>
              </div>
            ) : fleetStatus ? (
              <div className="space-y-4">
                {/* Fleet Summary */}
                <div className="grid grid-cols-3 gap-4 mb-6">
                  <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <p className="text-gray-400 text-xs">Total Capital</p>
                    <p className="text-2xl font-bold text-green-400">₹{fleetStatus.total_capital?.toLocaleString()}</p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <p className="text-gray-400 text-xs">Total P&L</p>
                    <p className={`text-2xl font-bold ${fleetStatus.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                      ₹{fleetStatus.total_pnl?.toLocaleString()}
                    </p>
                  </div>
                  <div className="bg-gray-800 rounded-xl p-4 text-center">
                    <p className="text-gray-400 text-xs">Active Agents</p>
                    <p className="text-2xl font-bold text-blue-400">
                      {Object.keys(fleetStatus.agents || {}).length}
                    </p>
                  </div>
                </div>

                {/* Individual Agents */}
                {fleetStatus.agents && Object.entries(fleetStatus.agents).map(([name, agent]: [string, any]) => (
                  <div key={name} className="bg-gray-800 rounded-xl p-5 border border-gray-700">
                    <div className="flex items-center justify-between mb-4">
                      <div>
                        <h3 className="text-lg font-bold capitalize flex items-center gap-2">
                          {name === "main_agent" ? "🤖" : name === "swing_agent" ? "🏌️" : "🪙"}
                          {name.replace("_agent", "").toUpperCase()} AGENT
                        </h3>
                        <p className="text-xs text-gray-400 mt-1">
                          Initial Capital: ₹{agent.initial_capital?.toLocaleString()}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-xs text-gray-400">Available Cash</p>
                        <p className="text-xl font-bold text-green-400">₹{agent.cash?.toLocaleString()}</p>
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-3 mb-4">
                      <div>
                        <p className="text-gray-500 text-[10px]">Total Value</p>
                        <p className="text-sm font-medium">₹{agent.total_value?.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-[10px]">Total P&L</p>
                        <p className={`text-sm font-medium ${agent.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                          ₹{agent.total_pnl?.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-[10px]">Week P&L</p>
                        <p className={`text-sm font-medium ${agent.week_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                          ₹{agent.week_pnl?.toLocaleString()}
                        </p>
                      </div>
                      <div>
                        <p className="text-gray-500 text-[10px]">Open Positions</p>
                        <p className="text-sm font-medium">{agent.position_count}</p>
                      </div>
                    </div>

                    {/* Positions if any */}
                    {agent.positions?.length > 0 && (
                      <div className="mt-3 pt-3 border-t border-gray-700">
                        <p className="text-xs text-gray-400 mb-2">📊 OPEN POSITIONS</p>
                        <div className="space-y-2">
                          {agent.positions.map((pos: any, idx: number) => (
                            <div key={idx} className="bg-gray-900 rounded-lg p-2 flex justify-between items-center text-sm">
                              <span className="font-medium">{pos.symbol}</span>
                              <span>Qty: {pos.quantity}</span>
                              <span>Entry: ₹{pos.buy_price}</span>
                              <span className={pos.pnl >= 0 ? "text-green-400" : "text-red-400"}>
                                P&L: ₹{pos.pnl} ({pos.pnl_pct}%)
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-gray-500">
                <Shield size={40} className="mx-auto mb-3 opacity-30" />
                <p>Click Refresh to load fleet status</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Auto Monitor Tab */}
      {activeTab === "monitor" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Shield size={20} className="text-green-400" />
                Auto Stop Loss Monitor
              </h2>
              <p className="text-gray-400 text-xs mt-1">Automatically checks positions against stop loss and targets</p>
            </div>
            <button
              onClick={monitorPositions}
              className="flex items-center gap-2 bg-green-700 hover:bg-green-600 px-4 py-2 rounded-lg text-sm"
            >
              <Shield size={14} />
              Check Now
            </button>
          </div>

          {monitorResult ? (
            <div className="space-y-4">
              <div className="bg-gray-800 rounded-xl p-4">
                <p className="text-gray-400 text-xs mb-1">POSITIONS MONITORED</p>
                <p className="text-2xl font-bold">{monitorResult.monitored}</p>
              </div>
              {monitorResult.actions?.length > 0 ? (
                <div>
                  <p className="text-yellow-400 text-xs font-bold mb-3">⚡ ACTIONS TAKEN</p>
                  {monitorResult.actions.map((action: any, i: number) => (
                    <div key={i} className="bg-gray-800 rounded-xl p-4 mb-2 border border-yellow-800">
                      <div className="flex justify-between">
                        <p className="font-bold">{action.symbol}</p>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          action.pnl_pct >= 0 ? "bg-green-900 text-green-400" : "bg-red-900 text-red-400"
                        }`}>{action.pnl_pct}%</span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">{action.reason}</p>
                      <p className="text-xs text-gray-500 mt-1">Sold at ₹{action.price} — {action.time}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="bg-gray-800 rounded-xl p-4 text-center text-gray-400">
                  <Shield size={24} className="mx-auto mb-2 text-green-400" />
                  <p className="text-sm">All positions healthy — no action needed</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <Shield size={40} className="mx-auto mb-3 opacity-30" />
              <p>Click Check Now to monitor your positions</p>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
