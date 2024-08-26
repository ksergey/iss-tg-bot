#!/bin/bash

echo "Uninstalling bot"
echo ""
echo "* Stopping service"
systemctl --user stop iss-tg-bot.service
echo "* Removing unit file"
rm ${HOME}/.config/systemd/user/iss-tg-bot.service
echo "* Removing enviroment"
rm -rf ${HOME}/iss-tg-bot-env
echo "Done"
