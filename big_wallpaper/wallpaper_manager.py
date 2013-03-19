from download_thread import DownloadThread
from gi.repository import Gio

import os
import tempfile

from big_wallpaper.download_thread import DownloadThread

class WallPaperManager:
    """
    Manager of dowloading thread, content and settings.

    Manager must created before Controller
    """

    SCHEMA = 'org.gnome.desktop.background'
    KEY = 'picture-uri'
    IMG_FILE = "big_wallpaper.jpg"
    URL_FILE = "big_wallpaper.url"
    DESKTOP_FILE = "big_wallpaper.desktop"
    AUTOSTART_DIR = os.path.expanduser("~/.config/autostart")

    def __init__(self, prefix_dir="share", img_dir='share/pixmaps'):
        """
        Constructor of WallPaperManager.

        prefix_dir: the installation folder of big_wallpaper
        img_dir: path to save downloaded images
        """
        self.update_lock = None
        self.prefix_dir = prefix_dir
        self.img_dir = img_dir

        self.img_file = "%s/%s" % (self.img_dir, self.IMG_FILE)
        self.url_file = "%s/%s" % (self.img_dir, self.URL_FILE)
        self.desktop_source_file = \
            "%s/%s" % (self.prefix_dir, self.DESKTOP_FILE)
        self.autostart_desktop_file = \
            "%s/%s" % (self.AUTOSTART_DIR, self.DESKTOP_FILE)
        self.real_img_file = None
        self.wp_url = None
        self.saved_url = None
        self.ui_controller = None

    def set_controller(self, ui_controller):
        self.ui_controller = ui_controller

    def get_autostart(self):
        return os.access(self.autostart_desktop_file, os.F_OK)
                       
    def update_autostart(self, autostart):
        try:
            os.unlink(self.autostart_desktop_file)
        except OSError:
            pass

        if autostart:
            f_source = open(self.desktop_source_file, "r")
            f_dest = open(self.autostart_desktop_file, "w")
            try:
                f_dest.write(f_source.read())
            finally:
                f_source.close()
                f_dest.close()

    def on_image_downloaded(self, image_file = None, url = None):
        self.update_gsettings(image_file = image_file, url = url)

    def update_gsettings(self, image_file = None, url = None):
        print "image_file = %s, url = %s" % (image_file, url)
        print "Current real_img_file = %s, saved_url = %s" % \
            (self.real_img_file, self.saved_url)
        if image_file is not None and image_file != self.real_img_file:
            # delete old image file, and update symbol link
            try:
                print "Delete old files..."
                if self.real_img_file is not None:
                    os.unlink(self.real_img_file) 
                os.unlink(self.img_file)
            except (IOError, OSError):
                pass

            print "Make new link: %s %s" % (image_file, self.img_file)
            os.symlink(image_file, self.img_file)
            self.real_img_file = image_file

        if url is not None:
            print "Saving URL %s to %s" % (url, self.url_file)
            self.saved_url = url

            f = open(self.url_file, "w")
            f.write(url)
            f.close()

        if self.real_img_file is not None and \
                self.wp_url != "file://" + self.real_img_file:
            gsettings = Gio.Settings.new(self.SCHEMA)
            gsettings.set_string(self.KEY, "file://" + self.real_img_file)
            GObject.idle_add(self.ui_controller.notify_wallpaper_update)

    def update_saved_content(self, image_file = None):
        # get saved URL
        try:
            f = open(self.url_file, "r")
            self.saved_url = f.readline()
            f.close()
        except IOError:
            pass

        # get saved image file name
        try:
            self.real_img_file = os.readlink(self.img_file)
        except OSError:
            pass
            
        # gsettings get org.gnome.desktop.background picture-uri
        gsettings = Gio.Settings.new(self.SCHEMA)
        self.wp_url = gsettings.get_string(self.KEY)

    def correct_link(self):
        try:
            os.mkdir(self.img_dir)
        except OSError:
            pass
        self.update_saved_content()
        self.update_gsettings()

    def update(self):
        print "Updating..."
        download_thread = DownloadThread(self, self.ui_controller)
        download_thread.start()

    def generate_img_file(self, suffix):
        return tempfile.mkstemp(suffix=suffix, dir=self.img_dir)
