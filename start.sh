#!/bin/bash 
#
#  Sample script to start Sprint View with Wiki page as a source. 
#
#  Save Wiki data file if it exists. 
unset SPRINTVIEW_PATH

#mv ./project_data .//project_data.bak 2>/dev/null || true

#
#  App token, no need to use your personal Gitlab account token.
#
export SPRINTVIEW_TOKEN=bBzt3zHyiMczmRXd6adm

#
#  Use this conversion table for developers names/login_id.
#
export SPRINTVIEW_DEVELOPERS='{ \
    "Hugh":    "Hugh",          \
    "Andy":   "Andy",       \
    "Angela":  "Angela",        \
    "Cara":     "Cara",         \
    "Matt":      "Matt",        \
    "Kaleb": "Kaleb",           \
    "Joseph":    "Joseph",      \
}'


export SPRINTVIEW_PATH="./project_data"
#
# Start Sprint View server in debug mode. 
#
python sprintview.py runserver 0.0.0.0:8000


#
#  Connect to server at browser with http://localhost:8000
#
