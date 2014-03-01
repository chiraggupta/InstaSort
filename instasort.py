import os
import json
import time
import exiftool

def fetchFilesWithExtensions(rootdir, extensions):
    matchedfiles = []
    dirs = [rootdir]
    while dirs:
        cur_dir = dirs[0]
        del dirs[0]
        # (path, dirnames, filenames)
        walk_result = os.walk(cur_dir).next()

        for subdir in walk_result[1]:
            dirs.append(os.path.join(cur_dir, subdir))

        for f in walk_result[2]:
            extension = os.path.splitext(f)[1].lower()
            if extension.startswith('.') and extension[1:] in extensions:
                matchedfiles.append(os.path.join(cur_dir, f))

    return matchedfiles

def getYearAndMonth(datestring):
    year, month = 9999, 99
    if isinstance(datestring, basestring) and len(datestring) > 10:
        year = int(datestring[0:4])
        month = int(datestring[5:7])
    return year, month


def printMetadata(files):
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata_batch(files)
    for md in metadata:
        print md['SourceFile']
        year, month, selectedkey = 99999, 99, ''
        for k in md.keys():
            klower = k.lower()
            if 'date' not in klower:
                del md[k]
                continue
            thisyear, thismonth = getYearAndMonth(md[k])
            if klower == 'exif:datetimeoriginal':
                year, month, selectedkey = thisyear, thismonth, k
                break
            if thisyear <= year and thismonth < month:
                year, month, selectedkey = thisyear, thismonth, k

        # Check if valid year/month were found
        if year != 9999 and month != 99:
            print "Year: ", year
            print "Month: ", month
            print

if __name__ == '__main__':
    filestoprocess = fetchFilesWithExtensions('/Users/cgupta/Desktop', ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi',])
    printMetadata(filestoprocess)

    print
