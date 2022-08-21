## AyWeigh

A discord bot for running weight-loss challenges.

### Overview

AyWeigh is a Django application. This provides a few useful features, mainly: ORM and admin. 

### Pre-requisites

The requirements for running the bot are getting a bot token and joining it to a server.

#### Bot Token

1. Login to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Go to the [Applications](https://discord.com/developers/applications) page and click `New Application`.
3. In the sidebar, click the Bot tab, click `Add Bot`, then press `Yes, do it`.
4. Ensure the toggle for `MESSAGE CONTENT INTENT` is enabled. Make sure to save changes to the bot.
5. To get the bot token, click the `Reset Token` button near the top of the page. Enter MFA if required.
6. Once the token is visible, copy it to somewhere secure (like 1password or a secrets manager). **Keep this token private.**

#### Joining The Bot

1. After getting your bot token, click on the `OAuth2` tab in your application's portal.
2. Click `Add Redirect`, enter `localhost:8000`
3. For scopes, select `bot` and `applications.commands`
4. For bot permissions, select:
   - `Manage Roles`
   - `Send Messages`
   - `Create Public Threads`
   - `Send Messages in Threads`
   - `Manage Messages`
   - `Manage Threads`
   - `Embed Links`
   - `Attach Files`
   - `Read Message History`
   - `Add Reactions`
   - `Use Slash Commands`
5. Next, click on the URL Generator in the sidebar under OAuth2 and select the same settings as above for scopes and permissions
6. Copy the generated URL at the bottom, and navigate to it in a browser. Select the server you'd like to join it to, and finish the process.
7. Once complete, the bot should appear in your selected server.

### Running The Bot

Make sure you've got the dependencies installed (typically in a virtualenv):

```shell
python -m pip install -r requirements.txt
```

The bot runs as two components, the bot itself, and a django application running the admin which doesn't need to run all the time.

In development, the following commands should be run simultaneously from the root of the project:

```shell
python manage.py runserver  # Runs the django admin and any other endpoints
```

```shell
BOT_TOKEN=<token_value> python manage.py run_bot  # Runs the discord bot
```
