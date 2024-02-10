#!/bin/bash

set -u

CATS=($(awk -F . '{print $1}' tags | grep -E '^.' | sort | uniq))

VALS=($(zenity --title TAGGER --text=TAGS --forms $(for CAT in ${CATS[*]} ; do
    echo --add-combo=${CAT^^} --combo-values=?\|$(sort tags | uniq | grep -E "^${CAT}([.]|$)" | sed -r -e 's/^[^.]*.//g' | tr '\n' '|' | tr [[:lower:]] [[:upper:]])
done) --add-entry='...' | tr ' ' '-' | tr [[:upper:]] [[:lower:]] | tr '|' ' '))

echo ${VALS[*]}
for c in $(seq 0 ${#VALS}) ; do
    
    eval VAL=\${VALS[$c]}
    if [ ${c} -gt ${#VALS} ] ; then
		echo -n amo${VAL}re
	else
		eval CAT=\${CATS[$c]}
		if [ ${VAL} = '?' ] ; then
			echo -n "${CAT}|"
		elif [ ${VAL} != '-' ] ; then
			echo -n "${CAT}.${VAL}|"
		fi
	fi
done
echo
