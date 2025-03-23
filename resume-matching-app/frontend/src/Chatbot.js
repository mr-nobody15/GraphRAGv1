import { useState } from "react";
import axios from "axios";

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("resume-job");

  const sendMessage = async () => {
    if (input.trim() !== "") {
      const userMessage = { text: input, sender: "user" };
      setMessages([...messages, userMessage]);
      setInput("");

      try {
        const response = await axios.post(
          "https://probable-space-sniffle-6w7vpr7574qhrw7-8000.app.github.dev/chat",
          { text: input, mode },
          { headers: { "Content-Type": "application/json" } }
        );
        setMessages([...messages, userMessage, { text: response.data.response, sender: "bot" }]);
      } catch (error) {
        console.error("Error fetching response:", error);
      }
    }
  };
  
  return (
    <div style={{ position: "fixed", bottom: "20px", right: "20px", zIndex: 1000 }}>
      {!open ? (
        <button
          onClick={() => setOpen(true)}
          style={{ padding: "10px", borderRadius: "50%", background: "black", color: "white", border: "none", cursor: "pointer" }}
        >
          💬
        </button>
      ) : (
        <div style={{ width: "300px", height: minimized ? "50px" : "400px", background: "white", boxShadow: "0 4px 8px rgba(0,0,0,0.2)", borderRadius: "10px", padding: "10px", display: "flex", flexDirection: "column", border: "1px solid #ccc" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ fontSize: "16px", margin: 0 }}>Chatbot</h2>
            <div>
              <button onClick={() => setMinimized(!minimized)} style={{ background: "none", border: "none", fontSize: "16px", cursor: "pointer", marginRight: "10px" }}>
                {minimized ? "🔼" : "🔽"}
              </button>
              <button onClick={() => setOpen(false)} style={{ background: "none", border: "none", fontSize: "18px", cursor: "pointer" }}>✖</button>
            </div>
          </div>
          
          {!minimized && (
            <>
              <div style={{ flex: 1, overflowY: "auto", padding: "5px", display: "flex", flexDirection: "column", alignItems: "flex-start", color: "black", fontSize: "14px" }}>
                {messages.map((msg, index) => (
                  <div key={index} style={{ background: msg.sender === "user" ? "#e9ecef" : "#d1e7dd", padding: "5px 10px", borderRadius: "5px", marginBottom: "5px", alignSelf: msg.sender === "user" ? "flex-end" : "flex-start" }}>{msg.text}</div>
                ))}
              </div>
              
              <div style={{ display: "flex", justifyContent: "space-between", marginTop: "10px", paddingBottom: "10px" }}>
                <button onClick={() => setMode("resume-job")} style={{ flex: 1, margin: "0 5px", padding: "10px", background: mode === "resume-job" ? "#0056b3" : "#007bff", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}>Resume-Job</button>
                <button onClick={() => setMode("job-match")} style={{ flex: 1, margin: "0 5px", padding: "10px", background: mode === "job-match" ? "#19692c" : "#28a745", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}>Job Match</button>
                <button onClick={() => setMode("info")} style={{ flex: 1, margin: "0 5px", padding: "10px", background: mode === "info" ? "#4c2c92" : "#6f42c1", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}>Info</button>
              </div>
              
              <div style={{ display: "flex", alignItems: "center", padding: "5px" }}>
                <input 
                  type="text" 
                  placeholder="Type a message..." 
                  value={input} 
                  onChange={(e) => setInput(e.target.value)}
                  style={{ flex: 1, padding: "8px", border: "none", outline: "none" }} 
                />
                <button 
                  onClick={sendMessage} 
                  style={{ padding: "8px", background: "#007bff", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}
                >
                  ➤
                </button>
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
