import express from 'express';
import { connectMongoDB } from './database/mongo.connection';
import { redisManager } from './database/redis.connection';
import { MessageController } from './controllers/message.controller';
import { logger } from './shared/logger';

// Arka planda kuyruğu dinleyecek Worker'ı buraya ithal ederek tetikliyoruz
import './queue/message.worker'; 

const app = express();
const PORT = process.env.PORT || 3000;

// Gelen JSON isteklerini ayrıştırmak için Express middleware
app.use(express.json());

const messageController = new MessageController();

// WhatsApp/Matrix botunun mesajları göndereceği API adresi (Webhook Endpoint)
app.post('/api/v1/messages', (req, res) => messageController.receiveMessage(req, res));

async function startServer() {
  try {
    // 1. Redis Bağlantısını Başlat
    await redisManager.connect();

    // 2. MongoDB Bağlantısını Başlat
    const mongoUri = process.env.MONGO_URI || 'mongodb://localhost:27017/matrix_webhook_db';
    await connectMongoDB(mongoUri);

    // 3. Express HTTP Sunucusunu Dinlemeye Başla
    app.listen(PORT, () => {
      logger.info(`[Server] Uygulama ${PORT} portu üzerinde başarıyla başlatıldı.`);
    });

  } catch (error) {
    logger.error('[Server] Uygulama başlatılamadı, kritik hata:', error);
    process.exit(1);
  }
}

// Sistemi ateşle
startServer();