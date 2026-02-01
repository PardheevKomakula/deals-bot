import asyncio
import re
import requests
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from keep_alive import keep_alive  # <--- UNCOMMENT THIS ONLY ON RENDER

# ================= CONFIGURATION ZONE ================= #
API_ID = 30367926
API_HASH = '3f846e3ad96fcc9dc7c4121cc94a1542'

# 1. SESSION STRING
STRING_SESSION = '1BVtsOHsBu7wUxFUcqrXfEX58GOrBdVlNqyiIXynUAkqwdvRJyKtDgWVXW7U7ABCOtd0CI6PhTCx0bjCwuI2oUkGakafbDlkxvdhtVCW5CNSQ6z7pgeZpg-4OttAwinGD5qvJ1vtc3z10Q72Gz1h_g-De0HF_MvefNOUEpCRumH-rnNB-IfowpQwBNmgyC6PSFarLjoNG3iUs1f_PhUvAbNNHo-TIwPAFqjp8oyecDU7SkKkzYjkpSaCmfi30bxq4rmBx453QL1_SBcNFE7_CD9B5UqZGiuFPxGf9WxOfhrBiOdpwzoCz9o_DPi2VjclgktOce1C5vN1zEDRsKoNfZI2cOuDNWKQ='

# 2. CHANNELS TO SPY ON
SOURCE_CHANNELS = [
    -1002486045463,
    -1001886505541,
    '@Mens_fashion_only',
    '@iamprasadtech',
    '@CKoffers',
    '@techglaredeals',
    -1001331753715,
    -1001289031146,
    -1001559259623
]

# 3. YOUR CHANNEL
MY_CHANNEL = 'deals_store_cheap'

# 4. EXTRAPE BOT USERNAME 
EXTRAPE_BOT = '@ExtraPeBot'

# 5. AMAZON FALLBACK TAG
AMAZON_TAG = 'pardheev-21'
# ====================================================== #

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)

# --- ENGINE: THE UNSHORTENER ---
def unshorten_url(url):
    """
    Follows redirects (bit.ly -> myntra) to find the REAL store link.
    Crucial for fixing '0 Earning' errors.
    """
    try:
        session = requests.Session()
        # Fake a real browser so Amazon/Myntra don't block us
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Allow up to 5 redirects
        response = session.get(url, allow_redirects=True, headers=headers, timeout=10)
        return response.url
    except Exception as e:
        print(f"⚠️ Unshorten Failed for {url}: {e}")
        return url

# --- ENGINE: THE CONVERTER ---
async def get_profit_link(original_url):
    # 1. Unshorten first (Reveal the true link)
    real_url = unshorten_url(original_url)
    print(f"🔗 Real URL: {real_url}")

    # 2. Fast Path: Amazon (Local Conversion)
    if "amazon" in real_url or "amzn" in real_url:
        return convert_amazon_tag(real_url)

    # 3. Slow Path: ExtraPe Bot (Flipkart, Myntra, Ajio)
    try:
        async with client.conversation(EXTRAPE_BOT, timeout=15) as conv:
            await conv.send_message(real_url) 
            response = await conv.get_response()
            
            # Find the new link (extp.in OR fkrt.co OR bit.ly)
            found_urls = re.findall(r'(https?://(?:extp\.in|fkrt\.co|bit\.ly|amzn\.to)/\S+)', response.text)
            
            if found_urls:
                return found_urls[0]
            else:
                print(f"⚠️ Bot replied but no link: {response.text[:50]}...")
                return original_url # Fail safe: post original
                
    except asyncio.TimeoutError:
        print("⚠️ ExtraPe Bot timed out (Too slow).")
        return original_url
    except Exception as e:
        print(f"⚠️ Bot Error: {e}")
        return original_url

def convert_amazon_tag(url):
    # Removes old tag, adds yours
    new_url = re.sub(r"tag=[^&]+", f"tag={AMAZON_TAG}", url)
    if "tag=" not in new_url:
        sep = "&" if "?" in new_url else "?"
        new_url = f"{new_url}{sep}tag={AMAZON_TAG}"
    return new_url

# --- ENGINE: THE STYLER ---
def format_message(original_text, new_link):
    """
    Beautifies the message. Adds headers and cleans up the link.
    """
    # 1. Remove the old link from text
    # (Regex finds http links and replaces them with an empty string temporarily)
    text_no_link = re.sub(r'https?://\S+', '', original_text).strip()
    
    # 2. Create a clean new message
    formatted_msg = (
        f"⚡ **FLASH DEAL ALERT** ⚡\n\n"
        f"{text_no_link}\n\n"
        f"🛒 **Buy Now:** {new_link}\n\n"
        f"━━━━━━━━━━━━━━━━━\n"
        f"🚀 **Join @deals_store_cheap**\n"
        f"🔍 **Need help?** DM: @Pardhu130806"
    )
    return formatted_msg

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    msg_text = event.message.text or ""
    
    # 1. FIND LINK (Regex to find any URL)
    urls = re.findall(r'(https?://\S+)', msg_text)
    if not urls:
        # Silently ignore messages without links (No print spam)
        return

    print(f"\n💰 Deal Detected! Processing...")
    original_link = urls[0]
    
    # 2. CONVERT
    final_link = await get_profit_link(original_link)
    
    if final_link == original_link:
        print("⚠️ Could not monetize. Posting original.")
    else:
        print(f"✅ Monetized: {final_link}")

    # 3. FORMAT
    # We don't just replace; we rebuild the message to look pretty
    final_message = format_message(msg_text, final_link)
    
    # 4. SEND (Safe Mode)
    # Only send media if it exists and is supported
    media_to_send = None
    if event.message.media:
        if isinstance(event.message.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
            media_to_send = event.message.media

    try:
        await client.send_message(
            MY_CHANNEL,
            final_message,
            file=media_to_send,
            link_preview=True
        )
        print("🚀 Posted to Channel!")
    except Exception as e:
        print(f"❌ Upload Error: {e}")

print("💎 The Perfect Deal Bot is Running...")

# --- KEEP ALIVE SERVER ---
# Remove '#' below when deploying to Render
keep_alive()
# -------------------------

client.start()
client.run_until_disconnected()
