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

def plot(db, cities, tdate):

   # ----------------------------------------------------------------
   # - Now going over the cities and plot some graphs with matplotlib 
   # ----------------------------------------------------------------
   for city in cities:

      sql = "SELECT * FROM wp_wetterturnier_tdatestats WHERE cityID="+str(city['ID'])+" AND tdate<"+str(tdate)+" ORDER BY tdate"
      data = pd.read_sql_query(sql, db)
      tdates = data["tdate"].values
      dates = []
      for i in tdates:
         dates.append( utils.tdate2datetime(i) )
      median = data["median"].values
      mean = data["mean"].values
      sd   = data["sd"].values
      MAX  = data["max"].values
      MIN  = data["min"].values
      part = data["part"].values
      Qlow = data["Qlow"].values
      Qupp = data["Qupp"].values

      rang = []
      for max, min in zip(MAX, MIN):
         rang.append( max - min )
      rang = MAX - MIN

      x = np.array(tdates) #transform your data in a numpy array of floats
      y = np.array(median) #so the curve_fit can work

      """
      create a function to fit with your data. a, b, c and d are the coefficients
      that curve_fit will calculate for you.
      In this part you need to guess and/or use mathematical knowledge to find
      a function that resembles your data
      """

      func = lambda x, a, b, c, d : a*x**3 + b*x**2 + c*x + d

      e_func = lambda x, a, b, c : a * np.log(b * x) + c

      sigmoid = lambda x, x0, k : 1 / (1 + np.exp(-k*(x-x0)))


      """
      make the curve_fit
      """
      print(city['hash'])
      popt, pcov = curve_fit(func, x, y)
      print("POLY FIT:")
      print("a = %s , b = %s, c = %s, d = %s" % (popt[0], popt[1], popt[2], popt[3]) )
      eopt, ecov = curve_fit(e_func, x, y, p0=[0.5,2,4])
      print("EXP FIT:")
      print("a = %s , b = %s, c = %s" % (eopt[0], eopt[1], eopt[2]) )
      sopt, scov = curve_fit(sigmoid, x, y, p0=[10000, 0.005], method='dogbox' )
      #print("SIGMOID FIT:")
      #print("x0 = %s , k = %s" % (sopt[0], sopt[1]) )
      """
      The result is:
      popt[0] = a , popt[1] = b, popt[2] = c and popt[3] = d of the function,
      so f(x) = popt[0]*x**3 + popt[1]*x**2 + popt[2]*x + popt[3].
      """

      """
      Use sympy to generate the latex sintax of the function
      """
      #xs = sp.Symbol('\lambda')    
      #tex = sp.latex(func(xs,*popt)).replace('$', '')


      ### PLOT MEDIAN

      fig, ax = pl.subplots()
      ax.plot_date( dates, median, label="Median", linestyle="-", marker="")
      ax.plot_date( dates, func(x, *popt), "-r", label="Poly-Fitted Curve")
      ax.plot_date( dates, e_func(x, *eopt), "-g", label="Exp-Fitted Curve")

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
      ax.set_ylabel("Median(points)")
      ax.set_title("Median Points of "+city['hash'])

      ax.grid(True)

      fig.set_size_inches(16,9)
      ax.legend()
      fig.autofmt_xdate()
      fig.savefig("plots/median_"+city['hash'], dpi=96)

      ### MEDIAN + IQR
      ax.fill_between(dates, Qlow, Qupp, color="grey")
      ax.set_title("Median Points + IQR of "+city['hash'])
      fig.savefig("plots/median_IQR_"+city['hash'], dpi=96)


      ### PLOT MEDIAN + RANGE
      fig, ax = pl.subplots()
      ax.plot_date( dates, median, label="Median", linestyle="-", marker="")
      ax.plot_date( dates, func(x, *popt), "-r", label="Poly-Fitted Curve")
      ax.plot_date( dates, e_func(x, *eopt), "-g", label="Exp-Fitted Curve")
      ax.fill_between(dates, MIN, MAX, color="grey", alpha=0.5)

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
      ax.set_ylabel("Median(points)")
      ax.set_title("Median Points + Range of "+city['hash'])

      ax.grid(True)

      fig.set_size_inches(16,9)
      ax.legend()
      fig.autofmt_xdate()
      fig.savefig("plots/median_range_"+city['hash'], dpi=96)


      ### PLOT PARTICIPANT COUNT
      fig, ax = pl.subplots()
      ax.plot_date( dates, part, marker=".", markeredgecolor="black", linestyle="-")

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
      ax.set_title("Participants in "+city['hash'])
      ax.grid(True)

      fig.set_size_inches(16,9)
      fig.autofmt_xdate()
      pl.savefig("plots/parts_"+city['hash'] , dpi=96)


      ### PLOT MEAN + SD
      y = np.array(mean) #so the curve_fit can work

      print(city['hash'])
      popt, pcov = curve_fit(func, x, y)
      print("POLY FIT:")
      print("a = %s , b = %s, c = %s, d = %s" % (popt[0], popt[1], popt[2], popt[3]) )
      eopt, ecov = curve_fit(e_func, x, y, p0=[0.5,2,4])
      print("EXP FIT:")
      print("a = %s , b = %s, c = %s" % (eopt[0], eopt[1], eopt[2]) )
      sopt, scov = curve_fit(sigmoid, x, y, p0=[10000, 0.005], method='dogbox' )

      fig, ax = pl.subplots()
      ax.plot_date( dates, y, label="Mean", linestyle="-", marker="")
      ax.plot_date( dates, func(x, *popt), "-r", label="Poly-Fitted Curve")
      ax.plot_date( dates, e_func(x, *eopt), "-g", label="Exp-Fitted Curve")
      ax.fill_between(dates, y-sd, y+sd, color="grey", alpha=0.5)

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
      ax.set_ylabel("Mean(points)")
      ax.set_title("Mean Points + SD of "+city['hash'])

      ax.grid(True)

      fig.set_size_inches(16,9)
      ax.legend()
      fig.autofmt_xdate()
      fig.savefig("plots/mean_"+city['hash'], dpi=96)


      ### PLOT SD ONLY + LINEAR FIT
      fig, ax = pl.subplots()
      ax.plot_date( dates, sd, marker=".", markeredgecolor="black", label="SD")

      (m, b) = np.polyfit(x, sd, 1)
      print(m, b)
      yp = np.polyval([m, b], x)
      ax.plot_date( dates, yp, "-r", label="Linear Fit")

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
      ax.set_ylabel("SD(points)")
      ax.set_title("Standard deviation of "+city['hash'])

      ax.grid(True)

      fig.set_size_inches(16,9)
      ax.legend()
      fig.autofmt_xdate()
      fig.savefig("plots/sd_"+city['hash'], dpi=96)


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

   if config['input_tdate'] == None:
      tdate     = db.current_tournament()
      print '  * Current tournament is %s' % utils.tdate2string( tdate )
   else:
      tdate = config['input_tdate']

   # - Calling the function now
   plot(db, cities, tdate)

   db.commit()
   db.close()
