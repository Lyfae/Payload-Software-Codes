
import os
import os.path
import pathlib
import semver
import shutil
import sys
import subprocess
import tempfile

IGNORE_PY = ["setup.py", "conf.py", "__init__.py"]
GLOB_PATTERNS = ["*.py", "font5x8.bin"]

def version_string(path=None, *, valid_semver=False):
    version = None
    tag = subprocess.run('git describe --tags --exact-match', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=path)
    if tag.returncode == 0:
        version = tag.stdout.strip().decode("utf-8", "strict")
    else:
        describe = subprocess.run("git describe --tags --always", shell=True, stdout=subprocess.PIPE, cwd=path)
        describe = describe.stdout.strip().decode("utf-8", "strict").rsplit("-", maxsplit=2)
        if len(describe) == 3:
            tag, additional_commits, commitish = describe
            commitish = commitish[1:]
        else:
            tag = "0.0.0"
            commit_count = subprocess.run("git rev-list --count HEAD", shell=True, stdout=subprocess.PIPE, cwd=path)
            additional_commits = commit_count.stdout.strip().decode("utf-8", "strict")
            commitish = describe[0]
        if valid_semver:
            version_info = semver.parse_version_info(tag)
            if not version_info.prerelease:
                version = semver.bump_patch(tag) + "-alpha.0.plus." + additional_commits + "+" + commitish
            else:
                version = tag + ".plus." + additional_commits + "+" + commitish
        else:
            version = commitish
    return version

def mpy_cross(mpy_cross_filename, circuitpython_tag, quiet=False):
    if os.path.isfile(mpy_cross_filename):
        return
    if not quiet:
        title = "Building mpy-cross for circuitpython " + circuitpython_tag
        print()
        print(title)
        print("=" * len(title))

    os.makedirs("build_deps/", exist_ok=True)
    if not os.path.isdir("build_deps/circuitpython"):
        clone = subprocess.run("git clone https://github.com/adafruit/circuitpython.git build_deps/circuitpython", shell=True)
        if clone.returncode != 0:
            sys.exit(clone.returncode)

    current_dir = os.getcwd()
    os.chdir("build_deps/circuitpython")
    make = subprocess.run("git fetch && git checkout {TAG} && git submodule update".format(TAG=circuitpython_tag), shell=True)
    os.chdir("tools")
    make = subprocess.run("git submodule update --init .", shell=True)
    os.chdir("../mpy-cross")
    make = subprocess.run("make clean && make", shell=True)
    os.chdir(current_dir)

    shutil.copy("build_deps/circuitpython/mpy-cross/mpy-cross", mpy_cross_filename)

    if make.returncode != 0:
        sys.exit(make.returncode)

def _munge_to_temp(original_path, temp_file, library_version):
    with open(original_path, "rb") as original_file:
        for line in original_file:
            if original_path.endswith(".bin"):
                # this is solely for adafruit_framebuf/examples/font5x8.bin
                temp_file.write(line)
            else:
                line = line.decode("utf-8").strip("\n")
                if line.startswith("__version__"):
                    line = line.replace("0.0.0-auto.0", library_version)
                temp_file.write(line.encode("utf-8") + b"\r\n")
    temp_file.flush()

def library(library_path, output_directory, package_folder_prefix,
            mpy_cross=None, example_bundle=False):
    py_files = []
    package_files = []
    example_files = []
    total_size = 512

    lib_path = pathlib.Path(library_path)
    parent_idx = len(lib_path.parts)
    glob_search = []
    for pattern in GLOB_PATTERNS:
        glob_search.extend(list(lib_path.rglob(pattern)))

    for file in glob_search:
        if file.parts[parent_idx] == "examples":
            example_files.append(file)
        else:
            if not example_bundle:
                is_package = False
                for prefix in package_folder_prefix:
                    if file.parts[parent_idx].startswith(prefix):
                        is_package = True

                if is_package:
                    package_files.append(file)
                else:
                    if file.name in IGNORE_PY:
                        #print("Ignoring:", file.resolve())
                        continue
                    if file.parent == lib_path:
                        py_files.append(file)

    if len(py_files) > 1:
        raise ValueError("Multiple top level py files not allowed. Please put "
                         "them in a package or combine them into a single file.")

    for fn in example_files:
        base_dir = os.path.join(output_directory.replace("/lib", "/"),
                                fn.relative_to(library_path).parent)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
            total_size += 512

    for fn in package_files:
        base_dir = os.path.join(output_directory,
                                fn.relative_to(library_path).parent)
        if not os.path.isdir(base_dir):
            os.makedirs(base_dir)
            total_size += 512

    new_extension = ".py"
    if mpy_cross:
        new_extension = ".mpy"

    try:
        library_version = version_string(library_path, valid_semver=True)
    except ValueError as e:
        print(library_path + " has version that doesn't follow SemVer (semver.org)")
        print(e)
        library_version = version_string(library_path)

    for filename in py_files:
        full_path = os.path.join(library_path, filename)
        output_file = os.path.join(
            output_directory,
            filename.relative_to(library_path).with_suffix(new_extension)
        )
        with tempfile.NamedTemporaryFile() as temp_file:
            _munge_to_temp(full_path, temp_file, library_version)

            if mpy_cross:
                mpy_success = subprocess.call([mpy_cross,
                                               "-o", output_file,
                                               "-s", str(filename),
                                               temp_file.name])
                if mpy_success != 0:
                    raise RuntimeError("mpy-cross failed on", full_path)
            else:
                shutil.copyfile(temp_file.name, output_file)

    for filename in package_files:
        full_path = os.path.join(library_path, filename)
        with tempfile.NamedTemporaryFile() as temp_file:
            _munge_to_temp(full_path, temp_file, library_version)
            if not mpy_cross or os.stat(full_path).st_size == 0:
                output_file = os.path.join(output_directory,
                                           filename.relative_to(library_path))
                shutil.copyfile(temp_file.name, output_file)
            else:
                output_file = os.path.join(
                    output_directory,
                    filename.relative_to(library_path).with_suffix(new_extension)
                )

                mpy_success = subprocess.call([mpy_cross,
                                               "-o", output_file,
                                               "-s", str(filename),
                                               temp_file.name])
                if mpy_success != 0:
                    raise RuntimeError("mpy-cross failed on", full_path)

    for filename in example_files:
        full_path = os.path.join(library_path, filename)
        output_file = os.path.join(output_directory.replace("/lib", "/"),
                                   filename.relative_to(library_path))
        with tempfile.NamedTemporaryFile() as temp_file:
            _munge_to_temp(full_path, temp_file, library_version)
            shutil.copyfile(temp_file.name, output_file)
