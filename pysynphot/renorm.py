"""This module handles normalization of source spectrum flux."""
from __future__ import division, print_function

import math
import numpy as np
from . import units
from .spectrum import FlatSpectrum, Vega
from .refs import _default_waveset
from .exceptions import DisjointError, OverlapError

# This is done here to avoid circular imports.
def DefineStdSpectraForUnits():
    """Define ``StdSpectrum`` attribute for all the supported
    :ref:`pysynphot-flux-units`.

    This is automatically done on module import. The attribute
    stores the source spectrum necessary for normalization in
    the corresponding flux unit.

    For ``photlam``, ``photnu``, ``flam``, ``fnu``, Jy, and mJy,
    the spectrum is flat in the respective units with flux value of 1.

    For counts and ``obmag``, it is flat in the unit of counts
    with flux value of :math:`1 / N`, where :math:`N` is the
    size of default wavelength set (see `~pysynphot.refs`).

    For ``abmag`` and ``stmag``, it is flat in the respective units
    with flux value of 0 mag. That is equivalent to
    :math:`3.63 \\times 10^{-20}` ``fnu`` and
    :math:`3.63 \\times 10^{-9}` ``flam``, respectively.

    For ``vegamag``, it is simply :ref:`pysynphot-vega-spec`.

    """
    # Linear flux-density units
    units.Flam.StdSpectrum = FlatSpectrum(1, fluxunits='flam')
    units.Fnu.StdSpectrum = FlatSpectrum(1, fluxunits='fnu')
    units.Photlam.StdSpectrum = FlatSpectrum(1, fluxunits='photlam')
    units.Photnu.StdSpectrum = FlatSpectrum(1, fluxunits='photnu')
    units.Jy.StdSpectrum = FlatSpectrum(1, fluxunits='jy')
    units.mJy.StdSpectrum = FlatSpectrum(1, fluxunits='mjy')

    # Non-density units
    scale = 1.0 / _default_waveset.size
    units.Counts.StdSpectrum = FlatSpectrum(1, fluxunits='counts') * scale
    units.OBMag.StdSpectrum = FlatSpectrum(1, fluxunits='counts') * scale

    # Magnitude flux-density units
    units.ABMag.StdSpectrum = FlatSpectrum(3.63e-20, fluxunits='fnu')
    units.STMag.StdSpectrum = FlatSpectrum(3.63e-9, fluxunits='flam')
    units.VegaMag.StdSpectrum = Vega


# Call this function so the attributes get added upon import.
DefineStdSpectraForUnits()


def StdRenorm(spectrum, band, RNval, RNunitstring, force=False):
    """This is used by `~pysynphot.spectrum.SourceSpectrum` for
    renormalization.

    Parameters
    ----------
    spectrum : `~pysynphot.spectrum.SourceSpectrum`
        Spectrum to renormalize.

    band, RNval, RNunitstring, force
        See :meth:`~pysynphot.spectrum.SourceSpectrum.renorm`.

    Returns
    -------
    newsp : `~pysynphot.spectrum.CompositeSourceSpectrum`
        Renormalized spectrum.

    """
    # Validate the overlap
    if not force:
        stat = band.check_overlap(spectrum)
        if stat == 'full':
            pass
        elif stat == 'partial':
            if band.check_sig(spectrum):
                spectrum.warnings['PartialRenorm'] = True
                print ('Warning: Spectrum is not defined everywhere in '
                       'renormalization bandpass. At least 99% of the band '
                       'throughput has data, therefore proceeding anyway. '
                       'Spectrum will be extrapolated at constant value.')
            else:
                raise OverlapError('Spectrum and renormalization band do not '
                                   'fully overlap. You may use force=True to '
                                   'force the renormalization to proceed.')
        elif stat == 'none':
            raise DisjointError('Spectrum and renormalization band are '
                                'disjoint.')

    # Compute the flux of the spectrum through the bandpass and make sure
    # the result makes sense.
    sp = spectrum * band

    totalflux = sp.integrate()
    if totalflux <= 0.0:
        raise ValueError('Integrated flux is <= 0')
    if np.isnan(totalflux):
        raise ValueError('Integrated flux is NaN')
    if np.isinf(totalflux):
        raise ValueError('Integrated flux is infinite')

    # Get the standard unit spectrum in the renormalization units
    RNunits = units.Units(RNunitstring)
    if RNunits.isDensity:
        up = RNunits.StdSpectrum * band
    else:
        up = RNunits.StdSpectrum

    # Renormalize in magnitudes....
    if RNunits.isMag:
        ratio = totalflux / up.integrate()
        dmag = RNval + 2.5 * math.log10(ratio)
        newsp = spectrum.addmag(dmag)

    #...or in linear flux units.
    else:
        const = RNval * (up.integrate() / totalflux)
        newsp = spectrum * const

    # Return the new spectrum
    return newsp
