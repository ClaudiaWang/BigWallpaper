from gi.repository import GObject
from urllib2 import urlopen, HTTPError, URLError
from httplib import HTTPException
from lxml.html import parse
from models import *
from storm.expr import *
from datetime import datetime

import threading
import os
import socket
from wallpaper_log import WallPaperLog


class DownloadThread(threading.Thread):

    """
    Thread for fetch homepage and image from Boston Big Picture.
    """

    def __init__(self, manager, ui_controller, config):
        """
        Constructor of DownloadThread.
        """
        super(DownloadThread, self).__init__()
        self.manager = manager
        self.ui_controller = ui_controller
        self.config = config

    def fetch_links(self):
        """
        Fetch links defined in source_site.
        """

        new_link = False

        for site in list(SourceSite.select().where(SourceSite.active == True)):
            WallPaperLog.getInstance(WallPaperLog).info("Fetching %s" % site.name )

            try:
                page = urlopen(
                    site.url, timeout=self.config.get_options().timeout)
            except (HTTPError, URLError, TypeError):
                WallPaperLog.getInstance(WallPaperLog).info("Failed to fetch %s" % site.url )
                continue

            try:
                p = parse(page)
                link = p.xpath(site.image_xpath)[0]
            except (HTTPException, IndexError, socket.error):
                WallPaperLog.getInstance(WallPaperLog).info("Failed to parse image path." )
                continue

            site.last_update = datetime.now()

            site.save()

            WallPaperLog.getInstance(WallPaperLog).info("Got a new image link: %s" % link )
            if Image.select().where(Image.source_image_url == unicode(link)).count() > 0:
                WallPaperLog.getInstance(WallPaperLog).info("Dulplicated image link: %s" % link)
                continue

            image = Image()
            image.source_site = site
            image.source_image_url = unicode(link)
            image.state = Image.STATE_PENDING
            image.active_wallpaper = False

            try:
                image.source_link = unicode(p.xpath(site.link_xpath)[0])
            except (IndexError, TypeError):
                WallPaperLog.getInstance(WallPaperLog).info("Failed to parse link.")
                image.source_link = None
                continue

            try:
                image.source_title = unicode(p.xpath(site.title_xpath)[0])
            except (IndexError, TypeError):
                WallPaperLog.getInstance(WallPaperLog).info("Failed to parse title.")
                image.source_title = None
                continue

            try:
                image.source_description = unicode(
                    p.xpath(site.description_xpath)[0])
            except (IndexError, TypeError):
                WallPaperLog.getInstance(WallPaperLog).info("Failed to parse decription.")
                image.source_description = None
                continue

            WallPaperLog.getInstance(WallPaperLog).info("Created a new image object: %s" % image.source_image_url)

            image.save()

            new_link = True

        return new_link

    def fetch_images(self):
        """
        Fetch latest pending images.
        """

        image_downloaded = False

        for image in list(Image.select().where(Image.state == Image.STATE_PENDING).order_by(Image.id.desc())):
            temp_file = self.manager.generate_img_file(".jpg")

            if self.download_img_file(temp_file[0], image.source_image_url):
                # os.close(temp_file[0])
                
                WallPaperLog.getInstance(WallPaperLog).info("Downloaded %s: %s" % (image.source_image_url, temp_file[1]))

                image.image_path = unicode(temp_file[1])
                image.download_time = datetime.now()
                image.state = Image.STATE_DOWNLOADED

                image_downloaded = True
            else:
                os.unlink(temp_file[1])
                WallPaperLog.getInstance(WallPaperLog).info("Failed to download %s" % image.source_image_url)

                image.state = Image.STATE_FAILED

            image.save()

        return image_downloaded

    def run(self):
        """
        Thread run callback.
        """

        if self.manager.update_lock is None:
            self.manager.update_lock = threading.Lock()

        if not self.manager.update_lock.acquire(False):
            # is updaing now, just return
            return

        GObject.idle_add(self.ui_controller.start_updating)

        try:
            WallPaperLog.getInstance(WallPaperLog).info("Get URL...")
            WallPaperLog.getInstance(WallPaperLog).info("Reconnected.")

            self.fetch_links()
            self.fetch_images()

            self.manager.update_wallpaper()
        finally:
            GObject.idle_add(self.ui_controller.finish_updating)
            self.manager.update_lock.release()

    def download_img_file(self, fd, url):
        """
        Download the image of url.
        """

        try:
            img = urlopen(url, timeout=self.config.get_options().timeout)
        except (HTTPError, URLError, IOError, TypeError):
            return False

        try:
            f = os.fdopen(fd, 'w')
            f.write(img.read())
            f.close()
        except (HTTPException, IndexError, socket.error):
            WallPaperLog.getInstance(WallPaperLog).info("Failed to download image: %s" % url)
            return False

        return True
