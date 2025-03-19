import { useState } from "react";
import { fetchChatResponse } from "../api";

export default function Chatbot() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [mode, setMode] = useState("resume-job");

  const sendMessage = async () => {
    if (!input.trim()) return;
    
    const userMessage = { text: input, sender: "user" };
    setMessages([...messages, userMessage]);
    setInput("");

    const data = await fetchChatResponse(input, mode);
    setMessages([...messages, userMessage, { text: data.response, sender: "bot" }]);
  };

  return (
    <div>
      {!open ? (
        <button onClick={() => setOpen(true)}>💬 Open Chat</button>
      ) : (
        <div>
          <button onClick={() => setOpen(false)}>✖ Close</button>
          <div>
            {messages.map((msg, idx) => (
              <div key={idx} style={{ background: msg.sender === "user" ? "#eee" : "#ddd" }}>
                {msg.text}
              </div>
            ))}
          </div>
          <input value={input} onChange={(e) => setInput(e.target.value)} />
          <button onClick={sendMessage}>Send</button>
        </div>
      )}
    </div>
  );
}
