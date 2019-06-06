# -------------------------------------------------------------------
# - NAME:        UpdateLicenseTags.sh
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-08-03
# -------------------------------------------------------------------
# - DESCRIPTION: Searches for a set of files and replaces the
#                copyright tag in the license.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-08-03, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-03 11:28 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

# - Replace all occurances of lines like:
#   "# - LICENSE: GPL-3" 
PATTERN="^(#\ -\ LICENSE:)\s+GPL-3,\ Reto\ Stauffer,\ copyright.+"
YEAR=`date "+%Y"`
REPLACE="\1 GPL-3, Reto Stauffer, copyright 2014-${YEAR}"

echo $REPLACE
exit
sed -ri "s/${PATTERN}/${REPLACE}/g" TEST.txt

