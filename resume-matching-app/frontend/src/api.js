export const fetchChatResponse = async (query, jobTitle) => {
    try {
      const response = await fetch(`http://localhost:8000/chat-response/?query=${encodeURIComponent(query)}&job_title=${jobTitle}`);
      return await response.json();
    } catch (error) {
      console.error("API error:", error);
      return { response: "Error fetching response." };
    }
  };
  