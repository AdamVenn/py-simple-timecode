# Many thanks to Joshua Banton and PyTimeCode developers
# Also thanks to Matthias Bürcher for his work on the Excel timecode calculator - an inspiration!
# I have never had to do drop-frame calculation, so I will not try to figure that out until it actually comes up

#################################################
# TO DO:    - Roll around timecode at 24hrs
#################################################


import re
from warnings import warn
from random import randint

rex = re.compile(r'^\d{2}:\d{2}:\d{2}:\d{2}$')


def is_timecode(timecode: str)->bool:
    if type(timecode) is not str: return False
    global rex
    if rex.match(timecode) is None: return False
    if int(timecode[0:2]) > 23: return False
    if int(timecode[3:5]) > 59: return False
    if int(timecode[6:8]) > 59: return False
    if int(timecode[9:11]) > 59: return False
    return True


class TimecodeError(Exception):
    """Raised when an error occurred in timecode calculation"""
    pass


class Timecode:
    def __init__(self, tc, fps, pull=True, samples=None):
        self._set_frame_rate(fps)

        if isinstance(tc, str):
            nums = ''.join([x for x in tc if x.isdigit()])
            if len(nums) > 8:
                nums = nums[0:8]
            elif nums == '':
                nums = '00000000'
            elif len(nums) < 8:
                nums = '{:08}'.format(int(nums))
            tc = '{:02}:{:02}:{:02}:{:02}'.format(int(nums[0:2]), int(nums[2:4]), int(nums[4:6]), int(nums[6:8]))

            if not is_timecode(tc):
                raise TimecodeError("Invalid timecode.".format(tc))
            else:
                self.frames = self.tc_to_frames(tc)

        elif isinstance(tc, int):
            if len(str(tc)) == 8:
                warn("Timecode object created by frames, not timecode. Input: {}".format(tc))
            self.frames = tc
        else:
            raise TimecodeError("Type %s not supported for creating a timecode object." % tc.__class__.__name__)

    def tc_to_frames(self, tc: str) -> int:
        fps = round(self.fps)
        h = int(tc[0:2])
        m = int(tc[3:5])
        s = int(tc[6:8])
        f = int(tc[9:11])
        frames = (h * 3600 * fps) + (m * 60 * fps) + (s * fps) + f
        return frames

    def frames_to_tc(self) -> str:
        fps = round(self.fps)
        f = self.frames
        h, f = divmod(f, (fps * 3600))
        m, f = divmod(f, (fps * 60))
        s, f = divmod(f,  fps)
        return self._format_timecode(h, m, s, f)

    def change_frame_rate(self, fps, convert=False):
        """Change the frame rate of the timecode object.
        convert = True  = keep the same no. of frames
        convert = False = keep the same timecode
        """
        if not convert:
            tc = self.frames_to_tc()
            self._set_frame_rate(fps)
            self.frames = self.tc_to_frames(tc)
        else:
            self._set_frame_rate(fps)

    def to_samples(self, sampleRate=48000.00):
        """Returns sample count according to sample rate. For use with Pro Tools."""
        ##############################
        # erm, not doing the pull??
        ##############################
        S = round(sampleRate/self.fps)
        samples = self.frames * S
        return samples

    def samples_to_frames(self, sampleRate=48000.00):
        """Returns sample count according to sample rate. For use with Pro Tools."""
        ##############################
        # erm, not doing the pull??
        ##############################
        S = round(sampleRate/self.fps)
        samples = self.frames * S
        return samples

    def _set_frame_rate(self, fps):
        if fps in [23, '23', 23.98, '23.98']:
            fps = 23.976
        try:
            self.fps = float(fps)
        except ValueError:
            try:
                self.fps = float(''.join([x for x in fps if x in '1234567890.']))
            except ValueError:
                raise TimecodeError("Invalid frame rate: {}".format(fps))
        except:
            raise TimecodeError("Invalid frame rate: {}".format(fps))

        try:
            if 'drop' in fps:
                warn("Drop frame rates not supported!")
        except:
            pass

    def _format_timecode(self, h: int, m: int, s: int, f: int) -> str:
        return '{:02}:{:02}:{:02}:{:02}'.format(h, m, s, f)

    def __str__(self):
        return self.frames_to_tc()

    def __repr__(self):
        return self.frames_to_tc() + ' at ' + str(self.fps) + ' fps'

    def __int__(self):
        return self.frames

    def __eq__(self, other):
        """the overridden equality operator"""
        if isinstance(other, Timecode):
            return self.fps == other.fps and self.frames == other.frames
        elif isinstance(other, str):
            new_tc = Timecode(other, self.fps)
            return self.__eq__(new_tc)
        elif isinstance(other, int):
            return self.frames == other

    def __ge__(self, other):
        """override greater or equal to operator"""
        if isinstance(other, Timecode):
            return self.frames >= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(other, self.fps)
            return self.frames >= new_tc.frames
        elif isinstance(other, int):
            return self.frames >= other

    def __le__(self, other):
        """override less or equal to operator"""
        if isinstance(other, Timecode):
            return self.frames <= other.frames
        elif isinstance(other, str):
            new_tc = Timecode(other, self.fps)
            return self.frames <= new_tc.frames
        elif isinstance(other, int):
            return self.frames <= other

    def __gt__(self, other):
        """override greater than operator"""
        if isinstance(other, Timecode):
            return self.frames > other.frames
        elif isinstance(other, str):
            new_tc = Timecode(other, self.fps)
            return self.frames > new_tc.frames
        elif isinstance(other, int):
            return self.frames > other

    def __lt__(self, other):
        """override less than operator"""
        if isinstance(other, Timecode):
            return self.frames < other.frames
        elif isinstance(other, str):
            new_tc = Timecode(other, self.fps)
            return self.frames < new_tc.frames
        elif isinstance(other, int):
            return self.frames < other

    def __add__(self, other):
        """returns new Timecode instance with subtracted value"""
        if isinstance(other, Timecode):
            added_frames = self.frames + other.frames
        elif isinstance(other, int):
            added_frames = self.frames + other
        elif isinstance(other, str):
            other = Timecode(other, self.fps)
            added_frames = self.frames + other.frames
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(added_frames, self.fps)

    def __sub__(self, other):
        """returns new Timecode instance with subtracted value"""
        if isinstance(other, Timecode):
            subtracted_frames = self.frames - other.frames
        elif isinstance(other, int):
            subtracted_frames = self.frames - other
        elif isinstance(other, str):
            other = Timecode(other, self.fps)
            subtracted_frames = self.frames - other.frames
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(subtracted_frames, self.fps)

    def __mul__(self, other):
        """returns new Timecode instance with multiplied value"""
        if isinstance(other, Timecode):
            multiplied_frames = self.frames * other.frames
        elif isinstance(other, int):
            multiplied_frames = self.frames * other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(multiplied_frames, self.fps)

    def __floordiv__(self, other):
        """returns new Timecode instance with divided value"""
        if isinstance(other, Timecode):
            div_frames = self.frames // other.frames
        elif isinstance(other, int):
            div_frames = self.frames // other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(div_frames, self.fps)

    def __truediv__(self, other):
        """returns new Timecode instance with (rounded) divided value"""
        if isinstance(other, Timecode):
            div_frames = round(self.frames / other.frames)
        elif isinstance(other, int):
            div_frames = round(self.frames / other)
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(div_frames, self.fps)

    def __mod__(self, other):
        """returns new Timecode instance with modded value"""
        if isinstance(other, Timecode):
            mod_frames = self.frames % other.frames
        elif isinstance(other, int):
            mod_frames = self.frames % other
        else:
            raise TimecodeError(
                'Type %s not supported for arithmetic.' %
                other.__class__.__name__
            )
        return Timecode(mod_frames, self.fps)

def rand_TC() -> str:
    hr = randint(0, 23)
    return '{:02}:{:02}:{:02}:{:02}'.format(hr, randint(0,59), randint(0,59), randint(0,23))

def testing():
    ################################################################
    # To Do: Unit testing!
    ################################################################

    a = Timecode('10:10:10:10', 23.976)
    b = Timecode('05:05:05:18', 23.976)

    print("a - 11 = {}".format(a - 11))
    print("{} - {} = {}".format(a, b, a - b))
    print('\n')

    print("a + 20 = {}".format(a + 20))
    print("{} + {} = {}".format(a, b, a + b))
    print('\n')

    print("a * 2 = {}".format(a * 2))
    print("{} * {} = {}".format(a, b, a * b))
    print('\n')

    print("a / 2 = {}".format(a / 2))
    print("{} / {} = {}".format(a, b, a / b))
    print('\n')

    print("a // 2 = {}".format(a // 2))
    print("{} // {} = {}".format(a, b, a // b))
    print('\n')

    print("a % 2 = {}".format(a % 2))
    print("{} % {} = {}".format(a, b, a % b))
    print('\n')

    print("a == '10:10:10:10' = {}".format(a == '10:10:10:10'))
    print("{} == {} = {}".format(a, b, a == b))
    print('\n')

    print("a > '10:10:10:10' = {}".format(a > '10:10:10:10'))
    print("{} > {} = {}".format(a, b, a > b))
    print('\n')

    print("a >= '10:10:10:10' = {}".format(a >= '10:10:10:10'))
    print("{} >= {} = {}".format(a, b, a >= b))
    print('\n')

    print("a < '10:10:10:10' = {}".format(a < '10:10:10:10'))
    print("{} < {} = {}".format(a, b, a < b))
    print('\n')

    print("a <= '10:10:10:10' = {}".format(a < '10:10:10:10'))
    print("{} <= {} = {}".format(a, b, a < b))
    print('\n')

if __name__ == '__main__':
    a = Timecode(12345678, 23)
    print(a)













