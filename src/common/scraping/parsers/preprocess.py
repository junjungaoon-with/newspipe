
def preprocess_for_5ch(raw_threads,url):
    if "livejupiter2" in url:
        # 最後の余計な要素をカット    
        return raw_threads[:-1]
    else:
        return raw_threads