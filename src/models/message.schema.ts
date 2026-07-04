import { Schema, model, Document } from 'mongoose';

export interface IMessage extends Document {
  messageId: string;
  eventId: string;
  roomId: string;
  platform: 'whatsapp' | 'matrix';
  sender: { id: string; name: string; phone?: string };
  type: string;
  content: Record<string, any>; // Esnek içerik yapısı
  status: { sent: boolean; delivered: boolean; read: boolean };
  timestamp: Date;
  aiMetadata?: {
    embedding?: number[]; // [Pro] AI Semantic Search için Vektör Verisi
    summary?: string;
    tags?: string[];
  };
}

const MessageSchema = new Schema<IMessage>(
  {
    messageId: { type: String, required: true },
    eventId: { type: String, required: true },
    roomId: { type: String, required: true },
    platform: { type: String, enum: ['whatsapp', 'matrix'], required: true },
    sender: {
      id: { type: String, required: true },
      name: { type: String, required: true },
      phone: { type: String }
    },
    type: { type: String, required: true },
    content: { type: Schema.Types.Mixed }, // Görsel, text, dosya vb. dinamik tutulur
    status: {
      sent: { type: Boolean, default: true },
      delivered: { type: Boolean, default: false },
      read: { type: Boolean, default: false }
    },
    timestamp: { type: Date, required: true },
    aiMetadata: {
      embedding: { type: [Number] },
      summary: { type: String },
      tags: [{ type: String }]
    }
  },
  { timestamps: true }
);

// Pro İndeksleme Stratejisi
MessageSchema.index({ roomId: 1, timestamp: -1 }); // Odaya göre geçmişi hızlı çekmek için bileşik indeks
MessageSchema.index({ 'sender.id': 1 }); // Kullanıcı bazlı analizler için
MessageSchema.index({ messageId: 1, eventId: 1 }, { unique: true }); // DB seviyesinde son güvenlik kilidi

export const MessageModel = model<IMessage>('Message', MessageSchema, 'messages');  