import { redisManager } from '../database/redis.connection';
import { messageSaveQueue } from '../queue/message.queue';
import { logger } from '../shared/logger';

export class MessageService {
  /**
   * Mesaj Geldi -> Redis Check -> Queue Push akışını yönetir.
   */
  async processIncomingMessage(rawMessage: any): Promise<{ success: boolean; message: string }> {
    try {
      const messageId = String(rawMessage.messageId).trim();
      
      if (!messageId) {
        return { success: false, message: 'Validation Error: messageId eksik.' };
      }

      // 1. REDIS DUPLICATE KONTROLÜ (O(1) Karmaşıklığı - Çok Hızlı)
      const redisKey = `msg_cache:${messageId}`;
      const isNew = await redisManager.setIfNotExists(redisKey);
      
      if (!isNew) {
        logger.info(`[Service] Mükerrer mesaj reddedildi, DB'ye gidilmedi. ID: ${messageId}`);
        return { success: true, message: 'Mükerrer (Duplicate) mesaj atlandı.' };
      }

      // 2. VERİYİ NORMALİZE ET
      const normalizedData = this.normalize(rawMessage);

      // 3. KUYRUĞA AT (Non-Blocking)
      // Sistemin cevap verme süresini milisaniyelere düşürür çünkü veritabanını beklemiyoruz.
      await messageSaveQueue.add('save_message', normalizedData);
      
      logger.info(`[Service] Mesaj başarıyla kuyruğa alındı. ID: ${messageId}`);
      return { success: true, message: 'Mesaj işleme alındı.' };

    } catch (error) {
      logger.error('[Service] Akış hatası:', error);
      return { success: false, message: 'İç Sunucu Hatası' };
    }
  }

  private normalize(raw: any): any {
    return {
      messageId: raw.messageId,
      eventId: raw.eventId,
      roomId: raw.roomId,
      platform: raw.platform || 'whatsapp',
      sender: {
        id: raw.sender?.id || 'unknown',
        name: raw.sender?.name || 'User',
      },
      type: raw.type || 'text',
      content: raw.content || {},
      timestamp: raw.timestamp ? new Date(raw.timestamp) : new Date()
    };
  }
}