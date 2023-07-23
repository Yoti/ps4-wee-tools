#==========================================================
# Common utils
# part of ps4 wee tools project
#==========================================================
import hashlib, os, math, random
from lang._i18n_ import *



INFO_FILE_NOR	= '_sflash0_.txt'
INFO_FILE_2BLS	= '_2bls_.txt'


def genRandBytes(size):
	return bytearray(random.getrandbits(8) for _ in range(size))



def getData(file, off, len):
	#file must be in rb/r+b mode
	file.seek(off);
	return file.read(len)



def setData(file, off, val):
	#file must be in r+b mode
	file.seek(off);
	return file.write(val)



def checkFileSize(file, size):
	if not file or not os.path.isfile(file):
		print((STR_FILE_NOT_EXISTS).format(file))
		input(STR_BACK)
		return False
	
	if os.stat(file).st_size != size:
		print((STR_INCORRECT_SIZE).format(file))
		input(STR_BACK)
		return False
	
	return True



def getFilePathWoExt(file, correct = False):
	name = os.path.splitext(os.path.basename(file))[0]
	path = os.path.join(os.path.dirname(file),name)
	return path.replace(" ", "_") if correct else path



def getFileMD5(file):
    f = open(file, 'rb')
    f.seek(0)
    with f:
        res = f.read()
        return hashlib.md5(res).hexdigest()



def getHex(buf,sep=' '):
	str = ""
	for c in buf:
		str += '{:02X}'.format(c)+sep
	return str[:len(str)-len(sep)]



def swapBytes(arr):
	res = [0]*len(arr)
	for i in range(0,len(arr),2):
		res[i] = arr[i+1]
		res[i+1] = arr[i]
	return bytes(res)



def rawToClock(raw):
	if (0x10 <= raw <= 0x50):
		return (raw - 0x10) * 25 + 400
	return 0



def clockToRaw(frq):
	return (frq - 400) // 25 + 0x10



def savePatchData(file, data, patch = False):
	with open(file, 'wb') as f:
		f.write(data)
	
	if patch:
		patchFile(file, patch)



def patchFile(file, patch):
	with open(file, 'r+b') as f:
		for i in range(len(patch)):
			f.seek(patch[i]['o'],0)
			f.write(patch[i]['d'])



def entropy(file):
	
	with open(file, "rb") as f:
		data = f.read()
	
	vals = {byte: 0 for byte in range(2**8)}
	size = len(data)
	pp = size // 100
	
	for i in range(size):
		vals[data[i]] += 1
		if i % pp == 0:
			print('\r'+STR_PROGRESS.format(i // pp),end='')
	
	probs = [val / size for val in vals.values()]
	entropy = -sum(prob * math.log2(prob) for prob in probs if prob > 0)
	
	return {'00':probs[0],'ff':probs[0xff],'ent':entropy}
