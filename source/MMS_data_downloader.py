import requests, datetime, yaml, glob, os, math
from multiprocessing.dummy import Pool as ThreadPool
from multiprocessing.dummy import Queue
from clint.textui import progress

def processRequests(reqs):
    allMatchingFiles = []
    allDownloadFiles = []
    allOutdatedFiles = []
    allDamagedFiles = []
    allUpToDateFiles = []
    for req, query in reqs.items():
        if query['sc_id'] == None:
            query['sc_id'] = default_sc_id
        if query['start_date'] == None:
            query['start_date'] = default_start_date
        if query['end_date'] == None:
            query['end_date'] = default_end_date
        printRequest(req, query)
        with requests.get(url.format('file_info'), params=query) as response:
            code = response.status_code
            if (code == 200):
                print('Request successful!')
            else:
                print('Request failed.')
            print('Response status code: {} '.format(code))
            if code != 200:
                continue
            dictionary = response.json()
            # open(dataRootPath + r'\test.json', 'wb').write(response.content)
        # print('files_were_truncated = {}'.format(dictionary['files_were_truncated']))
        matchingFiles = list(dictionary['files'])
        addInfo(matchingFiles)
        upToDateFiles, downloadFiles, damagedFiles, outdatedFiles = findExistingFiles(matchingFiles)
        allMatchingFiles += matchingFiles
        allDownloadFiles += downloadFiles
        allOutdatedFiles += outdatedFiles
        allDamagedFiles += damagedFiles
        allUpToDateFiles += upToDateFiles
    printRequestSummary(allMatchingFiles, allUpToDateFiles, allDownloadFiles, allDamagedFiles, allOutdatedFiles)
    return allDownloadFiles

def findExistingFiles(matchingFiles):
    downloadFiles = []
    outdatedFiles = []
    damagedFiles = []
    upToDateFiles = []
    for f in matchingFiles:
        fileNameAnyVersion = f['file_name'].replace(f['version'], '*')
        existingFiles = glob.glob(dataRootPath + f['path'] + fileNameAnyVersion)
        if len(existingFiles) > 0:
            existingFiles.sort(key=lambda ef: getComparableVersion(getFileVersion(ef)))
            highestExistingVersion = getComparableVersion(getFileVersion(existingFiles[-1]))
            fVersion = getComparableVersion(f['version'])
            if highestExistingVersion == fVersion:
                if len(existingFiles) > 1:
                    outdatedFiles.extend(existingFiles[:-1])

                if f['file_size'] != os.path.getsize(existingFiles[-1]):
                    damagedFiles.append(existingFiles[-1])
                    downloadFiles.append(f)
                else:
                    upToDateFiles.append(existingFiles[-1])
            elif highestExistingVersion < fVersion:
                outdatedFiles.extend(existingFiles)
                downloadFiles.append(f)
            else:
                upToDateFiles.append(existingFiles[-1])
                outdatedFiles.extend(existingFiles[:-1])
        else:
            downloadFiles.append(f)

    printDownloadInfo(matchingFiles, upToDateFiles, downloadFiles, damagedFiles, outdatedFiles)
    return upToDateFiles, downloadFiles, damagedFiles, outdatedFiles

def printDownloadInfo(matchingFiles, upToDateFiles, downloadFiles, damagedFiles, outdatedFiles, usePromt=False):
    n_files = len(matchingFiles)
    n_upToDateFiles = len(upToDateFiles)
    n_downloadList = len(downloadFiles)
    if n_files > 0:
        size_files = getSize(matchingFiles)
        print('Found {} matching files. {}'.format(n_files, getHumanReadableSize(size_files)))
        size_upToDateFiles = getSizePaths(upToDateFiles)
        print('  {} up-to-date files already exists locally. {}'.format(n_upToDateFiles, getHumanReadableSize(size_upToDateFiles)))
        size_downloadList = getSize(downloadFiles)
        print('  {} files need to be downloaded. {}'.format(n_downloadList, getHumanReadableSize(size_downloadList)))
    else:
        print('The request matches 0 files. Try changing the request in the config file.')

    if len(damagedFiles) > 0:
        print('Found {} damaged files ({}). They will be replaced when downloading.'.format(len(damagedFiles), getHumanReadableSize(getSizePaths(damagedFiles))))
    if len(outdatedFiles) > 0:
        if usePromt:
            choice = input('Found {} outdated files. {} Delete them? [Y/n] '.format(len(outdatedFiles), getHumanReadableSize(getSizePaths(outdatedFiles))))
            if choice in ('', 'Y', 'y', 'Yes', 'yes'):
                for path in outdatedFiles:
                    os.remove(path)
        else:
            print('Found {} outdated files. {}'.format(len(outdatedFiles), getHumanReadableSize(getSizePaths(outdatedFiles))))

def addInfo(files):
    for f in files:
        fileName = f['file_name']
        lastPeriodIndex = fileName.rfind('.')
        fileNameNoType = fileName[:lastPeriodIndex]
        nameSplit = fileNameNoType.split('_')
        version = nameSplit.pop()[1:]
        f['version'] = version
        date = nameSplit.pop()
        nameSplit += [date[:4], date[4:6]]
        path = ''
        for string in nameSplit:
            path += '\\{}'.format(string)
        path += '\\'
        f['path'] = path

def getFileVersion(fileName):
    return fileName[fileName.rfind('_') + 2:fileName.rfind('.')]

def getComparableVersion(versionString):
    return list(map(int, versionString.split('.')))

def printRequest(req, query):
    print("\n--- Request: '{}' ---".format(req))
    string = ''
    for param, value in query.items():
        if value != None:
            string += '{} = {}, '.format(param, value)
    print("Query: {}".format(string[:-2]))
    print('Sending request...')

def printRequestSummary(allMatchingFiles, allUpToDateFiles, allDownloadFiles, allDamagedFiles, allOutdatedFiles):
    print('\n--- Request Summary ---')
    printDownloadInfo(allMatchingFiles, allUpToDateFiles, allDownloadFiles, allDamagedFiles, allOutdatedFiles, True)
    

def getSize(files):
    size = 0
    for f in files:
        size += f['file_size']
    return size

def getSizePaths(paths):
    size = 0
    for p in paths:
        size += os.path.getsize(p)
    return size

def getHumanReadableSize(size):
    prefix = ['B', 'KB', 'MB', 'GB', 'TB']
    prefix_counter = 0
    while size > 1000 and prefix_counter + 1 < len(prefix):
        prefix_counter += 1
        size /= 1024
    return '{} {}'.format(round(size, 2), prefix[prefix_counter])

def startDownload(allDownloadFiles):
    n_allDownloadFiles = len(allDownloadFiles)

    if n_allDownloadFiles > 0:
        size_allDownloadFiles = getSize(allDownloadFiles)
        print('\nReady to download {} files of total size {} ({} B)'.format(n_allDownloadFiles, getHumanReadableSize(size_allDownloadFiles), size_allDownloadFiles))
        choice = input('Proceed? [Y/n] ')
        if choice in ('', 'Y', 'y', 'Yes', 'yes'):
            downloadFiles(allDownloadFiles, n_allDownloadFiles, size_allDownloadFiles)
    else:
        print('\nAll requested files already exists locally.')

def partitionDownload(downloadFiles, n_downloadFiles, size_downloadFiles):
    downloadChunks = []
    for downloadFile in downloadFiles:
        (n_full_chunks, last_chunk) = divmod(downloadFile['file_size'], size_chunk)
        for i in range(n_full_chunks):
            downloadChunks.append((downloadFile, i*size_chunk, (i + 1)*size_chunk - 1, i))
        downloadChunks.append((downloadFile, n_full_chunks*size_chunk, n_full_chunks*size_chunk + last_chunk - 1, n_full_chunks))
    return downloadChunks


def downloadFiles(downloadFiles, n_downloadFiles, size_downloadFiles):
    global q, writeDict
    downloadChunks = partitionDownload(downloadFiles, n_downloadFiles, size_downloadFiles)
    n_downloadChunks = len(downloadChunks)
    n_threads = min(n_concurrentConnections, n_downloadChunks)
    if (n_threads < n_concurrentConnections):
        print('Number of connection threads was limited by download size.')

    q = Queue()
    completedDict = {}
    writeDict = {}
    delList = []
    for df in downloadFiles:
        writeDict[df['file_name']] = [0, int(df['file_size']/size_chunk)]
    print('Starting {} connection threads.'.format(n_threads))
    with progress.Bar(expected_size=size_downloadFiles) as bar:
        tp = ThreadPool(n_threads)
        tp.imap_unordered(downloadChunk, downloadChunks)
        current_size = 0
        while current_size < size_downloadFiles:
            if q.qsize() > 0:
                f, chunk_id, content = q.get()
                completedDict[(f['file_name'], chunk_id)] = (content, f['path'])
            for writer in writeDict:
                chunk = completedDict.get((writer, writeDict[writer][0]))
                if chunk != None:
                    current_size += writeChunk(chunk, writer, writeDict[writer][0])
                    del completedDict[(writer, writeDict[writer][0])]
                    writeDict[writer][0] += 1
                    if writeDict[writer][0] > writeDict[writer][1]:
                        delList.append(writer)
            if len(delList) > 0:
                for item in delList:
                    del writeDict[item]
                delList.clear()
            bar.show(current_size)
        tp.close()
        tp.join()
    print('Download complete.')

def writeChunk(chunk, file_name, chunk_id):
    content, path = chunk
    path = dataRootPath + path
    os.makedirs(path, exist_ok=True)
    if chunk_id == 0:
        mode = 'wb'
    else:
        mode = 'ab'
    with open(path + file_name, mode) as sf:
        sf.write(content)
    return len(content)

# def downloadFile(f):
#     # f, start, end = pf
#     with requests.get(url.format('download'), params={'file': f['file_name']}, stream=True) as response:
#         # print(response)
#         path = dataRootPath + f['path']
#         # print(response.headers)
#         # print(dataRootPath + f['path'] + f['file_name'])
#         os.makedirs(path, exist_ok=True)
#         with open(path + f['file_name'], 'wb') as sf:
#             for chunk in response.iter_content(chunk_size=1024):
#                 if chunk:
#                     sf.write(chunk)
#                     q.put(len(chunk))
#     return path + f['file_name']

def downloadChunk(chunk):
    f, start, end, chunk_id = chunk
    with requests.get(url.format('download'), params={'file': f['file_name']}, headers={'Range': 'bytes={}-{}'.format(start, end)}, stream=True) as response:
        q.put((f, chunk_id, response.content))

def loadConfig():
    with open('config.yaml') as file:
        conf = yaml.full_load(file)
        reqs = conf['requests']
        settings = conf['settings']
        defaults = settings['defaults']
    return (reqs, settings, defaults)

if __name__ == "__main__":
    (reqs, settings, defaults) = loadConfig()
    dataRootPath = settings['dataRootPath']
    url = settings['url']
    size_chunk = settings['size_chunk']
    n_concurrentConnections = settings['n_concurrentConnections']
    default_sc_id = defaults['sc_id']
    default_start_date = defaults['start_date']
    default_end_date = defaults['end_date']

    allDownloadFiles = processRequests(reqs)
    startDownload(allDownloadFiles)

    print('Quitting...')
    input('Press enter to close.')