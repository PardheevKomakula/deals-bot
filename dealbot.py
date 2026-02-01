import asyncio
import re
from telethon import TelegramClient, events, types
from telethon.sessions import StringSession
from keep_alive import keep_alive  # <--- CRITICAL IMPORT

# ================= CONFIGURATION ZONE ================= #
API_ID = 30367926
API_HASH = '3f846e3ad96fcc9dc7c4121cc94a1542'

# 1. SESSION STRING
STRING_SESSION = '1BVtsOHsBuwmPNJ-CdahXCEYNyC1Bhn6QX3kvm0OY4YpsP1auf70y3OLdbZ6YNkU8iIgzjeV0viyzk5_qlyzNhM9h8vjwiUcAlTdl1IbdKtiS2vz_PIf2XMtKKmdk1uC_J6U-FhxkoAmSJEH2lZbVIVA8h7Mvdv8-nP2omQzdfET2xsAq8PVqKr2Kv8fHPvWd2Ohn6e_Vzk1wXAWFDKcwSONJyUgYlA1NZkrqx2-dQ9oY7T4qysp0h44_rZV7ivWkyoa2jaCSAqjZoKAvZpHctxD5ibpT6ZZZ8AJUQqS2Tv8AX25TeXqZAmP-hBLO_d2aE9viovk6yTbvP9p6EdgHMxmDU0Q7pwM=-r-5q-dj8QLfMDpcYxIDV3SyAEUDhY1vAOtFL010G3IBSLJhQiqb6cP0UJmwn6JI0Oh8_x4c_Izap8U0vqgvUtAsLsJPfb_U7Ax5J1UqI_osRlfS8='

# 2. CHANNELS TO SPY ON
SOURCE_CHANNELS = [
    -1002486045463, 
    -1001886505541, 
    '@Mens_fashion_only', 
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

async def get_profit_link(original_url):
    """
    Sends the link to ExtraPe Bot and waits for the monetized reply.
    """
    # A. Fast Path: Amazon (Do it ourselves, no bot needed)
    if "amazon" in original_url or "amzn" in original_url:
        return convert_amazon_tag(original_url)

    # B. Slow Path: Flipkart/Myntra (Ask the Bot)
    try:
        async with client.conversation(EXTRAPE_BOT, timeout=20) as conv: 
            await conv.send_message(original_url)
            response = await conv.get_response()
            
            # --- THE FIX IS HERE ---
            # Now we look for extp.in OR fkrt.co OR bit.ly
            found_urls = re.findall(r'(https?://(?:extp\.in|fkrt\.co|bit\.ly)/\S+)', response.text)
            
            if found_urls:
                return found_urls[0] # Success!
            else:
                print(f"⚠️ Bot sent text but no link found: {response.text[:30]}...")
                return original_url
                
    except Exception as e:
        print(f"⚠️ Bot Conversation Error: {e}")
        return original_url

def convert_amazon_tag(url):
    new_url = re.sub(r"tag=[^&]+", f"tag={AMAZON_TAG}", url)
    if "tag=" not in new_url:
        sep = "&" if "?" in new_url else "?"
        new_url = f"{new_url}{sep}tag={AMAZON_TAG}"
    return new_url

@client.on(events.NewMessage(chats=SOURCE_CHANNELS))
async def handler(event):
    msg_text = event.message.text or ""
    
    # 1. FIND LINK
    urls = re.findall(r'(https?://\S+)', msg_text)
    if not urls:
        return

    print(f"💰 Detected Deal: {urls[0]}")
    target_link = urls[0]
    
    # 2. CONVERT
    final_link = await get_profit_link(target_link)
    
    # 3. REPOST
    if final_link != target_link:
        print(f"✅ Converted to: {final_link}")
    else:
        print("⚠️ Posting original link (Conversion skipped)")
        
    new_caption = msg_text.replace(target_link, final_link)
    footer = (
    "\n\n🚀 **Join @deals_store_cheap**"
    "\n🔍 **Looking for something?** DM me: @Pardhu130806"
)
    
    # HANDLE MEDIA (Safe Mode)
    media_to_send = None
    if event.message.media:
        if isinstance(event.message.media, (types.MessageMediaPhoto, types.MessageMediaDocument)):
            media_to_send = event.message.media

    try:
        await client.send_message(
            MY_CHANNEL,
            new_caption + footer,
            file=media_to_send,
            link_preview=True
        )
        print("🚀 Posted Successfully!")
    except Exception as e:
        print(f"❌ Error Posting: {e}")

print("🕵️ Deal Mirror is Active...")

# --- KEEP ALIVE SERVER ---
# Remove '#' below when deploying to Render
keep_alive() 
# -------------------------

client.start()
client.run_until_disconnected()

