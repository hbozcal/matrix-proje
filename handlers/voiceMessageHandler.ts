import fs from 'fs';
import { downloadAudio } from '../utils/audioDownloader';
import { convertToMp3 } from '../utils/audioConverter';
import { transcribeAudio } from '../services/voiceTranscriptionService';

/**
 * Gelen WhatsApp sesli mesajını yakalar ve tam bir iş akışından geçirir.
 * @param mediaUrl WhatsApp medyasının URL'i
 * @param token WhatsApp API Token
 * @returns Çözümlenmiş metin
 */
export async function handleVoiceMessage(mediaUrl: string, token: string): Promise<string | null> {
    let originalAudioPath: string | null = null;
    let mp3AudioPath: string | null = null;

    try {
        // 1. İndir
        originalAudioPath = await downloadAudio(mediaUrl, token);

        // 2. Dönüştür
        mp3AudioPath = await convertToMp3(originalAudioPath);

        // 3. Metne Çevir
        const transcript = await transcribeAudio(mp3AudioPath);
        
        console.log(`[✅ BAŞARILI] Sesli mesaj çözümlendi: "${transcript}"`);
        
        return transcript;

    } catch (error) {
        console.error('[⚠️ İŞLEM İPTAL EDİLDİ] Sesli mesaj akışında kritik hata:', error);
        return null; // Sistemin geri kalanının çökmemesi için null dönüyoruz
    } finally {
        // 4. TEMİZLİK (Clean-up) - Ne olursa olsun geçici dosyaları diskten sil
        if (originalAudioPath && fs.existsSync(originalAudioPath)) {
            fs.unlinkSync(originalAudioPath);
        }
        if (mp3AudioPath && fs.existsSync(mp3AudioPath)) {
            fs.unlinkSync(mp3AudioPath);
        }
        console.log('[🧹 TEMİZLİK] Geçici ses dosyaları sunucudan silindi.');
    }
}