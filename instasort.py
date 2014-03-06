import os, shutil
import time
import exiftool
import json

LOGS_ENABLED = False

def findFiles(rootdir, extensions):
    matchedfiles = []
    for root, dirs, files in os.walk(rootdir):
        for f in files:
            extension = os.path.splitext(f)[1].lower()
            if extension.startswith('.') and extension[1:] in extensions:
                matchedfiles.append(os.path.join(root, f))
    return matchedfiles


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
                    print "ERROR: Failed to move [%s] to [%s]" % (filepath, folderpath)
                    pass


def removeEmptyFolders(rootdir):
    alldirs = []
    for root, dirs, files in os.walk(rootdir):
        for d in dirs:
            alldirs.append(os.path.join(root, d))
        for f in files:
            if f.startswith("."):
                os.remove(os.path.join(root, f))
                print f

    for d in reversed(alldirs):
        if os.listdir(d):
            continue
        try:
            os.rmdir(d)
            print "Deleted", d
        except:
            print "ERROR: Could not delete", d
            pass


# Returns (year, month)
def parseYearAndMonth(datestring):
    year, month = 99999, 99
    if isinstance(datestring, basestring) and len(datestring) > 10:
        try:
            year = int(datestring[0:4])
            month = int(datestring[5:7])
        except ValueError:
            pass
    return year, month


# Returns (year, month) or False
def getCreatedDate(filename, exifdata):
    year, month = 99999, 99
    for tag in exifdata:
        taglower = tag.lower()
        if 'date' not in taglower or taglower.startswith('icc_profile'):
            continue
        thisyear, thismonth = parseYearAndMonth(exifdata[tag])
        if LOGS_ENABLED:
            print "EXIF:", tag, exifdata[tag]

        if taglower == 'exif:datetimeoriginal':
            return thisyear, thismonth

        if thisyear < year or (thisyear == year and thismonth < month):
            year, month = thisyear, thismonth

    # Read file stats since the ideal tag wasn't found
    filetime = modifiedtime = time.gmtime(os.path.getmtime(filename))
    createdtime = time.gmtime(os.path.getctime(filename))
    if createdtime < modifiedtime:
        filetime = createdtime
    filemonth = int(time.strftime("%m", filetime))
    fileyear = int(time.strftime("%Y", filetime))
    if LOGS_ENABLED:
        print "File Timestamp:", time.strftime("%Y:%m:%d %H:%M:%S", (filetime))

    if fileyear < year or (fileyear == year and filemonth < month):
        year, month = fileyear, filemonth

    if year != 99999 and month != 99:
        return year, month

    return False


def collectDateMetadata(files):
    date_metadata = {}
    with exiftool.ExifTool() as et:
        allmetadata = et.get_metadata_batch(files)
    for metadata in allmetadata:
        filename = metadata['SourceFile']
        del metadata['SourceFile']
        if LOGS_ENABLED:
            print "File:", filename

        created_date = getCreatedDate(filename, metadata)
        if created_date:
            year = str(created_date[0])
            month = str(created_date[1]).zfill(2)
            if LOGS_ENABLED:
                print "Month Created: %s, %s" % (month, year)
                print
            # Construct multi level dict with year: month: [filenames]
            if not year in date_metadata:
                date_metadata[year] = {}
            if not month in date_metadata[year]:
                date_metadata[year][month] = []
            date_metadata[year][month].append(filename)
        else:
            print "ERROR: No valid date found for", filename
    return date_metadata

# Hacky temp function
def renameFiles():
    root = ''
    offset = 0
    filelist = os.listdir(root)

    for f in filelist:
        newf = 'DSC_' + str(int(f[4:-4]) + offset ).zfill(4) + '.JPG'
        os.rename(os.path.join(root, f), os.path.join(root, newf))

if __name__ == '__main__':
    rootdir = ''
    filetypes = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi', 'mov', 'nef']
    filteredfiles = findFiles(rootdir, filetypes)

    if not filteredfiles:
        print "ERROR: No media files found."
        exit(0)

    date_metadata = collectDateMetadata(filteredfiles)
    if LOGS_ENABLED:
        print json.dumps(date_metadata, indent=1, sort_keys=True)

    organizeFiles(rootdir, date_metadata)

    removeEmptyFolders(rootdir)
    print "\nDone :)"
