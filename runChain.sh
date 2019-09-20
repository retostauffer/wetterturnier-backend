# -------------------------------------------------------------------
# - NAME:        archive.sh
# - AUTHOR:      Reto Stauffer
# - DATE:        2016-07-25
# -------------------------------------------------------------------
# - DESCRIPTION:
# -------------------------------------------------------------------
# - EDITORIAL:   2016-07-25, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-09 15:37 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


source activate

date=17011
while [ $date -le 17319 ] ; do
   let date=$date+7
   echo $date
   python Chain.py -t $date

done
