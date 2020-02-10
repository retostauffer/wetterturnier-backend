def get_moses_coefs(self, cityID, tdate):
   """
   TODO: docstring
   """
   cur = self.db.cursor()
   moses = {}
   params = self.get_parameter_names()
   for param in params:
      moses[param] = {}
      paramID = self.get_parameter_id( param )
      sql = "SELECT userID, coef FROM %swetterturnier_coefs WHERE cityID=%d AND tdate=%d AND paramID=%d"
      cur.execute( sql % ( self.prefix, cityID, tdate, paramID ) )
      data = cur.fetchall()
      for i in data:
	      moses[param][int(i[0])] = i[1]
   return moses


def upsert_moses_coefs(self, cityID, tdate, moses):
   """
   TODO: docstring
   """
   cur = self.db.cursor()
   for param in moses.keys():
      paramID = self.get_parameter_id( param )
      for userID in moses[param].keys():
	      #print userID
	      coef = moses[param][userID]
	      sql = "INSERT INTO %swetterturnier_coefs (cityID, userID, paramID, tdate, coef) VALUES %s ON DUPLICATE KEY UPDATE coef=VALUES(coef)"
	      #print sql % ( self.prefix, sql_tuple( [cityID, userID, paramID, tdate, coef] ) )
	      cur.execute( sql % ( self.prefix, str(tuple( [cityID, userID, paramID, tdate, coef] ) ) ) )
