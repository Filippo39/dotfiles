#!/usr/bin/env bash
killall -q polybar

# For wait until the process is down
# Cerca con UID i processi plybar (-x exac matching) e finchè non è stato chiuso allora attende
while pgrep -u $UID -x polybar >/dev/null; do sleep 1; done

# Launch bar 1
polybar example 2>&1 | tee -a /tmp/polybar.log & disown

if type "xrandr"; then
  for m in $(xrandr --query | grep " connected" | cut -d" " -f1); do
    echo $m
    MONITOR=$m polybar --reload example &
  done
else
  polybar --reload example &
fi
