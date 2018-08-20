from subprocess import check_output
import re
import json
# from tqdm import tqdm
# import threading
import multiprocessing as mp
import urllib2
import time

cookie = 'A9E69ED40E56337D0E967F2E8C094704.worker2'
NUM_PROCS = 32


def load(file):
    def convert(input):
        if isinstance(input, dict):
            return {convert(key): convert(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [convert(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
    dict_unicode = json.loads(open(file).read())
    return convert(dict_unicode)

def save(dic, name):
    with open(name + ".json", "w") as outfile:
        json.dump(dic, outfile)

opener = urllib2.build_opener()
opener.addheaders.append(('Cookie', 'JSESSIONID={}'.format(cookie)))
        
def getGrades(params):
	stud_time = time.time()
	q, code = params[0], params[1]
	f = opener.open("https://erp.iitkgp.ac.in/Acad/Pre_Registration/subject_grade_status.jsp?subno={}".format(code))
	nums = re.findall('([A-Z\s]+)\(No. of Student\) : ([0-9]+)', f.read())
	if len(nums)!=0:
		res = {str(d[0].strip()): int(d[1]) for d in nums}
	else:
		res = {}

	if len(res) != 0:
		grades = uniformizeGradesJSON(res)
		grades.pop('X', None)
		q.put( {code : {'grades': grades}} )
		stud_delta = time.time() - stud_time
		print "Fetched: " + str(q.qsize())  + " [ " + ('%.2f' % (stud_delta)) + " ]"

def uniformizeGradesJSON(stats):
    for i in ['EX','A','B','C','D','P','F']:
        if i not in stats:
            stats[i] = 0
    return stats

def main():
	start_time = time.time()
	newGrades = {}
	allcourses = load('courses.json').keys()
	class ScrapingPool(): # Call it Iron-Man pool
		def __init__(self,courses):
			self.pool = mp.Pool(processes=NUM_PROCS)
			self.man = mp.Manager()
			self.q = self.man.Queue()
			self.courses=courses
		def run(self):
			self.pool.map(getGrades, [(self.q, code) for code in self.courses])
			self.pool.close()
			self.pool.join()

	sp = ScrapingPool(allcourses)
	sp.run()

	while not sp.q.empty():
		entry = sp.q.get()
		newGrades.update(entry)

	save(newGrades, 'newGrades')
	delta_time = time.time() - start_time
	print "\n\nTotal time: " + ('%.2f' % delta_time)

if __name__ == '__main__':
    main()
