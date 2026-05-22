"use client";

import { useEffect, useState } from "react";
import {
  TrendingUp,
  Activity,
  DollarSign,
  RefreshCw,
  Shield,
  Send,
  Play,
  Square,
} from "lucide-react";

const API_BASE = "http://localhost:8000/api";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [expandedCard, setExpandedCard] = useState<string | null>(null);
  
  // Dashboard state
  const [marketContext, setMarketContext] = useState<any>(null);
  const [fleetStatus, setFleetStatus] = useState<any>(null);
  const [agentLogs, setAgentLogs] = useState<any[]>([]);
  const [departmentActivity, setDepartmentActivity] = useState<any[]>([]);
  
  // Scanner state
  const [signals, setSignals] = useState<any[]>([]);
  const [scanning, setScanning] = useState(false);
  
  // Trades state
  const [portfolio, setPortfolio] = useState<any>(null);
  const [tradeHistory, setTradeHistory] = useState<any[]>([]);
  const [performance, setPerformance] = useState<any>(null);
  
  // Admin state
  const [blacklist, setBlacklist] = useState<string[]>([]);
  const [riskMode, setRiskMode] = useState("MODERATE");
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<{role: string, content: string}[]>([]);
  const [chatLoading, setChatLoading] = useState(false);

  // ============================================================
  // FETCH FUNCTIONS
  // ============================================================

  const fetchMarketContext = async () => {
    try {
      const res = await fetch(`${API_BASE}/market-context`);
      const data = await res.json();
      setMarketContext(data);
    } catch (err) {
      console.error("Market context failed:", err);
    }
  };

  const fetchFleetStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/fleet/status`);
      const data = await res.json();
      setFleetStatus(data);
    } catch (err) {
      console.error("Fleet status failed:", err);
    }
  };

  const fetchAgentLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/agent/logs`);
      const data = await res.json();
      setAgentLogs(data.logs || []);
    } catch (err) {
      console.error("Agent logs failed:", err);
    }
  };

  const fetchDepartmentActivity = async () => {
    try {
      const res = await fetch(`${API_BASE}/department/activity`);
      const data = await res.json();
      setDepartmentActivity(data.activities || []);
    } catch (err) {
      console.error("Department activity fetch failed:", err);
    }
  };

  const fetchSignals = async () => {
    setScanning(true);
    try {
      const res = await fetch(`${API_BASE}/scan/market/top`);
      const data = await res.json();
      setSignals(data.signals || []);
    } catch (err) {
      console.error("Scan failed:", err);
    }
    setScanning(false);
  };

  const fetchPortfolio = async () => {
    try {
      const res = await fetch(`${API_BASE}/portfolio`);
      const data = await res.json();
      setPortfolio(data);
    } catch (err) {
      console.error("Portfolio failed:", err);
    }
  };

  const fetchTradeHistory = async () => {
    try {
      const res = await fetch(`${API_BASE}/trades/history`);
      const data = await res.json();
      setTradeHistory(data.trades || []);
    } catch (err) {
      console.error("Trade history failed:", err);
    }
  };

  const fetchPerformance = async () => {
    try {
      const res = await fetch(`${API_BASE}/performance/analysis`);
      const data = await res.json();
      setPerformance(data);
    } catch (err) {
      console.error("Performance failed:", err);
    }
  };

  const fetchBlacklist = async () => {
    try {
      const res = await fetch(`${API_BASE}/control/settings`);
      const data = await res.json();
      setBlacklist(data.blacklist || []);
    } catch (err) {
      console.error("Blacklist failed:", err);
    }
  };

  // ============================================================
  // ACTIONS
  // ============================================================

  const startTrading = async () => {
    try {
      const res = await fetch(`${API_BASE}/agent/start`, { method: "POST" });
      const data = await res.json();
      alert(data.message || "Trading started");
      fetchFleetStatus();
      fetchAgentLogs();
    } catch (err) {
      alert("Failed to start trading");
    }
  };

  const stopTrading = async () => {
    try {
      const res = await fetch(`${API_BASE}/agent/stop`, { method: "POST" });
      const data = await res.json();
      alert(data.message || "Trading stopped");
      fetchFleetStatus();
      fetchAgentLogs();
    } catch (err) {
      alert("Failed to stop trading");
    }
  };

  const buyStock = async (signal: any) => {
    try {
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
      fetchTradeHistory();
      fetchAgentLogs();
    } catch (err) {
      alert("Buy failed");
    }
  };

  const sellStock = async (symbol: string, current_price: number) => {
    try {
      const res = await fetch(`${API_BASE}/trade/sell`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ symbol, current_price }),
      });
      const data = await res.json();
      if (data.status !== "success") {
        alert(data.message || data.error || "Sell failed");
        return;
      }
      alert(data.message || `Sold ${symbol}`);
      fetchPortfolio();
      fetchTradeHistory();
      fetchAgentLogs();
    } catch (err) {
      alert("Sell failed");
    }
  };

  const blacklistStock = async () => {
    const symbol = prompt("Enter stock symbol to blacklist:");
    if (symbol) {
      try {
        await fetch(`${API_BASE}/control/blacklist/${symbol}`, { method: "POST" });
        alert(`${symbol} blacklisted`);
        fetchBlacklist();
      } catch (err) {
        alert("Failed to blacklist");
      }
    }
  };

  const controlDepartment = async (name: string, action: "start" | "stop") => {
    try {
      const res = await fetch(`${API_BASE}/department/${name}/${action}`, { method: "POST" });
      const data = await res.json();
      alert(data.message || data.status || `${action} ${name}`);
      fetchFleetStatus();
      fetchDepartmentActivity();
    } catch (err) {
      alert(`Failed to ${action} ${name}`);
    }
  };

  const changeRiskMode = async (mode: string) => {
    try {
      await fetch(`${API_BASE}/control/risk/${mode}`, { method: "POST" });
      setRiskMode(mode);
      alert(`Risk mode changed to ${mode}`);
    } catch (err) {
      alert("Failed to change risk mode");
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim()) return;

    const userMessage = chatInput;
    setChatMessages(prev => [...prev, { role: "user", content: userMessage }]);
    setChatInput("");
    setChatLoading(true);

    try {
      const res = await fetch(`${API_BASE}/chat/manager`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: userMessage }),
      });
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: "assistant", content: data.response || "No response from manager." }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { role: "assistant", content: "AI chat failed. Please try again." }]);
    } finally {
      setChatLoading(false);
    }
  };

  // ============================================================
  // EFFECTS
  // ============================================================

  useEffect(() => {
    // Initial fetches
    fetchMarketContext();
    fetchFleetStatus();
    fetchAgentLogs();
    fetchSignals();
    fetchPortfolio();
    fetchTradeHistory();
    fetchPerformance();
    fetchBlacklist();
    fetchDepartmentActivity();

    // 30-second interval for market data
    const marketInterval = setInterval(() => {
      fetchMarketContext();
      fetchFleetStatus();
      fetchPortfolio();
      fetchAgentLogs();
    }, 30000);
    
    // 5-second interval for department activity (real-time)
    const activityInterval = setInterval(() => {
      fetchDepartmentActivity();
    }, 5000);
    
    return () => {
      clearInterval(marketInterval);
      clearInterval(activityInterval);
    };
  }, []);

  // ============================================================
  // RENDER HELPERS
  // ============================================================

  const getMoodColor = (mood: string) => {
    if (mood === "BULLISH") return "text-green-400";
    if (mood === "BEARISH") return "text-red-400";
    return "text-yellow-400";
  };

  const getSignalColor = (signal: string) => {
    if (signal === "STRONG BUY") return "bg-green-500";
    if (signal === "BUY") return "bg-green-400";
    if (signal === "WEAK BUY") return "bg-yellow-400";
    return "bg-red-400";
  };

  // Helper to get activity for a department
  const getActivity = (deptName: string) => {
    return departmentActivity.find(a => a.department === deptName);
  };

  // ============================================================
  // MAIN RENDER
  // ============================================================

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">🤖 AI Trading System</h1>
          <p className="text-gray-400 text-sm">Multi-Agent Trading Platform</p>
        </div>
        <button
          onClick={() => {
            fetchMarketContext();
            fetchFleetStatus();
            fetchPortfolio();
            fetchSignals();
            fetchAgentLogs();
            fetchDepartmentActivity();
          }}
          className="flex items-center gap-2 bg-gray-800 hover:bg-gray-700 px-4 py-2 rounded-lg text-sm"
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Market Regime Widget */}
      {marketContext && (
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="bg-gray-900 rounded-xl p-3 border border-gray-800">
            <p className="text-gray-400 text-xs">NIFTY</p>
            <p className="text-lg font-bold">{marketContext.nifty?.price?.toLocaleString()}</p>
            <p className={`text-xs ${marketContext.nifty?.change_pct >= 0 ? "text-green-400" : "text-red-400"}`}>
              {marketContext.nifty?.change_pct >= 0 ? "▲" : "▼"} {Math.abs(marketContext.nifty?.change_pct)}%
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-3 border border-gray-800">
            <p className="text-gray-400 text-xs">VIX</p>
            <p className="text-lg font-bold">{marketContext.india_vix}</p>
            <p className={`text-xs ${
              marketContext.volatility === "HIGH" ? "text-red-400" : 
              marketContext.volatility === "MEDIUM" ? "text-yellow-400" : "text-green-400"
            }`}>{marketContext.volatility}</p>
          </div>
          <div className="bg-gray-900 rounded-xl p-3 border border-gray-800">
            <p className="text-gray-400 text-xs">MARKET MOOD</p>
            <p className={`text-lg font-bold ${getMoodColor(marketContext.market_mood)}`}>
              {marketContext.market_mood}
            </p>
          </div>
          <div className="bg-gray-900 rounded-xl p-3 border border-gray-800">
            <p className="text-gray-400 text-xs">TOTAL P&L</p>
            <p className={`text-lg font-bold ${portfolio?.overall_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
              ₹{portfolio?.overall_pnl?.toLocaleString() || 0}
            </p>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="flex flex-wrap gap-2 mb-6">
        {[
          { id: "dashboard", label: "Agent Dashboard", icon: <Shield size={16} /> },
          { id: "scanner", label: "Scanner", icon: <Activity size={16} /> },
          { id: "trades", label: "Trades & Positions", icon: <DollarSign size={16} /> },
          { id: "admin", label: "Admin Control", icon: <TrendingUp size={16} /> },
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === tab.id
                ? "bg-blue-600 text-white"
                : "bg-gray-800 text-gray-400 hover:bg-gray-700"
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* ============================================================ */}
      {/* TAB 1: AGENT DASHBOARD */}
      {/* ============================================================ */}
      {activeTab === "dashboard" && (
        <div className="space-y-6">
          {/* Control Buttons */}
          <div className="flex gap-3">
            <button
              onClick={startTrading}
              className="bg-green-600 hover:bg-green-500 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
            >
              <Play size={14} /> Start Trading
            </button>
            <button
              onClick={stopTrading}
              className="bg-red-600 hover:bg-red-500 px-4 py-2 rounded-lg text-sm font-medium flex items-center gap-2"
            >
              <Square size={14} /> Stop Trading
            </button>
          </div>

          {/* All Departments Cards - Expandable */}
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-4">
            {fleetStatus?.agents && Object.entries(fleetStatus.agents).map(([name, agent]: [string, any]) => {
              const activity = getActivity(name);
              return (
                <div key={name} className="bg-gray-900 rounded-xl border border-gray-800">
                  {/* Card Header - Click to expand */}
                  <div 
                    className="p-4 cursor-pointer hover:bg-gray-800 transition-colors"
                    onClick={() => setExpandedCard(expandedCard === name ? null : name)}
                  >
                    <div className="flex justify-between items-start">
                      <h3 className="font-bold text-lg capitalize">{name}</h3>
                      <span className="text-xs text-gray-400">{expandedCard === name ? "▲" : "▼"}</span>
                    </div>
                    <p className="text-2xl font-bold text-green-400">₹{agent.cash?.toLocaleString() || agent.capital?.toLocaleString() || 0}</p>
                    <p className="text-xs text-gray-400">P&L: ₹{agent.total_pnl?.toLocaleString() || 0}</p>
                    <p className="text-xs text-gray-400">Status: {agent.status || "🟢 ACTIVE"}</p>
                    
                    {/* Current Task (always visible) */}
                    {activity && (
                      <p className="text-xs text-blue-400 mt-2 truncate">📋 {activity.current_task}</p>
                    )}
                    <div className="mt-3 flex gap-2">
                      <button
                        onClick={(event) => {
                          event.stopPropagation();
                          controlDepartment(name, (activity?.status || agent.status || "").toUpperCase().includes("ACTIVE") ? "stop" : "start");
                        }}
                        className="bg-blue-600 hover:bg-blue-500 px-3 py-1 rounded text-xs"
                      >
                        {(activity?.status || agent.status || "").toUpperCase().includes("ACTIVE") ? "Stop" : "Start"}
                      </button>
                    </div>
                  </div>
                  
                  {/* Expanded Content - Shows when clicked */}
                  {expandedCard === name && (
                    <div className="border-t border-gray-800 p-4 bg-gray-800/50">
                      <p className="text-sm text-gray-300 mb-2">📊 Details</p>
                      <div className="space-y-1 text-xs">
                        <p>Positions: {agent.position_count || 0}</p>
                        <p>Total Trades: {agent.total_trades || 0}</p>
                        <p>Win Rate: {agent.win_rate || 0}%</p>
                      </div>
                      
                      {/* Current Task & Progress */}
                      {activity && (
                        <div className="mt-3 pt-3 border-t border-gray-700">
                          <p className="text-xs text-blue-400">Current: {activity.current_task}</p>
                          {activity.progress > 0 && (
                            <div className="mt-2">
                              <div className="flex justify-between text-xs mb-1">
                                <span className="text-gray-400">Progress</span>
                                <span className="text-gray-400">{activity.progress}%</span>
                              </div>
                              <div className="bg-gray-700 rounded-full h-1.5">
                                <div 
                                  className="bg-blue-500 h-1.5 rounded-full transition-all duration-500" 
                                  style={{ width: `${activity.progress}%` }} 
                                />
                              </div>
                            </div>
                          )}
                          <p className="text-xs text-gray-500 mt-1">Last: {activity.last_action}</p>
                        </div>
                      )}
                      
                      {/* Progress bar for backtesting */}
                      {name === "backtesting" && agent.progress && (
                        <div className="mt-3">
                          <div className="flex justify-between text-xs mb-1">
                            <span>Backtest Progress</span>
                            <span>{agent.progress}%</span>
                          </div>
                          <div className="bg-gray-700 rounded-full h-2">
                            <div className="bg-purple-500 h-2 rounded-full" style={{ width: `${agent.progress}%` }} />
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Activity Log */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold mb-4">Activity Log</h2>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {agentLogs.length === 0 ? (
                <p className="text-gray-500 text-center">No activity yet</p>
              ) : (
                agentLogs.slice(0, 30).map((log, idx) => (
                  <div key={idx} className="bg-gray-800 rounded-lg p-2 text-sm">
                    <span className="text-gray-400">[{log.timestamp}]</span>{" "}
                    <span className="font-medium">{log.agent?.toUpperCase()}</span>{" "}
                    <span className="text-blue-400">{log.action}</span>{" "}
                    {log.message}
                    {log.details && <span className="text-gray-500 text-xs ml-2">({log.details})</span>}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 2: SCANNER */}
      {/* ============================================================ */}
      {activeTab === "scanner" && (
        <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
          <div className="flex justify-between mb-4">
            <h2 className="text-xl font-bold">Market Scanner</h2>
            <button
              onClick={fetchSignals}
              disabled={scanning}
              className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg text-sm"
            >
              {scanning ? "Scanning..." : "Scan Market"}
            </button>
          </div>

          {signals.length === 0 ? (
            <div className="text-center py-12 text-gray-500">
              <Activity size={40} className="mx-auto mb-3 opacity-30" />
              <p>Click Scan Market to find opportunities</p>
            </div>
          ) : (
            <div className="space-y-3">
              {signals.slice(0, 15).map((signal, i) => (
                <div key={i} className="bg-gray-800 rounded-lg p-4">
                  <div className="flex justify-between items-center mb-2">
                    <span className="font-bold text-lg">{signal.symbol}</span>
                    <span className={`${getSignalColor(signal.signal)} text-black text-xs font-bold px-2 py-1 rounded-full`}>
                      {signal.signal}
                    </span>
                  </div>
                  <div className="grid grid-cols-4 gap-2 text-sm mb-2">
                    <div>Price: ₹{signal.price}</div>
                    <div>Target: ₹{signal.target}</div>
                    <div>Stop: ₹{signal.stop_loss}</div>
                    <div>Score: {signal.score}/100</div>
                  </div>
                  {signal.strategy_used && (
                    <p className="text-xs text-gray-400 mb-2">Strategy: {signal.strategy_used}</p>
                  )}
                  <button
                    onClick={() => buyStock(signal)}
                    className="bg-green-700 hover:bg-green-600 px-3 py-1 rounded text-sm"
                  >
                    📈 Paper Buy
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 3: TRADES & POSITIONS */}
      {/* ============================================================ */}
      {activeTab === "trades" && (
        <div className="space-y-6">
          {/* Open Positions */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold mb-4">Open Positions</h2>
            {!portfolio?.positions?.length ? (
              <p className="text-gray-500 text-center">No open positions</p>
            ) : (
              <div className="space-y-2">
                {portfolio.positions.map((pos: any, i: number) => (
                  <div key={i} className="bg-gray-800 rounded-lg p-3 flex justify-between items-center">
                    <div>
                      <span className="font-bold">{pos.symbol}</span>
                      <span className="text-xs text-gray-400 ml-2">Qty: {pos.quantity}</span>
                    </div>
                    <div>Entry: ₹{pos.buy_price}</div>
                    <div>Current: ₹{pos.current_price}</div>
                    <div className={pos.pnl >= 0 ? "text-green-400" : "text-red-400"}>
                      P&L: ₹{pos.pnl} ({pos.pnl_pct}%)
                    </div>
                    <button
                      onClick={() => sellStock(pos.symbol, pos.current_price)}
                      className="bg-red-700 hover:bg-red-600 px-3 py-1 rounded text-xs"
                    >
                      Sell
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Performance Summary */}
          {performance && (
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4">Performance</h2>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <p className="text-gray-400 text-xs">Total Trades</p>
                  <p className="text-2xl font-bold">{performance.stats?.total_trades || 0}</p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs">Win Rate</p>
                  <p className="text-2xl font-bold text-green-400">{performance.stats?.win_rate || 0}%</p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs">Total P&L</p>
                  <p className={`text-2xl font-bold ${performance.stats?.total_pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                    ₹{performance.stats?.total_pnl || 0}
                  </p>
                </div>
                <div>
                  <p className="text-gray-400 text-xs">Grade</p>
                  <p className="text-2xl font-bold text-yellow-400">{performance.performance_grade || "N/A"}</p>
                </div>
              </div>
            </div>
          )}

          {/* Trade History */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold mb-4">Trade History</h2>
            {tradeHistory.length === 0 ? (
              <p className="text-gray-500 text-center">No trades yet</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-gray-400 border-b border-gray-800">
                      <th className="text-left py-2">Symbol</th>
                      <th className="text-left py-2">Type</th>
                      <th className="text-right py-2">Price</th>
                      <th className="text-right py-2">P&L</th>
                      <th className="text-left py-2">Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {tradeHistory.slice(0, 20).map((trade: any, i: number) => (
                      <tr key={i} className="border-b border-gray-800">
                        <td className="py-2 font-bold">{trade.symbol}</td>
                        <td className="py-2">{trade.trade_type}</td>
                        <td className="py-2 text-right">₹{trade.price}</td>
                        <td className={`py-2 text-right ${trade.pnl >= 0 ? "text-green-400" : "text-red-400"}`}>
                          {trade.pnl !== undefined && trade.pnl !== null ? `₹${trade.pnl}` : "-"}
                        </td>
                        <td className="py-2 text-left text-gray-400 text-xs">
                          {new Date(trade.created_at).toLocaleTimeString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ============================================================ */}
      {/* TAB 4: ADMIN CONTROL */}
      {/* ============================================================ */}
      {activeTab === "admin" && (
        <div className="space-y-6">
          {/* Risk & Blacklist */}
          <div className="grid grid-cols-2 gap-6">
            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4">Risk Settings</h2>
              <select
                value={riskMode}
                onChange={(e) => changeRiskMode(e.target.value)}
                className="bg-gray-800 text-white px-3 py-2 rounded-lg text-sm w-full mb-4"
              >
                <option value="CONSERVATIVE">Conservative</option>
                <option value="MODERATE">Moderate</option>
                <option value="AGGRESSIVE">Aggressive</option>
              </select>
              <button
                onClick={blacklistStock}
                className="bg-red-700 hover:bg-red-600 px-4 py-2 rounded-lg text-sm w-full"
              >
                ⛔ Blacklist Stock
              </button>
            </div>

            <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
              <h2 className="text-xl font-bold mb-4">Blacklisted Stocks</h2>
              {blacklist.length === 0 ? (
                <p className="text-gray-500 text-sm">No blacklisted stocks</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {blacklist.map((symbol, i) => (
                    <span key={i} className="bg-red-900 text-red-300 px-2 py-1 rounded text-xs">
                      {symbol}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Chat with Manager */}
          <div className="bg-gray-900 rounded-xl p-6 border border-gray-800">
            <h2 className="text-xl font-bold mb-4">🤖 Chat with Manager</h2>
            <div className="bg-gray-800 rounded-lg p-4 h-64 overflow-y-auto mb-4">
              {chatMessages.length === 0 ? (
                <p className="text-gray-500 text-center">Type a command. Try: "status" or "stop trading"</p>
              ) : (
                chatMessages.map((msg, i) => (
                  <div key={i} className={`mb-2 ${msg.role === "user" ? "text-right" : "text-left"}`}>
                    <span className={`inline-block px-3 py-1 rounded-lg text-sm ${msg.role === "user" ? "bg-blue-600" : "bg-gray-700"}`}>
                      {msg.content}
                    </span>
                  </div>
                ))
              )}
            </div>
            <div className="flex gap-2">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && sendChatMessage()}
                placeholder="Type command..."
                className="flex-1 bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 text-sm"
              />
              <button
                onClick={sendChatMessage}
                className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg"
              >
                <Send size={16} />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}