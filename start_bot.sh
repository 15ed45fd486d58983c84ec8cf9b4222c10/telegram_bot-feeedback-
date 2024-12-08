prisma generate
prisma migrate dev --name init
python app/interfaces/telegram_bot/bot.py
