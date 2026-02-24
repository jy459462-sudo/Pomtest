import os
import asyncio
from datetime import datetime
import logging

from pyrogram import Client, filters
from pyrogram.types import (
    Message, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    CallbackQuery
)
from pymongo import MongoClient

# ==================== CONFIGURATION ====================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Your Credentials
BOT_TOKEN = "7789945246:AAGNjyFnpsn5UyJnkrALw8S0EiGHC2zJSII"
API_ID = 6435225
API_HASH = "4e984ea35f854762dcde906dce426c2d"
MONGODB_URI = "mongodb+srv://ishantyadav708_db_user:JSOfdqSPeFp8uMOH@cluster0.1fnj10l.mongodb.net/?appName=Cluster0"
DB_NAME = "telegram_bot"
ADMIN_ID = 8386507312
START_IMAGE_URL = "https://files.catbox.moe/mtdlde.jpg"
DEMO_CHANNEL_LINK = "https://t.me/your_channel"
PROOF_CHANNEL_LINK = "https://t.me/your_channel"
SUPPORT_USERNAME = "@SUPPORT"  # Change this to your support username

# Initialize bot
app = Client(
    "procofile_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# Initialize MongoDB
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[DB_NAME]

# Collections
users_col = db['users']
premium_users_col = db['premium_users']
categories_col = db['categories']
contents_col = db['contents']
settings_col = db['settings']
admin_states_col = db['admin_states']

# Initialize settings
if not settings_col.find_one({'_id': 'qr_code'}):
    settings_col.insert_one({'_id': 'qr_code', 'file_id': None})

# States dictionary
admin_states = {}

# ==================== HELPER FUNCTIONS ====================
def is_premium(user_id):
    return premium_users_col.find_one({'user_id': user_id}) is not None

def is_admin(user_id):
    return user_id == ADMIN_ID

def get_main_keyboard():
    """2x2 Button Layout for Main Menu"""
    buttons = [
        [
            InlineKeyboardButton("💰 Get Premium", callback_data="get_premium"),
            InlineKeyboardButton("🎥 Demo Videos", callback_data="demo_videos")
        ],
        [
            InlineKeyboardButton("📢 Demo Channel", url=DEMO_CHANNEL_LINK),
            InlineKeyboardButton("✅ Proof", url=PROOF_CHANNEL_LINK)
        ],
        [
            InlineKeyboardButton("📞 Contact", callback_data="contact_support")
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def get_admin_keyboard():
    buttons = [
        [InlineKeyboardButton("📝 Add Category", callback_data="admin_add_category")],
        [InlineKeyboardButton("🗑️ Remove Category", callback_data="admin_remove_category")],
        [InlineKeyboardButton("🎬 Add Content", callback_data="admin_add_content")],
        [InlineKeyboardButton("🖼️ Change QR", callback_data="admin_change_qr")],
        [InlineKeyboardButton("👑 Add Premium User", callback_data="admin_add_premium")],
        [InlineKeyboardButton("👤 Remove Premium User", callback_data="admin_remove_premium")],
        [InlineKeyboardButton("📊 Stats", callback_data="admin_stats")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(buttons)

def get_welcome_text(first_name):
    return (
        f"👋 Welcome {first_name}!\n\n"
        "**Is Group me ye saara exclusive content milega 👇👇**\n\n"
        "• Desi Bhabhi\n"
        "• Mom-Son\n"
        "• Couple Videos\n"
        "• Hidden Cam\n"
        "• Instagram Viral Reels\n"
        "• Real Amateur Content\n"
        "• Dost ki Wife\n"
        "• Aur bohot kuch ⏩⏩\n\n"
        "**No Snaps – Pure Desi Video 😙**\n\n"
        "**50,000+ Rare Desi Videos 🎀**\n\n"
        "**Price :- ₹99/**-\n\n"
        "⚠️ **A BOT MADE BY @OTPSWALLAHBOT ** ⚠️"
    )

# ==================== START COMMAND ====================
@app.on_message(filters.command("start"))
async def start_command(client, message: Message):
    user_id = message.from_user.id
    
    # Save user
    users_col.update_one(
        {'user_id': user_id},
        {'$set': {
            'username': message.from_user.username,
            'first_name': message.from_user.first_name,
            'last_seen': datetime.now()
        }},
        upsert=True
    )
    
    # Send start image with welcome text
    await message.reply_photo(
        photo=START_IMAGE_URL,
        caption=get_welcome_text(message.from_user.first_name),
        reply_markup=get_main_keyboard()
    )

# ==================== ADMIN COMMAND ====================
@app.on_message(filters.command("admin"))
async def admin_command(client, message: Message):
    if not is_admin(message.from_user.id):
        await message.reply_text("❌ Unauthorized access!")
        return
    
    await message.reply_text(
        "👑 **Admin Panel**\n\nSelect an option:",
        reply_markup=get_admin_keyboard()
    )

# ==================== CALLBACK HANDLER ====================
@app.on_callback_query()
async def handle_callbacks(client, callback_query: CallbackQuery):
    data = callback_query.data
    user_id = callback_query.from_user.id
    message = callback_query.message
    first_name = callback_query.from_user.first_name
    
    try:
        # ========== CONTACT SUPPORT ==========
        if data == "contact_support":
            contact_text = (
                "📞 **Contact Support**\n\n"
                f"👤 **Username:** @{SUPPORT_USERNAME}\n\n"
                "Click the button below to message support:"
            )
            await message.edit_text(
                contact_text,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("💬 Message Support", url=f"https://t.me/{SUPPORT_USERNAME}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                ])
            )
        
        # ========== BACK TO MAIN MENU WITH START IMAGE ==========
        elif data == "back_to_main":
            # Delete current message
            await message.delete()
            # Send fresh start image
            await client.send_photo(
                chat_id=user_id,
                photo=START_IMAGE_URL,
                caption=get_welcome_text(first_name),
                reply_markup=get_main_keyboard()
            )
            # Clear any video viewing state
            if user_id in admin_states:
                del admin_states[user_id]
        
        # ========== GET PREMIUM WITH QR CODE ==========
        elif data == "get_premium":
            # Get QR code from database
            qr_data = settings_col.find_one({'_id': 'qr_code'})
            qr_file_id = qr_data.get('file_id') if qr_data else None
            
            caption = (
                "💰 **Get Premium Access**\n\n"
                "Pay ₹99 and get access to all premium content!\n\n"
                "**UPI ID:** yourname@okhdfcbank\n"
                "**Bank:** Account: XXXX-XXXX-XXXX\n\n"
                "📸 **Scan QR code below or send payment screenshot**"
            )
            
            # Delete current message
            await message.delete()
            
            # If QR exists, show image with caption
            if qr_file_id:
                await client.send_photo(
                    chat_id=user_id,
                    photo=qr_file_id,
                    caption=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📸 Send Screenshot", callback_data="send_payment")],
                        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                    ])
                )
            else:
                # If no QR, show text only
                await client.send_message(
                    chat_id=user_id,
                    text=caption,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📸 Send Screenshot", callback_data="send_payment")],
                        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                    ])
                )
        
        # ========== DEMO VIDEOS ==========
        elif data == "demo_videos":
            categories = list(categories_col.find())
            if not categories:
                await message.edit_text(
                    "📭 No categories available!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                    ])
                )
                return
            
            # Create 2x2 layout for categories if many
            buttons = []
            row = []
            for i, cat in enumerate(categories):
                # Check if category has demo videos
                has_demo = contents_col.find_one({'category': cat['name'], 'type': 'demo'})
                if has_demo:
                    row.append(InlineKeyboardButton(
                        cat['name'], 
                        callback_data=f"cat_demo_{cat['name']}"
                    ))
                    if len(row) == 2:  # 2 buttons per row
                        buttons.append(row)
                        row = []
            
            # Add remaining buttons
            if row:
                buttons.append(row)
            
            if not buttons:
                await message.edit_text(
                    "📭 No demo videos available!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💰 Get Premium", callback_data="get_premium")],
                        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                        [InlineKeyboardButton("🔙 Back", callback_data="back_to_main")]
                    ])
                )
                return
            
            # Add action buttons
            buttons.append([InlineKeyboardButton("💰 Get Premium", callback_data="get_premium")])
            buttons.append([InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")])
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="back_to_main")])
            
            await message.edit_text(
                "🎥 **Select Category**\n\nChoose a category to view demo videos:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        # ========== CATEGORY SELECTION FOR DEMO VIDEOS ==========
        elif data.startswith("cat_demo_"):
            cat_name = data.replace("cat_demo_", "")
            
            # Get demo videos for this category
            videos = list(contents_col.find({'category': cat_name, 'type': 'demo'}))
            
            if not videos:
                await message.edit_text(
                    f"📭 No demo videos in {cat_name}!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("💰 Get Premium", callback_data="get_premium")],
                        [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                        [InlineKeyboardButton("🔙 Back", callback_data="demo_videos")]
                    ])
                )
                return
            
            # Store current category and video list
            admin_states[user_id] = {
                'state': 'viewing_videos',
                'category': cat_name,
                'type': 'demo',
                'videos': videos,
                'index': 0
            }
            
            video = videos[0]
            
            # Create navigation buttons in 2x2 layout
            nav_buttons = []
            
            # First row - Navigation
            nav_row = []
            if len(videos) > 1:
                nav_row.append(InlineKeyboardButton("⏭️ Next", callback_data="next_video"))
            nav_buttons.append(nav_row)
            
            # Second row - Actions
            nav_buttons.append([
                InlineKeyboardButton("💰 Get Premium", callback_data="get_premium"),
                InlineKeyboardButton("📞 Contact", callback_data="contact_support")
            ])
            
            # Third row - Back
            nav_buttons.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="demo_videos")])
            
            await message.delete()
            await client.send_video(
                chat_id=user_id,
                video=video['file_id'],
                caption=f"🎥 **{cat_name} - Demo**\n\nVideo 1 of {len(videos)}",
                reply_markup=InlineKeyboardMarkup(nav_buttons)
            )
        
        # ========== NEXT VIDEO ==========
        elif data == "next_video":
            if user_id not in admin_states or admin_states[user_id].get('state') != 'viewing_videos':
                await message.delete()
                await client.send_photo(
                    chat_id=user_id,
                    photo=START_IMAGE_URL,
                    caption=get_welcome_text(first_name),
                    reply_markup=get_main_keyboard()
                )
                return
            
            state = admin_states[user_id]
            videos = state['videos']
            current_index = state['index']
            next_index = current_index + 1
            
            if next_index >= len(videos):
                next_index = 0
            
            state['index'] = next_index
            video = videos[next_index]
            
            # Create navigation buttons in 2x2 layout
            nav_buttons = []
            
            # First row - Navigation
            nav_row = []
            if len(videos) > 1:
                nav_row.append(InlineKeyboardButton("⏭️ Next", callback_data="next_video"))
            nav_buttons.append(nav_row)
            
            # Second row - Actions
            nav_buttons.append([
                InlineKeyboardButton("💰 Get Premium", callback_data="get_premium"),
                InlineKeyboardButton("📞 Contact", callback_data="contact_support")
            ])
            
            # Third row - Back
            nav_buttons.append([InlineKeyboardButton("🔙 Back to Categories", callback_data="demo_videos")])
            
            await message.delete()
            await client.send_video(
                chat_id=user_id,
                video=video['file_id'],
                caption=f"🎥 **{state['category']} - Demo**\n\nVideo {next_index + 1} of {len(videos)}",
                reply_markup=InlineKeyboardMarkup(nav_buttons)
            )
        
        # ========== SEND PAYMENT ==========
        elif data == "send_payment":
            await message.edit_text(
                "📸 **Send Payment Screenshot**\n\n"
                "Please forward/upload your payment screenshot.\n"
                "Admin will verify and activate premium.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📞 Contact Support", callback_data="contact_support")],
                    [InlineKeyboardButton("🔙 Cancel", callback_data="get_premium")]
                ])
            )
            admin_states[user_id] = {'state': 'waiting_payment'}
        
        # ========== ADMIN PANEL OPTIONS ==========
        elif data == "admin_add_category" and is_admin(user_id):
            await message.edit_text(
                "➕ **Add Category**\n\nSend me category name:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
                ])
            )
            admin_states[user_id] = {'state': 'add_category'}
        
        elif data == "admin_remove_category" and is_admin(user_id):
            categories = list(categories_col.find())
            if not categories:
                await message.edit_text(
                    "❌ No categories to remove!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
                    ])
                )
                return
            
            # Create 2x2 layout for categories
            buttons = []
            row = []
            for i, cat in enumerate(categories):
                row.append(InlineKeyboardButton(
                    f"❌ {cat['name']}", 
                    callback_data=f"remove_cat_{cat['name']}"
                ))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            
            if row:
                buttons.append(row)
            
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
            
            await message.edit_text(
                "🗑️ **Select Category to Remove:**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        elif data.startswith("remove_cat_") and is_admin(user_id):
            cat_name = data.replace("remove_cat_", "")
            categories_col.delete_one({'name': cat_name})
            contents_col.delete_many({'category': cat_name})
            
            await message.edit_text(
                f"✅ Category '{cat_name}' removed!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
                ])
            )
        
        elif data == "admin_add_content" and is_admin(user_id):
            categories = list(categories_col.find())
            if not categories:
                await message.edit_text(
                    "❌ No categories! Add one first.",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("➕ Add Category", callback_data="admin_add_category")],
                        [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
                    ])
                )
                return
            
            # Create 2x2 layout for categories
            buttons = []
            row = []
            for i, cat in enumerate(categories):
                row.append(InlineKeyboardButton(
                    cat['name'], 
                    callback_data=f"content_cat_{cat['name']}"
                ))
                if len(row) == 2:
                    buttons.append(row)
                    row = []
            
            if row:
                buttons.append(row)
            
            buttons.append([InlineKeyboardButton("🔙 Back", callback_data="admin_back")])
            
            await message.edit_text(
                "📝 **Select Category for Content:**",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        
        elif data.startswith("content_cat_") and is_admin(user_id):
            cat_name = data.replace("content_cat_", "")
            
            await message.edit_text(
                f"Category: **{cat_name}**\n\n"
                "Select content type:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🎥 Demo", callback_data=f"type_demo_{cat_name}"),
                     InlineKeyboardButton("💎 Premium", callback_data=f"type_premium_{cat_name}")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_add_content")]
                ])
            )
        
        elif data.startswith("type_") and is_admin(user_id):
            parts = data.split('_')
            content_type = parts[1]
            cat_name = parts[2]
            
            admin_states[user_id] = {
                'state': 'add_videos',
                'category': cat_name,
                'type': content_type,
                'videos': []
            }
            
            await message.edit_text(
                f"📤 **Send Videos**\n\n"
                f"Category: {cat_name}\n"
                f"Type: {content_type}\n\n"
                f"Send videos now.\n"
                f"Type /done when finished.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Done", callback_data="content_done")],
                    [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
                ])
            )
        
        elif data == "content_done" and is_admin(user_id):
            if user_id in admin_states:
                videos = admin_states[user_id].get('videos', [])
                for vid in videos:
                    contents_col.insert_one(vid)
                del admin_states[user_id]
            
            await message.edit_text(
                "✅ Videos added successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add More", callback_data="admin_add_content")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
                ])
            )
        
        elif data == "admin_change_qr" and is_admin(user_id):
            await message.edit_text(
                "🖼️ **Upload New QR Code**\n\nSend me the QR code image:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
                ])
            )
            admin_states[user_id] = {'state': 'change_qr'}
        
        elif data == "admin_add_premium" and is_admin(user_id):
            await message.edit_text(
                "👑 **Add Premium User**\n\nSend me user ID:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
                ])
            )
            admin_states[user_id] = {'state': 'add_premium'}
        
        elif data == "admin_remove_premium" and is_admin(user_id):
            await message.edit_text(
                "👤 **Remove Premium User**\n\nSend me user ID:",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔙 Cancel", callback_data="admin_back")]
                ])
            )
            admin_states[user_id] = {'state': 'remove_premium'}
        
        elif data == "admin_stats" and is_admin(user_id):
            total_users = users_col.count_documents({})
            total_premium = premium_users_col.count_documents({})
            total_categories = categories_col.count_documents({})
            total_demo = contents_col.count_documents({'type': 'demo'})
            total_premium_videos = contents_col.count_documents({'type': 'premium'})
            
            stats = (
                f"📊 **Bot Statistics**\n\n"
                f"👥 Total Users: {total_users}\n"
                f"👑 Premium Users: {total_premium}\n"
                f"📁 Categories: {total_categories}\n"
                f"🎬 Demo Videos: {total_demo}\n"
                f"💎 Premium Videos: {total_premium_videos}"
            )
            
            await message.edit_text(
                stats,
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Refresh", callback_data="admin_stats")],
                    [InlineKeyboardButton("🔙 Back", callback_data="admin_back")]
                ])
            )
        
        elif data == "admin_back" and is_admin(user_id):
            await message.edit_text(
                "👑 **Admin Panel**\n\nSelect an option:",
                reply_markup=get_admin_keyboard()
            )
        
        # ========== APPROVE/REJECT PAYMENT ==========
        elif data.startswith("approve_"):
            target_id = int(data.split("_")[1])
            premium_users_col.update_one(
                {'user_id': target_id},
                {'$set': {'user_id': target_id, 'approved_at': datetime.now()}},
                upsert=True
            )
            
            await message.edit_text(f"✅ Approved user {target_id}")
            
            try:
                await client.send_message(
                    target_id,
                    "✅ **Payment Approved!**\n\nYou now have premium access!"
                )
            except:
                pass
        
        elif data.startswith("reject_"):
            target_id = int(data.split("_")[1])
            await message.edit_text(f"❌ Rejected user {target_id}")
            
            try:
                await client.send_message(
                    target_id,
                    "❌ **Payment Rejected**\n\nContact admin for details."
                )
            except:
                pass
        
        await callback_query.answer()
    
    except Exception as e:
        logger.error(f"Error in callback: {e}")
        await callback_query.answer("Error occurred!", show_alert=True)

# ==================== MESSAGE HANDLER ====================
@app.on_message(filters.private & ~filters.command(["start", "admin", "done"]))
async def handle_messages(client, message: Message):
    user_id = message.from_user.id
    
    # Payment proof
    if user_id in admin_states and admin_states[user_id].get('state') == 'waiting_payment':
        caption = f"💳 **New Payment Proof**\n\n"
        caption += f"**User ID:** `{user_id}`\n"
        caption += f"**Username:** @{message.from_user.username or 'None'}\n"
        caption += f"**Name:** {message.from_user.first_name}\n"
        
        if message.photo:
            await client.send_photo(
                ADMIN_ID,
                photo=message.photo.file_id,
                caption=caption,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                    ]
                ])
            )
            await message.reply_text("✅ Proof sent to admin! You'll be notified once verified.")
        elif message.text:
            caption += f"\n**UTR/Message:** {message.text}"
            await client.send_message(
                ADMIN_ID,
                caption,
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{user_id}"),
                        InlineKeyboardButton("❌ Reject", callback_data=f"reject_{user_id}")
                    ]
                ])
            )
            await message.reply_text("✅ UTR sent to admin! You'll be notified once verified.")
        else:
            await message.reply_text("❌ Please send a screenshot/photo or UTR number.")
            return
        
        del admin_states[user_id]
    
    # Admin: Add Category
    elif is_admin(user_id) and user_id in admin_states:
        state = admin_states[user_id].get('state')
        
        if state == 'add_category':
            cat_name = message.text.strip()
            if categories_col.find_one({'name': cat_name}):
                await message.reply_text("❌ Category already exists! Try another name:")
                return
            
            categories_col.insert_one({
                'name': cat_name,
                'created_at': datetime.now()
            })
            
            await message.reply_text(
                f"✅ Category '{cat_name}' added successfully!",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("➕ Add Another", callback_data="admin_add_category")],
                    [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
                ])
            )
            del admin_states[user_id]
        
        elif state == 'add_videos':
            if message.video:
                video_data = {
                    'file_id': message.video.file_id,
                    'category': admin_states[user_id]['category'],
                    'type': admin_states[user_id]['type'],
                    'uploaded_at': datetime.now()
                }
                admin_states[user_id]['videos'].append(video_data)
                await message.reply_text(f"✅ Video saved! ({len(admin_states[user_id]['videos'])} so far)")
            else:
                await message.reply_text("❌ Please send a video file.")
        
        elif state == 'change_qr':
            if message.photo:
                settings_col.update_one(
                    {'_id': 'qr_code'},
                    {'$set': {'file_id': message.photo.file_id}},
                    upsert=True
                )
                await message.reply_text(
                    "✅ QR Code updated successfully!",
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
                    ])
                )
                del admin_states[user_id]
            else:
                await message.reply_text("❌ Please send an image file.")
        
        elif state == 'add_premium':
            try:
                target_id = int(message.text.strip())
                premium_users_col.update_one(
                    {'user_id': target_id},
                    {'$set': {'user_id': target_id, 'added_at': datetime.now()}},
                    upsert=True
                )
                await message.reply_text(f"✅ User {target_id} added to premium!")
                
                try:
                    await client.send_message(
                        target_id,
                        "🎉 **Premium Access Granted!**\n\nYou now have premium access!"
                    )
                except:
                    pass
                
                del admin_states[user_id]
            except ValueError:
                await message.reply_text("❌ Invalid user ID! Please enter numbers only.")
        
        elif state == 'remove_premium':
            try:
                target_id = int(message.text.strip())
                result = premium_users_col.delete_one({'user_id': target_id})
                if result.deleted_count > 0:
                    await message.reply_text(f"✅ User {target_id} removed from premium!")
                else:
                    await message.reply_text("❌ User not found in premium list!")
                del admin_states[user_id]
            except ValueError:
                await message.reply_text("❌ Invalid user ID! Please enter numbers only.")

# ==================== DONE COMMAND ====================
@app.on_message(filters.command("done"))
async def done_command(client, message: Message):
    user_id = message.from_user.id
    
    if user_id in admin_states and admin_states[user_id].get('state') == 'add_videos':
        videos = admin_states[user_id].get('videos', [])
        for vid in videos:
            contents_col.insert_one(vid)
        
        await message.reply_text(
            f"✅ {len(videos)} videos added successfully!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Add More", callback_data="admin_add_content")],
                [InlineKeyboardButton("🔙 Admin Panel", callback_data="admin_back")]
            ])
        )
        del admin_states[user_id]
    else:
        await message.reply_text("❌ No active video upload session.")

# ==================== RUN BOT ====================
if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Procofile Bot Started!")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print("=" * 50)
    app.run()
