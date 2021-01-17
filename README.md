# TeleLoad
A Telegram bot to keep track of the South African Loadshedding schedule

# Instructions

1. You need to have created a Telegram bot and obtained its secret token.
2. You need to have set up the basics of Google Cloud like having set up a billing account.
3. You need to have the GCloud SDK installed, and you need to have logged in.
4. For each file that begins with "boilerplate_", you need to create a new file with the same name without the word "boilerplate_" and fill in all your details at the top.
5. Run setup_and_deploy/setup.ps1
6. Run setup_and_deploy/deploy.ps1
7. Create 5 tables that align with models.py. Upload LoadShedding.csv as a database called LoadTime. Add the following to UpdateLog:
   
   csgo 2021.01.07

   overall 2021-01-11 18:21:25.310445

   load 2021-01-17 04:00:16.846161

8. You should be done. You can now message your bot with "/start".
