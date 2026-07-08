import React from 'react';
import { StyleSheet, Text, View, ActivityIndicator } from 'react-native';
import ProductCarousel from './ProductCarousel';

export default function ChatBubble({ msg, onSelectProduct }) {
  const isUser = msg.role === 'user';
  const isSystem = msg.role === 'system';
  const isLoading = msg.role === 'loading';

  if (isSystem) {
    return (
      <View style={styles.systemMessageContainer}>
        <Text style={styles.systemMessageText}>{msg.content}</Text>
      </View>
    );
  }

  if (isLoading) {
    return (
      <View style={[styles.messageRow, styles.messageRowMiko, { marginVertical: 8 }]}>
        <View style={styles.msgAvatar}>
          <Text style={styles.msgAvatarText}>M</Text>
        </View>
        <View style={[styles.messageBubble, styles.bubbleMiko, styles.bubbleLoading]}>
          <ActivityIndicator size="small" color="#0d9488" />
          <Text style={styles.loadingText}>{msg.content}</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={{ marginVertical: 12 }}>
      {/* Standard Message Bubble */}
      <View
        style={[
          styles.messageRow,
          isUser ? styles.messageRowUser : styles.messageRowMiko,
        ]}
      >
        {!isUser && (
          <View style={styles.msgAvatar}>
            <Text style={styles.msgAvatarText}>M</Text>
          </View>
        )}
        <View
          style={[
            styles.messageBubble,
            isUser ? styles.bubbleUser : styles.bubbleMiko,
          ]}
        >
          <Text
            style={[
              styles.messageText,
              isUser ? styles.textUser : styles.textMiko,
            ]}
          >
            {msg.content}
          </Text>
        </View>
      </View>

      {/* Product Horizontal Carousel if present */}
      {!isUser && msg.products && msg.products.length > 0 && (
        <ProductCarousel products={msg.products} onSelect={onSelectProduct} />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  messageRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    maxWidth: '75%',
  },
  messageRowUser: {
    alignSelf: 'flex-end',
  },
  messageRowMiko: {
    alignSelf: 'flex-start',
  },
  msgAvatar: {
    width: 30,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#0d9488',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 10,
    marginTop: 2,
  },
  msgAvatarText: {
    color: '#FFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  messageBubble: {
    flexShrink: 1,
    borderRadius: 18,
    paddingVertical: 12,
    paddingHorizontal: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  bubbleUser: {
    backgroundColor: '#0d9488',
    borderTopRightRadius: 2,
  },
  bubbleMiko: {
    backgroundColor: '#FFFFFF',
    borderTopLeftRadius: 2,
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  bubbleLoading: {
    flexDirection: 'row',
    alignItems: 'center',
    minWidth: 160,
  },
  loadingText: {
    color: '#6B7280',
    fontSize: 13,
    marginLeft: 12,
  },
  messageText: {
    fontSize: 14,
    lineHeight: 22,
    whiteSpace: 'pre-wrap',
  },
  textUser: {
    color: '#FFF',
  },
  textMiko: {
    color: '#1F2937',
  },
  systemMessageContainer: {
    alignSelf: 'center',
    backgroundColor: '#FEE2E2',
    paddingVertical: 6,
    paddingHorizontal: 16,
    borderRadius: 12,
    marginVertical: 12,
    borderWidth: 1,
    borderColor: '#FCA5A5',
  },
  systemMessageText: {
    color: '#DC2626',
    fontSize: 12,
    fontWeight: '500',
  },
});
