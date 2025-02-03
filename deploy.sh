#!/bin/bash
rsync -avz -e 'ssh -i /home/markos/.ssh/id_rsa_ch' --delete apografi_sync*.py psped_sync*.py apografi_check*.py count_distinct.py requirements.txt src wsgi.py ypes-backend:flask
ssh -o "IdentitiesOnly=yes" -i /home/markos/.ssh/id_rsa_ch ypes-backend ypes-backend 'source ~/flask/venv/bin/activate && pip install -r ~/flask/requirements.txt'
ssh oper@lola 'sudo supervisorctl reload'
