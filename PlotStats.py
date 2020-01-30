# -------------------------------------------------------------------
# - Embedded function. Can be used on its own (called from
#   CleanUpBets.py)
#   IF STARTED AS A SCRIPT PLEASE CHECK THE PART BELOW THE 
#   FUNCTION HERE!
# -------------------------------------------------------------------
from pywetterturnier import utils
import sys, os
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as pl
from scipy.optimize import curve_fit
import matplotlib.dates as mdates
import matplotlib.cbook as cbook
import pandas as pd

years = mdates.YearLocator()   # every year
months = mdates.MonthLocator()  # every month
years_fmt = mdates.DateFormatter('%Y')

#fit functions
func = lambda x, p, q, r, s : p*x**3 + q*x**2 + r*x + s

e_func = lambda x, a, b, c : a * np.log(b * x) + c

#log_func = lambda x, T, U, V : T * np.log(U / x) + V

#sigmoid = lambda x, x0, k : 1 / (1 + np.exp(-k*(x-x0)))


def plot(db, cities, tdate, verbose=False):
   boxdata, hashes = [], []
   cur = db.cursor()

   #prepare figure for multi-participations plots (all cities)
   figx, axx = pl.subplots()
   all_citystats = []

   #get dates for BER to get the maximum timespan
   sql = "SELECT tdate FROM wp_wetterturnier_tdatestats WHERE cityID=1 ORDER BY tdate"
   dataX = pd.read_sql_query(sql, db)
   datesX = []
   for i in dataX["tdate"].values:
      datesX.append( utils.tdate2datetime(i) )


   # ----------------------------------------------------------------
   # - Now going over the cities and plot some graphs with matplotlib 
   # ----------------------------------------------------------------
   for city in cities:
      boxdata.append([])
      hashes.append(city['hash'])
      #we want to exclude sleepy and all referenztipps
      exclude = [db.get_user_id("Sleepy")]
      groupID = db.get_group_id( "Referenztipps" )
      for j in db.get_participants_in_group( groupID, city['ID'], tdate, playing=False ):
         exclude.append( j )

      sql = "SELECT points FROM wp_wetterturnier_betstat WHERE cityID=%d AND tdate<%d AND userID NOT IN%s"
      cur.execute( sql % (city['ID'], tdate, tuple(exclude) ) )
      data = cur.fetchall()
      for i in data:
         if i[0] is False or i[0] is None:
            continue
         else: boxdata[city['ID']-1].append( i[0] )

      sql = "SELECT * FROM wp_wetterturnier_tdatestats WHERE cityID="+str(city['ID'])+" AND tdate<"+str(tdate)+" ORDER BY tdate"
      data = pd.read_sql_query(sql, db)
      tdates = data["tdate"].values
      dates = []
      for i in tdates:
         dates.append( utils.tdate2datetime(i) )

      part = data["part"    ].values
      sql = "SELECT max_part, min_part, mean_part, tdates FROM wp_wetterturnier_citystats WHERE cityID=%d"
      cur.execute( sql % city['ID'] )
      partdata = cur.fetchall()
      citystats = []
      for i in range(3):
         citystats.append( partdata[0][i] )
      #TODO print citystats on graphs

      ### PLOT PARTICIPANT COUNT (CURRENT CITY)
      fig, ax = pl.subplots()
      ax.plot_date( dates, part, marker=".", markeredgecolor="black", linestyle="-")
      for i,col in zip(range(3), ["r","b","g"]):
         ax.axhline( citystats[i], c=col )

      # format the ticks
      ax.xaxis.set_major_locator(years)
      ax.xaxis.set_major_formatter(years_fmt)
      ax.xaxis.set_minor_locator(months)

      # round to nearest years.
      datemin = np.datetime64(dates[0], 'Y')
      datemax = np.datetime64(dates[-1], 'Y') + np.timedelta64(1, 'Y')
      ax.set_xlim(datemin, datemax)

      # format the coords message box
      ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

      ax.set_xlabel("Tournament")
      ax.set_ylabel("Participants")
      ax.set_title("Participants in "+city['name'])
      ax.grid(True)

      fig.set_size_inches(16,9)
      fig.autofmt_xdate()
      pl.savefig("plots/"+city['hash']+"/parts", dpi=96)

      ### PLOT PARTICIPANT COUNT (ALL CITIES)
      axx.plot_date( dates, part, "-", label=city['name'])
      all_citystats.append(citystats)
      #WE DONT SAVE THE PLOT YET, LOOK OUTSIDE OF LOOP


      for i, day in zip(["","_d1","_d2"], [""," (Saturday)"," (Sunday)"]):
         median=data["median"+i].values
         mean = data["mean"  +i].values
         sd   = data["sd"    +i].values
         sd_u = data["sd_upp"+i].values
         MAX  = data["max"   +i].values
         MIN  = data["min"   +i].values
         part = data["part"    ].values
         Qlow = data["Qlow"  +i].values
         Qupp = data["Qupp"  +i].values

         rang = MAX - MIN
         median1 = MAX - median
         median0 = median - MIN

         x = np.array(tdates) #transform your data in a numpy array of floats
         y = np.array(median) #so the curve_fit can work

         #find missing median values (d1,d2 error in ZUR)
         which = []
         for ii, yi in enumerate(y):
            if np.isnan(yi):
               which.append(ii)

         #for var in [x, y, dates, Qlow, Qupp, MIN, MAX, median1, median0, sd, sd_u]:
         #   exec("var = np.delete(var, which)")

         x = np.delete(x, which)
         y = np.delete(y, which)
         pdates = np.delete(dates, which)
         Qlow, Qupp = np.delete(Qlow, which), np.delete(Qupp, which)
         MIN, MAX   = np.delete(MIN,  which), np.delete(MAX, which)
         median1, median0, sd, sd_u = np.delete(median1, which), np.delete(median0, which), np.delete(sd, which), np.delete(sd_u, which)

         #make the curve_fit
         popt, pcov = curve_fit(func, x, y)
         if verbose:
            print(city['hash'])
            print("POLY FIT:")
            print("a = %s , b = %s, c = %s, d = %s" % (popt[0], popt[1], popt[2], popt[3]) )
         stats = {"p" : popt[0], "q" : popt[1], "r" : popt[2], "s" : popt[3]}
         if i == "":
            db.upsert_stats( city["ID"], stats ) 
         eopt, ecov = curve_fit(e_func, x, y)
         if verbose:
            print("EXP FIT:")
            print("a = %s , b = %s, c = %s" % (eopt[0], eopt[1], eopt[2]) )
         stats = {"A" : eopt[0], "B" : eopt[1], "C" : eopt[2]}
         if i == "":
            db.upsert_stats( city["ID"], stats )

         #sopt, scov = curve_fit(sigmoid, x, y, p0=[10000, 0.005], method='dogbox' )
         #print("SIGMOID FIT:")
         #print("x0 = %s , k = %s" % (sopt[0], sopt[1]) )

         ### PLOT MEDIAN
         fig, ax = pl.subplots()
         ax.plot_date( pdates, x, label="Median", linestyle="-", marker="")
         ax.plot_date( pdates, func(x, *popt), "-g", label="Poly-Fitted Curve")
         ax.plot_date( pdates, e_func(x, *eopt), "-r", label="Log-Fitted Curve")

         # format the ticks
         ax.xaxis.set_major_locator(years)
         ax.xaxis.set_major_formatter(years_fmt)
         ax.xaxis.set_minor_locator(months)

         # round to nearest years.
         datemin = np.datetime64(pdates[0], 'Y')
         datemax = np.datetime64(pdates[-1], 'Y') + np.timedelta64(1, 'Y')
         ax.set_xlim(datemin, datemax)

         # format the coords message box
         ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

         ax.set_xlabel("Tournament")
         ax.set_ylabel("Median(points)")
         ax.set_title("Median Points in "+city['name']+day)

         ax.grid(True)

         fig.set_size_inches(16,9)
         ax.legend()
         fig.autofmt_xdate()
         fig.savefig("plots/"+city['hash']+"/median"+i, dpi=96)

         ### MEDIAN + IQR
         ax.fill_between(pdates, Qlow, Qupp, color="grey")
         ax.set_title("Median Points + IQR in "+city['name']+day)
         fig.savefig("plots/"+city['hash']+"/median_IQR"+i, dpi=96)


         ### PLOT MEDIAN + RANGE
         fig, ax = pl.subplots()
         ax.plot_date( pdates, x, label="Median", linestyle="-", marker="")
         ax.plot_date( pdates, func(x, *popt), "-g", label="Poly-Fitted Curve")
         ax.plot_date( pdates, e_func(x, *eopt), "-r", label="Log-Fitted Curve")
         ax.fill_between( pdates, MIN, MAX, color="grey", alpha=0.5)

         # format the ticks
         ax.xaxis.set_major_locator(years)
         ax.xaxis.set_major_formatter(years_fmt)
         ax.xaxis.set_minor_locator(months)

         # round to nearest years.
         datemin = np.datetime64(pdates[0], 'Y')
         datemax = np.datetime64(pdates[-1], 'Y') + np.timedelta64(1, 'Y')
         ax.set_xlim(datemin, datemax)

         # format the coords message box
         ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

         ax.set_xlabel("Tournament")
         ax.set_ylabel("Median(points)")
         ax.set_title("Median Points + Range in "+city['name']+day)

         ax.grid(True)

         fig.set_size_inches(16,9)
         ax.legend()
         fig.autofmt_xdate()
         fig.savefig("plots/"+city['hash']+"/median_range"+i, dpi=96)


         ### PLOT MEAN + SD
         y = np.array(mean) #so the curve_fit can work
         if which:
            y = np.delete(y, which)

         popt, pcov = curve_fit(func, x, y)
         if verbose:
            print(city['hash'])
            print("POLY FIT:")
            print("a = %s , b = %s, c = %s, d = %s" % (popt[0], popt[1], popt[2], popt[3]) )
         eopt, ecov = curve_fit(e_func, x, y, p0=[0.5,2,4])
         if verbose:
            print("EXP FIT:")
            print("a = %s , b = %s, c = %s" % (eopt[0], eopt[1], eopt[2]) )
         #sopt, scov = curve_fit(sigmoid, x, y, p0=[10000, 0.005], method='dogbox' )

         fig, ax = pl.subplots()
         ax.plot_date( pdates, y, label="Mean", linestyle="-", marker="")
         ax.plot_date( pdates, func(x, *popt), "-g", label="Poly-Fitted Curve")
         ax.plot_date( pdates, e_func(x, *eopt), "-r", label="Log-Fitted Curve")
         ax.fill_between( pdates, y-sd, y+sd, color="grey", alpha=0.5)

         # format the ticks
         ax.xaxis.set_major_locator(years)
         ax.xaxis.set_major_formatter(years_fmt)
         ax.xaxis.set_minor_locator(months)

         # round to nearest years.
         datemin = np.datetime64(pdates[0], 'Y')
         datemax = np.datetime64(pdates[-1], 'Y') + np.timedelta64(1, 'Y')
         ax.set_xlim(datemin, datemax)

         # format the coords message box
         ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

         ax.set_xlabel("Tournament")
         ax.set_ylabel("Mean(points)")
         ax.set_title("Mean Points + SD in "+city['name']+day)

         ax.grid(True)

         fig.set_size_inches(16,9)
         ax.legend()
         fig.autofmt_xdate()
         fig.savefig("plots/"+city['hash']+"/mean_sd"+i, dpi=96)


         ### PLOT MAX, MIN, median1, median0, sd with exact same settings
         datas = [MAX, MIN, median1, median0, sd, sd_u]
         ylabs = ["Max(points)","Min(points)","Max(points) - Median","Median - Min(points)","SD","SD(upper)"]
         titles = ["Maximum of points","Minimum of points","Maximum of points - Median","Median - Minimum of points","Standard deviation", "Standard deviation of upper half"]
         filenames = ["max","min","max-median","median-min","sd","sd_upp"]

         for dat, ylab, title, filename in zip(datas, ylabs, titles, filenames):
            fig, ax = pl.subplots()
            ax.plot_date( pdates, dat, marker=".", markeredgecolor="black", label = ylab )

            (m, n) = np.polyfit(x, dat, 1)
            yp = np.polyval([m, n], x)

            eopt, ecov = curve_fit(e_func, x, dat)

            #insert m,b to database (citystats)
            if filename+i == "sd_upp":
               if verbose:
                  print "SD_upp:\nm = %f | n = %f" % (m, n)
                  print("LOG FIT:")
                  print("T = %s , U = %s, V = %s" % (eopt[0], eopt[1], eopt[2]) )
               stats = {"m" : m, "n" : n, "T" : eopt[0], "U" : eopt[1], "V" : eopt[2]}
               db.upsert_stats( city["ID"], stats )

            ax.plot_date( pdates, yp, "-r", label="Linear Fit" )
            ax.plot_date( pdates, e_func(x, *eopt), "-g", label="Log-Fit" )          

            # format the ticks
            ax.xaxis.set_major_locator(years)
            ax.xaxis.set_major_formatter(years_fmt)
            ax.xaxis.set_minor_locator(months)

            # round to nearest years.
            datemin = np.datetime64(pdates[0], 'Y')
            datemax = np.datetime64(pdates[-1], 'Y') + np.timedelta64(1, 'Y')
            ax.set_xlim(datemin, datemax)

            # format the coords message box
            ax.format_xdata = mdates.DateFormatter('%Y-%m-%d')

            ax.set_xlabel("Tournament")
            ax.set_ylabel( ylab )
            ax.set_title( title + " in " + city['name'] + day )

            ax.grid(True)

            fig.set_size_inches(16,9)
            ax.legend()
            fig.autofmt_xdate()
            fig.savefig("plots/"+city['hash']+"/"+filename+i, dpi=96)
            pl.close("all")

   #save participation plot for all cities
   # format the ticks
   axx.xaxis.set_major_locator(years)
   axx.xaxis.set_major_formatter(years_fmt)
   axx.xaxis.set_minor_locator(months)
         
   # round to nearest years.
   datemin = np.datetime64(datesX[0], 'Y')
   datemax = np.datetime64(datesX[-1], 'Y') + np.timedelta64(1, 'Y')
   axx.set_xlim(datemin, datemax)

   # format the coords message box
   axx.format_xdata = mdates.DateFormatter('%Y-%m-%d')

   axx.set_xlabel("Tournament")
   axx.set_ylabel("Participants")
   axx.set_title("Participants in all cities")
   axx.grid(True)
   axx.legend()

   figx.set_size_inches(16,9)
   figx.autofmt_xdate()
   figx.savefig("plots/parts", dpi=96)
   pl.close("all") 

   #save boxplot for all cities
   fig, ax = pl.subplots()
   ax.boxplot( boxdata, showfliers=False, whiskerprops = dict(linestyle='-',linewidth=3, color='black'), medianprops = dict(linestyle=':', linewidth=3, color='firebrick'), boxprops = dict(linestyle='-', linewidth=3, color='darkgoldenrod'), capprops=dict(linewidth=3) )
   ax.grid( True )
   ax.set_title("Boxplot of points for all cities")
   ax.set_xlabel("City")
   ax.set_xticks(list(range( 1, len(cities)+1 )))
   ax.set_xticklabels(hashes)
   ax.set_ylabel("Points")

   fig.set_size_inches( 16,9 )
   fig.savefig("plots/boxplot", dpi=96)
   pl.close("all")

   #plot of mean+sd to compare difficulty of all cities
   meancities, sdcities = [], []
   for i in boxdata:
      meancities.append( np.mean(i) )
      sdcities.append( np.std(i, ddof=1) )
   fig, ax = pl.subplots()

   x = list(range( 1, len(cities)+1 ))
   ax.errorbar( x, meancities, yerr=sdcities, fmt='o', ecolor='blue', mec="black", marker="x", capsize=30, ms=25, lw=3, capthick=3 )
   ax.grid( True )
   ax.set_title("Mean+SD of points for all cities")
   ax.set_xlabel("City")
   ax.set_xticks(x)
   ax.set_xticklabels(hashes)
   ax.set_ylabel("Points")

   fig.set_size_inches( 16,9 )
   fig.savefig("plots/mean_sd", dpi=96)
   pl.close("all")

# - Start as main script (not as module)
# -------------------------------------------------------------------
if __name__ == '__main__':

   # - need to import the database
   from pywetterturnier import database, utils

   # - Evaluating input arguments
   inputs = utils.inputcheck('PlotStats')
   # - Read configuration file
   config = utils.readconfig('config.conf',inputs)

   # - Initializing class and open database connection
   db        = database.database(config)

   # ----------------------------------------------------------------
   # - Loading all different cities (active cities)
   cities     = db.get_cities()

   #TODO: only accepted input should be city!
   # - If input city set, then drop all other cities.
   if not config['input_city'] == None:
      tmp = []
      for elem in cities:
         if elem['name'] == config['input_city']: tmp.append( elem )
      cities = tmp

   if config['input_verbose'] == None:
      verbose = False
   else: verbose = config['input_verbose']

   if config['input_tdate'] == None:
      tdate     = db.current_tournament()
      print '  * Current tournament is %s' % utils.tdate2string( tdate )
   else:
      tdate = config['input_tdate']

   # - Calling the function now
   plot(db, cities, tdate, verbose=verbose)

   db.commit()
   db.close()
