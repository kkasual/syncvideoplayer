# Sync Player
# Copyright (C) 2023, Roman Arsenikhin
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

def ms_to_str(l, sign_always=False):
    if not l:
        return '0'
    if l < 0:
        sign = '-'
        l = -l
    else:
        if sign_always:
            sign = '+'
        else:
            sign = ''
    mins = l // 60000
    s = (l // 1000) % 60
    ms = l % 1000
    if mins > 0:
        return '%s%02d:%02d.%03d' % (sign, mins, s, ms)
    else:
        return '%s%d.%03d' % (sign, s, ms)

def ms_to_str_full(l, sign_always=False):
    if not l:
        return '00:00.000'
    if l < 0:
        sign = '-'
        l = -l
    else:
        if sign_always:
            sign = '+'
        else:
            sign = ''

    mins = l // 60000
    s = (l // 1000) % 60
    ms = l % 1000

    return '%s%02d:%02d.%03d' % (sign, mins, s, ms)
