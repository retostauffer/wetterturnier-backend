# -------------------------------------------------------------------
# - NAME:        autosubmit.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-31
# - VERSION:     0.1-1, August 2015
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Helper script to give the users the option to
#                use the autosubmit option as simple as possible.
#                Uses ConfigParser to read a special ASCII file
#                containing all necessary infos to make use of the
#                autosubmit.
#                WARNING: the script does ont check if all parameters
#                are set! Which means: if you forget to submit all
#                parameters you wont join the tournament as only
#                full tips will be used to compute the points.
#                However, the benefit is that we can easily extend
#                the parameter list if there will be other parameters
#                in the wetterturnier somewhen in the future
#                (not planned yet).
# -------------------------------------------------------------------
# - ERROR CODES: The error codes returned by the server-side php
#                script which takes your bet. Currently used:
#
#                error 11:     login not successful
#                error 12:     city cannot be found in database
#                error 13:     tournament is closed 
#                error 14:     at least one required input missing
#                              (e.g, user, password, ...)
#
#                Note: this python file will exit with the same
#                error code if one of these errors occur.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-31, RS: Created file on thinkreto.
#                2015-07-31, RS: Put version 0.1 online today.
#                2015-08-02, RS: Added more interpretable
#                error code handling (via string search).
# -------------------------------------------------------------------
# - LICENCE:     Wetterturnier Autosubmit by Reto Stauffer is
#                licensed under a Creative Commons
#                Attribution-ShareAlike 4.0 International License.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-03 14:46 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


# - Parsing inputs
from optparse import OptionParser

# -------------------------------------------------------------------
# - Parsing inputs
# -------------------------------------------------------------------
def parse_inputs():
   """Parsing input arguments to the main script"""

   parser = OptionParser(usage="usage: %prog [options]")
   
   parser.add_option("-s","--silent",action="store_true",dest="silent",default=False,
                     help="If set the logfile (containing server-side infos) will not be shown.")

   parser.add_option("-d","--dry-run",action="store_true",dest="dryrun",default=False,
                     help="If try-run is set the script wont submit the data to the wetterturnier")
   
   parser.add_option("-f","--filename",action="store",dest="filename",type="string",default=None,
                     help="File name of the ASCII file with the parameter/value pairs")
   
   (options, args) = parser.parse_args()
   if not options.filename:
      parser.error("Required input -f/--file not given!")
   elif not os.path.isfile( options.filename ):
      parser.error("Cannot find file \"%s\" as given as input." % options.filename )

   print "\n  * Script started, using options:"
   print "    - Dry-run option:       %s" % options.dryrun
   print "    - Script is silent:     %s" % options.silent
   print "    - Input file:           %s" % options.filename
   print "\n"

   return options
   
   
# -------------------------------------------------------------------
# - Parsing file
# -------------------------------------------------------------------
class read_file_content( object ):
   def __init__(self,options):
      import sys, os
      from ConfigParser import ConfigParser
      self.options = options

      CNF = ConfigParser()
      CNF.optionxform=str          # prevent script to ignore cases
      CNF.read( options.filename ) # reading config file

      # - If section [general settings] is missing or
      #   section [parameters] missing: stop
      if   not CNF.has_section("general settings"):
         sys.exit("ERROR: file does not contain required [general settings] section!")
      elif not CNF.has_section("parameters"):
         sys.exit("ERROR: file does not contain required [parameters] section!")

      # - Else areading [general settings] section, we need
      #   three arguments which is 'city','user','password'. If
      #   at least one is missing: stop.
      required = ['url','user','password','city']
      for req in required:
         if not CNF.has_option('general settings',req):
            sys.exit("ERROR: option \"%s\" in section [general settings] not defined." % req)
      # - Read these 3 strings
      self.url      = CNF.get('general settings','url')
      self.user     = CNF.get('general settings','user')
      self.password = CNF.get('general settings','password')
      self.city     = CNF.get('general settings','city')
      # - If logfile is defined: take argument. Else
      #   logfile is just options.filename+"log"
      if not CNF.has_option('general settings','logfile'):
         self.logfile = "%s.log" % options.filename
      else:
         self.logfile = CNF.get('general settings','logfile')
         self.logfile = self.logfile.replace("%city%",self.city)
         self.logfile = self.logfile.replace("%user%",self.user)

      # - Now reading parameters
      self.data = {}
      params = CNF.items('parameters')
      for rec in params:
         self.data[rec[0]] = CNF.getfloat('parameters',rec[0])

      # - Create options string
      self.args = "city=%s&user=%s&password=%s" % (self.city,self.user,self.password)
      for key, val in self.data.iteritems(): 
         self.args += "&%s=%.1f" % (key,val)

      # - Create list object wihch can be used in subprocess. 
      self.cmd = ['wget',self.url,'--post-data',self.args,'-O',self.logfile]

      # - Create command string (for copy and paste users)
      #   For wget with POST request
      self.cmdstring = "wget %s --post-data \"%s\" -O %s" % (self.url,self.args,self.logfile) 

      # - GET request
      if not self.url[-1] == "/":
         self.geturl = "%s/?%s" % (self.url,self.args) 
      else:
         self.geturl = "%s?%s" % (self.url,self.args) 

   # Summary
   def summary(self):

      print "\n  * Summary of the parsed data:"
      print "    - City:           %s" % self.city
      print "    - User:           %s" % self.city
      print "    - Password:       %s" % ("*"*len(self.password))
      print "    - Submit URL:     %s" % self.url 
      print "" # just a spacer
      print "    - Parameters loaded:"
      for key, val in self.data.iteritems():
         print "      %-10s %8.1f" % (key,val)

      # - If this was a dryrun just show the options
      if self.options.dryrun:
         print "\n  * You have choosen the dryrun option."
         print "    These are the commands which could be executed"
         print "    to submit the data via autosubmit."
         print "\n    Command to submit the data (POST, preferred!):"
         print "    - %s" % self.cmdstring
         print "\n    Command to submit via GET (copy to browser, for testing!):"
         print "    - %s" % self.geturl
         print "" # just a spacer


# -------------------------------------------------------------------
# - Main script part
# -------------------------------------------------------------------
if __name__ == "__main__":
   """Script has to be run as the main script."""

   import sys, os

   # - Parsing input arguments
   options = parse_inputs()
   
   # - Reading config from input file.
   data = read_file_content( options )

   # - If dryrun was choosen: just show the data
   data.summary()

   # - Execute command
   if not options.dryrun:

      import re, subprocess
      sub = subprocess.call(data.cmd,stdout=subprocess.PIPE,
               stderr=subprocess.PIPE)

      sub = subprocess.Popen(data.cmd,stdout=subprocess.PIPE,
               stderr=subprocess.PIPE)

      out,err = sub.communicate()

      # - Reading logfile
      logcontent = open(data.logfile,'r').readlines()
      logcontent = "".join( logcontent )
      logcontent = re.sub("<.*?>", " ", logcontent)
      if not options.silent:
         print " -------------------------logfile content------------------------- "
         print "                 logfile: %s" % data.logfile
         print logcontent
         print " -------------------------logfile content------------------------- "


      # - no errors reported
      print ""
      if sub.returncode == 0:
         print "[+] Wget return code was ok (equal to 0)" 
      else:
         print "[!] Wget exit code == %d" % sub.returncode
         print "    Everything != 0 indicates a problem. There is something wrong!" 
         print "    : Exit python with return code %d as well:" % sub.returncode
         sys.exit(sub.returncode)

      # - Evaluating the logcontent and see if we got
      #   an error code from the php script in there
      match = re.search(r"AUTOSUBMIT ERRORCODE [0-9]{1,}",logcontent)
      if not match == None:
         match = logcontent[match.start():match.end()]
         code  = re.search(r"[0-9]{1,}",match)
         code  = int(match[code.start():code.end()])
         if type(code) == type(int()) and code != 0:
            print "\n[!] Wetterturnier server-side script returned exit code %d" % code
            print "    Everything != 0 is an error. Check the logfile."
            print "    : Exit python with return codde %d as well:" % code
            sys.exit(code)













