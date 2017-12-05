import tarfile
import os.path
import gzip
from io import BytesIO

import ginit as g

tarpath = os.path.join("seeds","%s.tar.gz" % g.seed)

def tar_exists():
	return os.path.isfile(tarpath)

def add_to_tarfile(*filedata):
	try:
		tar = tarfile.open(fileobj=add_to_tarfile.fileobj,mode='a:')
	except AttributeError:
		add_to_tarfile.fileobj = BytesIO()
		tar = tarfile.open(fileobj=add_to_tarfile.fileobj,mode='w:')

	for f in filedata:
		data, filename = f
		tarinfo = tarfile.TarInfo(filename)
		if type(data).__name__ == 'bytes':
			tarinfo.size = len(data)
			data = BytesIO(data)
		else:
			tarinfo.size = len(data.getvalue())
		tar.addfile(tarinfo,data)
	tar.close()
	add_to_tarfile.fileobj.seek(0)

def save_tarfile():
	with gzip.GzipFile(tarpath,"wb") as targz_out:
		targz_out.write(add_to_tarfile.fileobj.getvalue())

def get_tar_data(filename):
	with tarfile.open(tarpath,'r:gz') as tar:
		for tarinfo in tar:
			if tarinfo.name == filename:
				file = tar.extractfile(filename)
				break
		else:
			print('%s not found in tarfile!'%filename)
			exit()
		return b"".join(file.readlines())

def get_tar_fileobj(filename):
	with tarfile.open(tarpath,'r:gz') as tar:
		for tarinfo in tar:
			if tarinfo.name == filename:
				file = tar.extractfile(filename)
				break
		else:
			print('%s not found in tarfile!'%filename)
			exit()
		return BytesIO(b"".join(file.readlines()))