import os
import json
import exiftool
import shutil

def findFiles(rootdir, extensions):
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


def parseYearAndMonth(datestring):
    year, month = 9999, 99
    if isinstance(datestring, basestring) and len(datestring) > 10:
        year = int(datestring[0:4])
        month = int(datestring[5:7])
    return year, month


def collectDateMetadata(files):
    dateMetadata = {}
    with exiftool.ExifTool() as et:
        allmetadata = et.get_metadata_batch(files)
    for metadata in allmetadata:
        filename = metadata['SourceFile']
        del metadata['SourceFile']
        year, month, selectedkey = 99999, 99, ''
        for k in metadata.keys():
            klower = k.lower()
            if 'date' not in klower:
                del metadata[k]
                continue
            thisyear, thismonth = parseYearAndMonth(metadata[k])
            if klower == 'exif:datetimeoriginal':
                year, month, selectedkey = thisyear, thismonth, k
                break
            if thisyear <= year and thismonth < month:
                year, month, selectedkey = thisyear, thismonth, k

        # Check if valid year/month were found
        if year != 9999 and month != 99:
            year = str(year)
            month = str(month).zfill(2)
            # Construct multi level dict with year: month: [filenames]
            if not year in dateMetadata:
                dateMetadata[year] = {}
            if not month in dateMetadata[year]:
                dateMetadata[year][month] = []
            dateMetadata[year][month].append(filename)
        else:
            print "No valid date found in", filename
    return dateMetadata


def makeFolder(folderpath):
    try:
        os.mkdir(folderpath)
    except OSError:
        pass


def organizeFiles(rootdir, metadata):
    for year in metadata:
        folderpath = os.path.join(rootdir, year)
        makeFolder(folderpath)
        for month in metadata[year]:
            folderpath = os.path.join(rootdir, year, month)
            makeFolder(folderpath)
            for filepath in metadata[year][month]:
                if os.path.dirname(filepath) == folderpath:
                    continue
                try:
                    shutil.move(filepath, folderpath)
                except shutil.Error:
                    print "Failed to move [%s] to [%s]" % (filepath, folderpath)
                    pass


if __name__ == '__main__':
    rootdir = '/Users/cgupta/Desktop'
    filetypes = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi',]
    filteredfiles = findFiles(rootdir, filetypes)

    dateMetadata = collectDateMetadata(filteredfiles)
    # print json.dumps(dateMetadata, indent = 1, sort_keys = True)
    organizeFiles(rootdir, dateMetadata)
    print "Done :)"
