# -------------------------------------------------------------------
# - NAME:        stationclass.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2015-07-24
# -------------------------------------------------------------------
# - DESCRIPTION: An easy to use stations class.
# -------------------------------------------------------------------
# - EDITORIAL:   2015-07-24, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-07-24 07:41 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------


class stationclass( object ):

   def __init__( self, desc, data ):

      # - Prepare cols
      cols = []
      for rec in desc: cols.append( str(rec[0]) )

      # - Empty entries first
      self.ID         = None 
      self.wmo        = None 
      self.cityID     = None 
      self.name       = None 
      self.nullconfig = None 
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
      












