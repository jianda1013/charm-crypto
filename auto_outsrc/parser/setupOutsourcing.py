from userFuncs import *
from charm import *
from toolbox import *
from toolbox.pairinggroup import *
from toolbox.secretutil import SecretUtil
from toolbox.ABEnc import *
from toolbox.symcrypto import AuthenticatedCryptoAbstraction
from toolbox.iterate import dotprod2
from schemes import *
from math import *
from charm.pairing import hash as SHA1

pk = {}
Y = {}
g = {}
h = {}
mk = {}
s = {}
egg = {}
attrs = {}
sh = {}
coeff = {}
share = {}
Dj = {}
Djp = {}
Cr = {}
Cpr = {}
DjBlinded = {}
DjpBlinded = {}

def setup():
	global pk
	global g
	global h
	global mk
	global egg

	input = None
	g = groupObj.random(G1)
	g2 = groupObj.random(G2)
	alpha = groupObj.random(ZR)
	beta = groupObj.random(ZR)
	h = (g ** beta)
	f = (g ** (1 / beta))
	i = (g2 ** alpha)
	egg = (pair(g, g2) ** alpha)
	mk = [beta, i]
	pk = [g, g2, h, f, egg]
	output = (mk, pk)

def keygen(S):
	global Y
	global s
	global Dj
	global Djp
	global DjBlinded
	global DjpBlinded

	input = [pk, mk, S]
	r = groupObj.random(ZR)
	p0 = (pk[1] ** r)
	D = ((mk[1] * p0) ** (1 / mk[0]))
	Y = len(S)
	for y in range(0, Y):
		s_y = groupObj.random(ZR)
		Dj[y] = (p0 * (groupObj.hash(S[y], G2) ** s_y))
		Djp[y] = (g ** s_y)
	sk = [S, D, Dj, Djp]
	zz = groupObj.random(ZR)
	SBlinded = S
	DBlinded = (D ** (1 / zz))
	lenDjBlinded = len(Dj)
	for y in range(0, lenDjBlinded):
		DjBlinded[y] = (Dj[y] ** (1 / zz))
	lenDjpBlinded = len(Djp)
	for y in range(0, lenDjpBlinded):
		DjpBlinded[y] = (Djp[y] ** (1 / zz))
	skBlinded = [SBlinded, DBlinded, DjBlinded, DjpBlinded]
	output = (zz, skBlinded)
	return output

def encrypt(M, policy_str):
	global Y
	global s
	global attrs
	global sh
	global share
	global Cr
	global Cpr

	input = [pk, M, policy_str]
	g, g2, h, f, egg = pk
	policy = createPolicy(policy_str)
	attrs = getAttributeList(policy)
	R = groupObj.random(GT)
	s = groupObj.hash([R, M], ZR)
	s_sesskey = SHA1(R)
	Ctl = (R * (egg ** s))
	sh = calculateSharesDict(s, policy)
	Y = len(sh)
	C = (h ** s)
	for y in range(0, Y):
		y1 = attrs[y]
		share[y] = sh[y1]
		Cr[y] = (g ** share[y])
		Cpr[y] = (groupObj.hash(attrs[y], G2) ** share[y])
	T1 = SymEnc(s_sesskey, M)
	ct = [policy_str, Ctl, C, Cr, Cpr, T1]
	output = ct
	return output

if __name__ == "__main__":
	global groupObj
	groupObj = PairingGroup('SS512')

	setup()
	(zz, skBlinded) = keygen(S)
	(ct) = encrypt(M, policy_str)