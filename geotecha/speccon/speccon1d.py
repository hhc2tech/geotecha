# geotecha - A software suite for geotechncial engineering
# Copyright (C) 2013  Rohan T. Walker (rtrwalker@gmail.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/gpl.html.

"""
This module has functions classes and common functionality for one dimensinal 
specral methods

"""
from __future__ import division, print_function

import geotecha.piecewise.piecewise_linear_1d as pwise
from geotecha.piecewise.piecewise_linear_1d import PolyLine
import geotecha.speccon.integrals as integ


import sys, imp
import textwrap
import numpy as np
import matplotlib.pyplot as plt
import geotecha.inputoutput.inputoutput as inputoutput

class Speccon1d(object):
    """solve 1D parabolic partial differential equation using spectral method
    
    """
    
    def __init__(self, reader = None):                        
        self._setup()
        
        inputoutput.initialize_objects_attributes(self, 
                                                  self._attributes, 
                                                  self._attribute_defaults,
                                                  not_found_value = None)        
        
        self._input_text = None
        if not reader is None:
            if isinstance(reader, str):
                self._input_text = reader
            else:
                self._input_text = reader.read()
                
            inputoutput.copy_attributes_from_text_to_object(reader,self, 
                self._attributes, self._attribute_defaults, 
                not_found_value = None)

            
    def _setup(self):        
        # to be overridden in subclasses
        self._attribute_defaults = dict()
        self._attributes = []
        
        self._attributes_that_should_be_lists= []
        self._attributes_that_should_have_same_x_limits = []
        self._attributes_that_should_have_same_len_pairs = []
        
        self._zero_or_all = []            
        self._at_least_one = []
                                          
        self._one_implies_others = []            
    
    def check_all(self):
        """perform checks on attributes
        
        Notes
        -----
        
        See also
        --------                        
        geotecha.inputoutput.inputoutput.check_attribute_combinations
        geotecha.inputoutput.inputoutput.check_attribute_is_list
        geotecha.inputoutput.inputoutput.check_attribute_PolyLines_have_same_x_limits        
        geotecha.inputoutput.inputoutput.check_attribute_pairs_have_equal_length
        
        """        
        
       
        inputoutput.check_attribute_combinations(self,
                                                 self._zero_or_all,
                                                 self._at_least_one,
                                                 self._one_implies_others)        
        inputoutput.check_attribute_is_list(self, self._attributes_that_should_be_lists, force_list=True)                        
        inputoutput.check_attribute_PolyLines_have_same_x_limits(self, attributes=self._attributes_that_should_have_same_x_limits)        
        inputoutput.check_attribute_pairs_have_equal_length(self, attributes=self._attributes_that_should_have_same_len_pairs)
        
        return

    def make_all(self):
        """run checks, make all arrays, make output
        
        Generally run this after attributes have been entered
        
        See also
        --------
        check_all
        make_time_independent_arrays
        make_time_dependent_arrays
        make_output
        
        """
        self.check_all()
        self.make_time_independent_arrays()
        self.make_time_dependent_arrays()
        self.make_output()
        
        return        
        
    def make_time_independent_arrays(self):
        """make all time-independent arrays. To be overridden in subclasses"""               
        pass    

    def make_time_dependent_arrays(self):
        """make all time-independent arrays. To be overridden in subclasses"""               
        pass    
        
    def make_output(self):
        """make all output. To be overridden in subclasses"""               
        pass    
    
    
def dim1sin_f(m, outz, tvals, v_E_Igamv_the, drn, top_vs_time = None, bot_vs_time=None):
    """assemble output u(Z,t) = phi * v_E_Igam_v_the + utop(t) * (1-Z) + ubot(t)*Z
    
    Basically calculates the phi part for each tvals value, then dot product
    with v_E_Igamv_the.  Then account for non-zero boundary conditions by 
    adding utop(t)*(1-Z) and ubot(t)*Z parts for each outz, tvals pair
    
    
    Parameters
    ----------
        
    
    Notes
    -----
    
    
    """
    
    phi = integ.dim1sin(m, outz)
    u = np.dot(phi, v_E_Igamv_the)    
    #top part
    if not top_vs_time is None:        
        for mag_vs_time in top_vs_time:
            if drn==1: 
                u += pwise.pinterp_x_y(mag_vs_time, tvals, choose_max=True)                                            
            else:
                u += pwise.pinterp_xa_ya_multipy_x1b_x2b_y1b_y2b(mag_vs_time, PolyLine([0], [1], [1], [0]), tvals, outz, achoose_max=True)  
    #bot part           
    if not bot_vs_time is None:
        for mag_vs_time in bot_vs_time:
            u += pwise.pinterp_xa_ya_multipy_x1b_x2b_y1b_y2b(mag_vs_time, PolyLine([0], [1], [0], [1]), tvals, outz, achoose_max=True)          
    return u 

def dim1sin_avgf(m, z, tvals, v_E_Igamv_the, drn, top_vs_time = None, bot_vs_time=None):
    """Average u between Z1 and Z;: u(Z,t) = phi * v_E_Igam_v_the + utop(t) * (1-Z) + ubot(t)*Z
    
    Basically calculates the average phi part for each tvals value, then dot product
    with v_E_Igamv_the.  Then account for non-zero boundary conditions by 
    adding average of utop(t)*(1-Z) and average of ubot(t)*Z parts for each 
    avgz, tvals pair.
    
    
    Parameters
    ----------
        
    
    Notes
    -----
    
    
    """
    
    phi = integ.dim1sin_avg_between(m, z)
    

    avg = np.dot(phi, v_E_Igamv_the)
                   
    z1 = np.asarray(z)[:,0]
    z2 = np.asarray(z)[:,1]
    
    #top part                                 
    if not top_vs_time is None:
        for mag_vs_time in top_vs_time:                            
            if drn==1:
                #bottom part
                avg += pwise.pinterp_x_y(mag_vs_time, tvals, choose_max=True)
            else:                                                            
                avg += pwise.pxa_ya_multipy_avg_x1b_x2b_y1b_y2b_between(mag_vs_time,
                                                                        PolyLine([0], [1], [1], [0]),
                                                                        tvals, z1, z2, achoose_max=True)                                                                                                                
    #botom part           
    if not bot_vs_time is None:
        for mag_vs_time in bot_vs_time:
            avg += pwise.pxa_ya_multipy_avg_x1b_x2b_y1b_y2b_between(mag_vs_time,
                                                                        PolyLine([0], [1], [0], [1]),
                                                                        tvals, z1,z2, achoose_max=True)                                                                             

    return avg    




def dim1sin_integrate_af(m, z, tvals, v_E_Igamv_the, drn, a, top_vs_time = None, bot_vs_time=None):
    """Integrate between Z1 and Z2: a(Z)*(phi * v_E_Igam_v_the + utop(t) * (1-Z) + ubot(t)*Z)
        
    
    
    Parameters
    ----------
        
    
    Notes
    -----
    
    
    """
    
    
    z1 = np.array(z)[:,0]
    z2 = np.array(z)[:,1]            
    #a*u part
    phi = integ.pdim1sin_a_linear_between(m, a, z)
    
    out = np.dot(phi, v_E_Igamv_the)    
                                                   
    #top part                        
    if not top_vs_time is None:
        for mag_vs_time in top_vs_time:                            
            if drn==1:                                
                out += pwise.pxa_ya_multiply_integrate_x1b_x2b_y1b_y2b_multiply_x1c_x2c_y1c_y2c_between(
                    mag_vs_time,
                    a,
                    PolyLine(a.x1, a.x2, np.ones_like(a.x1), np.ones_like(a.x2)),
                    tvals, z1, z2, achoose_max=True)  
            else:
                out += pwise.pxa_ya_multiply_integrate_x1b_x2b_y1b_y2b_multiply_x1c_x2c_y1c_y2c_between(
                    mag_vs_time,
                    a,
                    PolyLine(a.x1, a.x2, 1-a.x1, 1-a.x2),
                    tvals, z1, z2, achoose_max=True)
                                                        
                                                                                                                                
    #bot part           
    if not bot_vs_time is None:
        for mag_vs_time in bot_vs_time:
            out += pwise.pxa_ya_multiply_integrate_x1b_x2b_y1b_y2b_multiply_x1c_x2c_y1c_y2c_between(
                    mag_vs_time,
                    a,
                    PolyLine(a.x1, a.x2, a.x1, a.x2),
                    tvals, z1, z2, achoose_max=True) 
    #self.set *= self.H * self.mvref                                
    return out
    
def dim1sin_E_Igamv_the_aDmagDt_bilinear(m, eigs, a, mag_vs_depth, mag_vs_time, tvals, Igamv, dT=1.0):
    """Loading dependant E_Igamv_the matrix for a(z)*D[mag(z, t), t] where mag is bilinear in depth and time
    
    Make the E*inverse(gam*v)*theta part of solution u=phi*v*E*inverse(gam*v)*theta. 
    The contribution of each `mag_vs_time`-`mag_vs_depth` pair are superposed. 
    The result is an array
    of size (neig, len(tvals)). So the columns are the column array 
    E*inverse(gam*v)*theta calculated at each output time.  This will allow
    us later to do u = phi*v*E_Igamv_the

    Uses sin(m*z) in the calculation of theta.
    
    Parameters
    ----------
    m : ``list`` of ``float``
        eigenvlaues of BVP. generate with geoteca.speccon.m_from_sin_mx
    eigs : 1d numpy.ndarray
        list of eigenvalues
    a : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        loading term is mv*D[sigma(z, t), t] so a would be mv.
    mag_vs_depth : list of PolyLine
        Piecewise linear magnitude  vs depth.
    mag_vs_time : list of PolyLine
        Piecewise linear magnitude vs time
    tvals : 1d numpy.ndarray`
        list of time values to calculate integral at
    dT : ``float``, optional
        time factor multiple (default = 1.0)        
    
    Returns
    -------
    E_Igamv_the: ndarray
        loading matrix        
    
    Notes
    -----        
    Assuming the loads are formulated as the product of separate time and depth 
    dependant functions: 
    
    .. math:: \\sigma\\left({Z,t}\\right)=\\sigma\\left({Z}\\right)\\sigma\\left({t}\\right)
    
    the solution to the consolidation equation using the spectral method has 
    the form:
    
    .. math:: u\\left(Z,t\\right)=\\mathbf{\\Phi v E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta} 
    
    In this instance :math:`\\sigma\\left({Z}\\right)` 
    and :math:`\\sigma\\left({t}\\right)` are piecewise linear in depth and 
    time (hence the 'bilinear' in the function name).
    
    `dim1sin_E_Igamv_the_aDmagDt_bilinear` will calculate  
    :math:`\\mathbf{E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta}` 
    for terms with the form:
    
    .. math:: a\\left({z}\\right)\\frac{\\partial\\sigma\\left({Z,t}\\right)}{\\partial t}
    
    where :math:`a\\left(z\\right)` is a piecewise linear function 
    w.r.t. :math:`z`
    
    """
    
    E_Igamv_the = np.zeros((len(m), len(tvals)))
    
    
    if sum([v is None for v in [mag_vs_depth, mag_vs_time]])==0:
        
        for mag_vs_t, mag_vs_z in zip(mag_vs_time, mag_vs_depth):
            a, mag_vs_z = pwise.polyline_make_x_common(a, mag_vs_z)                      
            theta = integ.pdim1sin_ab_linear(m, a, mag_vs_z) 
            E = integ.pEDload_linear(mag_vs_t, eigs, tvals, dT)                                   

            #theta is 1d array, Igamv is nieg by neig array, np.dot(Igamv, theta) 
            #and np.dot(theta, Igamv) will give differetn 1d arrays.  
            #Basically np.dot(Igamv, theta) gives us what we want i.e. 
            #theta was treated as a column array.  The alternative 
            #np.dot(theta, Igamv) would have treated theta as a row vector.
            E_Igamv_the += (E*np.dot(Igamv, theta)).T
            
    return E_Igamv_the


def dim1sin_E_Igamv_the_abmag_bilinear(m, eigs, a,b, mag_vs_depth, mag_vs_time, tvals, Igamv, dT=1.0):
    """Loading dependant E_Igamv_the matrix for a(z)*b(z)*D[mag(z, t), t] where mag is bilinear in depth and time
    
    Make the E*inverse(gam*v)*theta part of solution u=phi*v*E*inverse(gam*v)*theta. 
    The contribution of each `mag_vs_time`-`mag_vs_depth` pair are superposed. 
    The result is an array
    of size (neig, len(tvals)). So the columns are the column array 
    E*inverse(gam*v)*theta calculated at each output time.  This will allow
    us later to do u = phi*v*E_Igamv_the

    Uses sin(m*z) in the calculation of theta.
    
    Parameters
    ----------
    m : ``list`` of ``float``
        eigenvlaues of BVP. generate with geoteca.speccon.m_from_sin_mx
    eigs : 1d numpy.ndarray
        list of eigenvalues
    a : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        loading term is mv*D[sigma(z, t), t] so a would be mv.
    b : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation vacuum term is 
         kh*et*w(z,t) so a would be `kh`, `b` would be `et`
    mag_vs_depth : list of PolyLine
        Piecewise linear magnitude  vs depth.
    mag_vs_time : list of PolyLine
        Piecewise linear magnitude vs time
    tvals : 1d numpy.ndarray`
        list of time values to calculate integral at
    dT : ``float``, optional
        time factor multiple (default = 1.0)        
    
    Returns
    -------
    E_Igamv_the: ndarray
        loading matrix        
    
    Notes
    -----        
    Assuming the loads are formulated as the product of separate time and depth 
    dependant functions: 
    
    .. math:: \\sigma\\left({Z,t}\\right)=\\sigma\\left({Z}\\right)\\sigma\\left({t}\\right)
    
    the solution to the consolidation equation using the spectral method has 
    the form:
    
    .. math:: u\\left(Z,t\\right)=\\mathbf{\\Phi v E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta} 
    
    In this instance :math:`\\sigma\\left({Z}\\right)` 
    and :math:`\\sigma\\left({t}\\right)` are piecewise linear in depth and 
    time (hence the 'bilinear' in the function name).
    
    `dim1sin_E_Igamv_the_abDmagDt_bilinear` will calculate  
    :math:`\\mathbf{E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta}` 
    for terms with the form:
    
    .. math:: a\\left({z}\\right)b\\left({z}\\right)\\frac{\\partial\\sigma\\left({Z,t}\\right)}{\\partial t}
    
    where :math:`a\\left(z\\right)`, :math:`b\\left(z\\right)` are 
    piecewise linear functions w.r.t. :math:`z`.
    
    
    """
    
    E_Igamv_the = np.zeros((len(m), len(tvals)))
    
    
    if sum([v is None for v in [mag_vs_depth, mag_vs_time]])==0:
        
        for mag_vs_t, mag_vs_z in zip(mag_vs_time, mag_vs_depth):
            a, b , mag_vs_z = pwise.polyline_make_x_common(a, b, mag_vs_z)                      
            theta = integ.pdim1sin_abc_linear(m, a, b, mag_vs_z) 
            E = integ.pEload_linear(mag_vs_t, eigs, tvals, dT)                                   

            #theta is 1d array, Igamv is nieg by neig array, np.dot(Igamv, theta) 
            #and np.dot(theta, Igamv) will give differetn 1d arrays.  
            #Basically np.dot(Igamv, theta) gives us what we want i.e. 
            #theta was treated as a column array.  The alternative 
            #np.dot(theta, Igamv) would have treated theta as a row vector.
            E_Igamv_the += (E*np.dot(Igamv, theta)).T
            
    return E_Igamv_the



def dim1sin_E_Igamv_the_BC_aDfDt_linear(drn, m, eigs, a, top_vs_time, bot_vs_time, tvals, Igamv, dT=1.0):
    """Loading dependant E_Igamv_the matrix that arise from homogenising a(z)*D[u(z, t), t] for non_zero top and bottom boundary conditions
    
    When accounting for non-zero boundary conditions we homogenise the 
    governing equation by letting u(Z,t) = v(Z,t) + utop(t)*(1-Z) + ubot(t)*Z 
    and solving for v(Z, t).  This function calculates the 
    E*inverse(gam*v)*theta part of solution v(Z,t)=phi*v*E*inverse(gam*v)*theta. 
    For the terms that arise by subbing the BC's into terms like a(z)*D[u(Z,t), t]
    
    The contribution of each `mag_vs_time` are superposed. 
    The result is an array
    of size (neig, len(tvals)). So the columns are the column array 
    E*inverse(gam*v)*theta calculated at each output time.  This will allow
    us later to do v(Z,t) = phi*v*E_Igamv_the

    Uses sin(m*z) in the calculation of theta.
    
    Parameters
    ----------
    drn : [0,1]
        drainage condition,
        0 = Pervious top pervious bottom (PTPB)
        1 = Pervious top impoervious bottom (PTIB)
    m : ``list`` of ``float``
        eigenvlaues of BVP. generate with geoteca.speccon.m_from_sin_mx
    eigs : 1d numpy.ndarray
        list of eigenvalues
    a : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        loading term is mv*D[sigma(z, t), t] so a would be mv.
    top_vs_time : list of PolyLine
        Piecewise linear magnitude  vs time for the top boundary.
    bot_vs_time : list of PolyLine
        Piecewise linear magnitude vs time for the bottom boundary.
    tvals : 1d numpy.ndarray`
        list of time values to calculate integral at
    dT : ``float``, optional
        time factor multiple (default = 1.0)        
    
    Returns
    -------
    E_Igamv_the: ndarray
        loading matrix        
    
    Notes
    -----        
    Assuming the loads are formulated as the product of separate time and depth 
    dependant functions: 
    
    .. math:: \\sigma\\left({Z,t}\\right)=\\sigma\\left({Z}\\right)\\sigma\\left({t}\\right)
    
    the solution to the consolidation equation using the spectral method has 
    the form:
    
    .. math:: u\\left(Z,t\\right)=\\mathbf{\\Phi v E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta} 
    
    
    when we consider non-zero boundary conditions, additional loading terms are
    created when we sub in the following into the original governing equation.
    
    .. math:: u\\left({Z,t}\\right)=v\\left({Z,t}\\right) + u_{top}\\left({t}\\right)\\left({1-Z}\\right)
    
    Two additional loading terms are created with each substitution, one 
    for the top boundary condition and one for the bottom boundary condition.
    
    This function calculates :math:`\\mathbf{E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta}`
    when substitutions are made in 
    terms of the following form:
    
    
    .. math:: a\\left({z}\\right)\\frac{\\partial u}{\\partial t}
    
    It is assumed that :math:`u_{top}\\left({t}\\right)` and 
    :math:`u_{bot}\\left({t}\\right)` are piecewise linear
    in time, and that multiple functions are superposed.  Also :math:`a\\left(z\\right)` 
    is a piecewise linear function w.r.t. :math:`z`
        
    
    """
    
    E_Igamv_the = np.zeros((len(m), len(tvals)))
    
    
    
    
    if not a is None:
        if drn==1:
            zdist = PolyLine(a.x1,a.x2, np.ones_like(a.x1), np.ones_like(a.x2))
            #bot_vs_time=None
        else:
            zdist = PolyLine(a.x1,a.x2, 1-a.x1, 1-a.x2)
                            
        if not top_vs_time is None:       
            theta = integ.pdim1sin_ab_linear(m, a, zdist)            
            for top_vs_t in top_vs_time:                                        
                E = integ.pEDload_linear(top_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
                
                    
        if not bot_vs_time is None:       
            theta = integ.pdim1sin_ab_linear(m, a, PolyLine(a.x1,a.x2,a.x1,a.x2))                        
            for bot_vs_t in bot_vs_time:                                                        
                E = integ.pEDload_linear(bot_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
            
    #theta is 1d array, Igamv is nieg by neig array, np.dot(Igamv, theta) 
    #and np.dot(theta, Igamv) will give differetn 1d arrays.  
    #Basically np.dot(Igamv, theta) gives us what we want i.e. 
    #theta was treated as a column array.  The alternative 
    #np.dot(theta, Igamv) would have treated theta as a row vector.            
    return E_Igamv_the
  
def dim1sin_E_Igamv_the_BC_abf_linear(drn, m, eigs, a, b, top_vs_time, bot_vs_time, tvals, Igamv, dT=1.0):
    """Loading dependant E_Igamv_the matrix that arise from homogenising a(z)*b(z)u(z, t) for non_zero top and bottom boundary conditions
    
    When accounting for non-zero boundary conditions we homogenise the 
    governing equation by letting u(Z,t) = v(Z,t) + utop(t)*(1-Z) + ubot(t)*Z 
    and solving for v(Z, t).  This function calculates the 
    E*inverse(gam*v)*theta part of solution v(Z,t)=phi*v*E*inverse(gam*v)*theta. 
    For the terms that arise by subbing the BC's into terms like a(z)*b(z)*u(Z,t)
    
    The contribution of each `mag_vs_time` are superposed. 
    The result is an array
    of size (neig, len(tvals)). So the columns are the column array 
    E*inverse(gam*v)*theta calculated at each output time.  This will allow
    us later to do v(Z,t) = phi*v*E_Igamv_the

    Uses sin(m*z) in the calculation of theta.
    
    Parameters
    ----------
    drn : [0,1]
        drainage condition,
        0 = Pervious top pervious bottom (PTPB)
        1 = Pervious top impoervious bottom (PTIB)
    m : ``list`` of ``float``
        eigenvlaues of BVP. generate with geoteca.speccon.m_from_sin_mx
    eigs : 1d numpy.ndarray
        list of eigenvalues
    a : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        radial draiange term is dTh*kh*et*U(Z,t) `a` would be kh.
    b : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        radial draiange term is dTh* kh*et*U(Z,t) so `b` would be et
    top_vs_time : list of PolyLine
        Piecewise linear magnitude  vs time for the top boundary.
    bot_vs_time : list of PolyLine
        Piecewise linear magnitude vs time for the bottom boundary.
    tvals : 1d numpy.ndarray`
        list of time values to calculate integral at
    dT : ``float``, optional
        time factor multiple (default = 1.0)        
    
    Returns
    -------
    E_Igamv_the: ndarray
        loading matrix        
    
    Notes
    -----        
    Assuming the loads are formulated as the product of separate time and depth 
    dependant functions: 
    
    .. math:: \\sigma\\left({Z,t}\\right)=\\sigma\\left({Z}\\right)\\sigma\\left({t}\\right)
    
    the solution to the consolidation equation using the spectral method has 
    the form:
    
    .. math:: u\\left(Z,t\\right)=\\mathbf{\\Phi v E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta} 
    
    
    when we consider non-zero boundary conditions, additional loading terms are
    created when we sub in the following into the original governing equation.
    
    .. math:: u\\left({Z,t}\\right)=v\\left({Z,t}\\right) + u_{top}\\left({t}\\right)\\left({1-Z}\\right)
    
    Two additional loading terms are created with each substitution, one 
    for the top boundary condition and one for the bottom boundary condition.
    
    This function calculates :math:`\\mathbf{E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta}`
    when substitutions are made in 
    terms of the following form:    
    
    .. math:: a\\left({z}\\right)b\\left({z}\\right)u\\left({Z,t}\\right)
    
    It is assumed that :math:`u_{top}\\left({t}\\right)` and 
    :math:`u_{bot}\\left({t}\\right)` are piecewise linear
    in time, and that multiple functions are superposed.  Also :math:`a\\left(z\\right)` 
    and :math:`b\\left(z\\right)` are piecewise linear functions w.r.t. :math:`z`.
          
    
    """
    
    E_Igamv_the = np.zeros((len(m), len(tvals)))
        
    if sum([v is None for v in [a, b]]) == 0:
        a, b = pwise.polyline_make_x_common(a, b)                
        if drn==1:
            zdist = PolyLine(a.x1,a.x2, np.ones_like(a.x1), np.ones_like(a.x2))
            #bot_vs_time=None
        else:
            zdist = PolyLine(a.x1,a.x2, 1-a.x1, 1-a.x2)
                            
        if not top_vs_time is None:       
            theta = integ.pdim1sin_abc_linear(m, a,b, zdist)            
            for top_vs_t in top_vs_time:                                        
                E = integ.pEload_linear(top_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
                                    
        if not bot_vs_time is None:       
            theta = integ.pdim1sin_abc_linear(m, a, b, PolyLine(a.x1,a.x2,a.x1,a.x2))            
            for bot_vs_t in bot_vs_time:                                        
                E = integ.pEload_linear(bot_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
            
    #theta is 1d array, Igamv is nieg by neig array, np.dot(Igamv, theta) 
    #and np.dot(theta, Igamv) will give differetn 1d arrays.  
    #Basically np.dot(Igamv, theta) gives us what we want i.e. 
    #theta was treated as a column array.  The alternative 
    #np.dot(theta, Igamv) would have treated theta as a row vector.            
    return E_Igamv_the
    
def dim1sin_E_Igamv_the_BC_D_aDf_linear(drn, m, eigs, a, top_vs_time, bot_vs_time, tvals, Igamv, dT=1.0):
    """Loading dependant E_Igamv_the matrix that arise from homogenising D[a(z)*D[u(z, t),z],z] for non_zero top and bottom boundary conditions
    
    When accounting for non-zero boundary conditions we homogenise the 
    governing equation by letting u(Z,t) = v(Z,t) + utop(t)*(1-Z) + ubot(t)*Z 
    and solving for v(Z, t).  This function calculates the 
    E*inverse(gam*v)*theta part of solution v(Z,t)=phi*v*E*inverse(gam*v)*theta. 
    For the terms that arise by subbing the BC's into terms like a(z)*b(z)*u(Z,t)
    
    The contribution of each `mag_vs_time` are superposed. 
    The result is an array
    of size (neig, len(tvals)). So the columns are the column array 
    E*inverse(gam*v)*theta calculated at each output time.  This will allow
    us later to do v(Z,t) = phi*v*E_Igamv_the

    Uses sin(m*z) in the calculation of theta.
    
    Parameters
    ----------
    drn : [0,1]
        drainage condition,
        0 = Pervious top pervious bottom (PTPB)
        1 = Pervious top impoervious bottom (PTIB)
    m : ``list`` of ``float``
        eigenvlaues of BVP. generate with geotecca.speccon.m_from_sin_mx
    eigs : 1d numpy.ndarray
        list of eigenvalues
    a : PolyLine
        Piewcewise linear function.  e.g. for 1d consolidation surcharge
        radial draiange term is D[kv(z)*D[u(Z,t), Z],Z] so `a` would be kv.    
    top_vs_time : list of PolyLine
        Piecewise linear magnitude  vs time for the top boundary.
    bot_vs_time : list of PolyLine
        Piecewise linear magnitude vs time for the bottom boundary.
    tvals : 1d numpy.ndarray`
        list of time values to calculate integral at
    dT : ``float``, optional
        time factor multiple (default = 1.0)        
    
    Returns
    -------
    E_Igamv_the: ndarray
        loading matrix        
    
    Notes
    -----        
    Assuming the loads are formulated as the product of separate time and depth 
    dependant functions: 
    
    .. math:: \\sigma\\left({Z,t}\\right)=\\sigma\\left({Z}\\right)\\sigma\\left({t}\\right)
    
    the solution to the consolidation equation using the spectral method has 
    the form:
    
    .. math:: u\\left(Z,t\\right)=\\mathbf{\\Phi v E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta} 
    
    
    when we consider non-zero boundary conditions, additional loading terms are
    created when we sub in the following into the original governing equation.
    
    .. math:: u\\left({Z,t}\\right)=v\\left({Z,t}\\right) + u_{top}\\left({t}\\right)\\left({1-Z}\\right)
    
    Two additional loading terms are created with each substitution, one 
    for the top boundary condition and one for the bottom boundary condition.
    
    This function calculates :math:`\\mathbf{E}\\left(\\mathbf{\\Gamma v}\\right)^{-1}\\mathbf{\\theta}`
    when substitutions are made in 
    terms of the following form:    
    
    .. math:: \\frac{\\partial}{\\partial Z}\\left({a\\left({Z}\\right)\\frac{\\partial u\\left({Z,t}\\right)}{\\partial Z}}\\right)
    
    It is assumed that :math:`u_{top}\\left({t}\\right)` and 
    :math:`u_{bot}\\left({t}\\right)` are piecewise linear
    in time, and that multiple functions are superposed.  Also :math:`a\\left(z\\right)` 
    is a piecewise linear functions w.r.t. :math:`z`.
          
    
    """
    
    E_Igamv_the = np.zeros((len(m), len(tvals)))
        
    if not a is None:                 
        if drn==1:
            zdist = PolyLine(a.x1,a.x2, np.ones_like(a.x1), np.ones_like(a.x2))
            #bot_vs_time=None
        else:
            zdist = PolyLine(a.x1,a.x2, 1-a.x1, 1-a.x2)
                            
        if not top_vs_time is None:       
            theta = integ.pdim1sin_D_aDb_linear(m, a, zdist)            
            for top_vs_t in top_vs_time:                                                        
                E = integ.pEload_linear(top_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
                                    
        if not bot_vs_time is None:       
            theta = integ.pdim1sin_D_aDb_linear(m, a, PolyLine(a.x1,a.x2,a.x1,a.x2))            
            for bot_vs_t in bot_vs_time:                                        
                E = integ.pEload_linear(bot_vs_t, eigs, tvals, dT)                        
                E_Igamv_the += (E*np.dot(Igamv, theta)).T
            
    #theta is 1d array, Igamv is nieg by neig array, np.dot(Igamv, theta) 
    #and np.dot(theta, Igamv) will give differetn 1d arrays.  
    #Basically np.dot(Igamv, theta) gives us what we want i.e. 
    #theta was treated as a column array.  The alternative 
    #np.dot(theta, Igamv) would have treated theta as a row vector.            
    return E_Igamv_the
