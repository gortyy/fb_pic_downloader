import argparse
import requests
import facebook
import os
import errno
from pprint import pprint as pp

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--token", dest="token")
    parser.add_argument("--page", dest="page")
    return parser.parse_args()

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def graph_connection(token, version):
    return facebook.GraphAPI(access_token=token, version=version)

def get_page_object(graph, query):
    search_result = graph.search(type="page", q=query)
    page = search_result["data"][0]
    return page

def page_info(graph, page, depth=0):
    def crawl(data, field):
        return [obj for obj in data[field]["data"]]
    fields = "cover, photos, albums"
    informations = graph.get_object(id=page["id"], fields=fields)

    cover = informations["cover"]
    photos = crawl(informations, "photos")
    albums = crawl(informations, "albums")
    return (cover, photos, albums)

def photos_in_album(graph, album, depth=0):
    photos_data = graph.get_object(id=album["id"], fields="photos")
    pp(photos_data)
    if "photos" in photos_data:
        photos_ids = [obj["id"] for obj in photos_data["photos"]["data"]]
    else:
        return
    links = []
    for photo_id in photos_ids:
        address = graph.get_object(id=photo_id, fields="images")["images"]
        links.append(sorted(address, key=lambda x: x["height"])[-1]["source"])
    return links

def download_photos(graph, albums, page_name):
    photos_per_album = dict()
    for album in albums:
        photos = photos_in_album(graph, album)
        if photos:
            photos_per_album[album["name"]] = photos
    for key, value in photos_per_album.items():
        mkdir_p("{}/{}".format(page_name, key))
        for index, photo in enumerate(value):
            with open("{}/{}/{}.jpg".format(page_name, key, index), "wb") as pic:
                pic.write(requests.get(photo).content)

def main():
    args = parse_args()
    graph = graph_connection(args.token, "2.7")
    
    page = get_page_object(graph, args.page)

    cover, photos, albums = page_info(graph, page)

    download_photos(graph, albums, args.page)
    

if __name__ == "__main__":
    main()