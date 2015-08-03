#!/bin/bash

# Clean up the directory (delete some techfiles)

echo "* Cleaning up the directory"
postfix=("aux" "log" "pdf")

i=0
while [ $i -lt ${#postfix[@]} ] ; do

  echo "  - ${postfix[$i]} files"
  rm *.${postfix[$i]} 2>/dev/null
  let i=$i+1
done
echo "* Done"
