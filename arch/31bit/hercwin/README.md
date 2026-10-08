# SDL Hercules 4.9.1 for Windows x64, cross-built with MinGW-w64

Work in progress (8 Oct 2026). Upstream builds Windows only with MSVC; this
builds Hyperion's own `_MSVC_` code paths with the MinGW-w64 compiler on Linux.

- `hyperion-4.9.1-mingw.patch` -- changes to SDL-Hercules-390/hyperion at
  tag Release_4.9.1 (guarded for MinGW).
- `Makefile`, `cflags.sh`, `compat.h`, `include/`, `telnet_pre.h` -- the
  build (copy into `<hyperion>/mingw/`, `make -C mingw`); the external
  packages crypto, decNumber, SoftFloat and telnet are rebuilt from their
  SDL GitHub repos for MinGW.

State: hercules.exe, the DLL set (hengine, hutil, hsys, hdasd, htape,
hdt*) and the utilities build. Under wine it starts, reads the VM/370 CE
configuration, opens the cckd disks and IPLs CP (that test copy stopped
with wait 17 -- a checkpoint of a copied pack, not yet looked at).
Not packaged or tested on real Windows yet; the user installed a 4.7
Windows binary meanwhile, so this is parked.
