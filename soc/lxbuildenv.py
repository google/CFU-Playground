#!/usr/bin/env python3

# This script enables easy, cross-platform building without the need
# to install third-party Python modules.

LXBUILDENV_VERSION = '2020.6.1.1'
import sys
import os
import subprocess
import argparse


DEPS_DIR = "deps"

DEFAULT_DEPS = {
    'migen':        'https://github.com/m-labs/migen.git',
    'litex':        'https://github.com/enjoy-digital/litex.git',
    'litedram':     'https://github.com/enjoy-digital/litedram.git',
    'litex_boards': 'https://github.com/litex-hub/litex-boards.git',
    # From OPTIONAL_DEPS
    'liteeth':      'https://github.com/enjoy-digital/liteeth.git',
    'liteiclink':   'https://github.com/enjoy-digital/liteiclink.git',
    'pyserial':     'https://github.com/pyserial/pyserial.git',
    # Other stuff
    'pythondata_cpu_vexriscv': 'https://github.com/litex-hub/pythondata-cpu-vexriscv.git',
    'pythondata_software_compiler_rt': 'https://github.com/litex-hub/pythondata-software-compiler_rt.git',
}

OPTIONAL_DEPS = {
    'liteeth':      'https://github.com/enjoy-digital/liteeth.git',
    'liteusb':      'https://github.com/enjoy-digital/liteusb.git',
    'litepcie':     'https://github.com/enjoy-digital/litepcie.git',
    'litesdcard':   'https://github.com/enjoy-digital/litesdcard.git',
    'litescope':    'https://github.com/enjoy-digital/litescope.git',
    'litevideo':    'https://github.com/enjoy-digital/litevideo.git',
    'usb':          'https://github.com/pyusb/pyusb.git',
}

# Obtain the path to this script, plus a trailing separator.  This will
# be used later on to construct various environment variables for paths
# to a variety of support directories.
script_path = os.path.dirname(os.path.realpath(__file__)) + os.path.sep

# Look through the specified file for known variables to get the dependency list
def read_configuration(filename, args):
    import ast

    # Always check the Python version
    dependencies = {
        'python': 1
    }
    configuration = {
        'skip-git': False
    }
    main_src = ""

    try:
        with open(sys.argv[0], 'r') as f:
            main_src = f.read()
        main_ast = ast.parse(main_src, filename=filename)
    except:
        configuration['dependencies'] = list(dependencies.keys())
        return configuration

    # Iterate through the top-level nodes looking for variables named
    # LX_DEPENDENCIES or LX_DEPENDENCY and get the values that are
    # assigned to them.
    for node in ast.iter_child_nodes(main_ast):
        if isinstance(node, ast.Assign):
            value = node.value
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "LX_DEPENDENCIES" or target.id == "LX_DEPENDENCY":
                        if isinstance(value, (ast.List, ast.Tuple)):
                            for elt in value.elts:
                                if isinstance(elt, ast.Str):
                                    dependencies[elt.s] = 1
                        elif isinstance(value, ast.Str):
                            dependencies[value.s] = 1
                    elif target.id == "LX_CONFIGURATION" or target.id == "LX_CONFIG":
                        if isinstance(value, (ast.List, ast.Tuple)):
                            for elt in value.elts:
                                if isinstance(elt, ast.Str):
                                    configuration[elt.s] = True
                        elif isinstance(value, ast.Str):
                            configuration[value.s] = True

    # Set up sub-dependencies
    if 'riscv' in dependencies:
        dependencies['make'] = 1
    if args.lx_check_git or (not configuration['skip-git'] and not args.lx_ignore_git):
        dependencies['git'] = 1
    configuration['dependencies'] = list(dependencies.keys())
    return configuration

def get_python_path(script_path, args):
    # Python has no concept of a local dependency path, such as the C `-I``
    # switch, or the nodejs `node_modules` path, or the rust cargo registry.
    # Instead, it relies on an environment variable to append to the search
    # path.
    # Construct this variable by adding each subdirectory under the `deps/`
    # directory to the PYTHONPATH environment variable.
    python_path = []
    if os.path.isdir(script_path + DEPS_DIR):
        for dep in os.listdir(script_path + DEPS_DIR):
            dep = script_path + DEPS_DIR + os.path.sep + dep
            if os.path.isdir(dep):
                python_path.append(dep)
    return python_path

def fixup_env(script_path, args):
    os.environ["PYTHONPATH"] = os.pathsep.join(get_python_path(script_path, 0))

    # Set the "LXBUILDENV_REEXEC" variable to prevent the script from continuously
    # reinvoking itself.
    os.environ["LXBUILDENV_REEXEC"] = "1"

    # Python randomizes the order in which it traverses hashes, and Migen uses
    # hashes an awful lot when bringing together modules.  As such, the order
    # in which Migen generates its output Verilog will change with every run,
    # and the addresses for various modules will change.
    # Make builds deterministic so that the generated Verilog code won't change
    # across runs.
    os.environ["PYTHONHASHSEED"] = "1"

    # Some Makefiles are invoked as part of the build process, and those Makefiles
    # occasionally have calls to Python.  Ensure those Makefiles use the same
    # interpreter that this script is using.
    os.environ["PYTHON"] = sys.executable

    # Set the environment variable "V" to 1.  This causes Makefiles to print
    # the commands they run, which makes them easier to debug.
    if "lx_verbose" in args and args.lx_verbose:
        os.environ["V"] = "1"

    # If the user just wanted to print the environment variables, do that and quit.
    if args.lx_print_env:
        print("PYTHONPATH={}".format(os.environ["PYTHONPATH"]))
        print("PYTHONHASHSEED={}".format(os.environ["PYTHONHASHSEED"]))
        print("PYTHON={}".format(sys.executable))
        print("LXBUILDENV_REEXEC={}".format(os.environ["LXBUILDENV_REEXEC"]))

        sys.exit(0)

# Equivalent to the powershell Get-Command, and kinda like `which`
def get_command(cmd):
    if os.name == 'nt':
        path_ext = os.environ["PATHEXT"].split(os.pathsep)
    else:
        path_ext = [""]
    for ext in path_ext:
        for path in os.environ["PATH"].split(os.pathsep):
            if os.path.exists(path + os.path.sep + cmd + ext):
                return path + os.path.sep + cmd + ext
    return None

def check_python_version(args):
    import platform
    # Litex / Migen require Python 3.5 or newer.  Ensure we're running
    # under a compatible version of Python.
    if sys.version_info[:3] < (3, 5):
        return (False,
            "python: You need Python 3.5+ (version {} found)".format(sys.version_info[:3]))
    return (True, "python 3.5+: ok (Python {} found)".format(platform.python_version()))

def check_vivado(args):
    vivado_path = get_command("vivado")
    if vivado_path == None:
        # Look for the default Vivado install directory
        if os.name == 'nt':
            base_dir = r"C:\Xilinx\Vivado"
        else:
            base_dir = "/opt/Xilinx/Vivado"
        if os.path.exists(base_dir):
            for file in os.listdir(base_dir):
                bin_dir = base_dir + os.path.sep + file + os.path.sep + "bin"
                if os.path.exists(bin_dir + os.path.sep + "vivado"):
                    os.environ["PATH"] += os.pathsep + bin_dir
                    vivado_path = bin_dir
                    break
    if vivado_path == None:
        return (False, "toolchain not found in your PATH", "download it from https://www.xilinx.com/support/download.html")
    return (True, "found at {}".format(vivado_path))

def check_cmd(args, cmd, name=None, fix=None):
    if name is None:
        name = cmd
    path = get_command(cmd)
    if path == None:
        return (False, name + " not found in your PATH", fix)
    return (True, "found at {}".format(path))

def check_make(args):
    return check_cmd(args, "make", "GNU Make")

def check_riscv(args):
    riscv64 = check_cmd(args, "riscv64-unknown-elf-gcc", "riscv toolchain", "download it from https://www.sifive.com/boards/")
    if riscv64[0] == True:
        return riscv64

    riscv32 = check_cmd(args, "riscv32-unknown-elf-gcc", "riscv toolchain", "download it from https://www.sifive.com/boards/")
    if riscv32[0] == True:
        return riscv32

    # See https://xpack.github.io/riscv-none-embed-gcc/#riscv64-unknown-elf-gcc
    xpm_riscv = check_cmd(args, "riscv-none-embed-gcc", "xPack GNU RISC-V Embedded GCC", "install it from https://xpack.github.io/riscv-none-embed-gcc/install/")
    if xpm_riscv[0] == True:
        return xpm_riscv

    return riscv64

def check_yosys(args):
    return check_cmd(args, "yosys")

def check_arachne(args):
    return check_cmd(args, "arachne-pnr")

def check_git(args):
    return check_cmd(args, "git")

def check_icestorm(args):
    return check_cmd(args, "icepack")

def check_nextpnr_ice40(args):
    return check_cmd(args, "nextpnr-ice40")

def check_nextpnr_ecp5(args):
    return check_cmd(args, "nextpnr-ecp5")

dependency_checkers = {
    'python': check_python_version,
    'vivado': check_vivado,
    'make': check_make,
    'git': check_git,
    'riscv': check_riscv,
    'yosys': check_yosys,
    'arachne-pnr': check_arachne,
    'icestorm': check_icestorm,
    'nextpnr-ice40': check_nextpnr_ice40,
    'nextpnr-ecp5': check_nextpnr_ecp5,
}

# Validate that the required dependencies (Vivado, compilers, etc.)
# have been installed.
def check_dependencies(args, dependency_list):
    dependency_errors = 0
    for dependency_name in dependency_list:
        if not dependency_name in dependency_checkers:
            print('lxbuildenv: WARNING: Unrecognized dependency "{}"'.format(dependency_name))
            continue
        result = dependency_checkers[dependency_name](args)
        if result[0] == False:
            if len(result) > 2:
                print('lxbuildenv: {}: {} -- {}'.format(dependency_name, result[1], result[2]))
            else:
                print('lxbuildenv: {}: {}'.format(dependency_name, result[1]))
            dependency_errors = dependency_errors + 1

        elif args.lx_check_deps or args.lx_verbose:
            print('lxbuildenv: dependency: {}: {}'.format(dependency_name, result[1]))
    if dependency_errors > 0:
        if args.lx_ignore_deps:
            if not args.lx_quiet:
                print('lxbuildenv: {} missing dependencies were found but continuing anyway'.format(dependency_errors))
        else:
            if not args.lx_quiet:
                print('lxbuildenv: To ignore dependencies, re-run with "--lx-ignore-deps"')
            raise SystemExit(str(dependency_errors) +
                             " missing dependencies were found")

    if args.lx_check_deps:
        sys.exit(0)

# Return True if the given tree needs to be initialized
def check_module(root_path, depth, verbose=False, recursive=True, breadcrumbs=[]):
    if verbose:
        print('git-dep: checking if "{}" requires updating (depth: {})...'.format(root_path, depth))

    # If the directory isn't a valid git repo, initialization is required
    if not os.path.exists(root_path):
        if verbose:
            print('git-dep: subdirectory {} does not exist, so starting update'.format(root_path))
        return True
    git_dir_cmd = subprocess.Popen(["git", "rev-parse", "--show-toplevel"],
                        cwd=root_path,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE)
    (git_stdout, _) = git_dir_cmd.communicate()
    if git_dir_cmd.wait() != 0:
        if verbose:
            print('git-dep: missing git directory, starting update...')
        return True
    git_dir = git_stdout.decode().strip()

    if git_dir in breadcrumbs:
        if verbose:
            print('git-dep: root path {} is not in git path'.format(root_path))
        return True
    breadcrumbs.append(git_dir)

    if not os.path.exists(git_dir + os.path.sep + '.git'):
        if verbose:
            print('git-dep: .git not found in "{}"'.format(git_dir))
        return True

    # If there are no submodules, no initialization needs to be done
    if not os.path.isfile(git_dir + os.path.sep + '.gitmodules'):
        if verbose:
            print('git-dep: .gitmodules not found in "{}", so not updating'.format(git_dir))
        return False

    # Loop through the gitmodules to check all submodules
    if recursive or depth == 0:
        gitmodules = open(git_dir + os.path.sep + '.gitmodules', 'r')
        for line in gitmodules:
            parts = line.split("=", 2)
            if parts[0].strip() == "path":
                path = parts[1].strip()
                if check_module(git_dir + os.path.sep + path, depth + 1, verbose=verbose, recursive=recursive, breadcrumbs=breadcrumbs):
                    return True
    return False

# Determine whether we need to invoke "git submodules init --recurse"
def check_submodules(script_path, args):
    if check_module(script_path, 0, verbose=args.lx_verbose, recursive=args.lx_recursive_git):
        if not args.lx_quiet:
            print("lxbuildenv: Missing git submodules -- updating")
            print("lxbuildenv: To ignore git issues, re-run with --lx-ignore-git")

        git_cmd = ["git", "submodule", "update", "--init"]
        if args.lx_recursive_git:
            git_cmd.append("--recursive")
        subprocess.Popen(git_cmd, cwd=script_path).wait()
    elif args.lx_verbose:
        if not args.lx_quiet:
            print("lxbuildenv: Submodule check: Submodules found")


def lx_git(cmd, *args):
    import subprocess
    git_cmd = ["git", cmd]
    if args is not None:
        for arg in args:
            git_cmd = git_cmd + [arg]
    subprocess.call(git_cmd)

def lx_print_deps():
    print('lxbuildenv: Supported dependencies:')
    for dep in dependency_checkers.keys():
        print('lxbuildenv:     {}'.format(dep))
    print('lxbuildenv: To define a dependency, add a variable inside {} at the top level called LX_DEPENDENCIES and assign it a list or tuple.'.format(sys.argv[0]))
    print('lxbuildenv: For example:')
    print('lxbuildenv: LX_DEPENDENCIES = ("riscv", "vivado")')


def lx_main(args):
    if args.lx_print_env:
        fixup_env(script_path, args)

    elif args.lx_print_deps:
        lx_print_deps()

    elif args.lx_run is not None:
        script_name=args.lx_run[0]
        config = read_configuration(script_name, args)

        fixup_env(script_path, args)
        if not config['skip-git']:
            check_submodules(script_path, args)

        try:
            sys.exit(subprocess.Popen(
                [sys.executable] + [script_name] + args.lx_run[1:]).wait())
        except:
            sys.exit(1)
    elif args.init:
        if args.main is None:
            main_name = os.getcwd().split(os.path.sep)[-1] + '.py'
            new_main_name = input('lxbuildenv: What would you like your main program to be called? [' + main_name + '] ')
            if new_main_name is not None and new_main_name != "":
                main_name = new_main_name
        else:
            main_name = args.main
        if not main_name.endswith('.py'):
            main_name = main_name + '.py'

        if args.no_git:
            print("lxbuildenv: skipping git initialization")
        else:
            if not os.path.exists(DEPS_DIR):
                os.mkdir(DEPS_DIR)

            if not os.path.exists(".git"):
                print("lxbuildenv: initializing git repository")
                lx_git('init')
            else:
                print("lxbuildenv: using existing git repository")
            lx_git('add', str(__file__))

            for dep_name, dep_url in DEFAULT_DEPS.items():
                dest_path = '{}{}{}'.format(DEPS_DIR, '/', dep_name)
                if not os.path.exists(dest_path):
                    lx_git('submodule', 'add', dep_url, dest_path)
                    lx_git('add', dest_path)

            if args.lx_recursive_git:
                lx_git('submodule', 'update', '--init', '--recursive')
            else:
                lx_git('submodule', 'update', '--init')

        if args.no_bin:
            print("lxbuildenv: skipping bin/ initialization")
        elif os.path.exists("bin"):
            print("lxbuildenv: bin/ directory exists -- remove bin/ directory to re-initialize")
        else:
            bin_tools = {
                'mkmscimg':           'litex.soc.software.mkmscimg',
                'litex_term':         'litex.tools.litex_term',
                'litex_server':       'litex.tools.litex_server',
                'litex_sim':          'litex.tools.litex_sim',
                'litex_read_verilog': 'litex.tools.litex_read_verilog',
                'litex_simple':       'litex.boards.targets.simple',
            }
            bin_template = """#!/usr/bin/env python3

import sys
import os

# This script lives in the "bin" directory, but uses a helper script in the parent
# directory.  Obtain the current path so we can get the absolute parent path.
script_path = os.path.dirname(os.path.realpath(
    __file__)) + os.path.sep + os.path.pardir + os.path.sep
sys.path.insert(0, script_path)
import lxbuildenv

"""
            print("lxbuildenv: Creating binaries")
            os.mkdir("bin")
            for bin_name, python_module in bin_tools.items():
                with open('bin' + os.path.sep + bin_name, 'w', newline='\n') as new_bin:
                    new_bin.write(bin_template)
                    new_bin.write('from ' + python_module + ' import main\n')
                    new_bin.write('main()\n')
                import stat
                os.chmod('bin' + os.path.sep + bin_name, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                if not args.no_git:
                    lx_git('add', '--chmod=+x', 'bin' + os.path.sep + bin_name)

        if os.path.exists(main_name):
            print("lxbuildenv: skipping creation of {}: file exists".format(main_name))
        else:
            print("lxbuildenv: creating main program {}".format(main_name))
            with open(main_name, 'w') as m:
                program_template = """#!/usr/bin/env python3
# This variable defines all the external programs that this module
# relies on.  lxbuildenv reads this variable in order to ensure
# the build will finish without exiting due to missing third-party
# programs.
LX_DEPENDENCIES = ["riscv", "vivado"]

# Import lxbuildenv to integrate the deps/ directory
import lxbuildenv

# Disable pylint's E1101, which breaks completely on migen
#pylint:disable=E1101

from migen import *
from litex.build.xilinx import VivadoProgrammer, XilinxPlatform
from litex.build.generic_platform import Pins, IOStandard
from litex.soc.integration import SoCSDRAM
from litex.soc.integration.builder import Builder
from litex.soc.integration.soc_core import csr_map_update

_io = [
    ("clk50", 0, Pins("J19"), IOStandard("LVCMOS33")),
]

class Platform(XilinxPlatform):
    def __init__(self, toolchain="vivado", programmer="vivado", part="35"):
        part = "xc7a" + part + "t-fgg484-2"
    def create_programmer(self):
        if self.programmer == "vivado":
            return VivadoProgrammer(flash_part="n25q128-3.3v-spi-x1_x2_x4")
        else:
            raise ValueError("{} programmer is not supported"
                             .format(self.programmer))

    def do_finalize(self, fragment):
        XilinxPlatform.do_finalize(self, fragment)

class BaseSoC(SoCSDRAM):
    csr_peripherals = [
        "ddrphy",
#        "dna",
        "xadc",
        "cpu_or_bridge",
    ]
    csr_map_update(SoCSDRAM.csr_map, csr_peripherals)

    def __init__(self, platform, **kwargs):
        clk_freq = int(100e6)

def main():
    platform = Platform()
    soc = BaseSoC(platform)
    builder = Builder(soc, output_dir="build", csr_csv="test/csr.csv")
    vns = builder.build()
    soc.do_exit(vns)

if __name__ == "__main__":
    main()
"""
                m.write(program_template)
                if not args.no_git:
                    lx_git("add", main_name)
    else:
        return False
    return True

# For the main command, parse args and hand it off to main()
def main():
    parser = argparse.ArgumentParser(
        description="Wrap Python code to enable quickstart",
        add_help=False)
    parser.add_argument(
        "-h", "--help", '--lx-help', help="show this help message and exit", action="help"
    )
    parser.add_argument(
        '-i', '--init', '--lx-init', help='initialize a new project', action="store_true"
    )
    parser.add_argument(
        '-m', '--main', '--lx-main', help='name of main project'
    )
    parser.add_argument(
        '--no-bin', '--lx-no-bin', help="don't create a bin/ directory"
    )
    parser.add_argument(
        '--no-git', '--lx-no-git', help="Don't create a git repository"
    )
    parser.add_argument(
        '-e', '--print-env', '--lx-print-env', dest="lx_print_env", help="print environment variable listing for pycharm, vscode, or bash", action="store_true"
    )
    parser.add_argument(
        '-d', '--print-deps', '--lx-print-deps', dest="lx_print_deps", help="print all possible dependencies and then exit", action="store_true"
    )
    parser.add_argument(
        "--lx-verbose", help="increase verboseness of some processes", action="store_true"
    )
    parser.add_argument(
        '-r', '--run', '--lx-run', dest='lx_run', help="run the given script under lxbuildenv", nargs=argparse.REMAINDER
    )
    parser.add_argument(
        "--lx-recursive-git", help="recursively check out submodules", action="store_true"
    )
    args = parser.parse_args()

    if not lx_main(args):
        parser.print_help()

if __name__ == "__main__":
    main()

elif not os.path.isfile(sys.argv[0]):
    print("lxbuildenv doesn't operate while in interactive mode")

elif "LXBUILDENV_REEXEC" not in os.environ:
    parser = argparse.ArgumentParser(
        description="Wrap Python code to enable quickstart",
        add_help=False)
    parser.add_argument(
        "--lx-verbose", help="increase verboseness of some processes", action="store_true"
    )
    parser.add_argument(
        "--lx-quiet", help="decrease verboseness of some processes", action="store_true"
    )
    parser.add_argument(
        "--lx-print-env", help="print environment variable listing for pycharm, vscode, or bash", action="store_true"
    )
    parser.add_argument(
        "--lx-check-deps", help="check build environment for dependencies such as compiler and fpga tools and then exit", action="store_true"
    )
    parser.add_argument(
        "--lx-print-deps", help="print all possible dependencies and then exit", action="store_true"
    )
    parser.add_argument(
        "--lx-help", action="help"
    )
    parser.add_argument(
        "--lx-ignore-deps", help="try building even if dependencies are missing", action="store_true"
    )
    parser.add_argument(
        "--lx-ignore-git", help="don't do a check of the git repo", action="store_true"
    )
    parser.add_argument(
        "--lx-check-git", help="force a git check even if it's otherwise disabled", action="store_true"
    )
    parser.add_argument(
        "--lx-recursive-git", help="recursively check out submodules", action="store_true"
    )
    (args, rest) = parser.parse_known_args()

    if not args.lx_quiet:
        print("lxbuildenv: v{} (run {} --lx-help for help)".format(LXBUILDENV_VERSION, sys.argv[0]))

    if args.lx_print_deps:
        lx_print_deps()
        sys.exit(0)

    config = read_configuration(sys.argv[0], args)
    deps = config['dependencies']

    fixup_env(script_path, args)
    check_dependencies(args, deps)
    if args.lx_check_git:
        check_submodules(script_path, args)
    elif config['skip-git']:
        if not args.lx_quiet:
            print('lxbuildenv: Skipping git configuration because "skip-git" was found in LX_CONFIGURATION')
            print('lxbuildenv: To fetch from git, run {} --lx-check-git'.format(" ".join(sys.argv)))
    elif args.lx_ignore_git:
        if not args.lx_quiet:
            print('lxbuildenv: Skipping git configuration because "--lx-ignore-git" Was specified')
    else:
        check_submodules(script_path, args)

    try:
        sys.exit(subprocess.Popen(
            [sys.executable] + [sys.argv[0]] + rest).wait())
    except Exception as e:
        print(e)
        sys.exit(1)
else:
    # Overwrite the deps directory.
    # Because we're running with a predefined PYTHONPATH, you'd think that
    # the DEPS_DIR would be first.
    # Unfortunately, setuptools causes the sitewide packages to take precedence
    # over the PYTHONPATH variable.
    # Work around this bug by inserting paths into the first index.
    for path in get_python_path(script_path, None):
        sys.path.insert(0, path)
