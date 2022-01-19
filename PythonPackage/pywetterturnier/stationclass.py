# -------------------------------------------------------------------
# - NAME:        stationclass.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-24
# -------------------------------------------------------------------
# - DESCRIPTION: An easy to use stations class.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-24, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2018-01-22 12:04 on marvin
# -------------------------------------------------------------------


"""Class to handle stations. Stations are used for the observations. While
user forecasts are linked to a specific city which can contain one or more
stations the observations itself are only valid for a very specific station.
This class allows to handle specific stations.
"""
class stationclass( object ):
   """A small class holding all infos for a specific WMO station.

   Args:
      desc (:obj:`list`): List/tuple of strings, value description of the values
         in input data.
      data (:obj:`list`): Values corresponding to input desc.
      db (:obj:`None` or :class:`database.database`): Default None,
         can be the database handler. The internal
         function self._has_db_connector_ can be used to check if the
         database handler has been set or not.
   """
   print("check")
   #WHY the fuck did need to add a print here for the next line 2 work?!?!?!
   def __init__( self, desc, data, db = None, dbprefix = None ):
      """Initializing a new stationclss object.
      """ 

      # - Prepare cols
      cols = [str( i[0] ) for i in desc]

      ## Station ID in the database. 
      self.ID         = None 
      ## Station WMO number.
      self.wmo        = None 
      ## To which city the station maches, city ID from database.
      self.cityID     = None 
      ## String, name of the station.
      self.name       = None 
      ## Date the station was changed the last time.
      self.changed    = None  
      ## Save database handler
      self.db         = db
      self.dbprefix   = dbprefix

      # - Save all different values onto the object
      if 'ID'         in cols:  self.ID         = int( data[cols.index('ID')] )
      if 'wmo'        in cols:  self.wmo        = int( data[cols.index('wmo')] )
      if 'cityID'     in cols:  self.cityID     = int( data[cols.index('cityID')] )
      if 'name'       in cols:  self.name       = str( data[cols.index('name')] )
      if 'changed'    in cols:  self.changed    = data[cols.index('changed')] 

      # - Shows full stationclass config.
      ###self.show()

   # ----------------------------------------------------------------
   # Checks if database handler is given or not (well, only checks
   # whether it is None or not).
   # ----------------------------------------------------------------
   def _has_db_connector_( self ):
      """Checks if the object already contains a db connector (if
      database connection has been opened or not).
      """
      if not self.db or not self.dbprefix:     return False
      else:                                    return True

   # ----------------------------------------------------------------
   # Returns active parameters for a specific city for a specific
   # tournament date!
   # ----------------------------------------------------------------
   def getActiveParams( self, tdate ):
      """Returns active parameters for a specific city for a specific
      tourmanet date. This is important as they active parameters can
      change over time while the system still has to know which ones
      have obeen active/inactive over the past.

      Args:
         tdate (:obj:`int`): Turnament date as days since 1970-01-01.

      Returns:
         list: Returns a list of ...

      .. todo:: Document return list format.
      """

      # Check if database connection is set or not
      if not self._has_db_connector_():
         import sys;
         sys.exit("stationsclass.getAcriveParams requires database connection. Not set.")
      
      # Loading active parameters for the tdate.
      from datetime import datetime as dt
      bgn = dt.fromtimestamp( int(tdate)    *86400 ).strftime("%Y-%m-%d %H:%M:%S")
      end = dt.fromtimestamp( (int(tdate)+1)*86400 ).strftime("%Y-%m-%d %H:%M:%S")

      sql = []
      sql.append("SELECT paramID FROM (SELECT paramID,")
      sql.append("CASE WHEN ( since <= '{0:s}' AND (until = 0 OR until >= '{1:s}'))".format(bgn,end))
      sql.append("THEN 1 ELSE 0 END AS active FROM {0:s}wetterturnier_stationparams WHERE".format(self.dbprefix))
      sql.append("stationID = {0:d}) AS tmp WHERE active = 1;".format(int(self.ID)))

      # Fetching parameter ID's of active parameters (given tdate)
      cur = self.db.cursor()
      cur.execute( " ".join(sql) )
      paramIDs = [int( i[0] ) for i in cur.fetchall()]
      paramIDs.sort()
      return paramIDs

   # ----------------------------------------------------------------
   # - Helper function. Shows content.
   # ----------------------------------------------------------------
   def show(self):
      """Small summary function which prints the content of a stationclass
      object in a nice way.
      """

      from datetime import datetime as dt
      import json

      print("    Show station-object settings:")
      print("    - Station ID:           %d" % self.ID)
      print("    - WMO station number:   %d" % self.wmo)
      print("    - Station name:         %s" % self.name)
      print("    - City ID:              %d" % self.cityID)
      print("    - Last changed:         %s" % self.changed.strftime('%Y-%m-%d %H:%M'))
