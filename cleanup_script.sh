#!/bin/bash

# Find all .mp3 files in the ./temp folder older than 24 hours and delete them
find ./temp/tt -name "*.mp3" -type f -mtime +0 -exec rm {} \;
