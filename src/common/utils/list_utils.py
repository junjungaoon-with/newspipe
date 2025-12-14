from src.common.media.media_utils import is_long_gif




def  extract_only_long_gif_urls(media_urls: list[str])-> list[str,bool]:
    only_long_gif_urls= []
    for e,media_url in enumerate(media_urls):
        if is_long_gif(media_url):
            only_long_gif_urls.append(media_url)
    return only_long_gif_urls




def process_raw_threads_from_long_gif_info(raw_threads:list[str], only_long_gif_urls:list[str]) -> list[str]:
    #長いGIFは文章との読み上げとセットではなく単体で見せたいのでGIFの前に空の要素を入れる
    result = []

    for item in raw_threads:
        if item in only_long_gif_urls:
            result.append("")  # 長いGIFの前に空行を挿入
        result.append(item) 

    raw_threads = result
    return raw_threads
