import axios from 'axios';
import fs from 'fs';
import path from 'path';
import { v4 as uuidv4 } from 'uuid';

const TEMP_DIR = path.join(process.cwd(), 'temp_audio');

// Geçici klasör yoksa oluştur
if (!fs.existsSync(TEMP_DIR)) {
    fs.mkdirSync(TEMP_DIR, { recursive: true });
}

/**
 * WhatsApp sunucularından ses dosyasını indirir.
 * @param mediaUrl İndirilecek medyanın URL'i
 * @param bearerToken WhatsApp Graph API Token'ı
 * @returns İndirilen dosyanın tam yolu
 */
export async function downloadAudio(mediaUrl: string, bearerToken: string): Promise<string> {
    const tempFilePath = path.join(TEMP_DIR, `${uuidv4()}.ogg`);

    try {
        console.log(`[⬇️ İNDİRİLİYOR] Ses dosyası alınıyor: ${mediaUrl}`);
        
        const response = await axios({
            method: 'GET',
            url: mediaUrl,
            responseType: 'stream',
            headers: {
                Authorization: `Bearer ${bearerToken}`,
            },
            timeout: 15000, // 15 saniye timeout (Büyük dosyalar veya takılmalar için)
        });

        const writer = fs.createWriteStream(tempFilePath);
        response.data.pipe(writer);

        return new Promise((resolve, reject) => {
            writer.on('finish', () => resolve(tempFilePath));
            writer.on('error', (err) => {
                fs.unlink(tempFilePath, () => {}); // Hata olursa yarım kalan dosyayı sil
                reject(err);
            });
        });
    } catch (error: any) {
        console.error(`[❌ İNDİRME HATASI] Dosya çekilemedi: ${error.message}`);
        throw new Error('Ses dosyası indirilemedi.');
    }
}