import binascii
import struct

from Crypto import Random
from Crypto.IO import PEM
from Crypto.Util.py3compat import tobytes, bord, bchr, b, tostr
from Crypto.Util.asn1 import DerSequence

from Crypto.Math.Numbers import Integer
from Crypto.Math.Primality import (test_probable_prime,COMPOSITE)
from Crypto.PublicKey import (_expand_subject_public_key_info)


class RsaKey(object):
    """Class defining an actual RSA key.
    :undocumented: __init__, __repr__, __getstate__, __eq__, __ne__, __str__,
                   sign, verify, encrypt, decrypt, blind, unblind, size
    """

    def __init__(self, **kwargs):
        """Build an RSA key.
        :Keywords:
          n : integer
            The modulus.
          e : integer
            The public exponent.
          d : integer
            The private exponent. Only required for private keys.
          p : integer
            The first factor of the modulus. Only required for private keys.
          q : integer
            The second factor of the modulus. Only required for private keys.
          u : integer
            The CRT coefficient (inverse of p modulo q). Only required for
            privta keys.
        """

        input_set = set(kwargs.keys())
        public_set = set(('n', 'e'))
        private_set = public_set | set(('p', 'q', 'd', 'u'))
        if input_set not in (private_set, public_set):
            raise ValueError("Some RSA components are missing")
        for component, value in kwargs.items():
            setattr(self, "_" + component, value)

    @property
    def n(self):
        """Modulus"""
        return int(self._n)

    @property
    def e(self):
        """Public exponent"""
        return int(self._e)

    @property
    def d(self):
        """Private exponent"""
        if not self.has_private():
            raise AttributeError("No private exponent available for public keys")
        return int(self._d)

    @property
    def p(self):
        """First factor of the modulus"""
        if not self.has_private():
            raise AttributeError("No CRT component 'p' available for public keys")
        return int(self._p)

    @property
    def q(self):
        """Second factor of the modulus"""
        if not self.has_private():
            raise AttributeError("No CRT component 'q' available for public keys")
        return int(self._q)

    @property
    def u(self):
        """Chinese remainder component (inverse of *p* modulo *q*)"""
        if not self.has_private():
            raise AttributeError("No CRT component 'u' available for public keys")
        return int(self._u)

    def size_in_bits(self):
        """Size of the RSA modulus in bits"""
        return self._n.size_in_bits()

    def size_in_bytes(self):
        """The minimal amount of bytes that can hold the RSA modulus"""
        return (self._n.size_in_bits() - 1) // 8 + 1

    def _encrypt(self, plaintext):
        if not 0 < plaintext < self._n:
            raise ValueError("Plaintext too large")
        return int(pow(Integer(plaintext), self._e, self._n))

    def _decrypt(self, ciphertext):
        if not 0 < ciphertext < self._n:
            raise ValueError("Ciphertext too large")
        if not self.has_private():
            raise TypeError("This is not a private key")

        # Blinded RSA decryption (to prevent timing attacks):
        # Step 1: Generate random secret blinding factor r,
        # such that 0 < r < n-1
        r = Integer.random_range(min_inclusive=1, max_exclusive=self._n)
        # Step 2: Compute c' = c * r**e mod n
        cp = Integer(ciphertext) * pow(r, self._e, self._n) % self._n
        # Step 3: Compute m' = c'**d mod n       (ordinary RSA decryption)
        m1 = pow(cp, self._d % (self._p - 1), self._p)
        m2 = pow(cp, self._d % (self._q - 1), self._q)
        h = m2 - m1
        while h < 0:
            h += self._q
        h = (h * self._u) % self._q
        mp = h * self._p + m1
        # Step 4: Compute m = m**(r-1) mod n
        result = (r.inverse(self._n) * mp) % self._n
        # Verify no faults occured
        if ciphertext != pow(result, self._e, self._n):
            raise ValueError("Fault detected in RSA decryption")
        return result

    def has_private(self):
        return hasattr(self, "_d")

    def can_encrypt(self):
        return True

    def can_sign(self):
        return True

    def publickey(self):
        return RsaKey(n=self._n, e=self._e)

    def __eq__(self, other):
        if self.has_private() != other.has_private():
            return False
        if self.n != other.n or self.e != other.e:
            return False
        if not self.has_private():
            return True
        return (self.d == other.d and
                self.q == other.q and
                self.p == other.p and
                self.u == other.u)

    def __ne__(self, other):
        return not (self == other)

    def __getstate__(self):
        # RSA key is not pickable
        from pickle import PicklingError
        raise PicklingError

    def __repr__(self):
        if self.has_private():
            extra = ", d=%d, p=%d, q=%d, u=%d" % (int(self._d), int(self._p),
                                                  int(self._q), int(self._u))
        else:
            extra = ""
        return "RsaKey(n=%d, e=%d%s)" % (int(self._n), int(self._e), extra)

    def __str__(self):
        if self.has_private():
            key_type = "Private"
        else:
            key_type = "Public"
        return "%s RSA key at 0x%X" % (key_type, id(self))


def construct(rsa_components, consistency_check=True):
    """Construct an RSA key from a tuple of valid RSA components.
    The modulus **n** must be the product of two primes.
    The public exponent **e** must be odd and larger than 1.
    In case of a private key, the following equations must apply:
    - e != 1
    - p*q = n
    - e*d = 1 mod lcm[(p-1)(q-1)]
    - p*u = 1 mod q
    :Parameters:
     rsa_components : tuple
        A tuple of long integers, with at least 2 and no
        more than 6 items. The items come in the following order:
            1. RSA modulus (*n*).
            2. Public exponent (*e*).
            3. Private exponent (*d*).
               Only required if the key is private.
            4. First factor of *n* (*p*).
               Optional, but factor q must also be present.
            5. Second factor of *n* (*q*). Optional.
            6. CRT coefficient, *(1/p) mod q* (*u*). Optional.
     consistency_check : boolean
        If *True*, the library will verify that the provided components
        fulfil the main RSA properties.
    :Raise ValueError:
        When the key being imported fails the most basic RSA validity checks.
    :Return: An RSA key object (`RsaKey`).
    """

    class InputComps(object):
        pass

    input_comps = InputComps()
    for (comp, value) in zip(('n', 'e', 'd', 'p', 'q', 'u'), rsa_components):
        setattr(input_comps, comp, Integer(value))

    n = input_comps.n
    e = input_comps.e
    if not hasattr(input_comps, 'd'):
        key = RsaKey(n=n, e=e)
    else:
        d = input_comps.d
        if hasattr(input_comps, 'q'):
            p = input_comps.p
            q = input_comps.q
        else:
            # Compute factors p and q from the private exponent d.
            # We assume that n has no more than two factors.
            # See 8.2.2(i) in Handbook of Applied Cryptography.
            ktot = d * e - 1
            # The quantity d*e-1 is a multiple of phi(n), even,
            # and can be represented as t*2^s.
            t = ktot
            while t % 2 == 0:
                t //= 2
            # Cycle through all multiplicative inverses in Zn.
            # The algorithm is non-deterministic, but there is a 50% chance
            # any candidate a leads to successful factoring.
            # See "Digitalized Signatures and Public Key Functions as Intractable
            # as Factorization", M. Rabin, 1979
            spotted = False
            a = Integer(2)
            while not spotted and a < 100:
                k = Integer(t)
                # Cycle through all values a^{t*2^i}=a^k
                while k < ktot:
                    cand = pow(a, k, n)
                    # Check if a^k is a non-trivial root of unity (mod n)
                    if cand != 1 and cand != (n - 1) and pow(cand, 2, n) == 1:
                        # We have found a number such that (cand-1)(cand+1)=0 (mod n).
                        # Either of the terms divides n.
                        p = Integer(n).gcd(cand + 1)
                        spotted = True
                        break
                    k *= 2
                # This value was not any good... let's try another!
                a += 2
            if not spotted:
                raise ValueError("Unable to compute factors p and q from exponent d.")
            # Found !
            assert ((n % p) == 0)
            q = n // p

        if hasattr(input_comps, 'u'):
            u = input_comps.u
        else:
            u = p.inverse(q)

        # Build key object
        key = RsaKey(n=n, e=e, d=d, p=p, q=q, u=u)

    # Very consistency of the key
    fmt_error = False
    if consistency_check:
        # Modulus and public exponent must be coprime
        fmt_error = e <= 1 or e >= n
        fmt_error |= Integer(n).gcd(e) != 1

        # For RSA, modulus must be odd
        fmt_error |= not n & 1

        if not fmt_error and key.has_private():
            # Modulus and private exponent must be coprime
            fmt_error = d <= 1 or d >= n
            fmt_error |= Integer(n).gcd(d) != 1
            # Modulus must be product of 2 primes
            fmt_error |= (p * q != n)
            fmt_error |= test_probable_prime(p) == COMPOSITE
            fmt_error |= test_probable_prime(q) == COMPOSITE
            # See Carmichael theorem
            phi = (p - 1) * (q - 1)
            lcm = phi // (p - 1).gcd(q - 1)
            fmt_error |= (e * d % int(lcm)) != 1
            if hasattr(key, 'u'):
                # CRT coefficient
                fmt_error |= u <= 1 or u >= q
                fmt_error |= (p * u % q) != 1
            else:
                fmt_error = True

    if fmt_error:
        raise ValueError("Invalid RSA key components")

    return key


def _import_pkcs1_public(encoded, *kwargs):
    # RSAPublicKey ::= SEQUENCE {
    #           modulus INTEGER, -- n
    #           publicExponent INTEGER -- e
    # }
    der = DerSequence().decode(encoded, nr_elements=2, only_ints_expected=True)
    return construct(der)


def _import_subjectPublicKeyInfo(encoded, *kwargs):

    algoid, encoded_key, params = _expand_subject_public_key_info(encoded)
    if algoid != oid or params is not None:
        raise ValueError("No RSA subjectPublicKeyInfo")
    return _import_pkcs1_public(encoded_key)


def _import_keyDER(extern_key, passphrase):
    """Import an RSA key (public or private half), encoded in DER form."""
    '''
    decodings = (_import_pkcs1_private,
                 _import_pkcs1_public,
                 _import_subjectPublicKeyInfo,
                 _import_x509_cert,
                 _import_pkcs8)
    '''
    try:
        #return _import_pkcs1_public(extern_key, passphrase)
        return _import_subjectPublicKeyInfo(extern_key, passphrase)
    except ValueError:
        pass
    '''
    for decoding in decodings:
        try:
            #return decoding(extern_key, passphrase)
            return _import_pkcs1_public(extern_key, passphrase)
        except ValueError:
            pass
    '''
    raise ValueError("RSA key format is not supported")


def import_key(extern_key, passphrase=None):
    """Import an RSA key (public or private half), encoded in standard
    form.
    :Parameter extern_key:
        The RSA key to import, encoded as a byte string.
        An RSA public key can be in any of the following formats:
        - X.509 certificate (binary or PEM format)
        - X.509 ``subjectPublicKeyInfo`` DER SEQUENCE (binary or PEM
          encoding)
        - `PKCS#1`_ ``RSAPublicKey`` DER SEQUENCE (binary or PEM encoding)
        - OpenSSH (textual public key only)
        An RSA private key can be in any of the following formats:
        - PKCS#1 ``RSAPrivateKey`` DER SEQUENCE (binary or PEM encoding)
        - `PKCS#8`_ ``PrivateKeyInfo`` or ``EncryptedPrivateKeyInfo``
          DER SEQUENCE (binary or PEM encoding)
        - OpenSSH (textual public key only)
        For details about the PEM encoding, see `RFC1421`_/`RFC1423`_.
        The private key may be encrypted by means of a certain pass phrase
        either at the PEM level or at the PKCS#8 level.
    :Type extern_key: string
    :Parameter passphrase:
        In case of an encrypted private key, this is the pass phrase from
        which the decryption key is derived.
    :Type passphrase: string
    :Return: An RSA key object (`RsaKey`).
    :Raise ValueError/IndexError/TypeError:
        When the given key cannot be parsed (possibly because the pass
        phrase is wrong).
    .. _RFC1421: http://www.ietf.org/rfc/rfc1421.txt
    .. _RFC1423: http://www.ietf.org/rfc/rfc1423.txt
    .. _`PKCS#1`: http://www.ietf.org/rfc/rfc3447.txt
    .. _`PKCS#8`: http://www.ietf.org/rfc/rfc5208.txt
    """
    extern_key = tobytes(extern_key)
    if passphrase is not None:
        passphrase = tobytes(passphrase)

    if extern_key.startswith(b('-----')):
        # This is probably a PEM encoded key.
        (der, marker, enc_flag) = PEM.decode(tostr(extern_key), passphrase)
        if enc_flag:
            passphrase = None
        return _import_keyDER(der, passphrase)

    raise ValueError("RSA key format is not supported")

# Backward compatibility
importKey = import_key

#: `Object ID`_ for the RSA encryption algorithm. This OID often indicates
#: a generic RSA key, even when such key will be actually used for digital
#: signatures.
#:
#: .. _`Object ID`: http://www.alvestrand.no/objectid/1.2.840.113549.1.1.1.html
oid = "1.2.840.113549.1.1.1"
