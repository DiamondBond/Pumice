#!/bin/sh
# pumice-info.sh: a small showcase of the current Pumice setup, for screenshots.
# Needs a truecolor terminal.
theme=$(xfconf-query -c xfwm4 -p /general/theme 2>/dev/null)
gtk=$(xfconf-query -c xsettings -p /Net/ThemeName 2>/dev/null)
css=$HOME/.local/share/pumice/current/panel.css
case $theme in Pumice-dark*) mode=dark ;; Pumice*) mode=light ;; *) mode="not active" ;; esac
case $theme in *-grey) flavour=grey ;; *) flavour=colour ;; esac

fg() { h=${1#\#}; printf '\033[38;2;%d;%d;%dm' 0x$(echo $h | cut -c1-2) 0x$(echo $h | cut -c3-4) 0x$(echo $h | cut -c5-6); }
pm() { sed -n "s/^@define-color pm_$1 \(#[0-9a-f]*\);/\1/p" "$css" 2>/dev/null; }
r=$(printf '\033[0m') b=$(printf '\033[1m') d=$(printf '\033[2m')

# window buttons as they look on a focused window: minimize, maximize, close
if [ $flavour = grey ]; then
  [ $mode = dark ] && g='#4f4f4f' || g='#e6e6e6'
  dots="$(fg $g)● ● ●$r"
else
  dots="$(fg '#f4bf4f')●$r $(fg '#61c554')●$r $(fg '#ec6a5e')●$r"
fi
swatches=
for k in bg line hover on dot dim text strong; do
  c=$(pm $k); [ -n "$c" ] && swatches="$swatches$(fg $c)██$r"
done

s=$(pm strong); c=$(fg "${s:-#e2e2e2}")   # the clover in the panel's strongest colour
paste -d' ' - - <<EOF
$c  ▄▄▄  ▄▄▄  $r
  ${b}pumice$r ${d}·$r $mode ${d}·$r $flavour
$c ████  ████ $r
  ${d}wm$r       $theme
$c ▀▀▀▀▄▄▀▀▀▀ $r
  ${d}gtk$r      $gtk
$c ▄▄▄▄▀▀▄▄▄▄ $r
  ${d}buttons$r  $dots
$c ████  ████ $r
  ${d}panel$r    $swatches
$c  ▀▀▀  ▀▀▀  $r
  ${d}github.com/DiamondBond/Pumice$r
EOF
