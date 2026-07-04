import mongoose from 'mongoose';
import { logger } from '../shared/logger';

export const connectMongoDB = async (uri: string): Promise<void> => {
  const options = {
    connectTimeoutMS: 10000,
    socketTimeoutMS: 45000,
    maxPoolSize: 50, // Pro ayarı: Aynı anda işlenebilecek bağlantı sayısı artırıldı
  };

  mongoose.connection.on('connected', () => logger.info('[MongoDB] Bağlantı başarılı.'));
  mongoose.connection.on('disconnected', () => logger.warn('[MongoDB] Bağlantı koptu!'));

  try {
    await mongoose.connect(uri, options);
  } catch (error) {
    logger.error('[MongoDB] Başlangıç bağlantı hatası, uygulama sonlandırılıyor.', error);
    process.exit(1);
  }
};