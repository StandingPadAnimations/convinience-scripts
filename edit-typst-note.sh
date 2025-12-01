#!/bin/bash

# If PDF file already exists, we don't
# need to wait as long to make sure it
# exists. We still wait a little bit though
# for reflex purposes
if [ ! -f "$1" ]; then
	touch "$1"
fi

tmux new-session "nvim $1" \; \
	new-window "typst watch $1" \; \
	new-window "sleep 2 && zathura ${1%.typ}.pdf" \; \
	select-window -t:-2
