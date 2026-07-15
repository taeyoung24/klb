# uv run -m scripts.generate_schedule_preview
import sys
import random
from sqlmodel import Session, SQLModel, create_engine, select
import yaml

from settings import DATABASE_URL
from src.models import League, Club, Match
from src.enums import MatchStatus
from src.services.schedule_utils import generate_regular_schedule

# 윈도우 콘솔 한글 깨짐 방지 설정
try:
    reconfig = getattr(sys.stdout, 'reconfigure', None)
    if reconfig is not None:
        reconfig(encoding='utf-8')
except Exception:
    pass

engine = create_engine(DATABASE_URL)

def seed_initial_data(session: Session):
    with open("./data/initial_leagues.yml", "r", encoding="utf-8") as f:
        initial_leagues_rawdata = yaml.safe_load(f)

    for league_rawdata in initial_leagues_rawdata:
        league = League(
            name=league_rawdata["name"],
            name_ko=league_rawdata["name_ko"],
            mascot_ko=league_rawdata["mascot_ko"],
            league_code=league_rawdata["league_code"],
            lore=league_rawdata["lore"]
        )
        session.add(league)
        session.commit()
        session.refresh(league)

        for club_rawdata in league_rawdata["clubs"]:
            club = Club(
                name=club_rawdata["name"], 
                name_ko=club_rawdata["name_ko"],
                hometown=club_rawdata["hometown"],
                hometown_ko=club_rawdata["hometown_ko"],
                team_code=club_rawdata["team_code"],
                abbr_name=club_rawdata["abbr_name"],
                stadium_name=club_rawdata["stadium_name"],
                stadium_name_ko=club_rawdata["stadium_name_ko"],
                league_id=league.id
            )
            session.add(club)
        session.commit()

def pad_korean(text: str, width: int, align: str = "<") -> str:
    """
    한글 전각 문자(2칸)와 영문/숫자 반각 문자(1칸)의 터미널 렌더링 너비를 계산하여
    f-string 패딩이 칼같이 정렬되도록 공백을 채워주는 헬퍼 함수.
    """
    actual_len = sum(2 if ord(char) > 127 else 1 for char in text)
    padding = max(0, width - actual_len)
    if align == "<":
        return text + " " * padding
    elif align == ">":
        return " " * padding + text
    else:
        left = padding // 2
        right = padding - left
        return " " * left + text + " " * right

def main():
    # 1. DB 클린 리셋 및 초기 스키마 생성
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # 2. 초기 구단 데이터 시딩
        seed_initial_data(session)

        # 3. 10개 구단 조회
        clubs = list(session.exec(select(Club)).all()[:10])
        clubs_dict = {club.id: club for club in clubs}
        
        # [핵심] 매번 실행 시 다른 대진표가 구성되도록 구단 순서를 셔플(Shuffle)합니다.
        # 시드 배정 순서만 달라지고, 3연전 및 홈/원정 72경기 규칙(알고리즘)은 엄격하게 유지됩니다.
        random.shuffle(clubs)
        
        matches = generate_regular_schedule(clubs)
        for match in matches:
            session.add(match)
        session.commit()

        # 4. 콘솔에 f-string 패딩을 활용해 예쁜 표 형식으로 정규시즌 일정 출력
        print("\n" + "=" * 105)
        print(f"{'KROWN LEAGUE BASEBALL 정규 시즌 일정표 (3연전 & 월요일 휴식)':^92}")
        print("=" * 105)

        db_matches = session.exec(select(Match).order_by("sim_day")).all()
        matches_by_day = {}
        for m in db_matches:
            matches_by_day.setdefault(m.sim_day, []).append(m)

        day_names = ["월", "화", "수", "목", "금", "토", "일"]

        # 총 24주차(168일) 출력
        for week in range(24):
            print(f"\n[ WEEK {week+1:02d} ]" + "-" * 93)
            
            for day_in_week in range(1, 8):
                sim_day = week * 7 + day_in_week
                day_name = day_names[sim_day % 7]
                
                # 월요일 (7의 배수일) 휴식
                if sim_day % 7 == 0:
                    rest_str = "◆ MONDAY OFF - 월요일 공식 휴식일 ◆"
                    padded_rest = pad_korean(rest_str, 86, "^")
                    print(f" Day {sim_day:03d} ({day_name}) | {padded_rest}")
                    continue
                
                day_matches = matches_by_day.get(sim_day, [])
                match_strings = []
                for m in day_matches:
                    home_club = clubs_dict[m.home_club_id]
                    away_club = clubs_dict[m.away_club_id]
                    
                    # 어웨이팀명(6칸 우정렬) @ 홈팀명(6칸 좌정렬)로 전각 문자폭 패딩
                    away_name_padded = pad_korean(away_club.name_ko, 6, ">")
                    home_name_padded = pad_korean(home_club.name_ko, 6, "<")
                    match_strings.append(f"{away_name_padded} @ {home_name_padded}")
                
                matches_str = "  |  ".join(match_strings)
                print(f" Day {sim_day:03d} ({day_name}) | {matches_str}")
            
        print("\n" + "=" * 105)

if __name__ == "__main__":
    main()
