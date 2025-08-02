# AJ Trading Academy Discord Bot

A Discord bot for the AJ Trading Academy with welcome message functionality, onboarding call booking, and automatic role assignment.

## Features

- **Persistent Welcome Message**: Welcome message persists across bot restarts and updates
- **Calendly Integration**: Direct link to Calendly for booking calls
- **Automatic Role Assignment**: Assigns member roles after 5 minutes of booking
- **Modular Commands**: Commands organized in the `cmds` folder
- **Slash Commands**: `/setup`, `/refresh`, and `/help_admin` commands for administrators
- **Environment Variables**: Secure configuration using .env files
- **Security System**: Owner-only access and guild authorization checks

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create Environment File**:
   ```bash
   cp env.example .env
   ```

3. **Configure Environment Variables**:
   Edit the `.env` file with your values:
   ```env
   TOKEN=your_discord_bot_token_here
   GUILD_ID=123456789
   MEMBER_ROLE_ID=123456789
   WELCOME_CHANNEL_ID=123456789
   CALENDLY_LINK=https://calendly.com/your-calendly-link
   ```

4. **Bot Permissions**:
   Make sure your bot has the following permissions:
   - Send Messages
   - Use Slash Commands
   - Manage Roles
   - Read Message History
   - Add Reactions

## Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `TOKEN` | ✅ | Discord bot token | - |
| `GUILD_ID` | ✅ | Discord server ID | - |
| `MEMBER_ROLE_ID` | ✅ | Member role ID | - |
| `WELCOME_CHANNEL_ID` | ✅ | Welcome channel ID | - |
| `CALENDLY_LINK` | ✅ | Calendly booking link | - |
| `ROLE_ASSIGNMENT_DELAY` | ❌ | Minutes to wait before role assignment | 5 |
| `CHECK_INTERVAL` | ❌ | Seconds between role checks | 30 |

## Security System

The bot includes a comprehensive security system:

- **Owner IDs**: Hardcoded owner user IDs for special access
- **Guild Authorization**: Commands only work in the specified guild
- **Admin Permissions**: All commands require Administrator permissions
- **DM Protection**: Commands cannot be used in DMs
- **Authorization Checks**: Multiple layers of security validation

## Usage

### Commands

- `/setup` - Set up the initial welcome message in the welcome channel (Admin only)
- `/refresh` - Refresh the welcome message in the welcome channel (Admin only)
- `/help_admin` - List all admin commands and their descriptions (Admin only)

### How it Works

1. **Persistent Welcome Message**: The bot automatically creates/updates a persistent welcome message in the specified channel
2. **Button Interaction**: When users click the "Book Your Onboarding Call" button
3. **Ephemeral Response**: Users receive an ephemeral message with Calendly booking link
4. **Automatic Role Assignment**: After 5 minutes, users automatically receive the member role
5. **Persistence**: All data is stored in JSON files and persists between bot restarts

### Data Storage

The bot creates two JSON files:
- `welcome_message.json` - Stores the persistent welcome message ID and channel ID
- `user_data.json` - Stores user booking information and role assignment status

## File Structure

```
├── main.py              # Main bot file
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── env.example         # Example environment file
├── .env                # Your environment variables (create this)
├── cmds/               # Commands folder
│   ├── __init__.py     # Package init
│   ├── setup.py        # Setup command
│   ├── refresh.py      # Refresh command
│   └── help.py         # Help command
├── welcome_message.json # Welcome message data (created automatically)
└── user_data.json      # User data (created automatically)
```

## Running the Bot

```bash
python main.py
```

## Customization

- **Welcome Message**: Edit the message content in `main.py`
- **Ephemeral Message**: Edit the message content in `main.py` in the `handle_onboarding_button` function
- **Role Assignment Time**: Change `ROLE_ASSIGNMENT_DELAY` in your `.env` file
- **Calendly Link**: Update `CALENDLY_LINK` in your `.env` file
- **Welcome Channel**: Update `WELCOME_CHANNEL_ID` in your `.env` file
- **Owner IDs**: Update `OWNER_USER_IDS` in `main.py` for special access

## Troubleshooting

- **Commands not syncing**: Make sure the bot has the `applications.commands` scope
- **Role assignment not working**: Check that the bot has the "Manage Roles" permission and the role ID is correct
- **Button not responding**: Ensure the bot has the necessary intents enabled
- **Environment variables not loading**: Make sure your `.env` file is in the same directory as `main.py`
- **Welcome message not appearing**: Check that `WELCOME_CHANNEL_ID` is correct and the bot has permission to send messages in that channel
- **Unauthorized access**: Make sure you're in the correct guild and have Administrator permissions 