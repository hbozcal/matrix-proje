import asyncio
import requests
import config

async def download_matrix_media_bruteforce(access_token, mxc_server, media_id):
    loop = asyncio.get_event_loop()
    headers = {"Authorization": f"Bearer {access_token}"}
    
    url_new = f"{config.HOMESERVER}/_matrix/client/v1/media/download/{mxc_server}/{media_id}"
    url_legacy = f"{config.HOMESERVER}/_matrix/media/v3/download/{mxc_server}/{media_id}"
    
    def fetch_url(url):
        try:
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.content
            return r.status_code
        except Exception as e:
            return str(e)

    res_new = await loop.run_in_executor(None, fetch_url, url_new)
    if isinstance(res_new, bytes):
        return res_new
        
    print(f"[LOG] Yeni nesil Matrix API yanıt vermedi. Legacy yola düşülüyor...")
    
    res_legacy = await loop.run_in_executor(None, fetch_url, url_legacy)
    if isinstance(res_legacy, bytes):
        return res_legacy
        
    print(f"[-] Kritik Hata: Medya indirilemedi!")
    return None