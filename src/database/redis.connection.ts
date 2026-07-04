import Redis from 'ioredis';
import { logger } from '../shared/logger';

class RedisManager {
  public client: Redis;

  constructor() {
    // ioredis bağlantısı ve BullMQ için zorunlu ayar
    this.client = new Redis(process.env.REDIS_URL || 'redis://localhost:6379', {
      maxRetriesPerRequest: null 
    });
    
    this.client.on('error', (err) => logger.error('[Redis] Bağlantı Hatası:', err));
    this.client.on('connect', () => logger.info('[Redis] Başarıyla bağlanıldı.'));
  }

  public async connect() {
    // ioredis otomatik olarak bağlanır, mevcut index.ts kodumuz hata vermesin diye boş bıraktık
  }

  /**
   * Atomic Duplicate Check: Aynı mesaj ID'si varsa false, yoksa true döner.
   */
  public async setIfNotExists(key: string, expirationSeconds: number = 86400): Promise<boolean> {
    // ioredis sözdizimi ile NX (sadece yoksa yaz) ve EX (saniye cinsinden süre) ayarı
    const result = await this.client.set(key, '1', 'EX', expirationSeconds, 'NX');
    return result === 'OK';
  }
}

export const redisManager = new RedisManager();