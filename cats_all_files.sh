#!/bin/bash

# Check if a directory path is provided as an argument
if [ $# -eq 0 ]; then
  echo "Error: Please provide a directory path as an argument."
  exit 1
fi

# Get the directory path from the first argument
dir_path="$1"

# Check if the directory exists
if [ ! -d "$dir_path" ]; then
  echo "Error: Directory '$dir_path' does not exist."
  exit 1
fi

# Loop through all files in the directory
for file in "$dir_path/"*; do
  # Check if it's a regular file (not a directory or other special file)
  if [ -f "$file" ]; then
    # Print the content of the file using cat
    cat "$file"
    echo "---"  # Add a separator between files (optional)
  fi
done

echo "All files in '$dir_path' processed."
