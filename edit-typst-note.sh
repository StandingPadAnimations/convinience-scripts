#!/bin/bash

# If typst file doesn't exist, create it
# so the typst compiler isn't taken by surprise
if [ ! -f "$1" ]; then
	touch "$1"
fi

tmux new-session "nvim $1" \; \
	new-window "typst watch $1" \; \
	new-window "sleep 2 && zathura ${1%.typ}.pdf" \; \
	select-window -t:-2
