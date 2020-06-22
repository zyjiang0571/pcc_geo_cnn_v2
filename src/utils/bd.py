#!/usr/bin/python
# Copyright 2014 Google.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Converts video encoding result data from text files to visualization
data source."""

# __author__ = "jzern@google.com (James Zern),"
# __author__ += "jimbankoski@google.com (Jim Bankoski)"
# __author__ += "hta@gogle.com (Harald Alvestrand)"
# From https://github.com/google/compare-codecs/blob/master/lib/visual_metrics.py
# Maurice Quach: Added Spline approximation


import math

import numpy as np
from scipy.interpolate import PchipInterpolator


def preprocess(x, col):
    x = np.asarray(x)
    x = np.unique(x, axis=0)
    x = x[np.argsort(x[:, col])]
    return x


def bdsnr(metric_set1, metric_set2, pchip=True):
    """
    BJONTEGAARD    Bjontegaard metric calculation
    Bjontegaard's metric allows to compute the average gain in psnr between two
    rate-distortion curves [1].
    rate1,psnr1 - RD points for curve 1
    rate2,psnr2 - RD points for curve 2

    returns the calculated Bjontegaard metric 'dsnr'

    code adapted from code written by : (c) 2010 Giuseppe Valenzise
    http://www.mathworks.com/matlabcentral/fileexchange/27798-bjontegaard-metric/content/bjontegaard.m
    """
    # pylint: disable=too-many-locals
    # numpy seems to do tricks with its exports.
    # pylint: disable=no-member
    # map() is recommended against.
    # pylint: disable=bad-builtin
    metric_set1 = preprocess(metric_set1, 0)
    metric_set2 = preprocess(metric_set2, 0)
    rate1 = [x[0] for x in metric_set1]
    psnr1 = [x[1] for x in metric_set1]
    rate2 = [x[0] for x in metric_set2]
    psnr2 = [x[1] for x in metric_set2]

    log_rate1 = list(map(math.log, rate1))
    log_rate2 = list(map(math.log, rate2))

    # Integration interval.
    min_int = max([min(log_rate1), min(log_rate2)])
    max_int = min([max(log_rate1), max(log_rate2)])

    if pchip:
        poly1 = PchipInterpolator(log_rate1, psnr1)
        poly2 = PchipInterpolator(log_rate2, psnr2)

        int1 = poly1.integrate(min_int, max_int)
        int2 = poly2.integrate(min_int, max_int)
    else:
        # Best cubic poly fit for graph represented by log_ratex, psrn_x.
        poly1 = np.polyfit(log_rate1, psnr1, 3)
        poly2 = np.polyfit(log_rate2, psnr2, 3)

        # Integrate poly1, and poly2.
        p_int1 = np.polyint(poly1)
        p_int2 = np.polyint(poly2)

        # Calculate the integrated value over the interval we care about.
        int1 = np.polyval(p_int1, max_int) - np.polyval(p_int1, min_int)
        int2 = np.polyval(p_int2, max_int) - np.polyval(p_int2, min_int)

    # Calculate the average improvement.
    if max_int != min_int:
        avg_diff = (int2 - int1) / (max_int - min_int)
    else:
        avg_diff = 0.0
    return avg_diff


def bdrate(metric_set1, metric_set2, pchip=True):
    """
    BJONTEGAARD    Bjontegaard metric calculation
    Bjontegaard's metric allows to compute the average % saving in bitrate
    between two rate-distortion curves [1].

    rate1,psnr1 - RD points for curve 1
    rate2,psnr2 - RD points for curve 2

    adapted from code from: (c) 2010 Giuseppe Valenzise

    """
    # numpy plays games with its exported functions.
    # pylint: disable=no-member
    # pylint: disable=too-many-locals
    # pylint: disable=bad-builtin
    metric_set1 = preprocess(metric_set1, 1)
    metric_set2 = preprocess(metric_set2, 1)
    rate1 = [x[0] for x in metric_set1]
    psnr1 = [x[1] for x in metric_set1]
    rate2 = [x[0] for x in metric_set2]
    psnr2 = [x[1] for x in metric_set2]

    log_rate1 = list(map(math.log, rate1))
    log_rate2 = list(map(math.log, rate2))

    # Integration interval.
    min_int = max([min(psnr1), min(psnr2)])
    max_int = min([max(psnr1), max(psnr2)])

    if pchip:
        poly1 = PchipInterpolator(psnr1, log_rate1)
        poly2 = PchipInterpolator(psnr2, log_rate2)

        int1 = poly1.integrate(min_int, max_int)
        int2 = poly2.integrate(min_int, max_int)
    else:
        # Best cubic poly fit for graph represented by log_ratex, psrn_x.
        poly1 = np.polyfit(psnr1, log_rate1, 3)
        poly2 = np.polyfit(psnr2, log_rate2, 3)

        # find integral
        p_int1 = np.polyint(poly1)
        p_int2 = np.polyint(poly2)

        # Calculate the integrated value over the interval we care about.
        int1 = np.polyval(p_int1, max_int) - np.polyval(p_int1, min_int)
        int2 = np.polyval(p_int2, max_int) - np.polyval(p_int2, min_int)

    # Calculate the average improvement.
    avg_exp_diff = (int2 - int1) / (max_int - min_int)

    # In really bad formed data the exponent can grow too large.
    # clamp it.
    if avg_exp_diff > 200:
        avg_exp_diff = 200

    # Convert to a percentage.
    avg_diff = (math.exp(avg_exp_diff) - 1) * 100

    return avg_diff

