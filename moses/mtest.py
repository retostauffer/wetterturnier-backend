import numpy
import moses as m

# Liste aller moeglichen Argumente bzw. Staedte
tournaments = ["bpw", "wpw", "zpw", "ipw", "lpw"]
#tournaments = ["bpw"]
#m.moses.processmoses("bpw")
# fuer jede Stadt einzeln das Fortran-Programm aufrufen
for t in tournaments:
    m.moses.processmoses(t)
