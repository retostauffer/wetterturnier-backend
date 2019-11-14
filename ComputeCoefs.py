from pywetterturnier import database, utils
import numpy
import moses as m

# - Evaluating input arguments
inputs = utils.inputcheck('ComputeMoses')
# - Read configuration file
config = utils.readconfig('config.conf',inputs)

# - Initializing class and open database connection
db        = database.database(config)
# - Loading tdate (day since 1970-01-01) for the tournament.
#   Normaly Friday-Tornament (tdate is then Friday) while
#   the bet-dates are for Saturday and Sunday if there was
#   no input tournament date -t/--tdate.
if config['input_tdate'] == None:
   tdates     = [db.current_tournament()]
else:
   tdates     = [config['input_tdate']]

# - Loading all different cities (active cities)
cities     = db.get_cities()
# - If input city set, then drop all other cities.
if not config['input_city'] == None:
   tmp = []
   for elem in cities:
      if elem['name'] == config['input_city']: tmp.append( elem )
   cities = tmp


#fill list of all cities
tournaments = []
for city in cities:
   tournaments.append( city['name'][0].lower() + "pw" )

print tournaments

# fuer jede Stadt einzeln das Fortran-Programm aufrufen
for t in tournaments:
    m.moses.processmoses(t)
