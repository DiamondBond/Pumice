#!/bin/sh
# pumice-mode.sh [light|dark|toggle] [colour|grey]
# Switches window frames, panel, GTK theme (Adwaita / Adwaita-dark) and the desktop
# colour scheme, which Firefox and GTK4 apps follow. Bound to Ctrl+Shift+F5 by
# install.sh. The flavour (colour or grey window buttons) stays unless given.
# Anything else that should follow along goes in an executable
# ~/.config/pumice/on-mode-change, which gets "light" or "dark" as its argument.
mode=${1:-toggle}
cur=$(xfconf-query -c xfwm4 -p /general/theme)
case ${2:-$cur} in *grey) suf=-grey ;; *) suf= ;; esac
if [ "$mode" = toggle ]; then
  case $cur in Pumice-dark*) mode=light ;; *) mode=dark ;; esac
fi
case $mode in
  light) theme=Pumice$suf      gtk=Adwaita      scheme=default     dark=false icons=breeze ;;
  dark)  theme=Pumice-dark$suf gtk=Adwaita-dark scheme=prefer-dark dark=true  icons=breeze-dark ;;
  *) echo "usage: $0 [light|dark|toggle] [colour|grey]" >&2; exit 1 ;;
esac

# the panel's CSS import and menu icon point at this link
mkdir -p ~/.local/share/pumice
ln -sfn "$HOME/.themes/$theme" ~/.local/share/pumice/current

xfconf-query -c xfwm4 -p /general/theme -s $theme
xfconf-query -c xsettings -p /Net/ThemeName -s $gtk
xfconf-query -c xfce4-panel -p /panels/dark-mode -n -t bool -s $dark
gsettings set org.gnome.desktop.interface color-scheme $scheme
# KDE apps take icons from kdeglobals, not GTK; Adwaita lacks their icons and its
# symbolic ones stay dark on a dark window
command -v kwriteconfig6 >/dev/null && kwriteconfig6 --file kdeglobals --group Icons --key Theme $icons
hook=${XDG_CONFIG_HOME:-$HOME/.config}/pumice/on-mode-change
[ -x "$hook" ] && "$hook" "$mode" &
xfce4-panel -r
