import pywikibot
from pywikibot import pagegenerators
import json
import re
from tqdm import tqdm

site = pywikibot.Site('en', 'metakgp')

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
    
def genFormattedGradeText(courseCode,new=False):
    # If new course, then text for the grades is different.
    stats = newGrades[courseCode]['grades']
    if new:
        text = u'\n| grades = {{Grades\n'+ ' '*11 +'| EX = '+ str(stats['EX']) +'\n'+ ' '*11 +'| A = '+ str(stats['A']) +'\n'+ ' '*11 +'| B = '+ str(stats['B']) +'\n'+ ' '*11 +'| C = '+ str(stats['C']) +'\n'+ ' '*11 +'| D = '+ str(stats['D']) +'\n'+ ' '*11 +'| P = '+ str(stats['P']) +'\n'+ ' '*11 +'| F = '+ str(stats['F']) +'\n'+ ' '*11 +'}}\n'
    else:
        text = u'{{Grades\n'+ ' '*11 +'| EX = '+ str(stats['EX']) +'\n'+ ' '*11 +'| A = '+ str(stats['A']) +'\n'+ ' '*11 +'| B = '+ str(stats['B']) +'\n'+ ' '*11 +'| C = '+ str(stats['C']) +'\n'+ ' '*11 +'| D = '+ str(stats['D']) +'\n'+ ' '*11 +'| P = '+ str(stats['P']) +'\n'+ ' '*11 +'| F = '+ str(stats['F']) +'\n'+ ' '*11 +'}}'
    return text

oldGrade = re.compile('{{Grades.*[0-9].* }}',re.DOTALL)
        
def updateGrades(code):
    temp = allcourses[code]
    temp.text = oldGrade.sub(genFormattedGradeText(code),temp.text)
    temp.save(summary='Updated grades',botflag=True)

def currentGradesOnWiki(code):
    g = re.findall(r'{{Grades.*[0-9].* }}',allcourses[code].text,re.DOTALL)[0]
    tupl = re.findall('([A-Z]+) = ([0-9]+)',g)
    return {i[0]:int(i[1]) for i in tupl}
    
def insertBefore(data, pattern, newText):
    i = data.find(pattern)
    return data[:i] + newText + data[i:]

def genPageNewText(courseCode):
    return insertBefore(allcourses[courseCode].text,'\n}}',genFormattedGradeText(courseCode,True))

def addGrades(courseCode):
    temp = allcourses[courseCode]
    temp.text = genPageNewText(courseCode)
    temp.save(summary='Added previous year\'s grade distribution',botflag=True)

def main():
    cat = pywikibot.Category(site,'Category:Courses')
    gen = pagegenerators.CategorizedPageGenerator(cat)
    global allcourses
    allcourses = {i.title()[:7]:i for i in gen}
    # allcourses = dict(allcourses.items()[0:20])
    # Update existing courses
    alreadyExistingGrades = []
    print 'Fetching existing grades'
    
    for i in tqdm(allcourses):
        if re.findall(r'{{Grades.*[0-9].* }}',allcourses[i].text,re.DOTALL):
            alreadyExistingGrades.append(i)
    
    for code in alreadyExistingGrades:
        try:
            if not currentGradesOnWiki(code) == newGrades[code]['grades']:
                updateGrades(code)
        except:
            pass
    # Add grades for new courses
    notExistingGrades = [i for i in allcourses if i in newGrades and i not in alreadyExistingGrades]
    for code in notExistingGrades:
        addGrades(code)
        
if __name__ == '__main__':
    newGrades = load('newGrades.json')
    main()
