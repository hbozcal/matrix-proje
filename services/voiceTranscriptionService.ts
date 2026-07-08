import OpenAI from 'openai';
import fs from 'fs';

// OpenAI yapılandırması (Kendi API anahtarını .env'den al)
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY, 
});

/**
 * Ses dosyasını STT (Whisper) modeli ile metne dönüştürür.
 * @param audioPath İşlenecek ses dosyasının yolu
 * @returns Sesin metin hali (Transkript)
 */
export async function transcribeAudio(audioPath: string): Promise<string> {
    console.log(`[🗣️ STT BAŞLADI] Ses dosyası metne çevriliyor...`);
    
    try {
        const response = await openai.audio.transcriptions.create({
            file: fs.createReadStream(audioPath),
            model: 'whisper-1',
            language: 'tr', // Türkçe ağırlıklıysa belirtmek kaliteyi ve hızı artırır
            response_format: 'text'
        });

        return response as unknown as string; // text formatında istediğimiz için string döner
    } catch (error: any) {
        console.error(`[❌ STT HATASI] Transkripsiyon başarısız: ${error.message}`);
        throw new Error('Yapay zeka sesi metne dönüştüremedi.');
    }
}