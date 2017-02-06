import re

def findPeriodString(input) :
    i = -4
    end = -1 * len(input)
    while i != end-1 and input[i] != '.':
        i -= 1

    result = input[i+1:-4]
    j = 0
    while not re.match("^[A-Za-z0-9]*$", result[j]):
        j += 1

    return result[j:]

def stringToEvents(lines):

    dates = ('January \d\d|January \d|February \d\d|February \d'
             '|March \d\d|March \d|April \d\d|April \d'
             '|May \d\d|May \d|June \d\d|June \d'
             '|July \d\d|July \d|August \d\d|August \d'
             '|September \d\d|September \d|October \d\d|October \d'
             '|November \d\d|November \d|December \d\d|December \d')

    d=re.findall(dates,lines)

    content=re.split(dates,lines)

    array_dates   = d
    array_content = []

    # for the first syllabus chunks - content before date
    found = False
    i = 0
    while found == False :
        current = content[i]
        lastWord = current[-3:-1]
        if lastWord == 'by' or lastWord == 'on' :
            newContent = findPeriodString(current)
            array_content.append(newContent)
        else :
            found = True
        i += 1

    # skipped bad chunk, now content after date
    while i < len(content):
        j = 0
        while not re.match("^[A-Za-z0-9]*$", content[i][j]):
            j += 1
        array_content.append(content[i][j:])
        i += 1

    return array_dates, array_content


def formatDate(stringDate) :
    split = re.split(' ', stringDate)
    month = split[0]
    m = '00'
    if month == 'January' :
        m = '01'
    elif month == 'February':
        m = '02'
    elif month == 'March':
        m = '03'
    elif month == 'April':
        m = '04'
    elif month == 'May':
        m = '05'
    else:
        m = '06'

    d = split[1]
    final = '2017-' + m + '-' + d + 'T17:00:00-08:00'
    finalEnd = '2017-' + m + '-' + d + 'T18:00:00-08:00'
    return final, finalEnd



