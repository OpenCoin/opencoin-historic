"""The fraction class. It converts ints and strings to fractions."""

# helper functions
def gcd(a, b):
    if b == 0:
        return a

    return gcd(b, a % b)

def lcm(a, b):
    return a * b / gcd(a, b)

class Fraction:
    def __init__(self, val):
        import types

        if isinstance(val, self.__class__):
            self.num = val.num
            self.den = val.den

            self.reduce()

        elif isinstance(val, types.StringType):
            if val.count('/') == 1:
                num, den = val.split('/')
                self.num, self.den = int(num), int(den)

                if self.den == 0:
                    raise ZeroDenominatorError()

                if self.den < 0: # Move negative denominator to the numerator
                    self.num, self.den = -self.num, -self.den

            else:
                self.num = int(val)
                self.den = 1

        elif isinstance(val, types.IntType) or isinstance(val, types.LongType):
            self.num = val
            self.den = 1

        elif isinstance(val, types.TupleType):
            self.num, self.den = val

            if not isinstance(self.num, types.IntType) or isinstance(self.num, types.LongType):
                raise Exception()

            if not isinstance(self.den, types.IntType) or isinstance(self.den, types.LongType):
                raise Exception()

            if self.den < 0: # Move negative denominator to the numberator
                self.num, self.den = -self.num, -self.den

        # TODO: optionally, float conversion?

        else:
            raise Exception('%s' % val)
            raise NotImplementedError()

        self.reduce()

    def __add__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)

        new = Fraction((((self.num * other.den) + (other.num * self.den)), (self.den * other.den)))

        new.reduce()

        return new

    def __sub__(self, other):
        copy = Fraction(other)
        copy.num = -copy.num

        return self + copy

    def __mul__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)

        new = Fraction(( (self.num * other.num), (self.den * other.den) ))

        new.reduce()

        return new

    def __div__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)

        new = Fraction(( other.den, other.num )) # Inverse of other

        return self * new

    def reduce(self):
        """Reduce reduces a fraction to it's smallest numerator and denominator."""

        if self.den == 0:
            raise ZeroDenominatorError()

        divisor = gcd(self.num, self.den)

        self.num = self.num / divisor
        self.den = self.den / divisor

    def __str__(self):
        if self.den != 1:
            return "%s/%s" % (self.num, self.den)
        else:
            return "%s" % (self.num)

    def __repr__(self):
        return "<Fraction: %s>" % str(self)

    def __eq__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)

        return self.num == other.num and self.den == other.den

    def __cmp__(self, other):
        if not isinstance(other, Fraction):
            other = Fraction(other)

        common = lcm(self.den, other.den)

        self_num = self.num * common / self.den
        other_num = other.num * common / other.den

        return self_num.__cmp__(other_num)

    def __gt__(self, other):
        return self.__cmp__(other) == 1

    def __lt__(self, other):
        return self.__cmp__(other) == -1

    def __ne__(self, other):
        return not self == other

    def __hash__(self):
        return str(self).__hash__()


class ZeroDenominatorError(Exception):
    """A fraction with a zero denominator cannot be computed."""
