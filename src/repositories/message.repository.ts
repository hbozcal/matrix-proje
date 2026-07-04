import { IMessage, MessageModel } from '../models/message.schema';
import { logger } from '../shared/logger';

export class MessageRepository {
  async upsertMessage(data: Partial<IMessage>): Promise<IMessage> {
    const startTime = Date.now();
    
    // İşlemciyi yormamak için lean() veya new: true kullanımı yönetimi
    const result = await MessageModel.findOneAndUpdate(
      { messageId: data.messageId, eventId: data.eventId },
      { $set: data },
      { upsert: true, new: true }
    ).exec();

    logger.info('[MongoDB] Mesaj Kaydedildi', {
      messageId: result.messageId,
      duration: `${Date.now() - startTime}ms`
    });

    return result;
  }
}