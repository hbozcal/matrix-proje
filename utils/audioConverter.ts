import ffmpeg from 'fluent-ffmpeg';
import path from 'path';

/**
 * OGG/OPUS vb. ses dosyasını MP3 formatına çevirir.
 * @param inputPath Orijinal dosyanın yolu
 * @returns Dönüştürülmüş MP3 dosyasının yolu
 */
export async function convertToMp3(inputPath: string): Promise<string> {
    const outputPath = inputPath.replace(path.extname(inputPath), '.mp3');

    console.log(`[🔄 DÖNÜŞTÜRÜLÜYOR] Format uyarlanıyor: ${inputPath} -> MP3`);

    return new Promise((resolve, reject) => {
        ffmpeg(inputPath)
            .toFormat('mp3')
            .on('end', () => {
                resolve(outputPath);
            })
            .on('error', (err) => {
                console.error(`[❌ FFmpeg HATASI] Dönüştürme başarısız: ${err.message}`);
                reject(err);
            })
            .save(outputPath);
    });
}