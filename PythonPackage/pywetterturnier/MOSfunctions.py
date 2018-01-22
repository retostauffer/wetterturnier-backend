# -------------------------------------------------------------------
# - NAME:        PrepareFunctions.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2017-06-28
# -------------------------------------------------------------------
# - DESCRIPTION:
# -------------------------------------------------------------------
# - EDITORIAL:   2017-06-28, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-22 18:28 on marvin
# -------------------------------------------------------------------


import sys, os
import logging, logging.config
log = logging.getLogger("PrepareMOS.fun")

# -------------------------------------------------------------------
# Small python class to handle reading/printing the MOS forecasts.
# -------------------------------------------------------------------
class MOSclass(object):
   """Initializing the MOSclass object. The object will crash if
   the file specified by the user does not exist given by the two
   input parameters datadir and file.


   Args:
      file (:obj:`str`): Name of the file including full path!
      preferred_order (:obj:`list`): List of strings (or None), list of
        preferred_order how the parameters should be returned.
        When writing the data
        the parameters in this list will be ordered as defined.
        Undefined parameters will be attached to the end.
   """

   _file    = None

   # ----------------------------------------------------------------
   # Initialize new object of this class
   # ----------------------------------------------------------------
   def __init__(self, file, preferred_order = None ):

      self._file    =  file
      self._preferred_order = preferred_order
      log.info("Processing {0:s}".format(self._file))

      if not os.path.isfile( self._file ):
         log.error("Sorry, file \"{0:s}\" does not exist".format(self._file))
         sys.exit(9)

   # ----------------------------------------------------------------
   # Extracts timestamp from file name
   # ----------------------------------------------------------------
   def filename2timestamp( self, file ):
      """Extracting date information from a file name of the form "all.yymmddhh"
      and returns the corresponding unix time stamp.

      Args:
           file (:obj:`str`): Name of the file containing the MOS forecasts,
               have to follow the pattern "*.[0-9]{8}$".
      Returns:
           int: Integer timestamp, seconds since 1970-01-01.
      """

      import re
      from datetime import datetime as dt
      # Extracting date/time information from the file name
      mtch = re.match(".*([0-9]{8})$",file)
      if not mtch:
         log.exit("Problems extracting datetime from file name! Exit.")
         sys.exit(9)
      # Else convert to UNIS time stamp
      return int(dt.strptime(mtch.group(1),"%y%m%d%H").strftime("%s"))


   # ----------------------------------------------------------------
   # Read data
   # ----------------------------------------------------------------
   def read(self):
      """Reading the file as specified when initializing this object.
      Saves everything internally, no return.
      """

      import re
      from datetime import datetime as dt

      fid = open(self._file,"r")

      # Initialize objects to store the data we are reading from the MOS
      # forecasts.
      self.locations = []
      self.models    = []
      self.data      = {}
      parameter      = [] # Store parameters we found

      self.timestamp = self.filename2timestamp( self._file )
       

      keep  = None # Keeps last found location and model. If None
                   # no header line has been found yet
      for line in fid.readlines():
         # Kill carriage return
         line = line.replace("\n","")
         # empty line
         if len(line.strip()) == 0: continue 
         # Else check content of the line
         # 1) Check whether the line is a model description line
         mtch1 = re.match("^[\s+]?([^\s]+)\s[\s+]?([^\s]+).*?$",line)
         # 2) check whether the line is a data line
         mtch2 = re.match("^[\s+]?([A-Za-z]+)\s+(-?[0-9|,|.]+)\s+(-?[0-9|,|.]+).*$",line)

         # If we have not yet found a header line at all and this is no header
         # or description line: just skip.
         if not keep and not mtch1:
            continue
         # If this is a new header line
         elif mtch1:

            # Extract information
            if not mtch1.group(1) in self.locations:
               self.locations.append( mtch1.group(1) )
            if not mtch1.group(2) in self.models:
               self.models.append(    mtch1.group(2) )

            # Append correct elements in self.data to store the data
            if not mtch1.group(1) in self.data.keys():
               #log.debug(print "     + location    ",mtch1.group(1))
               self.data[mtch1.group(1)] = {} # empty dict to store models and data
            if not mtch1.group(2) in self.data[mtch1.group(1)].keys():
               #log.debug("     + location    ",mtch1.group(1),"   model    ",mtch1.group(2))
               self.data[mtch1.group(1)][mtch1.group(2)] = {} # empty dict to store data

            # Keep latest location/model to append the data to self.data
            keep = {"location":mtch1.group(1),"model":mtch1.group(2)}

            
         # If this is a data line: append data
         elif mtch2:
            self.data[keep['location']][keep['model']][mtch2.group(1)] = \
                                           [mtch2.group(2),mtch2.group(3)]
            if not mtch2.group(1) in parameter:
               parameter.append( mtch2.group(1) )

      fid.close()

      # Create a list with parameter names.
      if not self._preferred_order:
         self.parameters = parameter
      else:
         # First stpe: check elements which are given in 
         # self._preferred_order but have not been read from the files.
         # If such parameters exist: drop them.
         self.parameters = []
         for param in self._preferred_order:
            if param in parameter: self.parameters.append(param)
         # Now check if we have read additional parameters. If so,
         # append them to the end.
         for param in parameter:
            if not param in self.parameters: self.parameters.append( param )



   # ----------------------------------------------------------------
   # Output for console
   # ----------------------------------------------------------------
   def show( self ):
      """Shows content of the parsed MOS file, used for development.
      No return, shows content on stdout.
      """

      for city in self.data.keys(): 
         for model in self.data[city].keys():
            log.info(' ---------------------------- ')
            log.info("{0:10s} {1:s}".format(city,model))
            for param in self.data[city][model].keys():
               val = self.data[city][model][param]
               val = " ".join(["%-10s"]*len(val)) % tuple(val)
               log.info("   {0:10s} {1:s}".format(param,val))


   # ----------------------------------------------------------------
   # Helper function to return some information
   # ----------------------------------------------------------------
   def get( self, what ):
      """Helper method to get meta information/information from the
      object itself. Allowed are: timestamp, locations, model, parameters,
      and rawfile.

      Args:
        what (:obj:`str`): One of the above, returns value (or exit's if
            input argument what is unknown).

      Returns:
        Depending on input ``what``.
      """

      if what == "timestamp":     return self.timestamp
      elif what == "locations":   return self.locations
      elif what == "models":      return self.models
      elif what == "parameters":  return self.parameters
      elif what == "rawfile":     return self._file
      else:
         print "Method MOSclass.get cannot understand input argument \"%s\"" % what
         sys.exit(9)

# ----------------------------------------------------------------
# Helper class to create the final object which will be returned
# or stored as json array for the frontend visualization script.
# ----------------------------------------------------------------
class MOSoutput( object ):
   """Converts the parsed information contained in a :class:`MOSclass`
   into JSON which can then be written in the final output file.

   Args:
        loaded (:class:`MOSclass`): Object of class :class:`MOSclass`.
   """

   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def __init__( self, loaded ):

      import os, glob

      # Fetching all the different timestamps
      all_timestamps = []
      for rec in loaded: all_timestamps.append( rec.get("timestamp") )

      # Take overlapping stations
      all_locations  = []
      all_models     = []
      all_parameters = []
      all_rawfiles   = {}
      for MOSobj in loaded:
         for rec in MOSobj.get("locations"):
            if not rec in all_locations:   all_locations.append( rec )
         for rec in MOSobj.get("models"):
            if not rec in all_models:      all_models.append( rec )
         for rec in MOSobj.get("parameters"):
            if not rec in all_parameters:  all_parameters.append( rec )

         # Append rawfile link
         url = "/referrerdata/mos/{0:s}.txt".format( os.path.basename(MOSobj.get("rawfile")) )
         all_rawfiles[MOSobj.get("rawfile")] = url

      # Remove old raw files in output directory
      targetdir = "/var/www/html/referrerdata/mos"
      oldfiles = glob.glob(os.path.join(targetdir,"all.*.txt"))
      for of in oldfiles: os.remove(of)

      # Copy new files
      from shutil import copyfile
      for src,url in all_rawfiles.iteritems():
         target = os.path.join(targetdir,os.path.basename(src)+".txt")
         log.info("Copy %s -> %s" % (src, target))
         copyfile( src, target )

      # Debut print
      from datetime import datetime as dt
      log.debug("  - Found dates")
      for rec in all_timestamps:
         log.debug("    {0:s}".format(dt.fromtimestamp(rec).strftime("%Y-%m-%d %H:%M")))
      log.debug("  - Found raw files")
      log.debug("    {0:s}".format(", ".join(all_rawfiles.keys())))
      log.debug("  - Found locations")
      log.debug("    {0:s}".format(", ".join(all_locations)))
      log.debug("  - Found models")
      log.debug("    {0:s}".format(", ".join(all_models)))
      log.debug("  - Found parameter")
      log.debug("    {0:s}".format(", ".join(all_parameters)))

      # Prepare dict
      self._prepare_data_(loaded,all_rawfiles,all_timestamps,all_locations,all_models,all_parameters)

   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def _prepare_data_(self,loaded,all_rawfiles,all_timestamps,all_locations,all_models,all_parameters):
      """Prepares the data.

      .. todo:: Detailed docstring missing.
      """

      self.data = {"rawfiles":all_rawfiles.values(),
                   "timestamps":all_timestamps,
                   "locations":all_locations,
                   "models":all_models,
                   "parameters":all_parameters}

      # Appending station data
      for MOSobj in loaded:
         self.data["data_{0:d}".format(MOSobj.get("timestamp"))] = MOSobj.data

   
   # ----------------------------------------------------------------
   # ----------------------------------------------------------------
   def data2json( self, file ):
      """Writes the data stored inside the object to a file using JSON format.

      Args:
        file (:obj:`str`): Output file name.
      """

      import json
      fid = open(file,"w")
      fid.write( json.dumps( self.data ) )
      fid.close()

      log.info("JSON written into file \"{0:s}\"".format(file))


