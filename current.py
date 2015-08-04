# -------------------------------------------------------------------
# - NAME:        current.py
# - AUTHOR:      Reto Stauffer
# - DATE:        2014-09-16
# - LICENSE: GPL-3, Reto Stauffer, copyright 2014
# -------------------------------------------------------------------
# - DESCRIPTION: Downloading and parsing the current wetterturnier
#                data from wetterturnier.de
# -------------------------------------------------------------------
# - EDITORIAL:   2014-09-16, RS: Created file on thinkreto.
# -------------------------------------------------------------------
# - L@ST MODIFIED: 2015-08-04 09:33 on prognose2.met.fu-berlin.de
# -------------------------------------------------------------------



# - Only start if called as main routine
if __name__ == '__main__':

   import subprocess as sub
   import getopt
   # - Wetterturnier specific modules
   from pywetterturnier import utils
   from pywetterturnier import importbets

   try:
      opts, args = getopt.getopt(sys.argv[1:],'-o',['--obs'])
   except getopt.GetoptError as err:
      print(err)
      utils.exit('Wrong input options set')
   obsonly = False
   for o, a in opts:
      if o in ['-o','--obs']:
         obsonly = True

   # - Reading configuration file first
   config = utils.readconfig()

   # - The url needed to download the data
   url_template = 'http://wetterturnier.de/wertungen/uebersicht_%s.php?p=ue0&stadt=%s'

   # ---------------------------------------------------------------
   # - No tags? No downloading shit.
   if config['migrate_citytags'] == None:
      print '  * No citytags from config file: nothing will be done.'
   # ---------------------------------------------------------------
   # - Else going trough and downloading the current wetterturnier
   #   bets.
   else:

      print '  * %s' % 'Downloading current bets now'

      for tag in config['migrate_citytags']: 
   
         print '    - Citytag is: %s' % tag

         # - Where to store the data
         outhtml = 'current_%s.html' % tag

         # - Define downloading url
         url = url_template % (tag,tag)

         # - First we have to download the file.
         p = sub.Popen(['wget',url,'-O',outhtml],cwd=config['rawdir'],
                        stdout=sub.PIPE,stderr=sub.PIPE)
         out,err = p.communicate()
         if not p.returncode == 0:
            print '    X Problems while downloading. Try next.'
            continue

         # - Reading full file and search for the two tags
         #   we need where it starts and ends.
         fid = open(config['rawdir']+'/'+outhtml,'r')
         lines = fid.readlines()
         bgn = -9; end = -9; counter = -1
         for line in lines:
            counter = counter + 1
            if bgn < 0 and 'Wetterprognoseturnier' in line:
               print '    - Found beginning line in %d' % counter
               bgn = counter
            elif 'ganz nach oben' in line:
               print '    - Found ending line in %d' % counter
               end = counter
               break
         # - Tags not found: stop
         if bgn < 0 or end < 0 or bgn >= end:
            print '    X Detection of data not successful. Continue with next City.'
            continue

         # - Else manipulating the output file
         import re
         content = '\n'.join(lines[bgn:end])
         content.replace('/^$/!{s/<[^>]*>','')
         content = re.sub("<.*?>","",content)
         # - Replace empty lines
         cleancontent = []
         for line in content.split('\n'):
            if len(line.strip()) > 0: cleancontent.append( line.strip() )
         cleancontent = '\n'.join(cleancontent)

         fid = open('%s/tmp_%s.txt' % (config['rawdir'],tag),'w')
         fid.write(cleancontent); fid.close()

         # - Import first file
         obj = importbets.importbets(config)
         obj.takedata(cleancontent.split('\n'),True)
         obj.identify_city()

         obj.extract_obs(1) 
         obj.extract_obs(2) 

         if not obsonly:
            obj.extract_bets(1) 
            obj.extract_bets(2) 
         obj.close()

         print "\n\n"






