# system/

Files that live outside `$HOME` and need root to install. Nothing here is touched
unless you run `./install.sh --system`.

| Path | Installed to | Notes |
|------|--------------|-------|
| `packages/pacman.txt` | `pacman -S --needed` | official repo packages |
| `packages/aur.txt` | `yay`/`paru -S --needed` | AUR packages |
| `services.txt` | `systemctl enable --now` | Bluetooth, NetworkManager, TLP |
| `etc/tlp.conf` | `/etc/tlp.conf` | battery and AC power policy |
| `etc/modprobe.d/nvidia-power.conf` | `/etc/modprobe.d/` | **hardware specific**: NVIDIA runtime power management |
| `etc/modprobe.d/hid_apple.conf` | `/etc/modprobe.d/` | **hardware specific**: Apple keyboard Fn-key mode |

The two `modprobe.d` files only apply to specific hardware, so the installer skips
them unless you pass `--hardware`. Existing files are backed up next to the
original as `*.dotfiles-bak` before being replaced.
