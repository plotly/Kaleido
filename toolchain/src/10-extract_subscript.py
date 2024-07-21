#!/usr/bin/env python3
import os
import json
import glob
import itertools

MAIN_DIR = os.environ['MAIN_DIR']
CHROMIUM_VERSION_TAG = os.environ['CHROMIUM_VERSION_TAG']
PLATFORM = os.environ['PLATFORM']
TARGET_ARCH = os.environ['TARGET_ARCH']
BUILD_DIR = os.environ['BUILD_DIR']
SRC_DIR = os.environ['SRC_DIR']

def hello_world():
  print("Hello world!")
  print(f"MAIN_DIR: {MAIN_DIR}")
  print(f"CHROMIUM_VERSION_TAG: {CHROMIUM_VERSION_TAG}")
  print(f"PLATFORM: {PLATFORM}")
  print(f"TARGET_ARCH: {TARGET_ARCH}")
  print(f"BUILD_DIR: {BUILD_DIR}")
  print(f"SRC_DIR: {SRC_DIR}")

def find_archive_name(archive):
  title = None
  if 'rename_dirs' in archive:
    for pair in archive['rename_dirs']:
      if pair['from_dir'] == '.': 
        title = pair['to_dir']
        break
  if not title:
    if 'gcs_path' in archive:
      title = archive['gcs_path']
  return title

def get_files_and_dirs_full_path(archive, src_dir):
    files = archive['files'] if 'files' in archive else []
    files = [ src_dir + "/" + f for f in files ]
    file_globs = archive['file_globs'] if 'file_globs' in archive else []
    file_globs = [ src_dir + "/" + file_glob for file_glob in file_globs ]
    for file_glob in file_globs:
      files.extend(glob.glob(file_glob))
    dirs = archive['dirs'] if 'dirs' in archive else [] # ruff
    dirs = [ src_dir + "/" + d for d in dirs ]
    return files, dirs

def match_json_to_directory(config_file, src_dir, relative=True, exists=True, missing=False, annotate=False):
  data = None
  with open(config_file) as f:
    data = json.load(f)
  if not data:
    raise ValueError(f"Couldn't find the file {config_file} to load")
  for archive in data['archive_datas']:
    title = find_archive_name(archive)
    if not title: title = "unamed"
    if annotate: print("    " + title)
    files, dirs = get_files_and_dirs_full_path(archive, src_dir)
    for f in itertools.chain(files, dirs):
      if (os.path.exists(f) and exists):
        if relative:
          f = f.removeprefix(src_dir)
        if annotate:
          print(f"exists: {f}")
        else:
          print(f)
      if (not os.path.exists(f) and missing):
        if relative:
          f = f.removeprefix(src_dir)
        if annotate:
          print(f"missing: {f}")
        else:
          print(f)

# 1) load a json and begin processing it
# 2) list what files you can and can't find
