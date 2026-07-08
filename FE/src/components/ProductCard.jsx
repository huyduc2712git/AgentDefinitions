import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity, Image, Platform } from 'react-native';
import { formatVND, calculateOriginalPrice } from '../utils/format';

export default function ProductCard({ product, onSelect }) {
  const name = product.product_name || product.name || 'Sản phẩm';
  const price = Number(product.price || product.sell_price || 0);
  const originalPrice = calculateOriginalPrice(price);

  return (
    <View style={styles.productCard}>
      <View style={styles.productImageContainer}>
        {product.image_thumb ? (
          <Image source={{ uri: product.image_thumb }} style={styles.productImage} />
        ) : (
          <Text style={styles.productPlaceholderText}>👕</Text>
        )}
      </View>
      <View style={styles.productDetails}>
        {/* Hỗ trợ hiển thị tên dài có dấu 3 chấm chuẩn Webkit-box */}
        <Text numberOfLines={2} style={styles.productName}>
          {name}
        </Text>
        <View style={styles.priceRow}>
          <Text style={styles.productPrice}>{formatVND(price)}</Text>
          <Text style={styles.productOriginalPrice}>{formatVND(originalPrice)}</Text>
        </View>
        <TouchableOpacity style={styles.selectButton} onPress={() => onSelect(product)}>
          <Text style={styles.selectButtonText}>chốt sản phẩm này</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  productCard: {
    width: 220,
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#E5E7EB',
    marginRight: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04,
    shadowRadius: 3,
    elevation: 2,
  },
  productImageContainer: {
    height: 140,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  productImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  productPlaceholderText: {
    fontSize: 48,
  },
  productDetails: {
    padding: 14,
  },
  productName: {
    color: '#1F2937',
    fontSize: 13,
    fontWeight: '700',
    marginBottom: 6,
    height: 38,
    lineHeight: 18,
    ...Platform.select({
      web: {
        display: '-webkit-box',
        WebkitLineClamp: 2,
        WebkitBoxOrient: 'vertical',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      },
    }),
  },
  priceRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 10,
  },
  productPrice: {
    color: '#0d9488',
    fontSize: 14,
    fontWeight: '700',
  },
  productOriginalPrice: {
    color: '#9CA3AF',
    fontSize: 11,
    textDecorationLine: 'line-through',
    marginLeft: 8,
  },
  selectButton: {
    borderWidth: 1,
    borderColor: '#0d9488',
    borderRadius: 10,
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#FFFFFF',
  },
  selectButtonText: {
    color: '#0d9488',
    fontSize: 11,
    fontWeight: '700',
  },
});
