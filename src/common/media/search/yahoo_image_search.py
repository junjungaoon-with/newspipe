from common.scraping.run_selenium import set_up_selenium
from common.scraping.run_selenium import search_picture_by_yahoo


def search_main_pictures(player_name: str, player_team:  str | None, settings: dict) -> list[str]:
    """
    人物名 + チーム・団体名から Yahoo 画像検索で画像URL一覧を取得する。
    """
    if player_team is None:
        query = f'{player_name} {settings["MAIN_PIC_EXTRA_WORD"]}'
    else:
        query = f"{player_name} {player_team} {settings['MAIN_PIC_EXTRA_WORD']}"

    driver = set_up_selenium()
    urls = search_picture_by_yahoo(driver, query)
    driver.quit()

    return urls