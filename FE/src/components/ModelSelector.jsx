import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity } from 'react-native';

export default function ModelSelector({
  activeProvider,
  activeModel,
  showModelDropdown,
  setShowModelDropdown,
  handleSwitchModel,
}) {
  const getModelDisplayName = () => {
    if (activeProvider === 'ollama') {
      return `✦ Ollama Local (${activeModel})`;
    }
    if (activeModel.includes('llama')) {
      return `✦ Llama-3.1 (NVIDIA Cloud - Siêu nhanh)`;
    }
    if (activeModel.includes('glm')) {
      return `✦ GLM-5.2 (NVIDIA Cloud - Siêu nhanh)`;
    }
    if (activeModel.includes('minimax')) {
      return `✦ MiniMax-M3 (NVIDIA Cloud - Nhanh)`;
    }
    return `✦ ${activeModel} (NVIDIA Cloud)`;
  };

  return (
    <View style={styles.modelSelectorContainer}>
      <TouchableOpacity
        style={styles.modelPill}
        onPress={() => setShowModelDropdown(!showModelDropdown)}
      >
        <Text style={styles.modelPillText}>{getModelDisplayName()}</Text>
        <Text style={styles.arrowIcon}> ▼</Text>
      </TouchableOpacity>

      {showModelDropdown && (
        <View style={styles.dropdownMenu}>
          <TouchableOpacity
            style={styles.dropdownItem}
            onPress={() => handleSwitchModel('ollama', 'qwen2.5:3b')}
          >
            <Text style={styles.dropdownItemText}>✦ Ollama Local (qwen2.5:3b)</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dropdownItem}
            onPress={() => handleSwitchModel('nvidia', 'meta/llama-3.1-8b-instruct')}
          >
            <Text style={styles.dropdownItemText}>✦ NVIDIA Cloud (Llama 3.1 8b)</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dropdownItem}
            onPress={() => handleSwitchModel('nvidia', 'z-ai/glm-5.2')}
          >
            <Text style={styles.dropdownItemText}>✦ NVIDIA Cloud (GLM-5.2)</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dropdownItem}
            onPress={() => handleSwitchModel('nvidia', 'deepseek-ai/deepseek-v4-flash')}
          >
            <Text style={styles.dropdownItemText}>✦ NVIDIA Cloud (DeepSeek v4 Flash)</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.dropdownItem}
            onPress={() => handleSwitchModel('nvidia', 'minimaxai/minimax-m3')}
          >
            <Text style={styles.dropdownItemText}>✦ NVIDIA Cloud (MiniMax-M3)</Text>
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  modelSelectorContainer: {
    position: 'relative',
  },
  modelPill: {
    backgroundColor: '#F3F4F6',
    borderRadius: 20,
    paddingVertical: 8,
    paddingHorizontal: 16,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  modelPillText: {
    color: '#374151',
    fontSize: 12,
    fontWeight: '600',
  },
  arrowIcon: {
    color: '#6B7280',
    fontSize: 9,
  },
  dropdownMenu: {
    position: 'absolute',
    top: 42,
    right: 0,
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    elevation: 5,
    width: 250,
    paddingVertical: 6,
    zIndex: 999,
  },
  dropdownItem: {
    paddingVertical: 10,
    paddingHorizontal: 16,
  },
  dropdownItemText: {
    color: '#374151',
    fontSize: 12,
    fontWeight: '500',
  },
});
