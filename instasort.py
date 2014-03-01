import os
import json
import time
import exiftool

def traverse(rootdir, filters):
    matchedfiles = []
    dirs = [rootdir]
    while dirs:
        cur_dir = dirs[0]
        del dirs[0]
        walk_result = os.walk(cur_dir).next()   # (path, dirnames, filenames)

        for subdir in walk_result[1]:
            dirs.append(os.path.join(cur_dir, subdir))

        for f in walk_result[2]:
            extension = os.path.splitext(f)[1].lower()
            if extension.startswith('.') and extension[1:] in filters:
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
        year, month, selectedkey = 9999, 99, ''
        for k in md.keys():
            klower = k.lower()
            if 'date' not in klower:
                del md[k]
            else:
                if klower == 'exif:datetimeoriginal':
                    year, month = getYearAndMonth(md[k])
                    selectedkey = k
                    break
                else:
                    thisyear, thismonth = getYearAndMonth(md[k])
                    if thisyear <= year and thismonth < month:
                        year, month, selectedkey = thisyear, thismonth, k
        print year, month

if __name__ == '__main__':
    filestoprocess = traverse('/Users/cgupta/Desktop', ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi',])
    printMetadata(filestoprocess)

    print
