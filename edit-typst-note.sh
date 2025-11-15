#!/bin/bash

tmux new-session "nvim $1" \; \
	new-window "typst watch $1" \; \
	new-window "sleep 5 && zathura ${1%.typ}.pdf" \; \
	select-window -t:-2
