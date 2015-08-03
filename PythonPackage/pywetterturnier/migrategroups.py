# -------------------------------------------------------------------
# - NAME:        migrategroups.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-14
# -------------------------------------------------------------------
# - DESCRIPTION: Migrate groups and users.
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-14, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2014-09-14 20:41 on sculptor.uberspace.de
# -------------------------------------------------------------------


class migrategroups(object):

   # ----------------------------------------------------------------
   # - Init
   # ----------------------------------------------------------------
   def __init__(self,config):
      """Downloading the groups list file from wetterturnier.de,
      Parse the content and create groups and its users if they
      are not allready existing."""

      from database import database

      self.config = config
      self.db = database(config)

      # - Downloading the file
      self.rawfile = 'raw/migrategroups.txt'
      self.__download_file__()
      self.__read_rawfile__()

   # ----------------------------------------------------------------
   # - Downloading the file
   # ----------------------------------------------------------------
   def __download_file__(self):
      """Downloading the html file and store locally"""

      import subprocess as sub
      import utils

      print '  * Downloading file %s' % self.rawfile

      cmd = ['wget','http://www.wetterturnier.de/mitteltipps.php',
             '-O',self.rawfile]
      p = sub.Popen(cmd,stdout=sub.PIPE,stderr=sub.PIPE)
      p.communicate()
      
      # - Error?
      if not p.returncode == 0:
         print 'ERROR: %s' % err
         print 'OUTPUT: %s' % out
         utils.exit('Problems downloading the mitteltipps file')


   # ----------------------------------------------------------------
   # - Reading the php file
   # ----------------------------------------------------------------
   def __read_rawfile__(self):
      """Parsing raw file and import groups and users."""

      import re
      import utils
      
      fid = open(self.rawfile,'r')
      lines = fid.readlines()
      fid.close()

      # - Create a dict object and save
      #   groups and users to them.
      res = {}

      # - Looping trough lines, search ul
      found = False
      group = None
      for line in lines:

         if not found and not '<ul type="circle">' in line:
            continue
         elif '<ul type="circle">' in line:
            found = True
            continue

         # - if it is a h3 tag, it is a group name.
         if '<h3' in line:
            rawgroup = re.sub('<[^<]+?>', '',line).strip()
            group    = utils.nicename( rawgroup )
            print '    %-30s %-30s' % (group,rawgroup)
            res[group] = {'rawgroup':rawgroup,'users':{}}
            continue
         # - Reached the end
         elif '</ul>' in line:
            break

         # - Else (if not empty) a user.
         rawuser = re.sub('<[^<]+?>', '',line).strip()
         user    = utils.nicename( rawuser )
         if len(user) == 0:
            continue
         else:
            print '    - %-30s %-30s' % (user,rawuser)
            res[group]['users'][user] = rawuser

      print '    Finished ...'

      self.data = res

   
   # ----------------------------------------------------------------
   # - Check and create groups and theyr users loaded
   #   from the list of the tournament website.
   # ----------------------------------------------------------------
   def create_groups_and_users(self):

      import utils

      for group in self.data:
         desc = self.data[group]['rawgroup']
         users = self.data[group]['users']

         self.db.create_group( group, desc )
         self.db.create_user( 'GRP_'+group )

         # - Adding usres to group
         for user in users:
            self.db.create_user(user)
            self.db.create_groupuser(user,group,'1990-01-01 00:00:00',1)
















