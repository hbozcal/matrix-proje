import { Request, Response } from 'express';
import { MessageService } from '../services/message.service';
import { logger } from '../shared/logger';

// Repository importunu ve injection işlemini kaldırdık, sadece servisi çağırıyoruz.
const messageService = new MessageService();

export class MessageController {
  
  public async receiveMessage(req: Request, res: Response): Promise<void> {
    try {
      const rawMessage = req.body;
      
      logger.info('[Controller] Yeni bir webhook isteği alındı.');

      const result = await messageService.processIncomingMessage(rawMessage);

      if (!result.success) {
        res.status(400).json({ error: result.message });
        return;
      }

      res.status(202).json({ message: result.message });
      
    } catch (error) {
      logger.error('[Controller] İstek işlenirken hata oluştu:', error);
      res.status(500).json({ error: 'İç Sunucu Hatası' });
    }
  }
}