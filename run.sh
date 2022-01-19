# -------------------------------------------------------------------
# - NAME:        runChain.sh
# - AUTHOR:      Reto Stauffer/sferics
# - DATE:        2019-12-25
# -------------------------------------------------------------------
# - DESCRIPTION:  helper tool to start Chain.py for multiple tdates
# -------------------------------------------------------------------
# - EDITORIAL:   2016-07-25, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2019-12-25 15:37 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------

#Enter to input arguments from, till. If only one input is given till=today
source activate

which=$1
from=$2
till=$3

if ! [ -n "$which" ]; then
   which="Chain"
fi

if ! [ -n "$till" ]; then
   timestamp=$(date +"%s")
   till=$((timestamp/86400))
fi

if [ $(($from + 7)) -gt $till ]; then
   exit
fi

while [ $from -le $till ] ; do
   let "from=$from+7"
   echo $from
   python ${which}.py -t $from
done
