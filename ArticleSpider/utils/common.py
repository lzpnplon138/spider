import hashlib


def get_md5(url):
    if isinstance(url, str):
        url = url.encode('utf-8')
    m = hashlib.md5(url)
    m.update(url)
    return m.hexdigest()


def extract_num(value):
    if value:
        return int(value)
    else:
        value = 0
        return value


if __name__ == '__main__':
    # Unicode-objects must be encoded before hashing
    print(get_md5('http://jobbole.com'.encode('utf-8')))
