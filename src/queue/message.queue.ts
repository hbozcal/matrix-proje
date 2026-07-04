import { Queue } from 'bullmq';

export const messageSaveQueue = new Queue('MessageSaveQueue', {
  // Dışarıdan client vermek yerine, sadece adresi veriyoruz. Kendi ioredis'ini kuracak.
  connection: { host: 'localhost', port: 6379 }, 
  defaultJobOptions: {
    attempts: 3, 
    backoff: { type: 'exponential', delay: 2000 }, 
    removeOnComplete: true, 
  }
});