import sys
import os
import testutil
import pysynphot as S
import numpy as N
from pysynphot.units import Units
from pysynphot import extinction, spectrum, units, newetc

class ticket121(testutil.FPTestCase):
    def setUp(self):
        self.sp=S.BlackBody(30000)
        self.bp = S.ObsBandpass('johnson,v')
        
    def testintegral(self):
        self.sp.convert('flam')
        self.sp.convert('Angstrom')
        wave,flux=self.sp.getArrays()
        self.ang=self.sp.trapezoidIntegration(wave,flux)
        self.sp.convert('fnu')
        self.sp.convert('hz')
        wave,flux=self.sp.getArrays()
        self.hz=self.sp.trapezoidIntegration(wave,flux)
        self.failUnlessAlmostEqual(self.ang/self.hz,1)

    def testresample_sp(self):
        #create a spectrum with wavelength in descending order
        self.sp2=S.ArraySpectrum(wave=self.sp.wave[::-1],
                                 flux=self.sp.flux[::-1],
                                 waveunits=self.sp.waveunits,
                                 fluxunits=self.sp.fluxunits)

        #.flux calls __call__ calls resample
        ref=self.sp.flux[::-1]
        tst=self.sp2.flux
        self.assertEqualNumpy(ref,tst)

    def testresample_bp(self):
        #create a bandpass with wavelength in descending order
        self.bp2=S.ArraySpectrum(wave=self.bp.wave[::-1],
                                 throughput=self.bp.throughput[::-1],
                                 waveunits=self.sp.waveunits)
                                
        
        #.flux calls __call__ calls resample
        ref=self.bp.throughput[::-1]
        tst=self.bp2.throughput
        self.assertEqualNumpy(ref,tst)
                                            
class ticket125(testutil.FPTestCase):
    def setUp(self):
        self.spstring="rn(icat(k93models,44500,0.0,5.0),band(nicmos,2,f222m),18,vegamag)"
    def testparse(self):
        self.spstring=newetc.parse_spec(self.spstring)

class ticket125_a(ticket125):
    def setUp(self):
        self.spstring="rn(icat(k93models,44500,0.0,5.0),band(v),18,vegamag)"

class ticket125_b(ticket125):
    def setUp(self):
        self.spstring="rn(icat(k93models,44500,0.0,5.0),band(johnson,v),18,vegamag)"

class ticket125_c(ticket125):
    def setUp(self):
        self.spstring="rn(icat(k93models,44500,0.0,5.0),band(johnson,v),18,vegamag)"
        self.spstring="rn(/grp/hst/cdbs/calspec/bd_75d325_stis_001.fits,band(u),9.5,vegamag)*band(fos,blue,4.3,g160l)"
        
class AddInverseMicron(testutil.FPTestCase):
    def setUp(self):
        self.x=Units('1/um')
        self.mwave=extinction._buildDefaultWaveset()[0:10]
        self.awave=(spectrum.default_waveset.copy()[::10])[0:10]
        
    def teststr(self):
        self.failUnless(str(self.x)=='1/um')

    def testunittoang(self):
        test=self.x.Convert(self.mwave,'angstrom')
        self.assertApproxNumpy(test,self.awave)

    def testunitfromang1(self):
        ang=Units('angstrom')
        test=ang.Convert(self.awave,'1/um')
        self.assertApproxNumpy(test,self.mwave)

    def testunitfromang2(self):
        ang=Units('angstrom')
        test=ang.Convert(self.awave,'InverseMicron')
        self.assertApproxNumpy(test,self.mwave)

    def testunitfromang3(self):
        ang=Units('angstrom')
        test=ang.Convert(self.awave,'inversemicrons')
        self.assertApproxNumpy(test,self.mwave)
        
        
    def testfromang(self):

        test=S.ArraySpectrum(wave=self.awave,
                             flux=N.ones(self.awave.shape),
                             waveunits='angstrom',
                             fluxunits='flam')
        test.convert('1/um')
        self.failUnless(isinstance(test.waveunits,units.InverseMicron))
        self.assertApproxNumpy(test.wave,self.mwave)

    def testcreate(self):
        test=S.ArraySpectrum(wave=self.mwave,
                             flux=N.ones(self.mwave.shape),
                             waveunits='1/um',
                             fluxunits='flam')
        self.failUnless(isinstance(test.waveunits,units.InverseMicron))
        self.assertEqualNumpy(test.wave,self.mwave)
                        
    def testtoang(self):
        test=S.ArraySpectrum(wave=self.mwave,
                            flux=N.ones(self.mwave.shape),
                            waveunits='1/um',
                            fluxunits='flam')
        
        test.convert('angstrom')
        self.failUnless(isinstance(test.waveunits,units.Angstrom))
        self.assertApproxNumpy(test.wave,self.awave)
                                                
class AddMag(testutil.FPTestCase):
    "Ticket #122"
    def setUp(self):
        self.bright=S.UnitSpectrum(18.0,fluxunits='abmag')
        self.faint=S.UnitSpectrum(21.0,fluxunits='abmag')
        self.delta=3

    def testadd(self):
        test=self.bright.addmag(self.delta)
        self.assertEqualNumpy(test.flux,self.faint.flux)

    def testsubtract(self):
        test=self.faint.addmag(self.delta*-1.0)
        self.assertEqualNumpy(test.flux,self.bright.flux)

    def testtypecatch(self):
        self.assertRaises(TypeError,
                          self.faint.addmag,
                          self.bright)

class Sample(testutil.FPTestCase):
    "Ticket #99"

    def setUp(self):
        self.sp=S.UnitSpectrum(10,fluxunits='flam')
        self.wave=S.Waveset(1000,11000,1000)
        self.ref=S.ArraySpectrum(wave=self.wave,
                                 flux=self.sp.flux[0]*N.ones(self.wave.shape),
                                 fluxunits=self.sp.fluxunits)

    def test1(self):
        test=self.sp.sample(self.wave)
        self.assertEqualNumpy(test,self.ref.flux)

class Ticket104(testutil.FPTestCase):
    """Use the extinction laws to test & make sure the conversion to
    SpectralElements works ok"""

    def test1(self):
        self.sp = S.Ebmvx(0.2,'gal1') #Make an extinction law
        self.sp.convert('1/um')       #convert to inverse microns
        refwave = extinction._buildDefaultWaveset()
        testwave = self.sp.wave
        self.assertApproxNumpy(testwave,refwave)
        
#--------------------------------------------------------------------
## I removed the spectrum.photonrate() method, but this test identified
## a problem with the GaussianSource when defined in frequency-based
## units. The test needs to be reworked & the problem solved.
##.....................................................................
## def testPhotonRate():
##     """Passes for Angstrom & count linear units; fails for Hertz-linear due
##     to a problem with the Gaussian source. Does not test Vegamag which are
##     special."""
##     ema=S.GaussianSource(100,1000,2,fluxunits='photlam')
##     emh=S.GaussianSource(100,1000,2,fluxunits='photnu',
##                          waveunits='hz')
##     emc=S.GaussianSource(100,1000,2,fluxunits='counts')
##     uset={ema:['photlam','flam','stmag'],
##           emh:['photnu', 'fnu', 'abmag','jy','mjy'],
##           emc:['counts','obmag']}
##     for em in (ema,emh,emc):
##         for u in uset[em]:

##             def checkrate(em,total,funits):
##                 em.convert(funits)
##                 test=em.photonrate()
##                 assert abs(test-total) < 0.0001, "Expected %f, got %f"%(total,test)
##             checkrate.description="%s.testPhotonRate.test%sfunc"%(__name__,u)

##             yield checkrate, em, 100, u

