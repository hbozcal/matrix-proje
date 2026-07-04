import winston from 'winston';
import path from 'path';

// Logların kaydedileceği dizin
const logDir = 'logs';

export const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || 'info',
  format: winston.format.combine(
    winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
    winston.format.errors({ stack: true }),
    winston.format.json() // Logların makine okunabilir (JSON) olması raporlama için kritiktir
  ),
  defaultMeta: { service: 'message-service' },
  transports: [
    // 1. Hataları (Error) ayrı bir dosyada tut (Sadece level: 'error' olanlar)
    new winston.transports.File({ 
      filename: path.join(logDir, 'error.log'), 
      level: 'error' 
    }),
    
    // 2. Tüm logları (Info, Warn, Error) genel bir dosyada tut
    new winston.transports.File({ 
      filename: path.join(logDir, 'combined.log') 
    }),
    
    // 3. Geliştirme (Console) ortamı için renklendirilmiş okunabilir format
    new winston.transports.Console({
      format: winston.format.combine(
        winston.format.colorize(),
        winston.format.printf(({ timestamp, level, message, ...metadata }) => {
          // Eğer ek veri (metadata) varsa, metnin sonuna ekle
          const metaString = Object.keys(metadata).length && metadata.service !== 'message-service' 
            ? JSON.stringify(metadata) 
            : '';
          return `[${timestamp}] ${level}: ${message} ${metaString}`;
        })
      )
    })
  ]
});

// Eğer uygulama çökerse (Uncaught Exception) loglayıp dosyaya yazar
logger.exceptions.handle(
  new winston.transports.File({ filename: path.join(logDir, 'exceptions.log') })
);