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
  [ $mode = dark ] && g='#4f4f4f' || g='#d8d8d8'
  dots="$(fg $g)● ● ●$r"
else
  dots="$(fg '#dab462')●$r $(fg '#71bb68')●$r $(fg '#da756c')●$r"
fi
swatches=
for k in bg line hover on dot dim text strong; do
  c=$(pm $k); [ -n "$c" ] && swatches="$swatches$(fg $c)██$r"
done

s=$(pm strong) m=$(pm dim) f=$(pm dot)
# the menu icon's ball beside the info, two half-block pixels per cell: a wave
# through it, faint above, strong below fading toward dim (too few pixels for
# the icon's half-tone band)
awk -v s="${s:-#e2e2e2}" -v m="${m:-#b4b4b4}" -v f="${f:-#4a4a4a}" '
function hex(h, i) { return index("0123456789abcdef", substr(tolower(h), i, 1)) - 1 }
function rgb(h, k) { return 16 * hex(h, 2 * k) + hex(h, 2 * k + 1) }
# colour of pixel x,y (of 12x12) into P[1..3], 4x4 supersampled; 0 if outside the ball
function px(x, y,   i, j, u, v, t, k, n) {
  P[1] = P[2] = P[3] = n = 0
  for (i = 0; i < 4; i++) for (j = 0; j < 4; j++) {
    u = x + (i + .5) / 4; v = y + (j + .5) / 4
    if ((u - 6) ^ 2 + (v - 6) ^ 2 > 25) continue
    n++; t = (u + 12 - v) / 24
    for (k = 1; k <= 3; k++)
      P[k] += v > 6 + 1.8 * sin((u - 6) * .75) ? rgb(s, k) * (1 - t) + rgb(m, k) * t : rgb(f, k)
  }
  for (k = 1; k <= 3; k++) P[k] = int(P[k] / (n ? n : 1) + .5)
  return n >= 8
}
{
  line = ""
  for (x = 0; x < 12; x++) {
    top = px(x, 2 * NR - 2); T1 = P[1]; T2 = P[2]; T3 = P[3]; bot = px(x, 2 * NR - 1)
    if (top && bot) line = line sprintf("\033[38;2;%d;%d;%d;48;2;%d;%d;%dm▀\033[0m", T1, T2, T3, P[1], P[2], P[3])
    else if (top)   line = line sprintf("\033[38;2;%d;%d;%dm▀\033[0m", T1, T2, T3)
    else if (bot)   line = line sprintf("\033[38;2;%d;%d;%dm▄\033[0m", P[1], P[2], P[3])
    else            line = line " "
  }
  print line, $0
}' <<EOF
  ${b}pumice$r ${d}·$r $mode ${d}·$r $flavour
  ${d}wm$r       $theme
  ${d}gtk$r      $gtk
  ${d}buttons$r  $dots
  ${d}panel$r    $swatches
  ${d}github.com/DiamondBond/Pumice$r
EOF
