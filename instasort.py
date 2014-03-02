import os, shutil
import time
import exiftool
import json

def findFiles(rootdir, extensions):
    matchedfiles = []
    for root, dirs, files in os.walk(rootdir):
        for f in files:
            extension = os.path.splitext(f)[1].lower()
            if extension.startswith('.') and extension[1:] in extensions:
                matchedfiles.append(os.path.join(root, f))
    return matchedfiles


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


def parseYearAndMonth(datestring):
    year, month = 9999, 99
    if isinstance(datestring, basestring) and len(datestring) > 10:
        try:
            year = int(datestring[0:4])
            month = int(datestring[5:7])
        except ValueError:
            pass
    return year, month


def collectDateMetadata(files, print_logs=False):
    dateMetadata = {}
    with exiftool.ExifTool() as et:
        allmetadata = et.get_metadata_batch(files)
    for metadata in allmetadata:
        good_exif_found = False
        filename = metadata['SourceFile']
        if print_logs:
            print "File:", filename
        year, month, selectedkey = 99999, 99, ''

        for k in metadata.keys():
            klower = k.lower()
            if 'date' not in klower or klower.startswith('icc_profile'):
                continue
            thisyear, thismonth = parseYearAndMonth(metadata[k])
            if klower == 'exif:datetimeoriginal':
                year, month, selectedkey = thisyear, thismonth, k
                good_exif_found = True
                break
            if thisyear < year or (thisyear == year and thismonth < month):
                year, month, selectedkey = thisyear, thismonth, k
                if print_logs:
                    print "Metadata Tag:", selectedkey, metadata[selectedkey]

        if not good_exif_found:
            selectedtime = modifiedtime = time.gmtime(os.path.getmtime(filename))
            createdtime = time.gmtime(os.path.getctime(filename))
            if createdtime < modifiedtime:
                selectedtime = createdtime
            selectedmonth = int(time.strftime("%m", selectedtime))
            selectedyear = int(time.strftime("%Y", selectedtime))
            if print_logs:
                print "File Timestamp:", time.strftime("%Y:%m:%d %H:%M:%S", (selectedtime))

            if selectedyear < year or (selectedyear == year and selectedmonth < month):
                year, month, selectedkey = selectedyear, selectedmonth, None

        # Check if valid year/month were found
        if year != 9999 and month != 99:
            if print_logs:
                if selectedkey:
                    print "Selected Tag:", selectedkey, metadata[selectedkey]
                else:
                    print "Using File Timestamp"
                print
            year = str(year)
            month = str(month).zfill(2)
            # Construct multi level dict with year: month: [filenames]
            if not year in dateMetadata:
                dateMetadata[year] = {}
            if not month in dateMetadata[year]:
                dateMetadata[year][month] = []
            dateMetadata[year][month].append(filename)
        else:
            print "ERROR: No valid date found in", filename
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
                    print "ERROR: Failed to move [%s] to [%s]" % (filepath, folderpath)
                    pass


if __name__ == '__main__':
    LOGS_ENABLED = False
    rootdir = '/Users/cgupta/Downloads/InstaSort'
    filetypes = ['jpg', 'jpeg', 'png', 'gif', 'mp4', 'avi',]
    filteredfiles = findFiles(rootdir, filetypes)

    if not filteredfiles:
        print "ERROR: No media files found."
        exit(0)

    dateMetadata = collectDateMetadata(filteredfiles, print_logs=LOGS_ENABLED)
    if LOGS_ENABLED:
        print json.dumps(dateMetadata, indent=1, sort_keys=True)

    organizeFiles(rootdir, dateMetadata)

    removeEmptyFolders(rootdir)
    print "\nDone :)"

