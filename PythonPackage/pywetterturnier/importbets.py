

import MySQLdb
import os, sys
import utils
import database

class importbets:
    """! USED TO IMPORT OLD ARCHIVE DATA FROM THE OLD WETTERTURNIER.
    AS I WILL NEVER USE THIS ROUTINE AGAIN I DONT DO THE DOCUMENTATION
    FOR ALL THE METHODS IN HERE."""

    data1 = None
    data2 = None

    cityID = None

    prefix = 'wp_'
    db_users  = prefix + 'users'
    db_param  = prefix + 'wetterturnier_param'
    db_bets   = prefix + 'wetterturnier_bets'
    db_betstat   = prefix + 'wetterturnier_betstat'
    db_cities = prefix + 'wetterturnier_cities'
    db_obs    = prefix + 'wetterturnier_obs'

    unames    = None

    # ---------------------------------------------------------------
    # - Init method
    # ---------------------------------------------------------------
    def __init__(self,config):

        self.config = config

        host   = self.config['mysql_host']
        user   = self.config['mysql_user']
        passwd = self.config['mysql_pass']
        db     = self.config['mysql_db']

        print '* Establishing database connection'
        self.db = database.database(config) 

    # ---------------------------------------------------------------
    # - Loading data from uri, then extract first and second block
    #   Input can be uri (file=False!) or a file name (file=True!)
    # ---------------------------------------------------------------
    def loadfile(self,uri,file=False):

        from datetime import datetime as dt
        import urllib

        def getLines(code):
            return code.readlines()

        def findstring(lines,string,start=0):
            for i in range(start,len(lines)):
                if string in lines[i]:
                    return i
            return None

        # -----------------------------------------------------------
        # - Reading data from url
        #   Find hash in lines
        # -----------------------------------------------------------
        if not file:
            code = urllib.urlopen(uri)
            lines = getLines(code)
        else:
            fid = open(uri,'r')
            lines = fid.readlines()
            fid.close()
            
        self.raw_lines = lines


    # ---------------------------------------------------------------
    # - Simply import a file.
    # ---------------------------------------------------------------
    def loadfilecontent(self,file):

      import os
      import utils

      if not os.path.isfile(file):
         utils.exit('In importbets.loadfilecontent error: cannot find file %s' % file)

      fid = open(file,'r'); self.raw_lines = fid.readlines(); fid.close()

    # ---------------------------------------------------------------
    # - Loading data from uri, then extract first and second block
    #   Input can be uri (file=False!) or a file name (file=True!)
    # ---------------------------------------------------------------
    def takedata(self,lines,file=False):

        from datetime import datetime as dt

        def getLines(code):
            res = []
            i = 0
            while i < 400:
                res.append(str(code.readline()))
                i+=1
            return res
    
        def findstring(lines,string,start=0):
            for i in range(start,len(lines)):
                if string in lines[i]:
                    return i
            return None

        # - Rewrite lines
        self.raw_lines = lines
    
        # ---------------------------------------------------------------
        # - Tournament date
        # ---------------------------------------------------------------
        a = findstring(lines,'Wetterprognoseturnier')
        date = lines[a].strip()[-10:]
    
        # ---------------------------------------------------------------
        # - Getting data. Searching for Samstag:, Sonntag: and 
        #   the datum again which defines the blocks. 
        # ---------------------------------------------------------------
        b1_from = findstring(lines,'Samstag:')
        b2_from = findstring(lines,'Sonntag:')
        b1_to   = b2_from
        if not file:
            b2_to   = findstring(lines,date,b2_from)
        else:
            b2_to   = len(lines)

        # ---------------------------------------------------------------
        # - Searching for the block where the Abgabezeiten are set
        # ---------------------------------------------------------------
        t1_from = findstring(lines,'Abgabezeitpunkt:')
        t1_to   = findstring(lines,'Auswertung Prognose')

        # ---------------------------------------------------------------
        # - Searching for the block where the Point sums are set
        # ---------------------------------------------------------------
        p_from = findstring(lines,'Punkte')
        p_to   = findstring(lines,'durchschnittliche Punktzahl')
        if not p_to:
            p_to   = findstring(lines,'aktuelle Jahreszeitenwertung')

        # ---------------------------------------------------------------
        # - Create timestamp
        # ---------------------------------------------------------------
        self.tournamentdate = ( dt.strptime(date,'%d.%m.%Y') - \
                                dt.strptime('1970-01-01 00:00','%Y-%m-%d %H:%M') ).days
    
        # ---------------------------------------------------------------
        # - Info
        # ---------------------------------------------------------------
        print '* loadfile method says'
        print '  - %-20s %s' % ('Date from:',date)
        print '  - %-20s %3d %3d' % ('Block Saturday:',b1_from,b1_to)
        print '  - %-20s %3d %3d' % ('Block sunday:',b2_from,b2_to)
        if not p_from == None and not p_to == None:
            print '  - %-20s %d %d' % ('The points:',p_from,p_to)

        self.data1 = lines[b1_from:b1_to]
        self.data2 = lines[b2_from:b2_to]

        # - Observations do start at the same position as the bets
        #   but we have to read just the next 5 lines.
        self.obs1  = lines[b1_from:(b1_from+5)]
        self.obs2  = lines[b2_from:(b2_from+5)]

        if p_from == None or p_to == None:
            self.points = None
        else:
            self.points = lines[p_from:p_to]

        # - The times where the bets have been placed
        if t1_from == None or t1_to == None:
            self.bettimes = None
            print 'Have not found start/end for bettimes! t1_from/t1_to wrong (None)'
        else:
            self.bettimes = lines[t1_from:t1_to]
            print '  - %-20s %d %d' % ('Block bettimes:',t1_from,t1_to)

    # ---------------------------------------------------------------
    # - Identify city and load city ID from database
    # ---------------------------------------------------------------
    def identify_city(self):

        from pywetterturnier import utils

        print "* Try to identify city based on the first few lines of the file"

        # - Only try first 5 lines.
        city_hash = False
        for line in self.raw_lines[0:5]:
            if not 'Wetterprognoseturnier' in line: continue

            if 'Innsbruck' in line:
                city_hash = 'IBK'
            elif 'Berlin' in line:
                city_hash = 'BER'
            elif 'Wien' in line:
                city_hash = 'VIE'
            elif 'Leipzig' in line:
                city_hash = 'LEI'
            elif 'richer' in line:
                city_hash = 'ZUR'
            elif 'rcher' in line:
                city_hash = 'ZUR'
            else:
               utils.exit('Problems identifying city in utils.identify_city in %s' % line)

        if not city_hash:
            print self.raw_lines[0:5]
            utils.exit('cannot identify city: in identify_city method')

        # Loading ID from database
        sql = "SELECT ID FROM " + self.db_cities + " WHERE " + \
             "hash = \"" + city_hash + "\""
        cur = self.db.cursor()
        cur.execute(sql)
        ID = cur.fetchone()[0]
        try:
            ID = int(ID)
        except:
            utils.exit('Problem converting the city ID into an integer value!')

        print '  - Identified city as [%s] with ID [%d]' % (city_hash, ID)

        self.cityID = ID


    # ---------------------------------------------------------------
    # - Extracting bettimes now 
    # ---------------------------------------------------------------
    def extract_bettimes(self):

        import re
        import datetime as dt
        from pywetterturnier import utils

        data = self.bettimes
        if data == None:
            print '[!] WARNING bettimes not found. Data empty. Skip.'
            return

        # betdate is
        tdate = self.tournamentdate
        print '* Extracting bettimes for date %d' % (tdate)

        # - Check if cityID is set
        if self.cityID == None:
            utils.exit('STOP. cityID equals None. Stop now')

        # - Caching usernames to extract the points afterwards. hopefully.
        unames = [] 

        # - Going trough lines.
        #   Stop if we find a user without user ID.
        res = []
        found = False
        for line in data:
            if "_________________" in line:
                found = True
                continue
            if not found:
                continue
            # - Link to jump to the top. Ignore.
            if "ganz nach oben" in line:
                continue

            line = line.replace('\n','').strip()
            if len(line) == 0:
               continue 

            # - Username and its nicename
            username = line.split()[0].strip()
            unames.append( username ) 
            time     = " ".join(line.split()[1:])
            # - For Friday, no offset
            #   Oh c'mon wetterturnier scripters. Fuck it.
            if 'xxxxx' in time:
               tdate_str = dt.datetime.fromtimestamp( 16332*86400 ).strftime('%Y-%m-%d') 
               time = "%s %s" % (tdate_str,'16:00:00')
            else:
               if time[0:3] == 'UTC':
                  print 'WRNOG TIME FORMAT, SKIP'
                  continue
               if 'Fri' in time: 
                  tdate_offset = 0
               elif 'Mon' in time:
                  tdate_offset = -4 
               elif 'Tue' in time:
                  tdate_offset = -3 
               elif 'Wed' in time:
                  tdate_offset = -2
               elif 'Thu' in time:
                  tdate_offset = -1 
               elif 'Sat' in time:
                  tdate_offset = 1 
               elif 'Sun' in time:
                  tdate_offset = 2
               else:
                  print time
                  print line.strip() 
                  print '[!] BET TIME FANCY DAY NAME IN DATE. CHEATED? :)'
                  utils.exit('reto think about it') 
                  
               tdate_str = dt.datetime.fromtimestamp( (tdate+tdate_offset)*86400 ).strftime('%Y-%m-%d') 
               time = "%s %s" % (tdate_str,time.split()[1])
            #time = dt.datetime.strptime(time,'%Y-%m-%d %H:%M:%S').strftime('%s')
            nicename = utils.nicename( username )
            # - Check if we have found a group
            if not self.db.get_group_id( nicename ) == False:
               nicename = 'GRP_%s' % nicename
            # - Now get username 
            userID = self.db.get_user_id_and_create_if_necessary( nicename )
            # - Problem detected.
            if not userID:
               utils.exit('Problems loading userID for %s' % nicename)

            print '    - [%3d] %-30s %-30s %s' % (userID,username,nicename,time)

            # - Append
            res.append( (time,userID,tdate,self.cityID) )

        # - Insert into database
        print '    - Update database now'
        cur = self.db.cursor()
        sql = 'UPDATE '+self.db.prefix+'wetterturnier_bets SET placed = %s ' + \
              ' WHERE userID = %s AND tournamentdate = %s AND cityID = %s'
        cur.executemany( sql, res )
        self.db.commit()
 
        # - Appending cached raw usernames to the object
        #   This will be used to extract the points afterwards.
        self.unames = unames 



    # ---------------------------------------------------------------
    # - Extracting user parameter points now. That is a test. 
    # ---------------------------------------------------------------
    def extract_parameter_points(self):

        if self.unames == None:
            utils.exit('sorry. importbets.unames not set, cannot extract the points')

        print '\n  * %s' % 'Extracting the points for the different parameters now'

        # - Cacing results 
        res = []

        for uname in self.unames:
            found = False
            day = None
            # - Convert raw username (in uname) into nicename
            nicename = utils.nicename( uname )
            # - Check if we have found a group
            if not self.db.get_group_id( nicename ) == False:
               nicename = 'GRP_%s' % nicename
            # - Now get username 
            userID = self.db.get_user_id_and_create_if_necessary( nicename )
            # - Problem detected.
            if not userID:
               utils.exit('Problems loading userID for %s' % nicename)

            # - Extracting points for which user?
            print '  - Extracting parameter points for: %s, city %s' % (nicename,self.config['current_city'])

            # - Now scanning the lines to get the user points
            for line in self.raw_lines:
                # - Check nicename in line
                if 'Auswertung' in line:
                    if uname == utils.nicename( line.split('Spieler')[1].replace(':','').strip() ) \
                       or uname.replace('GRP_','') == utils.nicename( line.split('Spieler')[1].replace(':','').strip()):
                        found = True
                        print '    Found line %s' % line.replace('\n','').strip()
                        continue
                    else:
                        continue
                elif not found:
                    continue 

                # - Found a day?
                if 'Samstag' in line:
                    day = 1
                    continue
                elif 'Sonntag' in line:
                    day = 2
                    continue
                elif len( line.strip() ) == 0:
                    continue
                elif 'Wert' in line:
                    continue
                elif '________' in line:
                    continue

                # - Next Auwertung? JUMP!
                if 'unktzahl' in line:
                    found = False
                    continue

                # - Extracting the parameter
                words = line.split()
                paramID = self.db.get_parameter_id( words[0] )
                try:
                    points = float( words[-1] )
                except:
                    print words
                    utils.exit('Problems getting points from that line')
                if not paramID:
                    utils.exit('Problems extracting parameter or getting paramID from line')
                
                #print ' %5d %8.2f %s ' % (paramID,points,line.strip())

                # - Results caching. Need
                #   userID               form self.db.get_user( uname )
                #   cityID               from self.cityID
                #   paramID              from self.db.get_parameter_id( ... )
                #   tournamentdate       from self.tournamentdate
                #   betdate              from self.tournamentdate + day
                res.append( (points, userID,paramID, \
                             self.tournamentdate,self.tournamentdate + day) )


        sql = 'UPDATE '+self.db.prefix+'wetterturnier_bets SET points = %s ' + \
              ' WHERE userID = %s AND paramID = %s AND tournamentdate = %s ' + \
              ' AND betdate = %s AND cityID = ' + str(self.cityID)
        cur = self.db.cursor()
        cur.executemany( sql , res ) 
        self.db.commit()
    

    # ---------------------------------------------------------------
    # - Extracting sum points for the users 
    # ---------------------------------------------------------------
    def extract_sum_points(self):

        print '\n  * %s' % 'Extracting the sum points for the players'

        import re

        # - Cacing results 
        res = []

        found = False
        for line in self.points:

            psum = None
            pd1  = None
            pd2  = None

            line = line.strip()
            if 'Name' in line and 'Punkte' in line:
                continue
            elif len(line) == 0:
                continue
            elif '____________' in line:
                found = True
                continue
            elif not found:
                continue

            tmp = line.split()
            print '  - Found rawname %s: ' % tmp[1]
            print '    ResT:         %s  ' % ' '.join(tmp[2:])
            rawdata = ''.join(tmp[2:])
            rawdata = rawdata.split(')')[0]
            data = filter(None,re.split( '[\(//\)]', rawdata))
            if not len(data) == 3 and not len(data) == 1:
                utils.exit('Cannot split \'%s\' as expected' % rawdata) 
            if len(data) == 3:
                try:
                   psum = float(data[0])
                   pd1  = float(data[1])
                   pd2  = float(data[2])
                except:
                   utils.exit('Problems getting points as float from \'%s\'' % rawdata)
            else:
                try:
                   psum = float(data[0])
                   pd1  = False
                   pd2  = False 
                except:
                   utils.exit('Problems getting points as float from \'%s\'' % rawdata)

            # - Convert raw username (in uname) into nicename
            nicename = utils.nicename( tmp[1] )
            # - Check if we have found a group
            if not self.db.get_group_id( nicename ) == False:
               nicename = 'GRP_%s' % nicename
            # - Now get username 
            userID = self.db.get_user_id_and_create_if_necessary( nicename )
            # - Problem detected.
            if not userID:
               utils.exit('Problems loading userID for %s' % nicename)

            # - Extracting points for which user?
            print '    Extracting parameter points for: %s' % nicename
            print '    %7.2f   %7.2f   %7.2f' % (psum,pd1,pd2)

            if not pd1:
               res.append( (userID, self.cityID, self.tournamentdate, psum) )
            else:
               res.append( (userID, self.cityID, self.tournamentdate, psum, pd1, pd2) )


        if len(res[1]) == 6:
            #sql = 'INSERT INTO '+self.db.prefix+'wetterturnier_betstat ' + \
            sql = 'INSERT INTO '+self.db_betstat+' ' + \
                  ' (userID, cityID, tdate, points, points_d1, points_d2) VALUES ' + \
                  ' (%s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE ' + \
                  ' points=VALUES(points), points_d1=VALUES(points_d1), ' + \
                  ' points_d2=VALUES(points_d2) '
        else:
            sql = 'INSERT INTO '+self.db_betstat+' ' + \
                  ' (userID, cityID, tdate, points) VALUES ' + \
                  ' (%s, %s, %s, %s) ON DUPLICATE KEY UPDATE ' + \
                  ' points=VALUES(points) '

        cur = self.db.cursor()
        cur.executemany( sql , res ) 
        self.db.commit()


    # ---------------------------------------------------------------
    # - Extracting obs now 
    # ---------------------------------------------------------------
    def extract_obs(self,block):

        import re
        from pywetterturnier import utils
        if block == 1:
            data = self.obs1
        elif block == 2:
            data = self.obs2
        else:
            utils.exit('wrong input to extract_obs. 1 or 2 allowed')

        # betdate is
        tdate = self.tournamentdate
        betdate = tdate + block
        print '* Extracting obs for block %d' % (block)

        # - Check if cityID is set
        if self.cityID == None:
            utils.exit('cityID equals None. Stop now')

        # - Loading parameters
        param = data[1].replace('WvWn','Wv Wn').split()[1:]

        # - First: find empty line. Those are followed by the
        #   single bets until another empty line shows up or until
        #   the end is reached..
        found = False
        obscount = 0
        print "\n".join(data)
        for line in data:
            line = line.replace('\n','').strip()
            if "_________________" in line:
                found = True
                continue
            if not found:
                continue

            # - Getting station name
            rawname = line.split()[0].strip()
            station_name = utils.nicename( rawname )
            wmo = self.__get_wmo_number__(station_name)
            if not wmo:
                utils.exit('Cannot find wmo number for station ' + station_name + ' in config file')
            print '  - Found station ' + str(wmo) + ' ' + station_name

            # - Check if we do have enough values 
            if not file:
                if not len(param) == len(line[26:].split()):
                    utils.exit('parameter length and data length not matching in obs line')
                obs = line[26:].split()
            else:
                # parse that shit by hand
                obs = []
                for i in range(len(param)):
                    obs.append(" ")
                # now try to read whats here

                if len( line[len(rawname):] ) == 0: continue
                data = line[len(rawname):].split()
                if not len(param) == len(data):
                    #utils.exit('noch nicht alle obs da, stop')
                    print 'noch nicht alle obs da, skip'
                    continue
                for i in range(len(param)):
                    obs[i] = data[i]

            # - Else write data into database
            for i in range(0,len(param)):
                paramID = self.wp_get_param_id(param[i])
                if paramID == None:
                    utils.exit('found param which does not exist in db')
                if len(obs[i].strip()) == 0:
                    continue
                #####print wmo,paramID,betdate,obs[i]
                self.__insert_obs_to_db__(wmo,paramID,betdate,obs[i])

            # - Increase obscount. If 2: break
            obscount = obscount + 1
            if obscount == 2:
                break;

        self.db.commit()


    # ---------------------------------------------------------------
    # - Insert bets into the database.
    # ---------------------------------------------------------------
    def __insert_obs_to_db__(self,station,paramID,bdate,value):

        from pywetterturnier import utils

        # - Skip if it was not observed.
        if value.strip() == 'n':
            return True

        # - Else convert
        if value == 'x': return
        try:
            value = int(round( float(value) * 10. ))
        except:
            utils.exit('could not convert value to float')

        sql = 'INSERT INTO ' + self.db_obs + ' (station, paramID, betdate, value) VALUES ' + \
              '({0:d},{1:d},{2:d},{3:d}) ON DUPLICATE KEY UPDATE value = {3:d}' \
              .format(int(station),int(paramID),int(bdate),value)

        print '  obs sql: %8d %3d %8d %f' % (int(station),int(paramID),int(bdate),value)
        cur = self.db.cursor(); cur.execute(sql)


    # ---------------------------------------------------------------
    # - Get wmo number from config.
    # ---------------------------------------------------------------
    def __get_wmo_number__(self,string):

        # - Lower string from config file
        string = string.lower()
        for key in self.config['stations'].keys():
            if key == string.strip():
                return self.config['stations'][key]
        # - Remove underline (LeipzigSchkeuditz is sometimes Leupzig_Schkeudiz
        for key in self.config['stations'].keys():
            if key == string.strip().replace('_',''):
                return self.config['stations'][key]
        return False 

         
    # ---------------------------------------------------------------
    # - Extracting bets now
    # ---------------------------------------------------------------
    def extract_bets(self,block):

        from pywetterturnier import utils
        import re
        if block == 1:
            data = self.data1
        elif block == 2:
            data = self.data2
        else:
            utils.exit('wrong input to extract_bets. 1 or 2 allowed')

        # betdate is
        tdate = self.tournamentdate
        betdate = tdate + block
        print '* Extracting data from block %d' % (block)

        # - Check if cityID is set
        if self.cityID == None:
            utils.exit('STOP. cityID equals None. Stop now')

        # - Loading parameters
        param = data[1].replace('WvWn','Wv Wn').split()[1:]

        self.unames = []
        # - First: find empty line. Those are followed by the
        #   single bets until another empty line shows up or until
        #   the end is reached..
        found = False
        countdown = None
        for line in data:
            line = line.replace('\n','').strip()
            if "______________" in line:
                countdown = 3
                continue
            elif not countdown == None:
                countdown = countdown - 1
                if countdown == 0:
                    countdown = None
                    found = True
                continue
            elif not found:
                continue
            if "ganz nach oben" in line:
                continue
            elif len(line.strip()) == 0:
                continue
            orig = line.split()[0]
            username = utils.nicename( orig )
            # - Check if we have found a group
            if not self.db.get_group_id( username ) == False:
               username = 'GRP_%s' % username
            # - Now get username 
            userID = self.db.get_user_id_and_create_if_necessary( username )
            # - Problem detected.
            if not userID:
               utils.exit('Problems loading userID for %s' % username)
            self.unames.append(username)

            if not len(param) == len(line[len(orig):].split()):
                utils.exit('parameter length and data length not matching')

            print '  - %-25s %d' % (username, userID)

            # - Else write data into database
            data = line[len(orig):].split()
            for i in range(0,len(param)):
                paramID = self.wp_get_param_id(param[i])
                if paramID == None:
                    utils.exit('found param which does not exist in db')
                #print userID,paramID,tdate,betdate,data[i]
                self.__insert_bet_to_db__(userID,paramID,tdate,betdate,data[i])
                self.__insert_betstat_to_db__(userID,tdate)

        self.db.commit()

    # ---------------------------------------------------------------
    # - Insert bets into the database.
    # ---------------------------------------------------------------
    def __insert_bet_to_db__(self,userID,paramID,tdate,bdate,value):

        from pywetterturnier import utils

        if value == 'x': return
        try:
            value = int(round( float(value) * 10. ))
        except:
            utils.exit('could not convert value to float')

        sql = 'INSERT INTO ' + self.db_bets + ' (userID, cityID, paramID, ' + \
              'tournamentdate, betdate, value) VALUES ' + \
              '({0:d},{1:d},{2:d},{3:d},{4:d},{5:d}) ON DUPLICATE KEY UPDATE value = {5:d}' \
              .format(int(userID),int(self.cityID),int(paramID),int(tdate),int(bdate),value)
        cur = self.db.cursor(); cur.execute(sql)

    # ---------------------------------------------------------------
    # - Insert betstat into the database.
    # ---------------------------------------------------------------
    def __insert_betstat_to_db__(self,userID,tdate):

        sql = 'INSERT INTO ' + self.db_betstat + ' (userID, cityID, tdate) VALUES ' + \
              '({0:d},{1:d},{2:d}) ON DUPLICATE KEY UPDATE tdate = {2:d}' \
              .format(int(userID),int(self.cityID),int(tdate))
        cur = self.db.cursor(); cur.execute(sql)


    # ---------------------------------------------------------------
    # - Create user if not existing 
    # ---------------------------------------------------------------
    def wp_create_user(self,username):

        if not self.wp_user_exists(username):
            cur = self.db.cursor()
            sql = 'INSERT INTO ' + self.db_users + \
                  ' (user_login,user_nicename,display_name) ' + \
                  ' VALUES (\'{0:s}\', \'{0:s}\', \'{0:s}\') '.format(username)
            cur.execute(sql) 

    # ---------------------------------------------------------------
    # - Checks if user exists
    # ---------------------------------------------------------------
    def wp_user_exists(self,username):

        userID = self.db.get_user_id(username)
        if userID == None:
            return False
        else:
            return True

    # ---------------------------------------------------------------
    # - Returns user id if user exists 
    # ---------------------------------------------------------------
    def wp_get_param_id(self,paramname):

        cur = self.db.cursor()
        cur.execute('SELECT paramID FROM ' + self.db_param + \
                    ' WHERE paramName = \"' + paramname + '\"')
        data = cur.fetchone()
        if data == None:
            return None 
        else:
            return data[0] 


    # ---------------------------------------------------------------
    def close(self):

        self.db.close()
