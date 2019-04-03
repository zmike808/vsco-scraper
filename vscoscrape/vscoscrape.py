import json
import requests
import traceback

import urllib3
from tqdm import tqdm
import vscoscrape.constants as constants
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
import os
import datetime
from pathlib import Path
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import concurrent.futures
import random
import argparse
import sys
import geocoder
import gmplot
from pytz import timezone
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

htmlcode = """
<!DOCTYPE>
<html>

<head>
  <meta http-equiv="content-type" content="text/html; charset=utf-8" />
  <title>MarkerClustererPlus V3 Example</title>

  <style type="text/css">
    hbody {
      margin: 0;
      padding: 0;
      font-family: Arial;
      font-size: 14px;
      height: 100%;
    }

    # panel {
      float: left;
      width: 300px;
      height: 100%;
    }

    # map-container {
      margin-left: 300px;
    }

    # map {
      height: 100%;
    }

    # markerlist {
      margin: 10px 5px 0 10px;
      overflow: scroll;
      height: 100%;
    }

    .title {
      border-bottom: 1px solid #e0ecff;
      overflow: hidden;
      width: 256px;
      cursor: pointer;
      padding: 2px 0;
      display: block;
      color: #000;
      text-decoration: none;
    }

    .title:visited {
      color: #000;
    }

    .title:hover {
      background: #e0ecff;
    }

    # timetaken {
      color: #f00;
    }

    .info {
      width: 200px;
    }

    .info img {
      border: 0;
    }

    .info-body {
      width: 200px;
      height: 200px;
      line-height: 200px;
      margin: 2px 0;
      text-align: center;
      overflow: hidden;
    }

    .info-img {
      height: 220px;
      width: 200px;
    }
  </style>

  <script src="https://maps.googleapis.com/maps/api/js?v=3&amp;sensor=false"></script>
  <script type="text/javascript" src="/Users/mzemsky/src/markerclusterer.js"></script>

  <script type="text/javascript" src="/Users/mzemsky/speed_test.js"></script>

  <script type="text/javascript">
    google.maps.event.addDomListener(window, 'load', speedTest.init);
  </script>
</head>

<body>
  <div id="panel">
    <h3 hidden>An example of MarkerClustererPlus</h3>

    <div>
      <input type="checkbox" checked="checked" id="usegmm" />
      <span>Use MarkerClusterer</span>
    </div>

    <div>
      Markers:
      <select id="nummarkers">
        <option value="10">10</option>
        <option value="50">50</option>
        <option value="100" selected="selected">100</option>
        <option value="500">500</option>
        <option value="1000">1000</option>
      </select>

      <span hidden>Time used:
        <span id="timetaken" hidden></span> ms</span>
    </div>

    <div id="markerlist">

    </div>
  </div>
  <div id="map-container">
    <div id="map"></div>
  </div>
</body>

</html>
"""



def buildPath(x=""):
    path = "%s%s%s" % (os.getcwd(), os.sep, x)
    return path


class Scraper(object):

    def __init__(self, username, workers=5):
        self.api_data = []
        self.location_data = []
        self.username = username
        self.session = requests.Session()
        self.session.get("http://vsco.co/content/Static/userinfo?callback=jsonp_%s_0" %
                         (str(round(time.time()*1000))), headers=constants.visituserinfo)
        self.uid = self.session.cookies.get_dict()['vs']
        # "%s/%s" % (os.getcwd(), self.username)
        self.path = Path(self.username)
        self.path.mkdir(exist_ok=True, parents=True)
        # if not os.path.exists(self.path):
        #     os.makedirs(self.path)
        # os.chdir(self.path)
        self.newSiteId()
        self.buildJSON()
        self.workers = workers
        self.collectionurl = "https://vsco.co/api/2.0/collections/{}/medias".format(
            self.collectionid)
        self.mediaurl = "https://vsco.co/api/2.0/medias?site_id={}".format(
            self.siteid)
        self.journalurl = "https://vsco.co/api/2.0/articles?site_id={}".format(
            self.siteid)
        # self.mediaurl = "https://vsco.co/api/2.0/collections/5c00dd501c9c7677f258fbb9/medias"
        # self.mediaurl = "https://vsco.co/api/2.0/collections/554bf1353f088382408b459b/medias"

        self.totalj = 0

    def newSiteId(self):
        base = "http://vsco.co/"
        res = self.session.get(
            "http://vsco.co/ajxp/%s/2.0/sites?subdomain=%s" % (self.uid, self.username))
        self.siteid = res.json()["sites"][0]["id"]
        self.collectionid = res.json()["sites"][0]["site_collection_id"]
        return self.siteid

    def buildJSON(self):
        self.mediaurl = "http://vsco.co/ajxp/%s/2.0/medias?site_id=%s" % (
            self.uid, self.siteid)
        self.journalurl = "http://vsco.co/ajxp/%s/2.0/articles?site_id=%s" % (
            self.uid, self.siteid)
        return self.mediaurl

    def getJournal(self):
        self.getJournalList()
        self.pbarj = tqdm(
            total=self.totalj, desc='Downloading journal posts of %s' % self.username, unit=' posts')
        for x in self.works:
            # path = buildPath(x[0])  # "%s/%s" % (os.getcwd(), x[0])
            self.jpath = self.path.joinpath('journal',x[0])
            self.jpath.mkdir(exist_ok=True,parents=True)
                # os.makedirs(path)
            # os.chdir(path)
            x.pop(0)
            for part in x:
                self.download_img_normal(part, journal = True)
            # with ThreadPoolExecutor(max_workers=5) as executor:
            #     future_to_url = {executor.submit(
            #         self.download_img_normal, part, journal=True): part for part in x}
            #     for future in concurrent.futures.as_completed(future_to_url):
            #         part = future_to_url[future]
            #         try:
            #             data = future.result()
            #         except:
            #             traceback.print_exc()
            #             sys.exit()
            # os.chdir(os.path.normpath(os.getcwd() + os.sep + os.pardir))
        self.pbarj.close()

    def getJournalList(self):
        self.works = []
        self.jour_found = self.session.get(self.journalurl, params={
                                           "size": 10000, "page": 1}, headers=constants.media).json()["articles"]
        self.pbarjlist = tqdm(
            desc='Finding new journal posts of %s' % self.username, unit=' posts')
        for x in self.jour_found:
            self.works.append([x["permalink"]])
        # path = buildPath("journal")  # %s/journal" % (os.getcwd())
        # if not os.path.exists(path):
        #     os.makedirs(path)
        # os.chdir(path)
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_url = {executor.submit(self.makeListJournal, len(
                self.jour_found), val): val for val in range(len(self.jour_found))}
            for future in concurrent.futures.as_completed(future_to_url):
                val = future_to_url[future]
                try:
                    data = future.result()
                except:
                    traceback.print_exc()
                    sys.exit()
        self.pbarjlist.close()

    def makeListJournal(self, num, loc):
        for item in self.jour_found[loc]["body"]:
            try:
                if os.path.exists(buildPath(self.jour_found[loc]["permalink"])):
                    # import pprint
                    # pprint.pprint(item)
                    if item['type'] is not "image" or item['type'] is not "video":
                        continue
                    if '%s.jpg' % str(item["content"][0]["id"]) in os.listdir(buildPath(self.jour_found[loc]["permalink"])) or '%s.mp4' % str(item["content"][0]["id"]) in os.listdir(buildPath(self.jour_found[loc]["permalink"])):
                        continue
                if item['type'] == "image":
                    self.works[loc].append(
                        ["http://%s" % item["content"][0]["responsive_url"], item["content"][0]["id"], False, item])
                elif item['type'] == "video":
                    # print(item)
                    self.works[loc].append(
                        ["http://%s" % item["content"][0]["video_url"], item["content"][0]["id"], True, item])
                self.totalj += 1
                self.pbarjlist.update()
            except:
                traceback.print_exc()
                sys.exit()
        return "done"

    def download_img_journal(self, lists):
        listdict = lists[-1]

        if isinstance(listdict, dict):
            width = listdict.get('width', 0)
            height = listdict.get('height', 0)
        else:
            width, height = (0, 0)
        dimsum = width + height
        dimsum = str(dimsum)
        width = str(width)
        height = str(height)
        fname = '%sx%s-%s' % (width, height, str(lists[1]))
        if lists[2] is False:
            if '%s.jpg' % fname in os.listdir():
                return "done"
            with open('%sx.jpg' % (fname), 'wb') as f:
                f.write(requests.get(lists[0], stream=True).content)

        else:
            if '%s.mp4' % fname in os.listdir():
                return "done"
            with open('%sx%s-%s.mp4' % (width, height, str(lists[1])), 'wb') as f:
                for chunk in requests.get(lists[0], stream=True).iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
        self.pbarj.update()
        return "done"

    def getImages(self, targeturl, key, write_json=True):
        self.imagelist = []
        self.api_data = []
        self.getImageList(targeturl, key)
        self.pbarj = tqdm(total = len(self.imagelist), desc = 'Downloading posts of %s' % self.username, unit = ' posts')
        for lists in self.imagelist:
            self.download_img_normal(lists)
        # with ThreadPoolExecutor(max_workers=self.workers) as executor:
        #     future_to_url = {executor.submit(
        #         self.download_img_normal, lists): lists for lists in self.imagelist}
        #     for future in concurrent.futures.as_completed(future_to_url):
        #         liste = future_to_url[future]
        #         try:
        #             data = future.result()
        #         except:
        #             traceback.print_exc()
        #             sys.exit()
        if write_json:
            with open(self.path.joinpath('api_data.json'), 'w') as f:
                json.dump(self.api_data, f, sort_keys=False, indent=2)
            self.plotter()

    def getImageList(self, targeturl, key):
        self.pbar = tqdm(desc='Finding new posts of %s' %
                         self.username, unit=' posts')
        self.makeImageList(0, targeturl, key)
        # with ThreadPoolExecutor(max_workers=1) as executor:
        #     future_to_url = {executor.submit(
        #         self.makeImageList, num, targeturl, key): num for num in range(1)}
        #     for future in tqdm(concurrent.futures.as_completed(future_to_url)):
        #         num = future_to_url[future]
        #         try:
        #             data = future.result()
        #         except:
        #             traceback.print_exc()
        #             sys.exit()
        self.pbar.close()

    def makeImageList(self, num, targeturl, key):
        num += 1
        # if 'collection' in targeturl:
        #     import pprint
        #     print(targeturl, key)
        #     pprint.pprint(self.session.get(targeturl, params={
        #         "size": 60, "page": num}, headers=constants.media).json()[key])
        #     exit()
        z = self.session.get(targeturl, params={"size": 10000,"page": num}, headers=constants.media, timeout=(120, 120), verify=False).json()[key]
        count = len(z)
        self.api_data.extend(z)
        while count > 0:
            for url in z:
                if url['has_location']:
                    self.location_data.append(url)

                # if '%s.jpg' % str(url["upload_date"]) in os.listdir() or '%s.mp4' % str(url["upload_date"]) in os.listdir():
                    # continue
                if url['is_video'] is True:
                    self.imagelist.append(
                        ["http://%s" % url["video_url"], str(url["upload_date"]), True, url])
                    self.pbar.update()
                else:
                    self.imagelist.append(
                        ["http://%s" % url["responsive_url"], str(url["upload_date"]), False, url])
                    self.pbar.update()
            num += 1
            # try:
            z = self.session.get(targeturl, params={"size": 10000, "page": num}, headers=constants.media, timeout=(999, 999),verify=False).json()[key]
            # except:
            # print("count=", count, "pagenum=", num)

            count = len(z)
        return "done"

    def download_img_normal(self, lists, journal=False):
        listdict = lists[-1]

        if isinstance(listdict, dict):
            width = listdict.get('width', 0)
            height = listdict.get('height', 0)
            subname = listdict.get('perma_subdomain', self.username)
        else:
            width, height = (0, 0)
            subname = self.username
        dimsum = width + height
        dimsum = str(dimsum)
        width = str(width)
        height = str(height)
        try:
            upload_date = datetime.datetime.fromtimestamp(
                int(lists[1])/1000).isoformat(' ')  # strftime('%Y-%m-%d %I:%M:%S %p')  # %A, %d. %B %Y %I:%M%p
        except:
            upload_date = datetime.datetime.now().isoformat(' ')
        def getExt():
            if lists[2]:
                return 'mp4'
            else:
                return 'jpg'
        fname = '{} - {}x{} - {}.{}'.format(
            subname, width, height, upload_date, getExt())
        if journal:
            fpath = self.jpath.joinpath(fname)
        else:
            # if 'collected_date' in listdict:
            #     fpath = self.path.joinpath('collection', fname)
            # else:
            fpath = self.path.joinpath(fname)
        if fpath.exists():
            return
        setctime = ["touch", "-c","--date={}".format(
            upload_date), fpath]
        # print(fpath)
        # print(setctime)
        # print(setctime)
        try:
            with requests.get(lists[0], stream=True, timeout=(60, 60), verify=False) as r:
                r.raise_for_status()
                with open(fpath, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
        except:
            traceback.print_exc()
            try:
                with requests.get(lists[0], stream=True, timeout=(60, 60), verify=False) as r:
                    with open(fpath, 'wb') as f:
                        f.write(r.content)
            except:
                traceback.print_exc()
                return
                        #requests.get(lists[0], stream=True, timeout=(999, 999)).content())
                # f.write(r.content)
                # r.
                # for chunk in r.iter_content(chunk_size=5*1024*1024*1024):
                #     if chunk:
                #         f.write(chunk)
            # f.write(.)
        subprocess.run(setctime)
        if 'collected_date' in listdict:
            # subpath = buildPath(subname)
            # if not os.path.exists(subpath):
            #     os.makedirs(subpath)
            destpath = self.path.joinpath(subname)
            if not destpath.exists():
                destpath.mkdir(parents=True, exist_ok=True)
            destpath = destpath.joinpath(fname)
            # print(destpath)
            if not destpath.exists():
                shutil.copy2(fpath,destpath)
                setctime = ["touch","-c", "--date={}".format(
                    upload_date), destpath]
                # print(setctime)
                subprocess.run(setctime)

        self.pbarj.update()

            # if '%s.mp4' % fname in os.listdir():
            #     return "done"
        # with requests.get(lists[0], stream=True) as r:
        #     with open(fname, 'wb') as f:
        #         for chunk in r.iter_content(chunk_size=5*1024*1024*1024):
        #             if chunk:
        #                 f.write(chunk)
        return

    def getCollection(self):
        # %s/journal" % (os.getcwd())
        # os.chdir(self.path)
        collectionpath = self.path.joinpath("collection")
        collectionpath.mkdir(parents=True, exist_ok=True)
        self.path = collectionpath
        # if not os.path.exists(self.path):
            # os.makedirs(self.path)
        # os.chdir(self.path)
        self.getImages(self.collectionurl, 'medias')

    def doit(self):
        self.getImages(self.mediaurl, 'media')
        self.getJournal()
        self.getCollection()
        return "username: {} finished!".format(self.username)
        # self.plotter()
        # with open('api_data.json', 'w') as f:
        #     json.dump(self.api_data, f, sort_keys=True, indent=2)

    # def plotter2(self):
    #     page=1
    #     r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page})
    #     count = len(r.json()["media"])
    #     coords = []
    #     index = 0
    #     indexs = []
    #     while count > 0:
    #         for loc in r.json()["media"]:
    #             if isinstance(loc, dict):
    #                 width = loc.get('width', 0)
    #                 height = loc.get('height', 0)
    #             else:
    #                 width, height = (0, 0)
    #             width = str(width)
    #             height = str(height)
    #             name = '%sx%s-%s' % (width, height, str(loc['upload_date']))
    #             # if not loc["location_coords"]:
    #             #     print(loc)
    #             #     continue
    #             # photo_file_url = "{0}/{1}x{2}-{3}.mp4".format(
    #             #     os.getcwd(), width, height, str(loc["upload_date"]))
    #             if loc["has_location"]:
    #                 coords.append([loc["location_coords"][1],loc["location_coords"][0],name])
    #                 index +=1
    #                 indexs.append(index)
    #             else:
    #                 index+=1
    #                 continue
    #         page+=1
    #         r = self.session.get(self.mediaurl,headers=constants.media,params = {"page":"%s"%page})
    #         count = len(r.json()["media"])
    #     gmap = gmplot.GoogleMapPlotter(39.106506,-77.555574,13)
    #     gmap.coloricon = 'file:///' + os.path.dirname(gmplot.__file__) + '/markers/%s.png'
    #     index = 0
    #     for coord in tqdm(coords,total=len(coords)):
    #         index +=1
    #         g = geocoder.google([coord[0],coord[1]],method='reverse').address
    #         crindex = 0
    #         while g is None:
    #             g = geocoder.google([coord[0],coord[1]],method='reverse').address
    #             crindex +=1
    #             if crindex == 10:
    #                 break
    #             else:
    #                 time.sleep(.3)
    #         gmap.marker(coord[0],coord[1], '#3B0B39','#E0FFFF', title="%s at %s" %(g,coord[2]))
    #         time.sleep(.15)
    #     gmap.draw("markers2.html")
    #     return gmap
    def plotter(self,):
        # print("cwd:", os.getcwd())
        # os.chdir(self.path)
        # print("cwd:", os.getcwd())
        loc_json = dict(photos=[])
        for loc in self.location_data:
            if isinstance(loc, dict):
                width = loc.get('width', 0)
                height = loc.get('height', 0)
            else:
                width, height = (0, 0)
            width = str(width)
            height = str(height)
            upload_date = datetime.datetime.fromtimestamp(
                int(loc["upload_date"]) / 1000).strftime('%Y-%m-%d %I:%M:%S %p')
            if not loc["location_coords"]:
                print(loc)
                continue
            lat = loc["location_coords"][1]
            if loc["is_video"]:
                photo_file_url = "{0}/{1}x{2}-{3}.mp4".format(
                    os.getcwd(), width, height, str(loc["upload_date"]))
                # photo_file_url = "http://" + loc["video_url"]
            else:
                photo_file_url = "{0}/{1}x{2}-{3}.jpg".format(
                    os.getcwd(), width, height, str(loc["upload_date"]))
            #     photo_file_url = "http://" + loc["responsive_url"]
            lon = loc["location_coords"][0]
            # if ".jpg" in loc["responsive_url"]:
            #     # buildPath(#"{}.jpg".format(str(loc["upload_date"])))
            #     photo_file_url = loc["responsive_url"]
            # else:
            #     photo_file_url = ""
            # photo_file_url = buildPath(
            #     "file://{}.jpg".format(str(loc["upload_date"])))
            # g = geocoder.google([coord[0], coord[1]], method='reverse').address
            # crindex = 0
            # while g is None:
            #     g = geocoder.google([coord[0], coord[1]],
            #                         method='reverse').address
            #     crindex += 1
            #     if crindex == 10:
            #         break
            #     else:
            #         time.sleep(.3)

            locdict = dict(photo_title=str(upload_date), longitude=lon,
                           latitude=lat, photo_file_url=photo_file_url)
            loc_json['photos'].append(locdict)
        with open(self.path.joinpath("markers.html"), 'w') as f:
            print("<script type=\"text/javascript\">\nvar data = {};\n</script>".format(
                json.dumps(loc_json)), file=f)
            print(htmlcode, file=f)
        with open(self.path.joinpath('loc_data.json'), 'w') as f:
            json.dump(loc_json, f, sort_keys=True, indent=2)
        self.location_data = []


def worker_function(scraper):
    scraper.getImages(scraper.mediaurl, 'media')
    scraper.getJournal()
    scraper.getCollection()
    return "username: {} finished!".format(scraper.username)

def main():
    parser = argparse.ArgumentParser(
        description="Scrapes a specified users VSCO, currently only supports one user at a time")
    parser.add_argument('username', help='VSCO user to scrape')
    parser.add_argument('-m', '--multiple',
                        action="store_true", help='Scrape multiple users')
    parser.add_argument('-s', '--siteId', action="store_true",
                        help='Grabs VSCO siteID for user')
    parser.add_argument('-i', '--getImages', action="store_true",
                        help='Get the pictures of the user')
    parser.add_argument('-j', '--getJournal', action="store_true",
                        help='Get the journal images of the user')
    parser.add_argument('-mj', '--multipleJournal',
                        action="store_true", help='Scrape multiple users journal')
    parser.add_argument('-a', '--all', action="store_true",
                        help='Scrape multiple users journals and images')
    parser.add_argument('-p', '--plot', action="store_true",
                        help='Plots locations of pictures on the VSCO')
    parser.add_argument('-w','--workers', type=int, default=5)
    args = parser.parse_args()

    if args.siteId:
        scraper = Scraper(args.username)
        print(scraper.newSiteId())

    if args.plot:
        scraper.plotter()

    if args.getImages:
        scraper = Scraper(args.username)
        scraper.getImages()

    if args.getJournal:
        scraper = Scraper(args.username)
        scraper.getJournal()

    if args.multiple:
        y = []
        vsco = os.getcwd()
        with open(args.username, 'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        y = list(set(y))
        y.sort()
        print(y, "set len=",len(y))
        aws = []
        # executor = ProcessPoolExecutor(max_workers=args.workers)
        for z in y:
            try:
                scraper = Scraper(z, args.workers)
                # os.chdir(vsco)
                # try:
                # executor.submit(Scraper(z, args.workers).doit)
                # aws.append(asyncio.create_task(Scraper(z, args.workers).doit()))
                print('Queued {}!'.format(z))
                # except:
                #     traceback.print_exc()
                #     continue
            except:
                traceback.print_exc()
                # sys.exit()
                continue
        # print(await asyncio.gather(aws))
        # for x in asyncio.as_completed(aws):
        #     earliest = await x
        #     print(earliest)
    else:
        scraper = Scraper(args.username, args.workers)
        # task = asyncio.create_task(scraper.doit())
        # await task
        scraper.doit()
        # print(await asyncio.create_task(scraper.doit()))
        print()

    if args.multipleJournal:
        y = []
        vsco = os.getcwd()
        with open(args.username, 'r') as f:
            for x in f:
                y.append(x.replace("\n", ""))
        for z in y:
            try:
                # os.chdir(vsco)
                Scraper(z).getJournal()
                print()
            except:
                traceback.print_exc()
                sys.exit()


if __name__ == '__main__':
    main()
# asyncio.run(main())
    # asyncio.get_event_loop().run_forever()
