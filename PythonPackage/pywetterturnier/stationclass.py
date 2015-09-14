# -------------------------------------------------------------------
# - NAME:        stationclass.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-24
# -------------------------------------------------------------------
# - DESCRIPTION: An easy to use stations class.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-24, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-04 11:41 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


class stationclass( object ):
   """!A small class holding all infors for a specific WMO station."""

   def __init__( self, desc, data ):
      """!Initializing a new stationclss object.
      @param desc. List/tuple of strings, value description of the values
         in input data.
      @param data. List/tuple of values corresponding to input desc.
      """ 

      # - Prepare cols
      cols = []
      for rec in desc: cols.append( str(rec[0]) )

      ## Station ID in the database. 
      self.ID         = None 
      ## Station WMO number.
      self.wmo        = None 
      ## To which city the station maches, city ID from database.
      self.cityID     = None 
      ## String, name of the station.
      self.name       = None 
      ## The nullconfig is a list of ID's where each ID corresponds to a parameter
      #  in the database (parameterID). All parameters included in the nullconfig
      #  are labeled as 'this station does NOT report this value at all'.
      self.nullconfig = None 
      ## Date the station was changed the last time.
      self.changed    = None  

      # - Save all different values onto the object
      if 'ID'         in cols:  self.ID         = int( data[cols.index('ID')] )
      if 'wmo'        in cols:  self.wmo        = int( data[cols.index('wmo')] )
      if 'cityID'     in cols:  self.cityID     = int( data[cols.index('cityID')] )
      if 'name'       in cols:  self.name       = str( data[cols.index('name')] )
      if 'nullconfig' in cols:  self.nullconfig = data[cols.index('nullconfig')]
      if 'changed'    in cols:  self.changed    = data[cols.index('changed')] 

      # -------------------------------------------------------------
      # - Converting nullconfig. Is either NULL or an array as
      #   a string of the form "[1,2,3]" where the ID's correspond
      #   to paramID which should not be concidered.
      # -------------------------------------------------------------
      if type(self.nullconfig) == type(str()): 
         # - Empty nullconfig
         if len(self.nullconfig.strip()) == 0:
            self.nullconfig = None
         else:
            import json
            self.nullconfig = json.loads( self.nullconfig )

      # - Shows full stationclass config.
      ###self.show()


   # ----------------------------------------------------------------
   # - Helper function. Shows content.
   # ----------------------------------------------------------------
   def show(self):
      """!Small summary function which prints the content of a stationclass
      object in a nice way."""

      from datetime import datetime as dt
      import json

      print "    Show station-object settings:"
      print "    - Station ID:           %d" % self.ID
      print "    - WMO station number:   %d" % self.wmo
      print "    - Station name:         %s" % self.name
      print "    - City ID:              %d" % self.cityID
      if not self.nullconfig:
         print "    - Nullconfig:           %s" % "No nullconfig set" 
      else:
         print "    - Nullconfig:           %s" % json.dumps(self.nullconfig)
      print "    - Last changed:         %s" % self.changed.strftime('%Y-%m-%d %H:%M')
      












