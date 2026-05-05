#!/bin/bash
# Запускаем бота в фоне
python main.py &
# Запускаем доктора на переднем плане (чтобы контейнер не упал)
python run_doctor.py --watch
