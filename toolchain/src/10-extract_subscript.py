#!/usr/bin/env python3
import json

def find_archive_name(archive):
  title = None
  if 'rename-dirs' in archive:
    for pair in archive['rename-dirs']:
      if pair['from-dir'] == '.': 
        title = pair['to-dir']
        break
  if not title:
    if 'gcs_path' in archive:
      title = archive['gcs_path']
  return title

def match_json_to_directory(config_file):
  data = None
  with open(config_file) as f:
    data = json.load(f)
  if not data:
    raise ValueError(f"Couldn't find the file {config_file} to load")
  for archive in data['archive_datas']:
    title = find_archive_name(archive)
    if not title: title = "unamed"
    print(title)
# 1) load a json and begin processing it
# 2) list what files you can and can't find
