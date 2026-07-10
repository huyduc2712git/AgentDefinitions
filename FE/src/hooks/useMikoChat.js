import { useState, useEffect } from 'react';

const BACKEND_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1' || window.location.hostname.startsWith('192.168.')
  ? 'http://localhost:8000'
  : 'https://agentdefinitions.onrender.com';

export default function useMikoChat() {
  const [sessionId] = useState(() => 'session_' + Math.random().toString(36).substring(2, 10));
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: 'Xin chào anh/chị! 👋 Em là Miko — trợ lý bán hàng.\nEm có thể giúp:\n- Tìm sản phẩm phù hợp\n- Tư vấn giá, tồn kho, chính sách\n- Đặt hàng ngay — không cần gọi điện\n\nAnh/chị đang cần tìm gì hôm nay ạ?',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('');
  const [activeProvider, setActiveProvider] = useState('ollama');
  const [activeModel, setActiveModel] = useState('llama-3.1-8b-instruct');
  const [showModelDropdown, setShowModelDropdown] = useState(false);

  // Get current backend configuration
  const fetchConfig = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/config`);
      if (response.ok) {
        const data = await response.json();
        setActiveProvider(data.llm_provider);
        setActiveModel(data.model);
      }
    } catch (error) {
      console.warn('Lỗi khi lấy config từ backend:', error);
    }
  };

  useEffect(() => {
    fetchConfig();
  }, []);

  // Loading step is set dynamically in handleSend via the NDJSON stream from the backend
  useEffect(() => {
    if (!isLoading) {
      setLoadingStep('');
    }
  }, [isLoading]);

  const handleSend = async (customText) => {
    const textToSend = typeof customText === 'string' ? customText : inputText;
    if (!textToSend.trim() || isLoading) return;

    setInputText('');

    const userMsg = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: textToSend.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setIsLoading(true);
    setLoadingStep('Miko đang suy nghĩ...'); // Default initial step

    const startTime = Date.now();

    try {
      const response = await fetch(`${BACKEND_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          message: textToSend.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error('Lỗi phản hồi từ server');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop(); // Giữ lại dòng chưa hoàn chỉnh cuối cùng

        for (const line of lines) {
          if (!line.trim()) continue;
          try {
            const data = JSON.parse(line);
            if (data.type === 'status') {
              setLoadingStep(data.message);
            } else if (data.type === 'result') {
              const duration = ((Date.now() - startTime) / 1000).toFixed(1);
              const assistantMsg = {
                id: `miko-${Date.now()}`,
                role: 'assistant',
                content: data.reply || 'Dạ em chưa nghe rõ, anh/chị nói lại giúp em nha.',
                products: data.products || [],
                timestamp: new Date(),
                responseTime: duration,
              };
              setMessages((prev) => [...prev, assistantMsg]);
            }
          } catch (e) {
            console.error('Lỗi parse dòng stream:', e);
          }
        }
      }
    } catch (error) {
      console.error('Lỗi gọi API chat:', error);
      const errorMsg = {
        id: `err-${Date.now()}`,
        role: 'system',
        content: '❌ Lỗi kết nối. Vui lòng kiểm tra lại server hoặc thử lại sau!',
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSwitchModel = async (provider, modelName) => {
    setShowModelDropdown(false);
    // Optimistic UI updates
    setActiveProvider(provider);
    setActiveModel(modelName);

    try {
      const response = await fetch(`${BACKEND_URL}/config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          llm_provider: provider,
          nvidia_model: modelName,
        }),
      });

      if (!response.ok) {
        throw new Error('Lỗi phản hồi từ server');
      }
    } catch (error) {
      console.warn('Lỗi đồng bộ cấu hình model với backend:', error);
    }
  };

  const handleSelectProduct = (product) => {
    const name = product.product_name || product.name;
    handleSend(`chốt ${name}`);
  };

  return {
    messages,
    inputText,
    setInputText,
    isLoading,
    loadingStep,
    activeProvider,
    activeModel,
    showModelDropdown,
    setShowModelDropdown,
    handleSend,
    handleSwitchModel,
    handleSelectProduct,
  };
}
