!     moses.f      24.07.1994  Klaus Knuepffer  METEO SERVICE
!
!
! YYMMDD au: change history *******************************************
!**********************************************************************
!**********************************************************************
! portiert nach linux /absoft 27.6.2001 Erik Zimmermann
!

      module moses
      use general
      implicit none


      contains

      subroutine processmoses(argcont)


      integer  cDimProbCl,cDimCl
 
      PARAMETER   (cDimCl=2)
      PARAMETER   (cDimProbCl=5)

      REAL         RVUL(0:cDimPr+1)
      character    argcont*(*)
      REAL         rPDMOD(cDimDag)
!      REAL         rPMOD(cDimDag,cDimPd,0:cDimFp,cDimCl)

      REAL         rX(0:cDimPr+1,cDimDag)
      INTEGER      QU(0:cDimPr+1,cDimPotPr)
      INTEGER      PotPrNr(0:cDimPr+1)
      INTEGER      SelPotPrNr(0:cDimPr+1)
      REAL         CO(0:cDimPr+1)
      REAL         RES(cDimDag)
      INTEGER      NDAG(0:cDimFp,cDimCl)
      REAL         R(0:cDimPr+1,0:cDimPr+1)

      REAL         CN(0:cDimPr+1)
      REAL         PROD(0:cDimPr+1)
      REAL         CNE(0:cDimPr+1,0:cDimPr+1) !Coeff Normal Equation
      REAL         E(0:cDimPr+1)       !Erwartungswert
      REAL         SD(0:cDimPr+1)      !Standardabweichung
      INTEGER      DagI
      INTEGER      FpI
      INTEGER      gPrX
      INTEGER      PotPrI

      INTEGER      PdI
      INTEGER      PrI
      INTEGER      I
      INTEGER      j
      INTEGER      K
      INTEGER      gNX
      INTEGER      QKRIT
      INTEGER      QKRITX
      REAL         RMSE
      INTEGER      M
      INTEGER      StpFrwI
      LOGICAL      KORR
      INTEGER      DRUCK
      INTEGER      nI
      REAL         rRMSI
      REAL         rRMSI_Old
      REAL         rRMSE_Old

      LOGICAL      COND
      LOGICAL      GEFUNDEN
      LOGICAL      Stop

      Character*245 HeadLine
      Character*32 Filename
      integer      DTG(cDimDag)
      integer      DTGR(cDimDag)
      integer      Persdt(cDimPd)
      integer      NIL
      integer      PrII
      integer      dFpI
      integer      dFp
      integer      dFp24(0:cDimFp)
      logical      Found
      logical      LeaveMreg
      logical      LinDepd(cDimPotPr)
      real          rt
      real          rrkrit
      integer       nPrX
      integer       Rc(2*cDimPr+10)
      integer       RcI
      integer       VT
      integer       ForwI
      integer   gDagN
      real      ra
      real      rb
      integer   DagI2nI(cDimPd,cDimDag)
      integer   NPrOblX
      integer   PrOblX
      integer   PrOblXX
      integer   PrObl(cDimPotPr)
      integer   PrOblI
!      logical   WithObl
      logical   qSortObl

      integer   DtgAddHrs
      integer   FpI2, PdI2           !nur fuer die Ausgabe

      real rModPrdKorr(0:cDimPr+1) ! Korrelation zwischen pot. Predikor und aktuellem Modell

      character    sElementNames*36
      integer      ElPos

      contest=argcont(1:3)
      print *, 'Contest:',contest
      call strgInit
      NIL=-999
      cNIL=-999
      crNIL=-999.0
      nPrX=cDimPr

      Fp=1
      DRUCK=2
      gFpX=cDimFp
      gPrX=cDimPr+1
      gPdX=cDimPd
      gDagN=1
      sElementNames='N  Sd dd ff fx Wv Wn PPPTTmTTnTTdRR '
!
!.......INPUT DATA ..........................
!
      call ReadInCfg
      call ReadPrCfg
      call ReadObsnFc(DTG,DTGR)
      CALL OpenListFile

! ... verschoben, weil abhaengig von in.cfg
      PrOblXX=70
      if (.not. WithObl) PrOblXX=1

!
!..............GREAT LOOPS..............................
!
       do PrOblX=1,PrOblXX
         qSortObl=.false.
         ElPos=1

         do PdI=1,gPdX  !#

            if (gsMode.eq.'sao') then
               if (ElPos.gt.1) write (21,*) ''
               write (21,'(A)') sElementNames(ElPos:ElPos+2)
               ElPos=ElPos+3
            end if
               
!     
!******************Leaving Great Loop Level***********************
!
!+++++++++++++++++++++++FP-Schleife++++++++++++++++++++++++
!
      do FpI=1,gFpX
        gnX=gDagX
!
!.......initialize Output Regression Coefficients..............
!
        RC(1)=0
        RC(2)=PdI
        RC(3)=1000*K+Fp
        RC(4)=gnX
        do RcI=5,7
          Rc(RcI)=NIL
        end do
!
!......AUSFUEHRUNG UNTERSCHIEDLICHER REGRESSIONSRECHNUNGEN
!
!
!..............Regressionsvorbereitung........


!ez:    geaenderte Ausgabe fuer Elemente und Sa/So zusammen
        FpI2=FpI
        PdI2=PdI
        if (gFpX.eq.1) FpI2=0
        if (gPdX.eq.1) PdI2=0

        grSD_prediktand=1.
        grE_prediktand=0.

        PRINT '(2A)', gsPdName(PdI2),gsFpName(FpI2)
        WRITE (101,'(2A,i3)') gsPdName(PdI2),' FpI=',FpI2
        PRINT *,' '
        WRITE (101,*)' '


        do PotPrI=1,gPotPrX
          LinDepd(PotPrI)=.False.
          gqUsed(PotPrI)=.False.
          grModPrdKorr(PotPrI)=0.
        end do

        do nI=1,gNX
           rPDMOD(nI)=0.
        end do

 1700   continue
 1701   do 1708 PotPrI=1,gPotPrX
        If (LinDepd(PotPrI)) gqUsed(PotPrI)=.True.
!........Defining PrNIL...............................................

 1708   continue
        LeaveMreg=.False.
        Stop=.FALSE.
        StpFrwI=0
        NPrOblX=0
        do PrOblI=0,gPrX
          do PotPrI=1,gPotPrX
            QU(PrOblI,PotPrI)=0
          end do
        end do
!
!..............Regressionsschleife........................
!
 1801   do 1808 WHILE (.NOT. Stop .and. .not. LeaveMreg)

 1891     continue
          PotPrI=0
          PrI=0
          Found=.False.

 1901     do 1908 WHILE (PotPrI .LT. gPotPrX)
            PotPrI=PotPrI+1
            IF ( .NOT. (gqNIL(PotPrI) .OR. gqUSED(PotPrI) ) ) THEN
              PrI=PrI+1
              PotPrNr(PrI)=PotPrI

              nI=0
 2001         do 2008 DagI=1,gDagX
                  nI=nI+1
                  rX(PrI,nI)=grPotPrVal(DagI,PotPrI,FpI,PdI)
!                  DTGR(nI)=DTG(DagI)
                  DagI2nI(PdI,nI)=DagI
 2008         continue   ! DagI
            END IF      ! EL_OK
 1908     continue      ! PrI

          gPrX=PrI+1

!..................Prediktand bereitstellen .................

          IF (StpFrwI .LT. 1) THEN
            nI=0
 2301       do 2308 DagI=1,gDagX
                nI=nI+1
                rX(gPrX,nI)=grPdVal(DagI,FpI,PdI)
 2308       continue     ! DagI
            PotPrNr(gPrX)=PdI
          ELSE
 2311       do 2318 nI=1,gNX
              rX(gPrX,nI)=RES(nI)
 2318       continue
          END IF

          IF (gPrX .GT. 1 .AND. gnX .GT. 10) THEN
            KORR=.TRUE.

            CALL EXE_MREG(LinDepd,LeaveMreg,nPrX,NPrOblX, &
         rPDMOD,CN,PROD,CNE,E,SD,R,RVUL,PrOblX,           &
         rRMSE_Old,rRMSI_Old,rRMSI,KORR,DRUCK,rX,gPrX,gNX,DTGR, &
         Stop,RES,PotPrNr,QU,CO,RMSE,StpFrwI,rrkrit)

          END IF
          if (LeaveMreg) goto 1891
 2401     do 2408 PrI=1,gPrX-1
           IF (PdI .GE. 50 .AND. StpFrwI .GE. 0 .and.    &
             PotPrNr(PrI) .LT. 4 .AND. Fp .LE. 236) then  
          PRINT *,PotPrNr(PrI),gsPotPrName(PotPrNr(PrI)) &
            ,QU(StpFrwI+1,PotPrNr(PrI))
          Write(101,*)PotPrNr(PrI),gsPotPrName(PotPrNr(PrI)) &
            ,QU(StpFrwI+1,PotPrNr(PrI))
           end if
 2408     continue
!
!....................Initialisierung
!
          QKRITX=1000

          GEFUNDEN = .FALSE.
 2501     do 2508 QKRIT=QKRITX,0,-1
 2601       do 2608 PotPrI=1,gPotPrX  !#
!              IF (ABS(QU(StpFrwI+1+NPrOblX,PotPrI)) .EQ. QKRIT !orig
              IF (QU(StpFrwI+1+NPrOblX,PotPrI) .EQ. QKRIT & !Moses
                  .AND. .NOT. GEFUNDEN) THEN
                 GEFUNDEN=.TRUE.
                 StpFrwI=StpFrwI+1
                 SelPotPrNr(StpFrwI+NPrOblX)=PotPrI
                 gqUSED(PotPrI)=.TRUE.
                 rt=( -LOG( 0.18/REAL(gPrX/2.) ) )**0.6135
                 rrkrit = rt / SQRT(Real(gNX-1)) !ckk950510: /2 wegen lin_Ab
!                 print *, "gPrX=",gPrX,'kritische Korrelation: ',rrkrit 
                 if (QKRIT.LT.NINT(1000.*rrkrit) .AND. StpFrwI.GT.1)then
                   Stop=.True.
                   StpFrwI=StpFrwI-1
                 end if
               END IF
 2608       continue
 2508     continue

!......Obliged Predictors sortieren nach Korrelation

        IF (.NOT. qSortObl) THEN
          PrOblI=0
 7501     do 7508 QKRIT=QKRITX,0,-1
 7601       do 7608 PotPrI=1,gPotPrX  !#
              IF (ABS(QU(StpFrwI+NPrOblX,PotPrI)) .EQ. QKRIT &
                 .AND. PrOblI .LT. PrOblX) THEN
                 PrOblI=PrOblI+1
                 PrObl(PrOblI)=PotPrI
               END IF
 7608       continue
 7508     continue
          qSortObl = .true.
        END IF

!
!....................Adding Obliged Predictors........
!
          If (StpFrwI .EQ. 1 .AND. WithObl) then
            PrI=1
            do PrOblI=2,PrOblX+1
!            do PrOblI=1,PrOblX
              PotPrI=PrObl(PrOblI-1)
              if (.NOT. (gqUsed(PotPrI) .OR. gqNIL(PotPrI))) then
                RVUL(PrI)=0
                NPrOblX=NPrOblX+1
                PrI=PrI+1
                SelPotPrNr(PrI)=PotPrI
!                print*,PrI,PotPrI,NPrOblX
                gqUSED(PotPrI)=.TRUE.
              end if
            end do
          end if
          gPrX=StpFrwI+1+NPrOblX
!
!     ....................Prediktoren......................
!
 8881     continue
          nI=0
 2851     do 2858 DagI=1,gDagX
              nI=nI+1
!              DTGR(nI)=DTG(DagI)
              DagI2nI(PdI,nI)=DagI
 2858     continue
 2701     do 2708 PrI=1,gPrX-1
            PotPrNr(PrI)=SelPotPrNr(PrI)
            nI=0
 2801       do 2808 DagI=1,gDagX
                nI=nI+1
                rX(PrI,nI)=grPotPrVal(DagI,PotPrNr(PrI),FpI,PdI)
 2808       continue   ! DagI

 2708     continue      ! PrI
!
!     ....................Prediktand......................
!
          IF (StpFrwI .NE. 0) THEN

            nI=0
 3101       do 3108 DagI=1,gDagX
                nI=nI+1
                rX(gPrX,nI)=grPdVal(DagI,FpI,PdI)
 3108       continue
          ELSE
 3201       do 3208 nI=1,gNX
              rX(gPrX,nI)=RES(nI)
 3208       continue
          END IF
!
!...............Executing multiple Regression......................
!
          PotPrNr(gPrX)=PdI

!         print *,gPrX, gNX
         IF (gPrX .GE. 1 .AND. gNX .GT. gPrX) THEN
            KORR=.FALSE.
            CALL EXE_MREG(LinDepd,LeaveMreg,nPrX,NPrOblX,  &
         rPDMOD,CN,PROD,CNE,E,SD,R,RVUL,PrOblX,            &
         rRMSE_Old,rRMSI_Old,rRMSI,KORR,DRUCK,rX,gPrX,gNX,DTGR, &
        Stop,RES,PotPrNr,QU,CO,RMSE,StpFrwI,rrkrit)

          if (.NOT. LeaveMreg) then
!
!.......................Assign rPMOD values...........................
!
            do nI=1,gNX
!              rPMOD(DagI2nI(PdI,nI),PdI,FpI,K)=rPdMod(nI)
            end do
          end if
!
!.........Assign Values to Regression Coefficient Record.....
!
          Rc(5)=NINT(10.*E(gPrX))
          Rc(6)=NINT(10.*SD(gPrX))
          Rc(7)=NINT(10.*rRMSI)
          Rc(8)=0
          Rc(9)=gPrX-1
          Rc(10)=NINT(1000.*Co(0))
          DO PrI=1,gPrX-1
            Rc(9+2*PrI)=PotPrNr(PrI)
            Rc(10+2*PrI)=NINT(1000.*Co(PrI))
          END DO
          END IF        ! EXE_MReg
 1807    continue       ! Pd=Const

 1808   continue        ! Stop
        if (LeaveMreg) goto 1700
       end do           ! K
       end do           ! FpI
!****************BACK TO GREAT LOOP LEVEL******************************
          end do      ! PdI
      Close (9)

 9999 END subroutine

      SUBROUTINE EXE_MREG(LinDepd,LeaveMreg,nPrX,NPrOblX,       &
         rPDMOD,CN,PROD,CNE,E,SD,R,RVUL,PrOblX,                 &
         rRMSE_Old,rRMSI_Old,rRMSI,KORR,DRUCK,rX,gPrX,gNX,DTGR, &
         Stop,RES,PotPrNr,QU,CO,RMSE,StpFrwI,rrkrit)


!     ....................................................................
!           This Subroutine executes the multiple regression             :
!     ...................................................................:
!

      REAL         rX(0:cDimPr+1,cDimDag)
      REAL         rPDMOD(cDimDag)
      INTEGER      PotPrNr(0:cDimPr+1)
      INTEGER      QU(0:cDimPr+1,cDimPotPr)
      REAL         CO(0:cDimPr+1)
      REAL         CN(0:cDimPr+1)
      REAL         PROD(0:cDimPr+1)
      REAL         ZW(0:cDimPr+1,0:cDimPr+1,0:cDimPr+1)   !Zwischenwert[CNE,PR3]
      REAL         CNE(0:cDimPr+1,0:cDimPr+1)    !Coefficient Normal Equation
      REAL         E(0:cDimPr+1)      !Erwartungswert
      REAL         SD(0:cDimPr+1)      !Standardabweichung
      REAL         R(0:cDimPr+1,0:cDimPr+1)
      REAL         RES(cDimDag)
      REAL         RVUL(0:cDimPr+1)
      INTEGER      DRUCK

      REAL         PROD2
      INTEGER      gNX   !Number of observations
      INTEGER      gPrX   !Number of predictors
      INTEGER      nI
      INTEGER      PrI      !gPrX: Predictand
      INTEGER      PR1
      INTEGER      PR2
      INTEGER      PR3

      REAL         Z
      REAL         SUM
      REAL         rSUM
      REAL         SUMCN
      REAL         SE
      REAL         CPR   !Vorfaktor des Koeffizienten PR in der
!                                reduzierten Normalengleichung
      REAL         RMSE
      REAL         rRMSI
      REAL         rRMSE_Old
      REAL         rRMSI_Old
      INTEGER      RVU
      INTEGER      Q
      REAL         ERR
      REAL         ME

      LOGICAL      KORR
      LOGICAL      Stop

      INTEGER      Q2
      INTEGER      StpFrwI
      INTEGER      NPrX
      real         Zwi
      integer      DTGR(cDimDag)
      logical      LeaveMreg
      logical      LinDepd(cDimPotPr)
      integer      PR2N
      real         rrkrit
      integer      NPrOblX
      integer      PrOblX
      integer iPotPrI

      real rSum_prediktand  ! summe der geschaetzten prediktandenelemente
      real rSum2_prediktand ! summe der quad. geschaetzten prediktandenelemente

!
!......Initialisierung Konstante
!
!      NPrX=13
      LeaveMreg=.False.

 1001   do 1008 nI=1,gNX
          rX(0,nI)=1.
 1008   continue

!
!......Koeffizienten der Normalengleichung berechnen
!

!c       print '(100i3)',(ni,ni=0,99)
 1101 do 1108 PR1=0,gPrX

!       PRINT *,rX(PR1,1),rX(PR1,2),PotPrNr(PR1)
 1201   do 1208 PR2=PR1,gPrX
          if (.NOT. KORR .OR. PR1 .EQ. 0 .OR. PR1 .EQ. PR2 &
               .OR. PR2 .EQ. gPrX) then
          rSUM=0.
 1301     do 1308 nI=1,gNX
            rSUM=rSUM+rX(PR1,nI)*rX(PR2,nI)
!            if (PR1 .eq. 0 .and. pr2 .eq. gPrX) &
!             print *,ni,NINT(rSum), NINT(rX(PR2,nI)),NINT(rX(PR2-1,nI))  
!            if (pr1.eq.0.and.pr2.eq.2.and.ni.gt.60.and.ni.lt.64) &
!            print *,gsPotPrName(PotPrNr(Pr2)),ni,rX(Pr2,nI),rSum
 1308     continue
          SUM = rSUM
            IF (PR1 .EQ. 0) E(PR2)=SUM/REAL(gNX)

          CNE(PR1,PR2)=SUM
!         IF (PR1 .EQ. gPrX) PRINT *,'SUMME=',SUM
!
!     .......Zwischenwert von pr3=0 ist gleich Normalgleichungskoeffizient
!
          ZW(PR1,PR2,0)=SUM
!
!......Erwartungswert und Standardabweichung des Prediktors berechnen
!
!        if ( PR1 .EQ. 05 .AND. PR2 .EQ. 26) THEN  
!       PRINT *,'PR1,PR2,CNE(PR1,PR2),SUM,E(PR1),E(PR2),gNX', &
!        PR1,PR2,gsPotPrName(PotPrNr(Pr1)),gsPotPrName(PotPrNr(Pr2)), &
!            CNE(PR1,PR2),SUM,E(PR1),E(PR2),gNX
!        end if

          IF (PR1 .EQ. PR2 .AND. PR1 .GT. 0) THEN
             SD(PR1)=SQRT(SUM/REAL(gNX)-E(PR1)**2)
          END IF
          end if
 1208   continue
 1108 continue     !PR1
      if (SD(gPrX) .LT. 0.0001) &
         print*,'MRG: Predictand is a Constant'

!
!     .......Korrelationskoeffizienten berechnen
!
 1401 do 1408 PR1=1,gPrX
        if (KORR)       PR2N=gPrX
        if (.NOT. KORR) Pr2N=PR1+1
 1501   do 1508 PR2=PR2N,gPrX
!       if (Pr1 .EQ. 1) &
!       PRINT *,Pr2,gsPotPrName(PotPrNr(Pr1)),gsPotPrName(PotPrNr(Pr2)), &
!         CNE(PR1,PR2),gNX,E(PR1),E(PR2),SD(PR1),SD(PR2),gPrX
          Z=CNE(PR1,PR2)-gNX*E(PR1)*E(PR2)
          if (gNX*SD(PR1)*SD(PR2) .gt. 0.000000001) then
            R(PR1,PR2)=MIN(0.9999,Z/(gNX*SD(PR1)*SD(PR2)))
           
          else
            R(PR1,PR2)=0.
          end if
 1508   continue
!c       print '(100i3)',pr1,(NINT(1000.-1000.*R(pr1,pr2)),PR2=1,gPrX)
 1408 continue
!           print *,3

      IF (.NOT. KORR) THEN
!
!...Berechnung der Zwischengroessen fuer reduzierte Normalengleichung
!
 1601   do 1608 PR3=1,gPrX-1
         if (.NOT. LeaveMreg) then
 1701     do 1708 PR1=PR3,gPrX-1
           if (.NOT. LeaveMreg) then
             Zwi=ZW(PR3-1,PR1,PR3-1)/ZW(PR3-1,PR3-1,PR3-1)
 1801        do 1808 PR2=PR1,gPrX
               if (.NOT. LeaveMreg) then
              ZW(PR1,PR2,PR3)=ZW(PR1,PR2,PR3-1)-ZW(PR3-1,PR2,PR3-1)*Zwi
                 IF (PR1 .EQ. PR2 .AND. PR2 .EQ. PR3 .and.             &
                    ZW(PR1,PR2,PR3) .LT. 0.0001) then
                    PRINT*,'Repeat Mreg because of linear              &
                       dependence of ',gsPotPrName(PotPrNr(PR1))
                    Write (101,'(2A)')'Repeat Mreg because of linear', &
                       ' dependence of ',gsPotPrName(PotPrNr(PR1))
                  LinDepd(PotPrNr(Pr1))=.True.
                  LeaveMreg=.True.
                END IF
              end if
 1808       continue
           end if
 1708     continue
         end if
 1608   continue

        if (LeaveMreg) goto 9988

!
!............Berechnung der Koeffizienten.......
!
 1901   do 1908 PrI=gPrX-1,0,-1
!           PRINT *,'ZW(PrI,PrI,PrI)',PrI,                    &
!           gsPotPrName(PotPrNr(PrI))ZW(PrI,PrI,PrI)

            SUM=ZW(PrI,gPrX,PrI)/ZW(PrI,PrI,PrI)
 1911       do 1918 CPR=gPrX-1,PrI+1,-1
!ez:linux
              SUM=SUM-CO(INT(CPR))*ZW(PrI,INT(CPR),PrI)/ZW(PrI,PrI,PrI)
 1918       continue
            CO(PrI)=SUM
 1908   continue
!
!       ........normierte Koeffizienten berechnen
!
        PROD2=0
        SUMCN=0
 2001   do 2008 PrI=1,gPrX-1
          CN(PrI)=CO(PrI)*SD(PrI)
          SUMCN=SUMCN+ABS(CN(PrI))
 2008   continue

 2101   do 2108 PrI=1,gPrX-1

          CN(PrI)=CN(PrI)*100/SUMCN
 2108   continue
!
!       ........RMSE der Modellierung berechnen
!
        SE=0.
        ERR=0.

        rSum_prediktand=0.
        rSum2_prediktand=0.

 2201   do 2208 nI=1,gNX
            rPDMOD(nI)=CO(0)

 2301     do 2308 PrI=1,gPrX-1
            rPDMOD(nI)=CO(PrI)*rX(PrI,nI)+rPDMOD(nI)
 2308     continue

          RES(nI)=rX(gPrX,nI)-rPDMOD(nI)
          SE=SE+RES(nI)**2
          ERR=ERR+ABS(RES(nI)) 
          rSum_prediktand=rSum_prediktand+rPDMOD(nI) ! Marco (27.11.01)
          rSum2_prediktand=rSum2_prediktand+rPDMOD(nI)**2 ! Marco (27.11.01)

 2208   continue
! --- Marco(27.11.2001) 
! --- berechne Erwartungswert und Standardabweichung vom, im Modell 
! --- geschaetzten, Prediktanden 
        grE_prediktand=rSum_prediktand/real(gNX)
        grSD_prediktand= &
             sqrt(rSum2_prediktand/real(gNX)-grE_prediktand**2) !SD(X)=sqrt(E(X^2)-E(X)^2)
! --- end Marco
        
!       PRINT *,'Quadratsumme Residuen=',SE
        IF (StpFrwI .LE. 1 .AND. .NOT. Stop) THEN
          rRMSI=SD(gPrX)
          RMSE=SD(gPrX)
        END IF
        if (.not. Stop) then
          rRMSI_Old=rRMSI
          rRMSE_Old=RMSE
          RMSE=SQRT(SE/REAL(gNX))
          ME=ERR/REAL(gNX)
          if (StpFrwI .EQ. 1) then
            rRMSI=RMSE/(1-REAL(gPrX)/REAL(gNX))
          else

        rRMSI=SQRT(RMSE**2./rRMSE_Old**2.*rRMSI_Old**2./(1-rrkrit**2.))
!        print *,rRMSI,RMSE,rRMSE_Old,rRMSI_Old
!        print *, RMSE**2./rRMSE_Old**2.,1-rrkrit**2.

          end if
!          print*,RMSE,rRMSI,rrkrit
!
!...........Guetemasse berechnen.......................
!
        IF (StpFrwI .GE. 1 ) THEN
          RVUL(StpFrwI+NPrOblX)=(1.-rRMSI**2./rRMSI_Old**2.)*100.
          if (RVUL(StpFrwI+NPrOblX) .LT. 0) Stop = .True.
        END IF
        Q=NINT( (1. - RMSE / SD(gPrX) ) * 100. )
        
        PRINT *,'RMSE  = ', RMSE
        PRINT *,'SD(g) = ', SD(gPrX)

        Q2=NINT((1.-RMSE**2./SD(gPrX)**2.)*100.)

        PRINT *,'Q2   = ', Q2

        RVU=NINT((1.-rRMSI**2./SD(gPrX)**2.)*100.)
      end if
!
!..........Ergebnisse drucken..........
!
        IF (gqShow .OR. Stop) THEN
 2401     do 2408 PrI=1,gPrX-1
            PROD(PrI)=100.*SD(PrI)*CO(PrI)*R(PrI,gPrX)/SD(gPrX)
            PROD2=PROD2+PROD(PrI)

             IF (DRUCK .GT. 1) THEN
               IF (PrI .EQ. 1) THEN
!                 WRITE (101,*) &
!      '------ ---------------------------------------------------------- &
!      ---'
!               PRINT *, &
!      '---------------------------------------------------------------- &
!      ---'
     

               WRITE(101,'(A)')  &
!c         '    MV    SD  r(Pd) r(Res)    Name               dRVI      Co  &
         '    MV    SD  r(Pd) dRV    Name               dRVI      Co   &
       Wgt Ctr'

               PRINT *, &
!c         '   MV    SD  r(Pd) r(Res)    Name               dRVI      Co &
         '    MV    SD  r(Pd) dRV    Name               dRVI      Co &
       Wgt Ctr'
                WRITE (101,*) &
      '----------------------------------------------------------------- &
      ---'
                PRINT *, &
      '----------------------------------------------------------------- &
      ---'
            END IF
             WRITE(101,'(2F6.1,2F7.2,A,A16,F7.2,F8.2,2I4,A,A)') &
                 E(PRI),SD(PrI),R(PrI,gPrX),                    &
                 100.*(QU(PrI,PotPrNr(PrI))/1000.)**2,          &
!                   QU(PrI,PotPrNr(PrI))/1000.,                 &
                 '    ',gsPotPrName(PotPrNr(PrI)),RVUL(PrI),CO(PrI), &
                 NINT(CN(PrI)),NINT(PROD(PrI))                   
              Print'(2F6.1,2F7.3,A,A16,F7.2,F8.2,2I4,A,A)',     &
                   E(PRI),SD(PrI),R(PrI,gPrX),                  &
                   100.*(QU(PrI,PotPrNr(PrI))/1000.)**2,        &
                   '    ',gsPotPrName(PotPrNr(PrI)),RVUL(PrI),CO(PrI), &
                   NINT(CN(PrI)),NINT(PROD(PrI))
                   Write(21,'(f7.5,x,A)')                      &
                         ABS(CN(PrI))/100.,gsPotPrName(PotPrNr(PrI))


              if (PrI .EQ. NPrOblX+1 .AND. PrI .LT. gPrX-1) then
                WRITE (101,*) &
      '----------------------------------------------------------------- &
      ---'
                PRINT *, &
      '----------------------------------------------------------------- &
      ---'
              end if
            END IF       ! DRUCK

            IF (MOD(PrI,5) .EQ. 0 .and. gPrX-PrI.gt.6) WRITE(101,*)' '
 2408     continue
!     
!........ Gesamtueberblick drucken...............
!
          IF (DRUCK .GT. 1) THEN
            WRITE (101,*) &
      '----------------------------------------------------------------- &
      ---'
           PRINT *,    &
      '----------------------------------------------------------------- &
      ---'
         END IF

         IF (DRUCK .GT. 0) THEN
             IF (DRUCK .EQ. 2) THEN
               WRITE (101,'(15x,A)') &
               'RMSE E(RMSI)   RV(HC)  E(RVI)  Const N_Pr N_Obs'
               PRINT '(15x,A)', &
               'RMSE E(RMSI)   RV(HC)  E(RVI)  Const N_Pr N_Obs'
             END IF
             

             Print'(F6.1,F7.2,F6.2,F8.2,I8,I8,F8.2,I4,I5)', E(gPrX), &
               SD(gPrX),RMSE,rRMSI,Q2,RVU,Co(0),gPrX-1,gNX
             Write(101,'(F6.1,F7.2,F6.2,F8.2,I8,I8,F8.2,I4,I5)') E(gPrX), &
               SD(gPrX),RMSE,rRMSI,Q2,RVU,Co(0),gPrX-1,gNX
           IF (DRUCK .GT. 1) THEN
             WRITE (101,*)
          END IF

!
!.........Ausreisser ausgeben...............
!
            WRITE (101,*)' '
 2501       do 2508 nI=1,gNX
              IF (ABS(RES(nI)) .GT. 7.*RMSE) THEN
                WRITE(101,'(i8,A,f6.1,A,f6.1,A,28f8.1)') &
          DTGR(nI),': Error=',-RES(nI),' Obs=',rX(gPrX,nI), &
               ' Pr=',(rX(PrI,nI),PrI=1,gPrX-1)
                Print '(i8,A,f6.1,A,f6.1,A,28f8.1)',  &
          DTGR(nI),': Error=',-RES(nI),' Obs=',rX(gPrX,nI), &
               ' Pr=',(rX(PrI,nI),PrI=1,gPrX-1)

              END IF
 2508       continue
            PRINT*,' '
         END IF                 ! DRUCK
      END IF
      ELSE                      ! NOT KORR (KORR is TRUE)


 2601    do 2608 PrI=1,gPrX-1
!     --- Marco (27.11.2001) 
!     --- berechne von jedem potentiellen Prediktor
!     --- die Korrelation zu dem im aktuellen Modell geschaetzen Prediktanden
            grModPrdProdukt(PrI)=0.
            do nI=1,gNX
               grModPrdProdukt(PrI)= &
                    grModPrdProdukt(PrI)+rX(PrI,nI)*rPdMod(nI)
            end do 
            
            Z=grModPrdProdukt(PrI)-gNX*grE_prediktand*E(PrI)
            if (gNX*grSD_prediktand*SD(PrI) .gt. 0.0000001) then
              grModPrdKorr(PrI)=Z/(gNX*grSD_prediktand*SD(PrI))
            else
              grModPrdKorr(PrI)=0.
            end if
            
!     --- Marco (27.11.2001)
!     --- berechne Verbesserung des Modells bei angenommener Hinzunahme 
!     --- des Regressors PrI 
            QU(StpFrwI+1+NPrOblX,PotPrNr(PrI))= &
                 NINT(1000*R(PrI,gPrX)/MAX(0.00001,    &
                 SQRT(1.0-grModPrdKorr(PrI)**2))) 
            
!            print *, "QU:",QU(StpFrwI+1+NPrOblX,PotPrNr(PrI))

!     WRITE (101,*)PrI,NINT(100*R(PrI,gPrX))/100.
!     QU(StpFrwI+1+NPrOblX,PotPrNr(PrI))=NINT(1000*(R(PrI,gPrX)))

 2608    continue
      END IF
 9988 continue
      END subroutine


      SUBROUTINE OpenListFile

      CHARACTER*32      FILENAME

      WRITE(FILENAME,'(A,A,I6.6,A)') 'moses/result/',contest,gDtgE,'.lst'
      OPEN(  UNIT=101,FILE=FILENAME,FORM='FORMATTED',STATUS='UNKNOWN')

      WRITE(FILENAME,'(A,A,I6.6,A,A)') 'moses/result/','moses',gDtgE,'.',contest
      OPEN(  UNIT=21,FILE=FILENAME,FORM='FORMATTED',STATUS='UNKNOWN')

      END subroutine


!-----------------------------------------------------------------------
!     DtgAddHrs
!-----------------------------------------------------------------------

      integer function DtgAddHrs (aDtg ,aHours)
      implicit none
      integer   aDtg ,aHours

      integer   Hrs,HH,i
      character s*23

      HH = MOD(aDtg,100) + aHours
      if (HH.ge.0 .and. HH.lt.24) then !! within same day
         DtgAddHrs = aDtg + aHours
      else
         Hrs       = Dtg2Hrs(aDtg)
         if (Hrs.eq.-9920) then
            write(s,'("YYYYMMDDHH = ",I10.10)',iostat=i) aDtg
!            call Err2('during date processing (DtgAddHrs).',s,0)
             write(*,*)' Error during date processing (DtgAddHrs).', &
                 s
             stop
         end if
         DtgAddHrs = Hrs2Dtg(Hrs + aHours)
      end if
      end function

      integer function Dtg2Hrs (aDtg)
      implicit none
      integer aDtg

      integer Dtg
      integer YYYYMMDD ,YYYYMM ,YYYY ,MM ,DD ,HH ,M4

      integer gCDT(0:48)
      data    gCDT                                                &
              / 0 ,31 ,60 ,91,121,152,182,213,244 ,274 ,305 ,335, &
              366,397,425,456,486,517,547,578,609 ,639 ,670 ,700, &
              731,762,790,821,851,882,912,943,974,1004,1035,1065, &
              1096,1127,1155,1186,1216,1247,1277,1308,1339,1369,  &
              1400,1430,1461/

      Dtg2Hrs = -9920
      Dtg = aDtg
      if (Dtg.gt.0 .and. Dtg.lt.0200000000) then
         if (Dtg.lt.0040000000) then
            Dtg=Dtg+2000000000
         else
            Dtg=Dtg+1900000000
         end if
      end if
      YYYY      = Dtg / 1000000
      YYYYMM    = Dtg / 10000
      YYYYMMDD  = Dtg / 100
      MM        = YYYYMM   - YYYY     * 100
      DD        = YYYYMMDD - YYYYMM   * 100
      HH        = Dtg - YYYYMMDD * 100
      M4        = MOD(YYYY,4) * 12 + MM - 1

      if (    (Dtg .GE. 1900030100) .AND.     &
              (Dtg .LE. 2100022823) .AND.     &
              (MM .GE. 01)          .AND.     &
              (MM .LE. 12)          .AND.     &
              (HH .LE. 23)          .AND.     &
              (DD .GE. 01)          .AND.     &
              (DD .LE. gCDT(M4+1)-gCDT(M4)) ) &
      then
         Dtg2Hrs = (((YYYY-1900)/4)*1461 + gCDT(M4) + DD - 1) * 24 + HH
      end if
      end function

      integer function Hrs2Dtg (aHrs)
      implicit none
      integer   aHrs

      integer   Day ,YYYY ,MM ,DD ,HH ,Y4 ,M4 ,D4

      integer gCDT(0:48)
      data    gCDT                                                 &
              / 0 ,31 ,60 ,91,121,152,182,213,244 ,274 ,305 ,335,  &
              366,397,425,456,486,517,547,578,609 ,639 ,670 ,700,  &
              731,762,790,821,851,882,912,943,974,1004,1035,1065,  &
              1096,1127,1155,1186,1216,1247,1277,1308,1339,1369,   &
              1400,1430,1461/

!     Analyse
      Day = aHrs / 24
      Y4  = Day  / 1461
      D4  = Day - Y4 * 1461
      if (D4 .LT. gCDT(16))  then
        M4 = 0
      else  if (D4 .LT. gCDT(32))  then
        M4 = 16
      else
        M4 = 32
      end if
      if (D4 .GE. gCDT(M4+ 8))  M4 = M4 + 8
      if (D4 .GE. gCDT(M4+ 4))  M4 = M4 + 4
      if (D4 .GE. gCDT(M4+ 2))  M4 = M4 + 2
      if (D4 .GE. gCDT(M4+ 1))  M4 = M4 + 1
      YYYY  = Y4 * 4 + M4 / 12 + 1900
      MM  = M4   - (M4 / 12) * 12 + 1
      DD  = D4   - gCDT(M4) + 1
      HH  = aHrs - Day * 24

!     Calculate
      Hrs2Dtg = (((YYYY * 100) + MM) * 100 + DD) * 100 + HH
      if (Hrs2Dtg .LT. 1900030100 .OR. Hrs2Dtg .GT. 2100022823) then
         Hrs2Dtg=-9920
      end if
      end function


!-------------------------------------------------------------------
!          ReadPrCfg
!-------------------------------------------------------------------

      Subroutine ReadPrCfg

      character*32 Filename

      integer   i, PotPrI
      character*20 HeadLine

      write (Filename,'(A,A3,A3,A4)')'moses/','pr_',contest,'.cfg'
      Open(23,FILE=Filename,FORM='FORMATTED',STATUS='OLD')
      Read(23,'(A)') HeadLine
      Read(23,'(i3)') gPotPrX
      do PotPrI=1,gPotPrX
        read(23,'(i2,1x,A)') i,gsPotPrName(PotPrI)
        if (i .ne. PotPrI) then
          print *,'Error reading pr.cfg'
          Stop
        end if
      print '(i2,A25)', PotPrI, gsPotPrName(PotPrI)
 1108 end do
 1109 continue

!      print *, gPotPrX, gsPotPrName(gPotPrX)
      gsPotPrName(0)='Const               '
      close (23)
      end subroutine

!---------------------------------------------------------------------
!     ReadInCfg
!--------------------------------------------------------------------

      subroutine ReadInCfg


      character*32 filename
      character*5 sShow
      character*4 sMode
      integer n,m,l
      logical qword

      open(63,FILE='moses/in.cfg',form='FORMATTED', status='OLD')
      do n=1, 40
         read (63,'(A)') filename ! lange Stringvariable missbraucht
         if (filename(2:4).eq.contest) exit
      end do
      if (n.ge.30) print *,'##### IN.CFG READ ERROR!'


      read (63,'(i8)') gDtgB
      read (63,'(i8)') gDtgE
      read (63,'(A)') filename  ! lange Stringvariable missbraucht
      read (63,'(A4,A5)') sMode, sShow
      close(63)

      print *,gDtgB, gDtgE

      gqShow=.false.
      gsMode=sMode(1:3)
!      print *, sMode, sShow, gsMode
      if (sShow.eq.'yshow') gqShow=.true.


!... Auswerten der Regressionssteuerung
      qword=.false.
      m=1
      l=0
      grrkrit=cNil

      do n=1, 20
!         if (qword) print *,'Y', n,m,l, filename(m:n)
!         if (.not.qword) print *,'N', n,m,l, filename(m:n)

         if (qword) then
            if (filename(n:n).eq.' ') then !!word zu ende

               qword=.false.
               if (l.eq.1) read(filename(m:n),'(i2)')gExcPr
               if (l.eq.2) then
                  if (filename(m:n-1) .eq. 'YOBL') WithObl=.true.
                  if (filename(m:n-1) .eq. 'NOBL') WithObl=.false.

               end if
               if (l.eq.3) grrkrit=s2r(filename(m:n-1))
            else
               cycle
            end if
         else
            if (filename(n:n).eq.' ') cycle
            qword=.true.        !!word geht los
            m=n                 !!word-start merken
            l=l+1
         end if
      end do

!      if (WithObl) print *,'WOBL ', gsMode, gExcPr, grrkrit
!      if (.not.WithObl) print *,'NOBL ', gsMode, gExcPr, grrkrit
      end subroutine

!-----------------------------------------------------------
!     ReadObs and Forecasts
!-----------------------------------------------------------

      subroutine ReadObsnFc(DTG,DTGR)

      Character*32 Filename
      Character*25  cname, c1
      Character*100 HeadLine
      Character*100 Line
      Character*100 Line1,Line2
      Character*10  Value1,Value2
      integer       Pd1(cDimEl) , Pd2(cDimEl), Pr1(cDimPotPr)
      integer      SunD,FX   ! Dummy
      real          rPd1(cDimEl),rPd2(cDimEl),rPr1(cDimPotPr)
      integer       PdI,DagI,FpI, PrI,PetrusI
      integer       DTG(cDimDag),PotPrI,n,m,k,l
      integer       DagNil(cDimPotPr)
      real          rPdConst(cDimPd)
      real          rPdFactor(cDimPd)
      real          rPdOne(cDimDag,1,1)
      real          rPrOne(cDimDag,cDimPotPr,1,1)
      integer       CaseI
      real          rPdVal
      real          rPrVal

      real          rPdTen(cDimDag,1,cDimPd)
      real          rPrTen(cDimDag,cDimPotPr,1,cDimPd)

      real          rPdTwo(cDimDag,cDimFp,1)
      real          rPrTwo(cDimDag,cDimPotPr,cDimFp,1)
      real          rSum(cDimPd),rSum2(cDimPd),rAErr,rSumm
      integer       nn(cDimPd)
      real          rPdDiff(cDimDag,cDimFp,cDimPd)
      integer       LastDay, DagN
      integer      DTGR(cDimDag)

      data rPdConst /0.,0.,-10.,0.,0. ,5., 5.,-1000.,  0.,  0.,  0.,10./
      data rPdFactor/2.,.3, 0.1,1.,.25,1., 1.,    1., 1.5, 1.5, 1.5, 1./

!.....unnoetige Zeilen werden mit Read * HeadLine ueberlesen
!.....Obs-Daten werden in Felder Pd1, rPd1, Pd2 und rPd2
!.....1 fuer Tegel, 2 fuer Tempelhof gelesen.
!.....Danach werden sie (1 und 2) gemittelt und ins
!.....Prediktanden-Feld weggeschrieben.

!.... Nil init grPotPrVal
      do DagI=1,cDimDag
         do PotPrI=1, cDimPotPr
            do FpI=1, cDimFp
               do PdI=1, cDimPd
                 grPotPrVal(DagI,PotPrI,FpI,PdI)=crNIL
               end do
            end do
         end do
      end do

      DagI=1
      Dtg(DagI)=gDtgB
      do while (Dtg(DagI).le.gDtgE)          ! DagI
!        print*,Dtg(DagI)

        write(Filename,'(A,A,i6.6,2A)') 'moses/input/','dat', &
            (MOD(Dtg(DagI),100000000)/100),'.',contest

        open(13,FILE=Filename,FORM='FORMATTED',Status='OLD',ERR=1001)
        LastDay = MOD(Dtg(DagI),100000000)/100

!.... In allen Dateien kommt Sa vor So, deswegen machen wir den Code
!.... mit FpI in do-Schleife ein bisschen uebersichtlicher.
!.... Header muss eigentlich nicht ausgewertet, sondern nur korrekt
!.... uebersprungen werden

        do FpI=1,2
!....Petrus initialisieren....................................
          PetrusI=0
          do PdI=1,gPdX
            grPetrus(DagI,FpI,PdI)=0.
            Pd1=-9999
            Pd2=-9999
            rPd1=-9999.0
            rPd2=-9999.0
          end do

!          print *, "Index:", FpI
1011      Read(13,'(A)') HeadLine
!          print*,Headline(9:11)
!          print*,Dtg(DagI)
          if (Dtg(DagI)<17121400 .and. HeadLine(2:4).NE.'ame') goto 1011
          if (Dtg(DagI)>17121400 .and. HeadLine(9:11).NE.'ame')goto 1011
 
         print *, Filename
!         print *, Headline(1:20)

!.... Prediktor/Referenz pro Sa/so einlesen
!          read(13,'(A)') HeadLine
          read(13,'(A)') HeadLine
            read(13,'(A)') Line1
            read(13,'(A)') Line2
          if(Dtg(DagI)>17121400.and.contest=='ipw')Read(13,'(A)')HeadLine
            
            call GetValues(Line1(23:27),Line2(23:27),Pd1(1),Pd2(1), &
                 "(i5)")                                              !N
!            print *, 'N'
            call GetValues(Line1(28:31),Line2(28:31),Pd1(2),Pd2(2), &
                 "(i4)")                                              !Sd
!            print *, 'Sd'
            call GetValues(Line1(32:36),Line2(32:36),Pd1(3),Pd2(3), &
                 "(i5)")                                              !DD
!            print *, 'DD'            
            call GetValues(Line1(37:39),Line2(37:39),Pd1(4),Pd2(4), &
                 "(i3)")                                              !FF
!            print *, 'FF'
            call GetValues(Line1(40:42),Line2(40:42),Pd1(5),Pd2(5), &
                 "(i3)")                                              !FX
!            print *, 'FX'
            call GetValues(Line1(43:45),Line2(43:45),Pd1(6),Pd2(6), &
                 "(i3)")                                              !Wv
!            print *, 'Wv' 
            call GetValues(Line1(46:47),Line2(46:47),Pd1(7),Pd2(7), &
                 "(i2)")                                              !Wn
!            print *, 'Wn'
            
            call rGetValues(Line1(48:55),Line2(48:55),rPd1(8),rPd2(8), &
                 "(f8.1)")                                            !PPP
!            print *, 'PPP'
            call rGetValues(Line1(56:62),Line2(56:62),rPd1(9),rPd2(9), &
                 "(f7.1)")                                            !TTm
!            print *, 'TTm' 
            call rGetValues(Line1(63:68),Line2(63:68),rPd1(10),rPd2(10), &
                 "(f6.1)")                                            !TTn
!            print *, 'TTn'
            call rGetValues(Line1(69:74),Line2(69:74),rPd1(11),rPd2(11), &
                 "(f6.1)")                                            !TTd
!            print *, 'TTd' 
            call rGetValues(Line1(75:80),Line2(75:80),rPd1(12),rPd2(12), &
                 "(f6.1)")                                            !RR
!            print *, 'RR' 
!    Mittelt im Moment auch dd und WW; kein Problem,
!    wenn's nicht weiter beachtet wird

          if (Pd1(2) .eq. 0) Pd1(2) = -15
          if (Pd2(2) .eq. 0) Pd2(2) = -15

          if (Pd1(3) .eq. 0 .or. Pd1(3) .gt. 360) Pd1(3)=Pd2(3)
          if (Pd2(3) .eq. 0 .or. Pd2(3) .gt. 360) Pd2(3)=Pd1(3)
          if (Pd2(3) .eq. 0) Pd2(3)=Pd1(3)
          if (Pd1(3) .eq. 0 .or. Pd2(3) .eq. 0 .or. &
              Pd1(3)+Pd2(3) .gt. 720) print*,'dd=',Pd1(3),Pd2(3)
          if  (Pd1(3)-Pd2(3) .GT. 180) Pd2(3)=Pd2(3)+360
          if  (Pd2(3)-Pd1(3) .GT. 180) Pd1(3)=Pd1(3)+360
          if ((Pd1(3) + Pd2(3))/2. .GT. 360.) then
               Pd1(3)=Pd1(3)-360.
               Pd2(3)=Pd2(3)-360.
          end if

          if (Pd1(5) .eq. 0) Pd1(5) = 12
          if (Pd2(5) .eq. 0) Pd2(5) = 12

          if (Pd1(6) .GT. 3) Pd1(6)=9 
          if (Pd2(6) .GT. 3) Pd2(6)=9 
          if (Pd1(7) .GT. 3) Pd1(7)=9 
          if (Pd2(7) .GT. 3) Pd2(7)=9 

          if (rPd1(12) .ge. 0.) rPd1(12)=3.5*SQRT(rPd1(12))
          if (rPd2(12) .ge. 0.) rPd2(12)=3.5*SQRT(rPd2(12))
          if (rPd1(12) .le. -2.9) rPd1(12)=-3.0
          if (rPd2(12) .le. -2.9) rPd2(12)=-3.0
          do PdI=1, 7
            if (Pd1(PdI).le.-9999.OR. &
                  Pd2(PdI).le.-9999) then

                  write(*,*) Pd1(PdI),Pd2(PdI)   !B
                  STOP "Value is missing!"

              grPdVal(DagI,FpI,PdI)=-99999
              rPdDiff(DagI,FpI,PdI)=-99999
              goto 4111
            end if
            grPdVal(DagI,FpI,PdI)=REAL(Pd1(PdI)+Pd2(PdI))/2.0
            rPdDiff(DagI,FpI,PdI)=REAL(ABS(Pd1(PdI)-Pd2(PdI)))
!          write(*,*) PdI,grPdVal(DagI,FpI,PdI),rPdDiff(DagI,FpI,PdI)
4111      end do

          do PdI=8,12
            if (rPd1(PdI).le.-9999..OR. rPd2(PdI).le.-9999.) then

               write(*,*) rPd1(PdI),rPd2(PdI) !B
               STOP "Value is missing!"            

            end if
            grPdVal(DagI,FpI,PdI)=(rPd1(PdI)+rPd2(PdI))/2.
            rPdDiff(DagI,FpI,PdI)=ABS(rPd1(PdI)-rPd2(PdI))
          end do
          read(13,'(A)') Headline   !Leerzeile nach den Referenzwerten

! .... Referenz fertig, jetzt wird das Teilnehmerfeld eingelesen bis zu
!      naechsten Leerzeile

          do while (.true.)     ! PotPrI

             read(13,'(A)') Line
             if (line(1:10).eq.'          ') exit !Teilnehmerfeld zu

               read(Line, '(A22,i5,i4,i5,3i3,i2,f8.1,f7.1,3f6.1)') &
                    cname,Pr1(1),Pr1(2),Pr1(3),Pr1(4),Pr1(5),Pr1(6), &
                    Pr1(7),rPr1(8),rPr1(9),rPr1(10),rPr1(11),rPr1(12)
!     TeilnehmerIndex ermitteln
         do PotPrI=1, gPotPrX
            c1=gsPotPrName(PotPrI)
               if (c1(1:15).eq.cname(1:15)) exit
            end do
            if (PotPrI.gt.gPotPrX) then
!             print *,'Teilnehmer ', cname,'steht nicht in der pr.cfg'
              cycle              ! nichts wegschreiben, nexte Zeile
            end if                ! einlesen...

!     Teilnehmerwerte wegschreiben
!     (erstmal aufbereiten)
!     (grPotPrVal(DagI,PotPrI,FpI,PdI),PotPrI=1,gPotPrX)

            if (Pr1(2) .EQ. 0) Pr1(2)=-15
            if (Pr1(5) .EQ. 0) Pr1(5)= 12

            if (rPr1(12) .ge. 0.) rPr1(12)=3.5*SQRT(rPr1(12))
            if (rPr1(12) .lt. -3.0) rPr1(12)=-3.0
            if (Pr1(6) .GT. 3) Pr1(6)=9
            if (Pr1(7) .GT. 3) Pr1(7)=9
            do PdI=1,7
               grPotPrVal(DagI,PotPrI,FpI,PdI)=REAL(Pr1(PdI))
            end do

            do PdI=8, cDimPd
               grPotPrVal(DagI,PotPrI,FpI,PdI)=rPr1(PdI)
            end do
! Kontrolle
!            print '(I2,x,A25,12f7.1)',PotPrI, gsPotPrName(PotPrI), &
!                 (grPotPrVal(DagI,PotPrI,FpI,PdI), PdI=1,12)

!....grPetrus berechnen

            do PdI=1, cDimPd
              grPetrus(DagI,FpI,PdI)=grPetrus(DagI,FpI,PdI) &
                                     + grPotPrVal(DagI,PotPrI,FpI,PdI)
!              print *,grPetrus(DagI,FpI,PdI) 
            end do
            PetrusI=PetrusI+1
         end do                 ! PotPrI

          do PdI=1,gPdX
            grPetrus(DagI,FpI,PdI)=grPetrus(DagI,FpI,PdI)/REAL(PetrusI)
!            print *,grPetrus(DagI,FpI,PdI) 
          end do

!...... dd=000 und 990 gesondert behandeln ............................





        end do                 ! FpI

!Hier ersetzen der Nilwerte druch Petrus Basti
        do PdI=1,7
           if(Pd1(PdI) .le. -9999 .OR. Pd2(PdI) .le. -9999) then
              grPdVal(DagI,FpI,PdI)=grPetrus(DagI,FpI,PdI)
              rPdDiff(DagI,FpI,PdI)=0
!           write(*,*) PdI,grPdVal(DagI,FpI,PdI),rPdDiff(DagI,FpI,PdI),&
!                "Heyho"
           end if
        end do 


!        print *,'Dtg', Dtg(DagI)
        Dtg(DagI+1)=DtgAddHrs(Dtg(DagI),168)
        DagI=DagI+1

        if (Dtg(DagI).gt.2000000000) Dtg(DagI)= Dtg(DagI)-2000000000
!        print *,'Dtg', Dtg(DagI), DagI
        goto 1008

!......Behandlung fehlender Tage

 1001   Dtg(DagI)=DtgAddHrs(Dtg(DagI),168)
        if (Dtg(DagI).gt.2000000000) Dtg(DagI)= Dtg(DagI)-2000000000
!        print *,'Dtg', Dtg(DagI)

 1008 end do                    ! DagI
      gDtgE = LastDay
      gDagX=DagI-1

!....Nur Pr verwenden, die an mindestens 100*gExcPr % (aus in.cfg)
!......aller Faelle verfuebar sind, ansonsten komplett NIL setzen.


      do PotPrI=1, gPotPrX
        DagNil(PotPrI)=0
      end do
      CaseI = 0

      do n=0,12
        DagN=1+gDagX-gDagX/(2**n)         
        do DagI=DagN,gDagX
          CaseI=CaseI+1
          do PotPrI=1, gPotPrX
            if (grPotPrVal(DagI,PotPrI,1,1) .LE. -900) then
              DagNil(PotPrI)=DagNil(PotPrI)+1
            end if
          end do
        end do
      end do

      print*,'Name       Nichtteilnahme / %'
      print*,'-----------------------------'
      do PotPrI=1, gPotPrX
        print *,gsPotPrName(PotPrI),NINT(100.*DagNil(PotPrI)/CaseI)
        if (DagNil(PotPrI)/REAL(CaseI) .GT. (1.-gExcPr/100.)) then

!.... komplett NIL setzen
          gqNIL(PotPrI)=.TRUE.
          do DagI=1,gDagX
            do FpI=1,gFpX
              do PdI=1,gPdX
                grPotPrVal(DagI,PotPrI,FpI,PdI)=crNIL
              end do
            end do
          end do
        else

!.... oder fehlende Vorhersagen durch grPetrus ersetzen

          do DagI=1,cDimDag
            if (grPotPrVal(DagI,PotPrI,1,1) .LE. -900) then
              do FpI=1,gFpX
                do PdI=1,gPdX
                  grPotPrVal(DagI,PotPrI,FpI,PdI)=grPetrus(DagI,FpI,PdI)
                end do
              end do
            end if
          end do
        end if
      end do          ! PotPrI
      print*,' '


!........turnierspezifische Transformationen...


      do DagI=1,gDagX
        do FpI=1,gFpX
          do PdI=1,gPdX
            grPdVal(DagI,FpI,PdI)=grPdVal(DagI,FpI,PdI) &
                                  *rPdFactor(PdI)+rPdConst(PdI)
          end do
        end do
      end do

      do DagI=1,gDagX
        do PotPrI=1,gPotPrX
          do FpI=1,gFpX
!           print '(I2,x,A25,12f7.1)',PotPrI, gsPotPrName(PotPrI), &
!                 (grPotPrVal(DagI,PotPrI,FpI,PdI), PdI=1,12)
            if (grPotPrVal(DagI,PotPrI,1,1) .GE. -900) then
              do PdI=1,gPdX
                rPrVal=grPotPrVal(DagI,PotPrI,FpI,PdI)
                rPrVal=rPrVal*rPdFactor(PdI)+rPdConst(PdI)
                if (PdI.eq.6 .or. PdI.eq.7 .and. rPrVal .GT. 11) &
                  rPrVal=rPrVal-2
!..... Schadensbegrenzung fuer Fehlvorhersagen auf gMaxErr
                rPdVal=grPdVal(DagI,FpI,PdI)
                if (PdI .eq. 3) then
!             print *,'ddd',dagI,potpri,fpi,NINT(rPdVal), NINT(rPrVal)
                  if (rPdVal - rPrVal .GT.  18.) rPrVal = rPrVal + 36.
                  if (rPdVal - rPrVal .LT. -18.) rPrVal = rPrVal - 36.
                end if
      rPrVal=MIN(MAX(rPrVal,rPdVal-gMaxErr(PdI)),rPdVal+gMaxErr(PdI))
                grPotPrVal(DagI,PotPrI,FpI,PdI)=rPrVal
              end do
            end if
          end do
        end do

        do FpI=1,gFpX
!          print '(I2,x,A25,12f7.1)',gPotPrX+1,'grPetrus        ', &
!            (grPetrus(DagI,FpI,PdI), PdI=1,12)
!            print '(I2,x,A25,12f7.1)',00,'grPdVal        ', &
!                   (grPdVal(DagI,FpI,PdI), PdI=1,12)
          end do
      end do

!........Transformationen abhaengig von Modus in in.cfg
      select case (gsMode)
      case ('aio', 'aIo')
!........Alle FpI und PdI in ein Feld wegschreiben.........
        do DagI=1,gDagX
          do FpI=1,gFpX
            do PdI=1,gPdX
              CaseI=(DagI-1)*gPdX*gFpX+(FpI-1)*gPdX+PdI
                    rPdOne(CaseI,1,1)=grPdVal(DagI,FpI,PdI)
              DTGR(CaseI)=DTG(DagI)
              do PotPrI=1,gPotPrX
                 rPrOne(CaseI,PotPrI,1,1)= &
                  grPotPrVal(DagI,PotPrI,FpI,PdI)
              end do
            end do
          end do
        end do

        gDagX=gDagX*gFpX*gPdX
        gFpX=1
        gPdX=1

        CaseI=0
        do n=0,12
          DagN=1+gDagX-gDagX/(2**n)         
          do DagI=DagN,gDagX
            if (rPdOne(DagI,1,1) .GE. -900.) then
              CaseI=CaseI+1
              grPdVal(CaseI,1,1)=rPdOne(DagI,1,1)
              DTGR(CaseI)=DTGR(DagI)
!              print*,'ddd',DagI,CaseI, DTGR(CaseI),rPdOne(DagI,1,1)
              do PotPrI=1,gPotPrX
                 grPotPrVal(CaseI,PotPrI,1,1)= &
                  rPrOne(DagI,PotPrI,1,1)
              end do
            end if
          end do
        end do
        gDagX=CaseI


      case ('sao', 'Sao','SAO', 'soa', 'Soa', 'SOA')
         print *, 'Sa & So zusammen:'

!........Alle FpI in ein Feld wegschreiben.........
!         print *,'gDagX, gFpX, gPdX = ',gDagX,gFpX, gPdX

         do PdI=1,gPdX
           rSum(PdI)=0.
           nn(PdI)=0
         end do

         do DagI=1,gDagX
           do FpI=1,gFpX
             CaseI=(DagI-1)*gFpX+FpI
             do PdI=1,gPdX
               rPdTen(CaseI,1,PdI)=grPdVal(DagI,FpI,PdI)
               do PotPrI=1,gPotPrX
                 rPrTen(CaseI,PotPrI,1,PdI)=            &
                   grPotPrVal(DagI,PotPrI,FpI,PdI)
                   rAErr=ABS(rPrTen(CaseI,PotPrI,1,PdI) &
                         -rPdTen(CaseI,1,PdI))
                   if (rAErr .LT. 900) then 
                       rAErr=ABS(MAX(0.,rAErr-rPdDiff(DagI,FpI,PdI) &
                             *rPdFactor(PdI)/2.))
                       rSum(PdI)=rSum(PdI)+rAErr
                       rSum2(PdI)=rSum2(PdI)+rAErr**2.
                       nn(PdI)=nn(PdI)+1
                   end if
                 end do
               end do
            end do
         end do

         rSumm=0.
         do PdI=1,gPdX
            rSum2(PdI)=rSum2(PdI)/REAL(nn(PdI))
            rSum(PdI)=rSum(PdI)/REAL(nn(PdI))
            rSum2(PdI)=SQRT(rSum2(PdI)-rSum(PdI)**2.)
            rSumm=rSumm+rSum2(PdI)
         end do

!.......... Statistik ueber Wichtigkeit der Elemente drucken...............

         do PdI=1,gPdX
!            print '(A,2f7.2,i4)',gsPdName(PdI),rSum(PdI),rSum2(PdI), &
!                                   NINT(100.*rSum2(PdI)/rSumm)
         end do




         gDagX=gDagX*gFpX
!         print *,'gDagX , gPdX = ',gDagX , gPdX
         gFpX=1

! if Schleife fuer die ungueltigen Predictanden noch nicht
! wieder eingearbeitet; bleibt fuer den Betrieb ohne Auswirkungen

         do DagI=1,gDagX
            do PdI=1,gPdX
               grPdVal(DagI,1,PdI)=rPdTen(DagI,1,PdI)
               do PotPrI=1,gPotPrX
                  grPotPrVal(DagI,PotPrI,1,PdI)= &
                       rPrTen(DagI,PotPrI,1,PdI)
               end do
            end do
         end do

         do PdI=1,gPdX
           CaseI=0
           do n=0,12
             DagN=1+gDagX-gDagX/(2**n)         
             do DagI=DagN,gDagX
               if (rPdTen(DagI,1,PdI) .GE. -900.) then
                 CaseI=CaseI+1
                 grPdVal(CaseI,1,PdI)=rPdTen(DagI,1,PdI)
                 do PotPrI=1,gPotPrX
                    grPotPrVal(CaseI,PotPrI,1,PdI)= &
                    rPrTen(DagI,PotPrI,1,PdI)
                 end do
               end if
             end do
           end do
         end do
         gDagX=CaseI



      case ('aSS','ass')
         print *,'all in one, Sa & So'

!........All PdI in ein Feld wegschreiben.........
         do DagI=1,gDagX
            do FpI=1,gFpX
               do PdI=1,gPdX
                  CaseI=(DagI-1)*gPdX+PdI
                  rPdTwo(CaseI,FpI,1)=grPdVal(DagI,FpI,PdI)
!     print *,CaseI, rPdOne(CaseI,1,1)
                  do PotPrI=1,gPotPrX
                     rPrTwo(CaseI,PotPrI,FpI,1)= &
                      grPotPrVal(DagI,PotPrI,FpI,PdI)
                  end do
               end do
            end do
         end do

         gDagX=gDagX*gPdX
         gFpX=2
         gPdX=1
!         print *,'gDagX , FpX, gPdX=',gDagX,gFpX, gPdX


         do FpI=1, gFpX
            CaseI=0
            do DagI=1,gDagX
               if (rPdTwo(DagI,FpI,1) .GE. -900.) then
                  CaseI=CaseI+1
                  grPdVal(CaseI,FpI,1)=rPdTwo(DagI,FpI,1)
                  do PotPrI=1,gPotPrX
                     grPotPrVal(CaseI,PotPrI,FpI,1)= &
                          rPrTwo(DagI,PotPrI,FpI,1)
                  end do
               end if
            end do
         end do

      case ('ais', 'aIs')
      case DEFAULT
         print *,'### Warning: no Valid Mode in in.cfg !'
         print *,'Defaulting to : all in Single'
      end select

      end subroutine

!---------------------------------------------------------------------
!     s2r
!---------------------------------------------------------------------

!
! Read a real value from the first digit or period up to the first space
! Extra leading or trailing characters are ignored.

      real function s2r(as)

!      include 'moses.inc'

      integer i,j,k
      character as*(*)
      s2r=-9999
 1001 do i=1,LEN(as)
         if (INDEX('.1234567890',as(i:i)).gt.0) goto 1009
      end do
      return
 1009 continue
 2001 do j=i,LEN(as)-1
         if (as(j+1:j+1).eq.' ') goto 2009
      end do
 2009 continue
      read(as(i:j),'(BN,F10.0)',iostat=k) s2r
      if (k.ne.0) s2r=-9999
      if (s2r.eq.0 .and. INDEX(as,'0').eq.0) s2r=-9999
      end function

!--------------------------------------------------------
!   strginit
! because modules don't like data
!--------------------------------------------------------
      subroutine strgInit()

      integer n
      character*8 sFpName(0:cdimFp)
      character*6 sPdName(0:cdimPd)
      integer  MaxErr(cDimPd)

      data    MaxErr  /8,99,18,99,99,10,10,10,99,99,99,99/
!     data    MaxErr  /9,9,10,10,10,10,12,12,10,10/
!      data    MaxErr  /99,10,910,910,910,910,912,912,910,910/
      data    sFpName /'  Sa+So ',' Samstag',' Sontag'/
      data sPdName                                              &
       /'  All ','  N-- ','  rSd ','  dd- ','  ff- ','  fx- ',  &
       '  Wv- ','  Wn- ','  PPP ','  TTm ','  TTn ','  TTd ','  RR- '/
      
      gsFpName(:)=sFpName(:)
      gsPdName(:)=sPdName(:)
      gMaxErr(:)=MaxErr(:)

      end subroutine

!--------------------------------------------------------
! rGetValues 
!--------------------------------------------------------
!

      subroutine rGetValues(aSource1,aSource2,aDest1,aDest2,aFormat)
      character aSource1*(*),aSource2*(*),aFormat*(*)
      real aDest1,aDest2
      
      if (SCAN(aSource1//aSource2,"Xxn").eq.0) then 
         read(aSource1,aFormat) aDest1
         read(aSource2,aFormat) aDest2
      elseif (SCAN(aSource1,"Xxn").eq.0) then
         read(aSource1,aFormat) aDest1
         read(aSource1,aFormat) aDest2
      elseif (SCAN(aSource2,"Xxn").eq.0) then
         read(aSource2,aFormat) aDest1
         read(aSource2,aFormat) aDest2
      else
         stop "Can't evaluate Element"
      end if
      end subroutine

!--------------------------------------------------------
! GetValues 
!--------------------------------------------------------

      subroutine GetValues(aSource1,aSource2,aDest1,aDest2,aFormat)
      character aSource1*(*),aSource2*(*),aFormat*(*)
      integer aDest1,aDest2

      if (SCAN(aSource1//aSource2,"Xxn").eq.0) then 
         read(aSource1,aFormat) aDest1
         read(aSource2,aFormat) aDest2
      elseif (SCAN(aSource1,"Xxn").eq.0) then
         read(aSource1,aFormat) aDest1
         read(aSource1,aFormat) aDest2
      elseif (SCAN(aSource2,"Xxn").eq.0) then
         read(aSource2,aFormat) aDest1
         read(aSource2,aFormat) aDest2
      else
         aDest1=-99999                          !B
         aDest2=-99999                          !B 
         stop "Can't evaluate Element!!"
         write(*,*) aDest1,aDest2               !B
          stop "Can't evaluate Element!"
      end if
      end subroutine

      end module moses













