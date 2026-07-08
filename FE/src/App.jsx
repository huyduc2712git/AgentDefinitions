import React, { useRef, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TextInput,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Platform,
} from 'react-native';

import useMikoChat from './hooks/useMikoChat';
import ModelSelector from './components/ModelSelector';
import ChatBubble from './components/ChatBubble';

export default function App() {
  const {
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
  } = useMikoChat();

  const scrollViewRef = useRef();

  // Auto-scroll chat to bottom
  useEffect(() => {
    if (scrollViewRef.current) {
      scrollViewRef.current.scrollToEnd({ animated: true });
    }
  }, [messages, isLoading]);

  return (
    <SafeAreaView style={styles.container}>
      {/* Header Area */}
      <View style={styles.header}>
        <View style={styles.headerTitleContainer}>
          <View style={styles.avatarCircle}>
            <Text style={styles.avatarText}>M</Text>
            <View style={styles.activeDot} />
          </View>
          <View style={styles.headerInfo}>
            <Text style={styles.headerName}>Miko</Text>
            <Text style={styles.headerSub}>🟢 Đang trực tuyến 24/7</Text>
          </View>
        </View>

        {/* Model Selector Dropdown */}
        <ModelSelector
          activeProvider={activeProvider}
          activeModel={activeModel}
          showModelDropdown={showModelDropdown}
          setShowModelDropdown={setShowModelDropdown}
          handleSwitchModel={handleSwitchModel}
        />
      </View>

      {/* Chat Area */}
      <View style={styles.chatContainer}>
        <ScrollView
          ref={scrollViewRef}
          contentContainerStyle={styles.chatScrollContent}
          style={styles.chatScrollView}
        >
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              msg={msg}
              onSelectProduct={handleSelectProduct}
            />
          ))}

          {isLoading && (
            <ChatBubble
              msg={{
                id: 'loading-indicator',
                role: 'loading',
                content: loadingStep,
              }}
            />
          )}
        </ScrollView>

        {/* Input Bar */}
        <View style={styles.inputOuterContainer}>
          <View style={styles.inputInnerContainer}>
            <TextInput
              style={styles.textInput}
              value={inputText}
              onChangeText={setInputText}
              placeholder="Nhắn tin cho Miko..."
              placeholderTextColor="#8B8B9A"
              onSubmitEditing={() => handleSend()}
              blurOnSubmit={false}
              editable={!isLoading}
            />
            <TouchableOpacity
              style={[styles.sendButton, isLoading && styles.sendButtonDisabled]}
              onPress={() => handleSend()}
              disabled={isLoading}
            >
              <Text style={styles.sendButtonArrow}>↑</Text>
            </TouchableOpacity>
          </View>
          
          <Text style={styles.footerText}>
            Demo Trực tuyến với Python Backend & Ollama
          </Text>
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#F8F9FA',
    ...Platform.select({
      web: {
        outlineStyle: 'none',
        overflow: 'hidden',
      },
    }),
  },
  header: {
    height: 70,
    backgroundColor: '#FFFFFF',
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 24,
    zIndex: 100,
  },
  headerTitleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#0d9488',
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  avatarText: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  activeDot: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#10B981',
    borderWidth: 2,
    borderColor: '#FFF',
    position: 'absolute',
    bottom: 0,
    right: 0,
  },
  headerInfo: {
    marginLeft: 12,
  },
  headerName: {
    color: '#111827',
    fontSize: 16,
    fontWeight: 'bold',
  },
  headerSub: {
    color: '#0d9488',
    fontSize: 11,
    fontWeight: '500',
    marginTop: 2,
  },
  chatContainer: {
    flex: 1,
    justifyContent: 'space-between',
    overflow: 'hidden',
  },
  chatScrollView: {
    flex: 1,
  },
  chatScrollContent: {
    paddingHorizontal: 24,
    paddingTop: 24,
    paddingBottom: 40,
    width: '100%',
  },
  inputOuterContainer: {
    backgroundColor: '#FFFFFF',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingVertical: 16,
    paddingHorizontal: 24,
    alignItems: 'center',
  },
  inputInnerContainer: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1.5,
    borderColor: '#0d9488',
    borderRadius: 30,
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 20,
    paddingVertical: 6,
  },
  textInput: {
    flex: 1,
    color: '#1F2937',
    fontSize: 14,
    paddingVertical: 10,
    outlineWidth: 0,
    ...Platform.select({
      web: {
        outlineStyle: 'none',
      },
    }),
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#0d9488',
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  sendButtonArrow: {
    color: '#FFF',
    fontSize: 18,
    fontWeight: 'bold',
    lineHeight: 18,
    textAlign: 'center',
  },
  footerText: {
    color: '#9CA3AF',
    fontSize: 11,
    marginTop: 8,
    textAlign: 'center',
  },
});
