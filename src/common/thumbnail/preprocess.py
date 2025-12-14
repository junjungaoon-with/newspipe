def normalize_players(players:list[dict]) -> list[dict]:
    if players == 'None':
        return None
    return players

def split_players(players: list[dict]) -> tuple[dict, dict]:
    """
    プレイヤー一覧から 1人目・2人目の情報を取り出し、
    name / team を含む辞書として返す。

    players[0], players[1] を前提としており、
    該当情報が無い場合は None が設定される。
    """
    first_player = {"name": None, "team": None}
    second_player = {"name": None, "team": None}
    
    first_player["name"] = players[0]["name"]
    first_player["team"] = players[0]["team"]
    second_player["name"] = players[1]["name"]
    second_player["team"] = players[1]["team"]
    return first_player ,second_player