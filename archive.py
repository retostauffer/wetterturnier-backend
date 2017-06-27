# -------------------------------------------------------------------
# - NAME:        archive.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-23
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Downloading an archive file and extract all the
#                information we need.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-23, RS: Created file on pc24-c707.
#                2014-09-26, RS: Using local files now.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-06-27 11:36 on thinkreto
# -------------------------------------------------------------------




# - Only start if called as main routine
if __name__ == '__main__':

   import sys, os
   import re
   import urllib
   import glob
   #import MySQLdb
   import ConfigParser
   import subprocess as sub
   from pywetterturnier import utils
   from pywetterturnier import importbets
   from pywetterturnier.utils import nicename


   # Some MOS systems have been renamed. Loading conversion table.
   fid = open("data/MOSrenaming.txt","r")
   conversion_table = {}
   for line in fid.readlines():
      if line.strip()[0] == "#": continue
      line = line.split(";")
      conversion_table[ nicename(line[1].strip()) ] = nicename(line[0].strip())
      print line[1].strip(), nicename(line[1].strip())
      print "   - Old: %-20s  New: %-20s" % (nicename(line[1]),
                                             nicename(line[0]))

   # - Reading configuration file first
   inputs = utils.inputcheck('archive')
   config = utils.readconfig(inputs = inputs, conversion_table = conversion_table)

   # ----------------------------------------------------------------
   # - Because of the observations we have to compute the
   #   points city by city. Loading city data here first. 
   # ----------------------------------------------------------------
   from pywetterturnier import database
   # - Initializing class and open database connection
   db        = database.database(config)

   # - Loading all different cities (active cities)
   cities     = db.get_cities()
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   db.close()

   # ----------------------------------------------------------------
   # - Now downloading archive files if not allready on disc and
   #   read the content. Note that I have included an exit after
   #   several files.
   # ----------------------------------------------------------------
   print '  * Downloading archive data and process them now'
   for city in cities:

      city = city['name'][0].lower()
   
      print '    City is %s' % city
      # - List of all archive files
      config['current_city'] = city

      archive_files = glob.glob( 'wert_%s/wer*.txt' % city )
      archive_files.sort(reverse=True)

      #archive_files = ["wert_b/wert150313.txt"]

      counter = 0
      for file in archive_files:

         file = file.replace('\n','') 
         #counter = counter + 1

         # ----------------------------------------------------------
         # - Allready processed?
         # ----------------------------------------------------------

         # - Extract tournament date. Used to force a certain file
         #   to be processed ('live' for development).
         print "* Processing file %s" % file
         mtch = re.match(".*wert([0-9]{6}).txt$",file)
         if not mtch:
            print "  File name does not match required pattern, skip"
            continue
         file_date = int("20{0:s}".format(mtch.group(1)))

         # - Force in
         if file_date in [20170616]:
            print "[!] FORCE file {0:s} to database now".format(file)
            file_forced = True
         else:
            file_forced = False
            print '  Checking {0:s}s in logfile'.format(file)
            if os.path.isfile( config['rawdir']+'/archivefiles_processed_%s.txt' % city ):
               aid = open(config['rawdir']+'/archivefiles_processed_%s.txt' % city, 'r')
               aco = aid.readlines()
               aid.close()
               skip = False
               for aline in aco:
                  if file in aline:
                     print '    - ALLREADY PROCESSED. Skip'
                     skip = True
               if skip: continue
                  

         print '* Loading: %s' % (file)

         if counter >= 5: utils.exit('dev stop, counter >= 5 here')

         # - Import first file
         obj = importbets.importbets(config,file_forced)
         obj.loadfilecontent( file )

         obj.identify_city()

         # - Getting data from raw files
         obj.takedata(obj.raw_lines)

         obj.extract_sum_points() 

         obj.extract_obs(1)
         obj.extract_obs(2)

         obj.extract_bets(1)
         obj.extract_bets(2)

         # - Extracting .. points?

         # - Try to get the points of all the users
         obj.extract_parameter_points()

         # - Now extracting bet-times
         #   OH FUCK THIS IS REALLY, REALLY NASTY. 
         #   I NEED TO UPDATE THEM BEFORE TO GET obj.unames
         #   BUT AFER UPDATING THE PINTS THE UPDATE TIME GETS
         #   FUCKED. THIS IS THE REASON TO DO IT AGAIN.
         #   PLEASE DON'T DO THIS .. ELSEWHERE. AT LEAST NOT
         #   IF YOU GET MONNEY FOR THIS SHIT. 
         obj.extract_bettimes()

         obj.close()

         # - If everything was fine, write the file name
         #   into a "logging" file. If filename is allready
         #   in there the script wont process it during
         #   the next run.
         print '    - Everything fine for this file. Write to processed logfile'
         aid = open(config['rawdir']+'/archivefiles_processed_%s.txt' % city, 'a+')
         aid.write('%s\n' % file)
         aid.close()

         print "\n\n"

