# - Start as main script (not as module)
if __name__ == '__main__':

   import numpy as np
   # - Wetterturnier specific modules
   from pywetterturnier import utils, database
   # - Evaluating input arguments
   inputs = utils.inputcheck('UserVoting')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)
   post_id   = config['input_param']
   t         = config['input_tdate']
   
   excluded_usernames = ["WB-Berlin","Foehni"]
   excluded_users = [db.get_user_id(i) for i in excluded_usernames]

   for i in ("Automaten", "Referenztipps", "MM-MOS", "WAV2", "Aviatik"):
      group_users = db.get_users_in_group( group=i )
      print(i)
      for j in group_users:
         print(j)
         excluded_users.append( int(j) )

   #find out which users have at least played once in wetterturnier
   sql = "SELECT DISTINCT userID FROM %swetterturnier_betstat"
   cur = db.cursor()
   cur.execute( sql % db.prefix )
   data = cur.fetchall()

   users_played = []
   for i in data:
      #print(int(i[0]))
      users_played.append( int(i[0]) )

   #who of them did actually play this year?
   sql = "SELECT userID FROM %swetterturnier_betstat WHERE tdate BETWEEN 18635 AND 19000 AND userID IN %s ORDER BY userID ASC"
   cur.execute( sql % (db.prefix, db.sql_tuple( users_played) ) )
   data = cur.fetchall()
   
   users_played = []
   users = sorted([i[0] for i in data])
   users_unique = np.unique(users)

   for i in users_unique:
      if np.count_nonzero(users == i) >= 20:
         users_played.append(i)

   print( users_played )

   sql = "SELECT user_login FROM %susers WHERE ID NOT IN %s %sAND ID IN %s ORDER BY user_login ASC"

   skip = str("")
   for i in ("GRP_%", "Acinn%", "%-MOS%"):
      skip += "AND user_login NOT LIKE '%s' " %i
   print(skip)


   cur.execute( sql % ( db.prefix, db.sql_tuple( excluded_users ), skip[:-1], db.sql_tuple( users_played ) ) )
   data = cur.fetchall()

   data = data[:t]

   for i in data:
      print( i[0] )

   count = len(data)

   users_str = str("")
   for i in enumerate(data):
      user = i[1][0]
      users_str += 'i:%d;a:2:{s:2:"id";i:%d;s:8:"response";s:%d:"%s";}' % (i[0], i[0]+1, len(user), user)

   _poll_responses = "a:%d:{%s}" % ( len(data), users_str )

   print(_poll_responses)

   #insert in database; table wp_postmeta

   try:
      print( int(post_id) )
   except:
      import sys
      sys.exit("post_id (-p) not set!")

   sql = "UPDATE %spostmeta SET meta_value='%s' WHERE post_id=%s AND `meta_key` = '_poll_responses'"
   cur.execute( sql % ( db.prefix, _poll_responses, post_id ) )
   db.commit()
