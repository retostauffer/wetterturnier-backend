# -------------------------------------------------------------------
# - NAME:        PrepareMOS.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2017-06-28
# -------------------------------------------------------------------
# - DESCRIPTION: Preprocessing MSwr MOS all.xxxxxxxxxx files
# -------------------------------------------------------------------
# - EDITORIAL:   2017-06-28, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-22 18:32 on marvin
# -------------------------------------------------------------------

# -------------------------------------------------------------------
# Setting up the logger
# -------------------------------------------------------------------
import logging, logging.config

import sys, os
os.environ['TZ'] = 'UTC'

# Initialize logging
log_level = logging.DEBUG
log = logging.getLogger('PrepareMOS')
log.setLevel(log_level)
ch = logging.StreamHandler()
ch.setLevel(log_level)
ch.setFormatter(logging.Formatter('# %(levelname)s - %(message)s'))
##ch.setFormatter(logging.Formatter('# %(levelname)s - %(name)s - %(message)s'))
log.addHandler(ch)

# -------------------------------------------------------------------
# Setting attributes/settings to process the data
# -------------------------------------------------------------------
datadir = "/home/knuepffer/abgabe"
outfile = "/var/www/html/referrerdata/mos/mos.json"

# -------------------------------------------------------------------
# Start main script
# -------------------------------------------------------------------
if __name__ == "__main__":
   """!Main routine of PrepareMOS.py. This is a single-proccessing
   file (no package) and only includes the function file PrepareFunctions.py."""

   preferred_order = ["N","rSd","foo","dd","ff","fx","Wv","Wn","PPP","TTm","TTn","TTd","RR",]

   from pywetterturnier.MOSfunctions import *
   import glob

   # If input directory does not exist, or output directory does not
   # exist, stop.
   if not os.path.isdir( datadir ):
      log.error("Sorry, data directory \"{0:s}\" does not exist!".format(datadir))
      sys.exit(9)
   elif not os.path.isdir( os.path.dirname( outfile ) ):
      log.error("Directory \"{0:s}\" to save \"{1:s}\" does not exist!".format(
          os.path.dirname(outfile), outfile))
      sys.exit(9)

   files = glob.glob("%s/all.%s" % (datadir, "[0-9]" * 8))
   files.sort()
   files = files[-3:]
   

   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   loaded = []
   for file in files:
   
      # Initialize a new MOSclass object and read the file.
      # Store object into 'loaded' at the end.
      tmp = MOSclass( file, preferred_order )
      tmp.read()
      #tmp.show()
      loaded.append( tmp )

   # ----------------------------------------------------------------
   # After all models we have been loading all the data:
   # prepare final object
   # ----------------------------------------------------------------
   result = MOSoutput( loaded )
   result.data2json( outfile )











