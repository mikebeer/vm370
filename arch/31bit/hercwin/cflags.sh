# sourced by build scripts: common compiler flags
HERC=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
CC=${CC:-x86_64-w64-mingw32-gcc}
VFLAGS="-DVERSION=\"$VERSION\" -DVERS_MAJ=$VERS_MAJ -DVERS_INT=$VERS_INT -DVERS_MIN=$VERS_MIN -DVERS_BLD=$VERS_BLD"
CFLAGS="-O2 -g0 -pipe -include $HERC/mingw/compat.h -I$HERC/mingw/include -I$HERC \
 -I$HERC/crypto/include -I$HERC/decNumber/include -I$HERC/SoftFloat/include -I$HERC/telnet/include \
 -I$ZLIB_INC \
 -D_MSVC_ -DWIN32 -D_WIN32 -D_WINNT -D_WIN32_WINNT=0x0600 -DNTDDI_VERSION=0x06000000 -D_WIN32_IE=0x0700 -DWINVER=0x0600 \
 -D_AMD64_=1 -DWIN64 -D_WIN64 -D_MT -DHOST_ARCH=AMD64 -D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE \
 -DFD_SETSIZE=1024 -DHAVE_SOCKLEN_T -DENABLE_IPV6 -DHAVE_ZLIB -DHAVE_ZLIB_H \
 $VFLAGS -fno-strict-aliasing -fwrapv -Wno-unknown-pragmas -Wno-attributes"
