import { Worker } from 'bullmq';
import { MessageRepository } from '../repositories/message.repository';
import { logger } from '../shared/logger';

const messageRepo = new MessageRepository();

export const messageWorker = new Worker('MessageSaveQueue', async job => {
  try {
    const messageData = job.data;
    await messageRepo.upsertMessage(messageData);
  } catch (error: any) {
    logger.error(`[Worker] İşlem başarısız oldu (Job ID: ${job.id})`, error.message);
    throw error;
  }
}, { 
  // Burada da dışarıdan client vermek yerine doğrudan adresi veriyoruz
  connection: { host: 'localhost', port: 6379 },
  concurrency: 10 
});