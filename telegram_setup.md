# Telegram Setup Guide for Arbitrum Presale Bot

## Step 1: Create a Telegram Bot

1. **Open Telegram** and search for `@BotFather`
2. **Start a chat** with BotFather
3. **Send the command**: `/newbot`
4. **Follow the prompts**:
   - Enter a name for your bot (e.g., "My Presale Bot")
   - Enter a username for your bot (must end with 'bot', e.g., "my_presale_bot")
5. **Copy the bot token** that BotFather gives you (looks like: `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

## Step 2: Get Your Chat ID

### Method 1: Using @userinfobot
1. Search for `@userinfobot` in Telegram
2. Start a chat with it
3. Send any message
4. It will reply with your chat ID (a number like `123456789`)

### Method 2: Using @RawDataBot
1. Search for `@RawDataBot` in Telegram
2. Start a chat with it
3. Send any message
4. Look for the `"id"` field in the response

### Method 3: Using the API directly
1. Send a message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Look for the `"id"` field in the response

## Step 3: Configure Your .env File

Add these lines to your `.env` file:

```env
# Telegram Configuration
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

**Example:**
```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

## Step 4: Test Your Setup

1. **Start your bot** with `python3 main.py`
2. **Check your Telegram** for the startup notification
3. **If you receive the message**, your setup is working!

## Notifications You'll Receive

The bot will send you notifications for:

- 🚀 **Bot Startup**: When the bot starts monitoring
- 📋 **Presale Start**: When the presale begins
- 🔄 **Buy Attempts**: When trying to buy tokens
- ✅ **Buy Success**: When purchase is successful
- ❌ **Buy Failures**: When transactions fail
- ⛽ **Gas Warnings**: When gas prices are too high
- ⚠️ **Balance Warnings**: When wallet balance is low
- 🏁 **Presale End**: When presale concludes
- 🚨 **Errors**: When something goes wrong
- 🛑 **Bot Shutdown**: When the bot stops

## Troubleshooting

### No notifications received?
1. **Check your bot token** - make sure it's correct
2. **Check your chat ID** - make sure it's a number
3. **Start a chat with your bot** - send it a message first
4. **Check the logs** - look for Telegram-related errors

### Bot token invalid?
- Make sure you copied the entire token from BotFather
- Don't include any extra spaces or characters

### Chat ID not working?
- Make sure you're using your personal chat ID, not a group ID
- Try getting your chat ID again using one of the methods above

### Bot not responding?
- Make sure you've started a conversation with your bot
- Send `/start` to your bot first

## Security Notes

- **Keep your bot token private** - don't share it publicly
- **The bot token can be regenerated** if compromised
- **Chat ID is not sensitive** - it's just your user ID

## Advanced Features

### Group Notifications
To send notifications to a group:
1. Add your bot to the group
2. Get the group's chat ID (usually negative numbers)
3. Use that as your `TELEGRAM_CHAT_ID`

### Multiple Recipients
To send to multiple people:
1. Create a group with just you and your bot
2. Use the group's chat ID
3. Add other people to the group

### Custom Messages
You can modify the notification messages in `telegram_notifier.py` to customize the format and content. 