#!/bin/bash
# Requires PCRE-enabled grep
#set -x
DIR="${HOME}/rift-xml-firsts-parser"
cd ${DIR}
OLD=$(ls ${DIR} | grep -oP "Rift_Discoveries.*zip")
OLDDATE=$(echo ${OLD} | grep -oP "\d{4}-\d{1,2}-\d{1,2}")
TODAY=$(date +"%Y-%-m-%-d")
EXIT=99
DATE=${TODAY}
TRIES=0
# The Web server this lives on has historically been odd. For example just because
# a file is listed on the index page does not mean that it is there.
# So we just start with today's date and go backwards in time until a file
# is found, or we give up, or we find the one we already have
until [ $EXIT == 0 ] || [ $TRIES -gt 31 ] || [ "${DATE}" == "${OLDDATE}" ]; do
        curl -Os -f http://webcdn.triongames.com/addons/assets/Rift_Discoveries_${DATE}.zip
        EXIT=$?
        if [ ${EXIT} -ne 0 ]; then
                ((TRIES++))
                DATE=$(date +"%Y-%-m-%-d" -d "${DATE} - 1 day")
        fi
done
if [ "${DATE}" != "${OLDDATE}" ]; then
        [ -e "${OLD}" ] && rm ${OLD}
        nice ionice -c3 nocache unzip -oq Rift_Discoveries_${DATE}.zip
        chmod o-w *.xml
        nice ionice -c3 nocache ${DIR}/parse.py
#        nice nocache ${DIR}/parseall.pl
fi
