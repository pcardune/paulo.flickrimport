import os
import urllib2
from anyjson import serialize, deserialize
from flickrapi import FlickrAPI

from paulo.flickrimport.client import DivvyshotClient

FLICKR_KEY = '492b04c740650375b72a075723eaf28a'
FLICKR_SECRET = '162c4a5d283b470b'


class Importer(object):

    def __init__(self):
        self.flickr = FlickrAPI(FLICKR_KEY)

    def get_photosets(self, username, filename=None):
        filename = filename or username+'.json'
        if os.path.exists(filename):
            print "Looks like we already have information about your photos."
            if raw_input("Refresh? (y/n): ").lower().startswith('n'):
                return deserialize(open(filename).read())

        print "Downloading information about your photos."
        if '@' in username:
            response = self.flickr.people_findByEmail(find_email=username)
        else:
            response = self.flickr.people_findByUsername(username=username)
        nsid = response[0].get('nsid')

        response = self.flickr.photosets_getList(user_id=nsid)
        photosets = []
        photo_ids = []
        for ps in response[0]:
            photoset = {'id': ps.get('id'),
                        'title': ps[0].text,
                        'description': ps[1].text,
                        'photos':[]}
            photos_response = self.flickr.photosets_getPhotos(photoset_id=photoset['id'],
                                                              extras='url_o')
            for pxml in photos_response[0]:
                photo = {'id':pxml.get('id'),
                         'title':pxml.get('title')}
                photoset['photos'].append(photo)
                photo_ids.append(photo['id'])
            print photoset['title'],'-',len(photoset['photos']),'photos'
            photosets.append(photoset)

        # get photos not in photosets
        photos_response = self.flickr.photos_search(user_id=nsid, per_page=500)
        photoset = {'id':'stream',
                    'title':'Flickr Stream',
                    'description':'Photos from my flickr stream',
                    'photos':[]}
        for pxml in response[0]:
            photo = {'id':pxml.get('id'),
                     'title':pxml.get('title')}
            if photo['id'] not in photo_ids:
                photoset['photos'].append(photo)
                photo_ids.append(photo['id'])
        if photoset['photos']:
            print photoset['title'],'-',len(photoset['photos']),'photos'
            photosets.append(photoset)

        f = open(filename, "w")
        f.write(serialize(photosets))
        f.close()
        return photosets

    def download_images(self, photosets, directory):
        print "Downloading your photos"
        if not os.path.exists(directory):
            os.mkdir(directory)
        default = None
        for photoset in photosets:
            dirpath = os.path.join(directory, photoset['id']+' - '+photoset['title'])
            if not os.path.exists(dirpath):
                os.mkdir(dirpath)
            for photo in photoset['photos']:
                filename = os.path.join(dirpath, photo['id']+'.jpg')
                if os.path.exists(filename):
                    if default is None:
                        print "Photo", photo['id'], "has already been downloaded."
                        default = raw_input("Download again? (y/n/Y/N) (capital to not ask again): ")
                    if default == 'n':
                        default = None
                        continue
                    elif default == 'N':
                        continue
                    elif default == 'y':
                        default = None

                f = open(filename, 'w')
                if not photo.get('url'):
                    try:
                        sizes_response = self.flickr.photos_getSizes(photo_id=photo['id'])
                    except:
                        print "Failed to download photo:", photo['id'], '... sorry!'
                    else:
                        photo['url'] = sizes_response[0][-1].get('source')
                if photo.get('url'):
                    print "Downloading", photo['title'], 'from', photo['url']
                    remote = urllib2.urlopen(photo['url'])
                    f.write(remote.read())
                    f.close()
                    remote.close()

    def upload_images(self, photosets, directory):
        client = DivvyshotClient()
        for photoset in photosets:
            event_data = client.create_event(name=photoset['title'],
                                           description=photoset['description'])
            event_path = '/api/v2/json/event/%s/photo/' % event_data['url_slug']
            for photo in photoset['photos']:
                print "Uploading", photo['title']
                filename = os.path.join(directory, photoset['id']+' - '+photoset['title'], photo['id']+'.jpg')
                if not os.path.exists(filename):
                    print "Looks like photo",photo['id'],'did not get downloaded.'
                    continue
                photo_data = client.create_photo(event_data['url_slug'], filename)
                photo_data = client.update_photo(photo_data['url_slug'], name=photo['title'])
                print "Finished uploading", photo_data['name']
                os.remove(filename)

    def do_import(self):
        username = raw_input("Your flickr username/email: ")
        # Step 1: grab the list of photos from flickr
        photosets = self.get_photosets(username)
        # Step 2: download the images from flickr
        self.download_images(photosets, username)
        self.upload_images(photosets, username)


def main():
    Importer().do_import()
