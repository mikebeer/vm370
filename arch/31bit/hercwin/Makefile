# ===========================================================================
#  mingw/Makefile -- cross-build SDL Hercules for Windows x64 with MinGW-w64
#
#  Reproduces the MSVC DLL layout (msvc.makefile.includes/OBJ_CODE.msvc,
#  MODULES.msvc, MOD_RULES2.msvc) using GNU make + x86_64-w64-mingw32-gcc
#  and the _MSVC_ (Win32 API) code paths of Hercules.
#
#  Required variables (normally supplied by build-mingw.sh):
#    EXTLIB   dir containing libcrypto64.a libdecNumber64.a libSoftFloat64.a
#             libtelnet64.a libz.a  (MinGW builds of the external packages)
#    ZLIB_INC dir containing zlib.h / zconf.h
#    VERSION VERS_MAJ VERS_INT VERS_MIN VERS_BLD
# ===========================================================================

HERC      := $(abspath $(dir $(lastword $(MAKEFILE_LIST)))..)
CROSS     ?= x86_64-w64-mingw32-
CC        := $(CROSS)gcc
WINDRES   := $(CROSS)windres
STRIP     := $(CROSS)strip
O         ?= $(HERC)/mingw-build/obj
X         ?= $(HERC)/mingw-build/bin
MAX_CPU_ENGS ?= 64
OPTFLAGS  ?= -O2

DEFS := -D_MSVC_ -DWIN32 -D_WIN32 -D_WINNT -D_WIN32_WINNT=0x0600 \
        -DNTDDI_VERSION=0x06000000 -D_WIN32_IE=0x0700 -DWINVER=0x0600 \
        -D_AMD64_=1 -DWIN64 -D_WIN64 -D_MT -DHOST_ARCH=AMD64 \
        -D_CRT_SECURE_NO_DEPRECATE -D_CRT_NONSTDC_NO_DEPRECATE \
        -DFD_SETSIZE=1024 -DHAVE_SOCKLEN_T -DENABLE_IPV6 \
        -DHAVE_ZLIB -DHAVE_ZLIB_H -DMAX_CPU_ENGS=$(MAX_CPU_ENGS) \
        -DVERSION=\"$(VERSION)\" -DVERS_MAJ=$(VERS_MAJ) -DVERS_INT=$(VERS_INT) \
        -DVERS_MIN=$(VERS_MIN) -DVERS_BLD=$(VERS_BLD) \
        -DCUSTOM_BUILD_STRING=\"MinGW-w64\ cross-build\"

INCS := -include $(HERC)/mingw/compat.h -I$(HERC)/mingw/include -I$(HERC) \
        -I$(HERC)/crypto/include -I$(HERC)/decNumber/include \
        -I$(HERC)/SoftFloat/include -I$(HERC)/telnet/include -I$(ZLIB_INC)

CFLAGS := $(OPTFLAGS) -g0 -pipe -mcx16 -msse4.2 -mpclmul -maes \
          -fno-strict-aliasing -fwrapv -fno-common \
          -Wno-unknown-pragmas -Wno-attributes -Wno-incompatible-pointer-types \
          -Wno-builtin-declaration-mismatch $(EXTRA_CFLAGS) $(DEFS) $(INCS)

SYSLIBS := -lws2_32 -lmswsock -ladvapi32 -luser32 -lwinmm -liphlpapi \
           -ldbghelp -lpsapi -lshell32 -lole32 -lbcrypt -lnetapi32
EXTLIBS := -L$(EXTLIB) -lcrypto64 -ldecNumber64 -lSoftFloat64 -ltelnet64 -lz
LDFLAGS := -static -static-libgcc -Wl,--enable-auto-import $(EXTRA_LDFLAGS)
LDLIBS  := $(EXTLIBS) $(SYSLIBS)

# ---------------------------------------------------------------------------
#  Object groups (from OBJ_CODE.msvc)
# ---------------------------------------------------------------------------
hsys_OBJ   := hsys
hdasd_OBJ  := cache cckddasd cckdutil ckddasd cckddasd64 cckdutil64 ckddasd64 \
              dasdtab dasdutil fbadasd dasdutil64 fbadasd64 shared
htape_OBJ  := hetlib ftlib sllib w32stape
hdt3420_OBJ:= tapedev tapeccws awstape faketape hettape omatape scsitape scsiutil
tuntap_OBJ := tuntap w32ctca resolve
ctc_OBJ    := ctc_lcs ctc_ctci ctcadpt netsupp
hutil_OBJ  := codepage fthreads getopt hdl hostinfo hscutl hexdumpe logger \
              logmsg memrchr parser hthreads pttrace version hsocket w32util
crypto_OBJ := crypto
loadparm_OBJ := loadparm
hengine_OBJ:= archlvl assist bldcfg script cgibin channel chsc clock cmdtab \
              cmpsc_2012 cmpscdbg cmpscdct cmpscget cmpscmem cmpscput config \
              control cpu dat decimal dfp diagmssf diagnose dyn76 ecpsvm esame \
              external facility fillfnam float general1 general2 general3 \
              hbyteswp hconsole hdiagf18 history hsccmd hscemode hscpufun \
              hscloc hao hscmisc httpserv ieee impl inline io ipl loadmem losc \
              machchk machdep nnpa opcode panel pfpo plo qdio mpc hRexx hRexx_o \
              hRexx_r service scedasd scescsi sie skey sr stack tcpip timer \
              trace transact vector vm vmd250 vstore x75 xstore zvector \
              zvector2 zvector3

o = $(addprefix $(O)/,$(addsuffix .o,$(1)))

# ---------------------------------------------------------------------------
#  Device / feature modules (from MOD_RULES2.msvc)
# ---------------------------------------------------------------------------
dyncrypt_MOD  := dyncrypt crypto loadparm
dyngui_MOD    := dyngui
hdt1052c_MOD  := con1052c
hdt1403_MOD   := printer sockdev
hdt2703_MOD   := commadpt
hdt2880_MOD   := hchan
hdt3088_MOD   := $(ctc_OBJ) $(tuntap_OBJ)
hdt3270_MOD   := console
hdt3420_MOD   := $(hdt3420_OBJ)
hdt3505_MOD   := cardrdr sockdev
hdt3525_MOD   := cardpch sockdev
hdt3705_MOD   := comm3705
hdtdummy_MOD  := dummydev
hdteq_MOD     := hdteq
hdtptp_MOD    := ctc_ptp $(tuntap_OBJ) netsupp
hdtqeth_MOD   := qeth $(tuntap_OBJ)
hdttcph_MOD   := him $(tuntap_OBJ)
hdttcpnje_MOD := tcpnje $(tuntap_OBJ)
hdtzfcp_MOD   := zfcp

MODNAMES := dyncrypt dyngui hdt1052c hdt1403 hdt2703 hdt2880 hdt3088 hdt3270 \
            hdt3420 hdt3505 hdt3525 hdt3705 hdtdummy hdteq hdtptp hdtqeth \
            hdttcph hdttcpnje hdtzfcp

CORE_DLLS := hsys hutil hdasd htape hengine
DASD_UTILS := cckdcdsk cckdcomp cckddiag cckdswap cckdcdsk64 cckdcomp64 \
              cckddiag64 cckdswap64 dasdcat dasdconv dasdcopy dasdconv64 \
              dasdcopy64 convto64 cckdmap dasdinit dasdinit64 dasdisup \
              dasdload dasdload64 dasdls dasdpdsu dasdseq dasdser
TAPE_UTILS := hetget hetinit hetmap hetupd maketape tapecopy tapemap tapesplt
MISC_UTILS := dmap2hrc tfswap txt2card card2txt
ENG_UTILS  := tfprint
COPIES := ckd2cckd:dasdcopy cckd2ckd:dasdcopy fba2cfba:dasdcopy \
          cfba2fba:dasdcopy ckd2cckd64:dasdcopy64 cckd642ckd:dasdcopy64 \
          fba2cfba64:dasdcopy64 cfba642fba:dasdcopy64

ALL_DLLS := $(addprefix $(X)/,$(addsuffix .dll,$(CORE_DLLS) $(MODNAMES)))
ALL_EXES := $(addprefix $(X)/,$(addsuffix .exe,hercules herclin vmfplc2 \
              $(DASD_UTILS) $(TAPE_UTILS) $(MISC_UTILS) $(ENG_UTILS)))

.PHONY: all core hercules clean copies
all: $(ALL_DLLS) $(ALL_EXES) copies
core: $(addprefix $(X)/,$(addsuffix .dll,$(CORE_DLLS) $(MODNAMES))) $(X)/hercules.exe

$(O) $(X):
	mkdir -p $@

$(O)/%.o: $(HERC)/%.c | $(O)
	$(CC) $(CFLAGS) -c $< -o $@

# resource files
RCFLAGS := -I$(HERC) -DWIN32 -D_WIN32 -D_WIN64 -DWIN64 -DMAX_CPU_ENGS=$(MAX_CPU_ENGS) \
           -DVERSION=\\\"$(VERSION)\\\" -DVERS_MAJ=$(VERS_MAJ) -DVERS_INT=$(VERS_INT) \
           -DVERS_MIN=$(VERS_MIN) -DVERS_BLD=$(VERS_BLD) -D_MSVC_
$(O)/%.res.o: $(HERC)/%.rc | $(O)
	$(WINDRES) $(RCFLAGS) -i $< -o $@

PCH := $(O)/build_pch.o
RES_PROD := $(O)/hercprod.res.o
RES_DASD := $(O)/hercdasd.res.o
RES_TAPE := $(O)/herctape.res.o
RES_MISC := $(O)/hercmisc.res.o

# link helpers:  $(call linkdll,objs...,implibs...)
define LINKDLL
	$(CC) -shared -o $@ $(PCH) $(1) $(2) $(LDFLAGS) -Wl,--export-all-symbols -Wl,--exclude-libs,ALL -Wl,--out-implib,$(O)/lib$(basename $(notdir $@)).dll.a $(LDLIBS)
endef
define LINKEXE
	$(CC) -o $@ $(PCH) $(1) $(2) $(LDFLAGS) $(LDLIBS)
endef

IMP = $(addprefix $(O)/lib,$(addsuffix .dll.a,$(1)))

$(O)/libhsys.dll.a:    $(X)/hsys.dll
$(O)/libhutil.dll.a:   $(X)/hutil.dll
$(O)/libhdasd.dll.a:   $(X)/hdasd.dll
$(O)/libhtape.dll.a:   $(X)/htape.dll
$(O)/libhengine.dll.a: $(X)/hengine.dll
$(O)/libhdt3420.dll.a: $(X)/hdt3420.dll

$(X)/hsys.dll: $(PCH) $(call o,$(hsys_OBJ)) $(RES_PROD) | $(X)
	$(call LINKDLL,$(call o,$(hsys_OBJ)) $(RES_PROD),)
$(X)/hutil.dll: $(PCH) $(call o,$(hutil_OBJ)) $(RES_PROD) $(call IMP,hsys) | $(X)
	$(call LINKDLL,$(call o,$(hutil_OBJ)) $(RES_PROD),$(call IMP,hsys))
$(X)/hdasd.dll: $(PCH) $(call o,$(hdasd_OBJ)) $(RES_PROD) $(call IMP,hutil hsys) | $(X)
	$(call LINKDLL,$(call o,$(hdasd_OBJ)) $(RES_PROD),$(call IMP,hutil hsys))
$(X)/htape.dll: $(PCH) $(call o,$(htape_OBJ)) $(RES_PROD) $(call IMP,hutil hsys) | $(X)
	$(call LINKDLL,$(call o,$(htape_OBJ)) $(RES_PROD),$(call IMP,hutil hsys))
HENG_OBJS = $(call o,$(hengine_OBJ) w32ctca $(crypto_OBJ) $(loadparm_OBJ))
$(X)/hengine.dll: $(PCH) $(HENG_OBJS) $(RES_PROD) $(call IMP,hdasd htape hutil hsys) | $(X)
	$(call LINKDLL,$(HENG_OBJS) $(RES_PROD),$(call IMP,hdasd htape hutil hsys))

# device / feature modules
define MODRULE
$(X)/$(1).dll: $(PCH) $(call o,$($(1)_MOD)) $(RES_PROD) $(call IMP,hengine hutil hsys) | $(X)
	$$(call LINKDLL,$(call o,$($(1)_MOD)) $(RES_PROD),$(call IMP,hengine hutil hsys) $(2))
endef
$(foreach m,$(filter-out hdt3420,$(MODNAMES)),$(eval $(call MODRULE,$(m),)))
$(eval $(call MODRULE,hdt3420,$(call IMP,htape)))
$(X)/hdt3420.dll: $(call IMP,htape)

# executables
$(X)/hercules.exe: $(PCH) $(O)/bootstrap.o $(RES_PROD) $(call IMP,hengine hdasd hsys hutil) | $(X)
	$(call LINKEXE,$(O)/bootstrap.o $(RES_PROD),$(call IMP,hengine hdasd hsys hutil))
$(X)/herclin.exe: $(PCH) $(O)/herclin.o $(RES_PROD) $(call IMP,hengine hdasd hsys hutil) | $(X)
	$(call LINKEXE,$(O)/herclin.o $(RES_PROD),$(call IMP,hengine hdasd hsys hutil))
$(X)/vmfplc2.exe: $(PCH) $(O)/vmfplc2.o $(RES_TAPE) $(call IMP,htape hsys hutil hdt3420) | $(X)
	$(call LINKEXE,$(O)/vmfplc2.o $(RES_TAPE),$(call IMP,htape hsys hutil hdt3420))
$(X)/tapecopy.exe: $(PCH) $(O)/tapecopy.o $(O)/scsiutil.o $(RES_TAPE) $(call IMP,htape hsys hutil) | $(X)
	$(call LINKEXE,$(O)/tapecopy.o $(O)/scsiutil.o $(RES_TAPE),$(call IMP,htape hsys hutil))
$(X)/tfprint.exe: $(PCH) $(O)/tfprint.o $(RES_MISC) $(call IMP,hengine hsys hutil) | $(X)
	$(call LINKEXE,$(O)/tfprint.o $(RES_MISC),$(call IMP,hengine hsys hutil))

define EXERULE
$(X)/$(1).exe: $(PCH) $(O)/$(1).o $(2) $(call IMP,$(3)) | $(X)
	$$(call LINKEXE,$(O)/$(1).o $(2),$(call IMP,$(3)))
endef
$(foreach e,$(DASD_UTILS),$(eval $(call EXERULE,$(e),$(RES_DASD),hdasd hsys hutil)))
$(foreach e,$(filter-out tapecopy,$(TAPE_UTILS)),$(eval $(call EXERULE,$(e),$(RES_TAPE),htape hsys hutil)))
$(foreach e,$(MISC_UTILS),$(eval $(call EXERULE,$(e),$(RES_MISC),hsys hutil)))

copies: $(X)/dasdcopy.exe $(X)/dasdcopy64.exe
	@for p in $(COPIES); do cp -f $(X)/$${p#*:}.exe $(X)/$${p%%:*}.exe; done

clean:
	rm -rf $(O) $(X)
