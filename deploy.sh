#!/bin/bash
rsync -avz --delete apografi_sync*.py psped_sync*.py apografi_check*.py count_distinct.py run_sdad_sync.sh requirements.txt src wsgi.py lola:ypes-backend
ssh lola 'source ~/ypes-backend/venv/bin/activate && pip install -r ~/ypes-backend/requirements.txt'
ssh oper@lola 'sudo supervisorctl reload'
