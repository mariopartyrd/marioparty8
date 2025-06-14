#!/usr/bin/env python3

###
# Generates build files for the project.
# This file also includes the project configuration,
# such as compiler flags and the object matching status.
#
# Usage:
#   python3 configure.py
#   ninja
#
# Append --help to see available options.
###

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List

from tools.project import (
    Object,
    ProjectConfig,
    calculate_progress,
    generate_build,
    is_windows,
)

# Game versions
DEFAULT_VERSION = 0
VERSIONS = [
    "RM8E01",  # 0
]

parser = argparse.ArgumentParser()
parser.add_argument(
    "mode",
    choices=["configure", "progress"],
    default="configure",
    help="script mode (default: configure)",
    nargs="?",
)
parser.add_argument(
    "-v",
    "--version",
    choices=VERSIONS,
    type=str.upper,
    default=VERSIONS[DEFAULT_VERSION],
    help="version to build",
)
parser.add_argument(
    "--build-dir",
    metavar="DIR",
    type=Path,
    default=Path("build"),
    help="base build directory (default: build)",
)
parser.add_argument(
    "--binutils",
    metavar="BINARY",
    type=Path,
    help="path to binutils (optional)",
)
parser.add_argument(
    "--compilers",
    metavar="DIR",
    type=Path,
    help="path to compilers (optional)",
)
parser.add_argument(
    "--map",
    action="store_true",
    help="generate map file(s)",
)
parser.add_argument(
    "--no-asm",
    action="store_true",
    help="don't incorporate .s files from asm directory",
)
parser.add_argument(
    "--debug",
    action="store_true",
    help="build with debug info (non-matching)",
)
if not is_windows():
    parser.add_argument(
        "--wrapper",
        metavar="BINARY",
        type=Path,
        help="path to wibo or wine (optional)",
    )
parser.add_argument(
    "--dtk",
    metavar="BINARY | DIR",
    type=Path,
    help="path to decomp-toolkit binary or source (optional)",
)
parser.add_argument(
    "--sjiswrap",
    metavar="EXE",
    type=Path,
    help="path to sjiswrap.exe (optional)",
)
parser.add_argument(
    "--verbose",
    action="store_true",
    help="print verbose output",
)
parser.add_argument(
    "--non-matching",
    dest="non_matching",
    action="store_true",
    help="builds equivalent (but non-matching) or modded objects",
)
args = parser.parse_args()

config = ProjectConfig()
config.version = str(args.version)
version_num = VERSIONS.index(config.version)

# Apply arguments
config.build_dir = args.build_dir
config.dtk_path = args.dtk
config.binutils_path = args.binutils
config.compilers_path = args.compilers
config.debug = args.debug
config.generate_map = args.map
config.non_matching = args.non_matching
config.sjiswrap_path = args.sjiswrap
if not is_windows():
    config.wrapper = args.wrapper
if args.no_asm:
    config.asm_dir = None

# Tool versions
config.binutils_tag = "2.42-1"
config.compilers_tag = "20231018"
config.dtk_tag = "v0.9.2"
config.sjiswrap_tag = "v1.1.1"
config.wibo_tag = "0.6.11"

# Project
config.config_path = Path("config") / config.version / "config.yml"
config.check_sha_path = Path("config") / config.version / "build.sha1"
config.asflags = [
    "-mgekko",
    "--strip-local-absolute",
    "-I include",
    f"-I build/{config.version}/include",
    f"--defsym version={version_num}",
]
config.ldflags = [
    "-fp hardware",
    "-nodefaults",
    "-listclosure", # Uncomment for Wii linkers
]
# Use for any additional files that should cause a re-configure when modified
config.reconfig_deps = []

# Base flags, common to most GC/Wii games.
# Generally leave untouched, with overrides added below.
cflags_base = [
    "-nodefaults",
    "-proc gekko",
    "-align powerpc",
    "-enum int",
    "-fp hardware",
    "-Cpp_exceptions off",
    # "-W all",
    "-O4,p",
    "-inline auto",
    '-pragma "cats off"',
    '-pragma "warn_notinlined off"',
    "-maxerrors 1",
    "-nosyspath",
    "-RTTI off",
    "-fp_contract on",
    "-str reuse",
    "-enc SJIS",  # For Wii compilers, replace with `-enc SJIS`
    "-i include",
    f"-i build/{config.version}/include",
    f"-DVERSION={version_num}",
]

# Debug flags
if config.debug:
    cflags_base.extend(["-sym on", "-DDEBUG=1"])
else:
    cflags_base.append("-DNDEBUG=1")

# Metrowerks library flags
cflags_runtime = [
    *cflags_base,
    "-use_lmw_stmw on",
    "-str reuse,pool,readonly",
    "-gccinc",
    "-common off",
    "-inline auto",
]

# Game flags
cflags_game = [
    *cflags_base,
    "-O0,p",
    "-char unsigned",
    "-fp_contract off",
]

# REL flags
cflags_rel = [
    *cflags_game,
    "-sdata 0",
    "-sdata2 0",
    "-pool off"
]


config.linker_version = "GC/3.0a5.2"
config.rel_strip_partial = False
config.rel_empty_file = "REL/empty.c"

# Helper function for Dolphin libraries
def DolphinLib(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": "GC/1.2.5n",
        "cflags": cflags_base,
        "host": False,
        "objects": objects,
    }


# Helper function for REL script objects
def Rel(lib_name: str, objects: List[Object]) -> Dict[str, Any]:
    return {
        "lib": lib_name,
        "mw_version": "GC/3.0a5.2",
        "cflags": cflags_rel,
        "host": True,
        "objects": objects,
    }


Matching = True                   # Object matches and should be linked
NonMatching = False               # Object does not match and should not be linked
Equivalent = config.non_matching  # Object should be linked when configured with --non-matching

config.warn_missing_config = True
config.warn_missing_source = False
config.libs = [
    {
        "lib": "Runtime.PPCEABI.H",
        "mw_version": config.linker_version,
        "cflags": cflags_runtime,
        "host": False,
        "objects": [
            Object(NonMatching, "Runtime.PPCEABI.H/global_destructor_chain.c"),
            Object(NonMatching, "Runtime.PPCEABI.H/__init_cpp_exceptions.cpp"),
        ],
    },
    {
        "lib": "Game",
        "mw_version": config.linker_version,
        "cflags": cflags_game,
        "host": False,
        "objects": [
            Object(NonMatching, "game/objmain.c"),
            Object(NonMatching, "game/main.c"),
            Object(NonMatching, "game/pad.c"),
            Object(NonMatching, "game/dvd.c"),
            Object(NonMatching, "game/data.c"),
            Object(NonMatching, "game/decode.c"),
            Object(NonMatching, "game/font.c"),
            Object(NonMatching, "game/init.c"),
            Object(NonMatching, "game/jmp.c"),
            Object(NonMatching, "game/malloc.c"),
            Object(NonMatching, "game/memory.c"),
            Object(NonMatching, "game/printfunc.c"),
            Object(NonMatching, "game/process.c"),
            Object(NonMatching, "game/sprman.c"),
            Object(NonMatching, "game/sprput.c"),
            Object(NonMatching, "game/sprex.c"),
            Object(NonMatching, "game/hsfdraw.c"),
            Object(NonMatching, "game/hsfload.c"),
            Object(NonMatching, "game/hsfman.c"),
            Object(NonMatching, "game/hsfmotion.c"),
            Object(NonMatching, "game/hsfanim.c"),
            Object(NonMatching, "game/hsfex.c"),
            Object(NonMatching, "game/perf.c"),
            Object(NonMatching, "game/fault.c"),
            Object(NonMatching, "game/gamework.c"),
            Object(NonMatching, "game/objsysobj.c"),
            Object(NonMatching, "game/objdll.c"),
            Object(NonMatching, "game/frand.c"),
            Object(NonMatching, "game/audioman.cpp"),
            Object(NonMatching, "game/EnvelopeExec.c"),
            Object(NonMatching, "game/esprite.c"),
            Object(NonMatching, "game/ovllist.c"),
            Object(NonMatching, "game/ClusterExec.c"),
            Object(NonMatching, "game/ShapeExec.c"),
            Object(NonMatching, "game/wipe.c"),
            Object(NonMatching, "game/window.c"),
            Object(NonMatching, "game/card.c"),
            Object(NonMatching, "game/THPSimple.c"),
            Object(NonMatching, "game/THPDraw.c"),
            Object(NonMatching, "game/thpmain.c"),
            Object(NonMatching, "game/mgmovie.c"),
            Object(NonMatching, "game/objsub.c"),
            Object(NonMatching, "game/flag.c"),
            Object(NonMatching, "game/sreset.c"),
            Object(NonMatching, "game/charman.c"),
            Object(NonMatching, "game/colman.c"),
            Object(NonMatching, "game/actman.c"),
            Object(NonMatching, "game/gamemes.c"),
            Object(NonMatching, "game/mgdata.c"),
            Object(NonMatching, "game/saveload.c"),
            Object(NonMatching, "game/mgtimer.c"),
            Object(NonMatching, "game/mggamemes.c"),
            Object(NonMatching, "game/mgresult.c"),
            Object(NonMatching, "game/mgscore.c"),
            Object(NonMatching, "game/seqman.c"),
            Object(NonMatching, "game/home.cpp"),
            Object(NonMatching, "game/nand.c"),
            Object(NonMatching, "game/mii.c"),
            Object(NonMatching, "game/kerent.c"),
        ],
    },
    {
        "lib": "REL",
        "mw_version": config.linker_version,
        "cflags": cflags_rel,
        "host": False,
        "objects": [
            Object(Matching, "REL/empty.c"),  # Must be marked as matching
        ],
    },
    {
        "lib": "board",
        "mw_version": config.linker_version,
        "cflags": cflags_rel,
        "host": False,
        "objects": [
            Object(NonMatching, "REL/board/board_process.cpp"),
            Object(NonMatching, "REL/board/game_object.cpp"),
            Object(NonMatching, "REL/board/game_event.cpp"),
            Object(NonMatching, "REL/board/game_memory.cpp"),
            Object(NonMatching, "REL/board/game_math.cpp"),
            Object(NonMatching, "REL/board/board_fileman.cpp"),
            Object(NonMatching, "REL/board/board.cpp"),
            Object(NonMatching, "REL/board/board_core.cpp"),
            Object(NonMatching, "REL/board/board_camera.cpp"),
            Object(NonMatching, "REL/board/board_objectman.cpp"),
            Object(NonMatching, "REL/board/board_masuman.cpp"),
            Object(NonMatching, "REL/board/board_window.cpp"),
        ],
    },
    Rel(
        "w03dll",
        objects={
            Object(NonMatching, "REL/w03dll/world03.cpp"),
            Object(NonMatching, "REL/w03dll/world03_stage.cpp"),
            Object(NonMatching, "REL/w03dll/world03_object.cpp"),
            Object(NonMatching, "REL/w03dll/world03_eventobj.cpp"),
            Object(NonMatching, "REL/w03dll/world03_event.cpp"),
            Object(NonMatching, "REL/w03dll/world03_eventman.cpp"),
            Object(NonMatching, "REL/w03dll/world03_effect.cpp"),
            Object(NonMatching, "REL/w03dll/world03_open.cpp"),
            Object(NonMatching, "REL/w03dll/world03_light.cpp"),
            Object(NonMatching, "REL/w03dll/world03_chusan.cpp"),
        },
    ),
]

if args.mode == "configure":
    # Write build.ninja and objdiff.json
    generate_build(config)
elif args.mode == "progress":
    # Print progress and write progress.json
    config.progress_each_module = args.verbose
    calculate_progress(config)
else:
    sys.exit("Unknown mode: " + args.mode)
