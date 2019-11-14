!-----------------------------------------------------------------------
!     general.f
!-----------------------------------------------------------------------

      module general

      integer cDimPr
      integer cDimPd
      integer cDimPotPr
      integer cDimEl
      integer cDimFp
      integer cDimDag
      integer cDimDtg
      integer cDimThs

      parameter (cDimPd=12)
      parameter (cDimEl=200)
      parameter (cDimPotPr=100)
      parameter (cDimFp=2)
      parameter (cDimDag=8000)
      parameter (cDimDtg=10)
      parameter (cDimThs=3)
      PARAMETER (cDimPr=cDimPotPr-1)

      Real     grPdVal(cDimDag,cDimFp,cDimPd)
      Real     grPetrus(cDimDag,cDimFp,cDimPd)
      INTEGER  gPotPrVal(cDimDag,cDimPotPr,cDimFp)
      integer  gElNr(cDimEl)
      integer  gMaxErr(cDimPd)
      integer  gPotPrNr(cDimPotPr),gPotPrI ,gPotPrX
      integer  gDtg(cDimDtg),gDtgI,gDtgX,gDtgB,gDtgE
      integer  gElI,gElX,gFpX
      integer  gPdX
      integer  gDagX,gDtgIssue
      integer  gVerbos,gThsX
      real     grDat(cDimPotPr,0:cDimFp)
      integer  cNIL
      integer  Fp
      real     crNIL
      integer gExcPr
      real    grPotPrVal(cDimDag,cDimPotPr,cDimFp,cDimPd)
      real    grrkrit

      logical gqUSED(cDimPotPr+1)
      logical gqNIL(cDimPotPr+1)
      logical WithObl, gWithObl
      logical gqShow

      character*9  gsElName(cDimEl)
      character*8  gsFpName(0:cDimFp)
      character*25 gsPotPrName(0:cDimPotPr)
      character*6  gsPdName(0:cDimPd)
      character*3  gsMode
      character*3  contest
      
!      data    gMaxErr / 9,   10,18 ,10 ,10,10,12,12,10,10/
      data    gMaxErr /12,10,18,100,100,10,10,12,100,100,100,100/
      data    gsPdName &
           /'  All ','   N  ',' rSd  ','  dd  ','  ff  ','  fx  ', &
           ' Wv  ','  Wn  ', ' PPP  ','  TTm ','  TTn ',' TTd  ',  &
           ' RR  '/

      data    gsFpName &
              /'  Sa+So ',' Samstag',' Sonntag'/

      real grE_prediktand    ! Erwartungswert der geschaetzten prediktandenelemente
      real grSD_prediktand   ! Standardabweichung der geschaetzten prediktandenelemente
      real grModPrdProdukt(0:cDimPr+1) ! Produkt zwischen Predikor und im aktuellem Modell geschaetztem Prediktanden
      real grModPrdKorr(0:cDimPr+1) ! Korrelation zwischen Predikor und im aktuellem Modell geschaetztem Prediktanden

    
      end module general
!-----------------------------------------------------------------------




        
