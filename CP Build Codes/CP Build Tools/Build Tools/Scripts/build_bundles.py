
import json
import os
import os.path
import shlex
import shutil
import subprocess
import sys
import zipfile

import click

from circuitpython_build_tools import build
from circuitpython_build_tools import target_versions

import pkg_resources

def add_file(bundle, src_file, zip_name):
    bundle.write(src_file, zip_name)
    file_size = os.stat(src_file).st_size
    file_sector_size = file_size
    if file_size % 512 != 0:
        file_sector_size = (file_size // 512 + 1) * 512
    print(zip_name, file_size, file_sector_size)
    return file_sector_size


def build_bundle(libs, bundle_version, output_filename, package_folder_prefix,
        build_tools_version="devel", mpy_cross=None, example_bundle=False):
    build_dir = "build-" + os.path.basename(output_filename)
    top_folder = os.path.basename(output_filename).replace(".zip", "")
    build_lib_dir = os.path.join(build_dir, top_folder, "lib")
    build_example_dir = os.path.join(build_dir, top_folder, "examples")
    if os.path.isdir(build_dir):
        print("Deleting existing build.")
        shutil.rmtree(build_dir)
    total_size = 0
    if not example_bundle:
        os.makedirs(build_lib_dir)
        total_size += 512
    os.makedirs(build_example_dir)
    total_size += 512

    multiple_libs = len(libs) > 1

    success = True
    for library_path in libs:
        try:
            build.library(library_path, build_lib_dir,  package_folder_prefix,
                          mpy_cross=mpy_cross, example_bundle=example_bundle)
        except ValueError as e:
            print("build.library failure:", library_path)
            print(e)
            success = False

    print()
    print("Generating VERSIONS")
    if multiple_libs:
        with open(os.path.join(build_dir, top_folder, "VERSIONS.txt"), "w") as f:
            f.write(bundle_version + "\r\n")
            versions = subprocess.run('git submodule --quiet foreach \"git remote get-url origin && git describe --tags\"', shell=True, stdout=subprocess.PIPE, cwd=os.path.commonpath(libs))
            if versions.returncode != 0:
                print("Failed to generate versions file. Its likely a library hasn't been "
                      "released yet.")
                success = False

            repo = None
            for line in versions.stdout.split(b"\n"):
                if not line:
                    continue
                if line.startswith(b"git@"):
                    repo = b"https://github.com/" + line.split(b":")[1][:-len(".git")]
                elif line.startswith(b"https:"):
                    repo = line.strip()[:-len(".git")]
                else:
                    f.write(repo.decode("utf-8", "strict") + "/releases/tag/" + line.strip().decode("utf-8", "strict") + "\r\n")

    if not success:
        print("WARNING: some failures above")
        sys.exit(2)

    print()
    print("Zipping")

    with zipfile.ZipFile(output_filename, 'w') as bundle:
        build_metadata = {"build-tools-version": build_tools_version}
        bundle.comment = json.dumps(build_metadata).encode("utf-8")
        if multiple_libs:
            total_size += add_file(bundle, "README.txt", os.path.join(top_folder, "README.txt"))
        for root, dirs, files in os.walk(build_dir):
            ziproot = root[len(build_dir + "/"):]
            for filename in files:
                total_size += add_file(bundle, os.path.join(root, filename),
                                       os.path.join(ziproot, filename.replace("-", "_")))

    print()
    print(total_size, "B", total_size / 1024, "kiB", total_size / 1024 / 1024, "MiB")
    print("Bundled in", output_filename)

def _find_libraries(current_path, depth):
    if depth <= 0:
        return [current_path]
    subdirectories = []
    for subdirectory in os.listdir(current_path):
        path = os.path.join(current_path, subdirectory)
        if os.path.isdir(path):
            subdirectories.extend(_find_libraries(path, depth - 1))
    return subdirectories

@click.command()
@click.option('--filename_prefix', required=True, help="Filename prefix for the output zip files.")
@click.option('--output_directory', default="bundles", help="Output location for the zip files.")
@click.option('--library_location', required=True, help="Location of libraries to bundle.")
@click.option('--library_depth', default=0, help="Depth of library folders. This is useful when multiple libraries are bundled together but are initially in separate subfolders.")
@click.option('--package_folder_prefix', default="adafruit_", help="Prefix string used to determine package folders to bundle.")
def build_bundles(filename_prefix, output_directory, library_location, library_depth, package_folder_prefix):
    os.makedirs(output_directory, exist_ok=True)

    package_folder_prefix = package_folder_prefix.split(", ")

    bundle_version = build.version_string()

    libs = _find_libraries(os.path.abspath(library_location), library_depth)

    pkg = pkg_resources.get_distribution("circuitpython-build-tools")
    build_tools_version = "devel"
    if pkg:
        build_tools_version = pkg.version

    build_tools_fn = "z-build_tools_version-{}.ignore".format(
        build_tools_version)
    build_tools_fn = os.path.join(output_directory, build_tools_fn)
    with open(build_tools_fn, "w") as f:
        f.write(build_tools_version)

    # Build raw source .py bundle
    zip_filename = os.path.join(output_directory,
        filename_prefix + '-py-{VERSION}.zip'.format(
            VERSION=bundle_version))
    build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                 build_tools_version=build_tools_version)

    # Build .mpy bundle(s)
    os.makedirs("build_deps", exist_ok=True)
    for version in target_versions.VERSIONS:
        # Use prebuilt mpy-cross on Travis, otherwise build our own.
        if "TRAVIS" in os.environ:
            mpy_cross = pkg_resources.resource_filename(
                target_versions.__name__, "data/mpy-cross-" + version["name"])
        else:
            mpy_cross = "build_deps/mpy-cross-" + version["name"]
            build.mpy_cross(mpy_cross, version["tag"])
        zip_filename = os.path.join(output_directory,
            filename_prefix + '-{TAG}-mpy-{VERSION}.zip'.format(
                TAG=version["name"],
                VERSION=bundle_version))
        build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                     mpy_cross=mpy_cross, build_tools_version=build_tools_version)

    # Build example bundle
    zip_filename = os.path.join(output_directory,
        filename_prefix + '-examples-{VERSION}.zip'.format(
            VERSION=bundle_version))
    build_bundle(libs, bundle_version, zip_filename, package_folder_prefix,
                 build_tools_version=build_tools_version, example_bundle=True)
