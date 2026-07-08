import React from 'react';
import { StyleSheet, ScrollView, View, Platform } from 'react-native';
import ProductCard from './ProductCard';

export default function ProductCarousel({ products, onSelect }) {
  if (!products || products.length === 0) return null;

  return (
    <View style={styles.carouselWrapper}>
      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={Platform.OS === 'web'}
        contentContainerStyle={styles.productCarouselContent}
        style={styles.productCarousel}
      >
        {products.map((prod) => (
          <ProductCard
            key={prod.id || prod.product_id}
            product={prod}
            onSelect={onSelect}
          />
        ))}
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  carouselWrapper: {
    marginLeft: 40,
    marginTop: 8,
    maxWidth: '100%',
    overflow: 'hidden',
  },
  productCarousel: {
    flexDirection: 'row',
    width: '100%',
  },
  productCarouselContent: {
    paddingBottom: 8,
  },
});
