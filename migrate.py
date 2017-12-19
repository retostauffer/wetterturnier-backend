# -------------------------------------------------------------------
# - NAME:        migrate.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-14
# -------------------------------------------------------------------
# - DESCRIPTION:
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-14, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2017-12-19 13:30 on prognose2
# -------------------------------------------------------------------


import sys

#sys.exit('THIS SCRIPT WAS FOR MIGRATIOIN ... ')

if __name__ == '__main__':

   import sys, os
   import hashlib # to create md5 passwords
   from pywetterturnier import utils
   from pywetterturnier import migrategroups
   from pywetterturnier import database

   # - Reading configuration file first
   config = utils.readconfig()

   # - Migrate mitspieler.txt file with
   #   passwords ans shit?
   if config['migrate_mitspieler']: 

      db = database.database(config)

      print '  * Migrating mitspieler list'
      try:
         fid = open(config['migrate_mitspielerfile'],'r')
      except:
         utils.exit('Cannot read file %s' % config['migrate_mitspielerfile'])

      # - Write changed usernames to file
      # A local file to store all users where 
      # the username changed because of special characters.
      try:
          ufile = open('changed_usernames.txt','w+')
      except:
          utils.exit('Problems creating file changed_usernames.txt write mode')

      # - Else loop trough file and convert usernames and
      #   passwords to prepare for database
      res = []
      for line in fid.readlines():
         line = line.strip()
         words = line.split()
         if not len(words) == 2 or len(line) == 0:
            print '    - Skip: %2d %s' % (len(words), line); continue
         elif words[1] == 'station':
            print '    - Skip user: %s' % line; continue
         elif words[0] == 'end':
            print '    - Reached the end ...'; break

         # - Generate nicename and password.
         newname = utils.nicename(words[0])
         md5pass = hashlib.md5( words[1] ).hexdigest()
   
         # - Check if user is a group
         groupID = db.get_group_id( newname )
         if not groupID == False:
            newname = 'GRP_%s' % newname
         
         # - Changed username because of special characters?
         if not words[0] == newname:
            ufile.write('         %-s & %-s \\\\\n' % (words[0], newname))

         print '    - %-25s %s' % (newname, md5pass)

         # - Check if user exists or not. If existig, just update
         #   the password. Else create new user.
         db.create_user( newname, words[1] )

      ufile.close()

   # - Migrate groups from wetterturnire.de if
   #   flag set in config file.
   if config['migrate_groups']:
      groups = migrategroups.migrategroups(config)
      groups.create_groups_and_users()















