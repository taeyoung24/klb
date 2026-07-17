import unittest
from sqlmodel import SQLModel, create_engine, Session, select
from src.models import Club, Match, MatchPlaceholder, League
from src.enums import MatchStatus
from src.services.schedule_utils import (
    generate_regular_schedule,
    generate_krown_elite_schedule,
    generate_knockout_schedule,
    save_knockout_placeholders
)

class TestScheduleUtils(unittest.TestCase):
    def setUp(self):
        # 인메모리 SQLite DB 초기화
        self.engine = create_engine("sqlite:///:memory:")
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        
        # 테스트용 리그 생성
        self.league = League(name="Test League", name_ko="테스트 리그", mascot_ko="마스코트", league_code="TL", lore="lore")
        self.session.add(self.league)
        self.session.commit()
        
        # 테스트용 16개 구단 생성
        self.clubs = []
        for i in range(16):
            club = Club(
                name=f"Club {i}",
                name_ko=f"구단 {i}",
                hometown="Seoul",
                hometown_ko="서울",
                team_code=f"C{i:02d}",
                abbr_name=f"C{i}",
                stadium_name="Stadium",
                stadium_name_ko="경기장",
                league_id=self.league.id
            )
            self.session.add(club)
            self.clubs.append(club)
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_generate_regular_schedule(self):
        # 10개 구단을 추려내기
        clubs_10 = self.clubs[:10]
        
        # 시나리오 A: 2024년(윤년), base_sim_day = 1
        # 2024년 1월 1일(월) 대비 3월 첫 화요일은 3월 5일(+64일) -> 글로벌 sim_day = 65
        matches = generate_regular_schedule(clubs_10, 2024, 1)
        
        # 전체 경기 수 = 10 * 144 / 2 = 720 경기여야 함.
        self.assertEqual(len(matches), 720)
        
        # sim_day 목록 추출 및 검증
        sim_days = {m.sim_day for m in matches}
        start_sim_day = 64
        self.assertEqual(min(sim_days), start_sim_day)
        # 24주차 스케줄의 마지막 경기는 230일차(일요일)여야 함 (231일은 월요일 휴식)
        self.assertEqual(max(sim_days), start_sim_day + 166)
        
        # 월요일 경기가 없어야 함 (시작일 64 = 화요일이므로, (day - 64) % 7 == 6 인 날이 월요일)
        for day in sim_days:
            self.assertNotEqual((day - start_sim_day) % 7, 6, f"Monday (sim_day {day}) should not have matches.")
            
        # 3연전 연속성 검증
        # 경기들을 날짜와 홈팀별로 정렬/그루핑하여 3일 연속 동일 대진인지 확인
        matches_by_day_and_home = {}
        for m in matches:
            matches_by_day_and_home[(m.sim_day, m.home_club_id)] = m.away_club_id
            
        # 모든 주차(0~23)의 주중(화수목), 주말(금토일)에 대해 대진 고정 여부 확인
        for week in range(24):
            # 주중 3연전 검증 (화요일 시작)
            midweek_start = start_sim_day + week * 7
            # 주말 3연전 검증 (금요일 시작)
            weekend_start = start_sim_day + week * 7 + 3
            
            for start_day in (midweek_start, weekend_start):
                # 첫날 대진 추출
                first_day_matchings = {
                    home_id: away_id 
                    for (day, home_id), away_id in matches_by_day_and_home.items()
                    if day == start_day
                }
                self.assertEqual(len(first_day_matchings), 5) # 하루 5경기
                
                # 2일차와 3일차가 동일한 대진 조합 및 홈/원정을 가지는지 체크
                for offset in (1, 2):
                    current_day = start_day + offset
                    current_day_matchings = {
                        home_id: away_id 
                        for (day, home_id), away_id in matches_by_day_and_home.items()
                        if day == current_day
                    }
                    self.assertEqual(first_day_matchings, current_day_matchings)
        
        # 팀당 경기 수 및 홈/원정 밸런스 검증
        team_match_counts = {}
        team_home_counts = {}
        team_away_counts = {}
        for m in matches:
            team_match_counts[m.home_club_id] = team_match_counts.get(m.home_club_id, 0) + 1
            team_match_counts[m.away_club_id] = team_match_counts.get(m.away_club_id, 0) + 1
            team_home_counts[m.home_club_id] = team_home_counts.get(m.home_club_id, 0) + 1
            team_away_counts[m.away_club_id] = team_away_counts.get(m.away_club_id, 0) + 1
            
        for club in clubs_10:
            # 팀당 총 144경기여야 함
            self.assertEqual(team_match_counts[club.id], 144)
            # 홈 72회, 원정 72회 검증
            self.assertEqual(team_home_counts[club.id], 72)
            self.assertEqual(team_away_counts[club.id], 72)

    def test_generate_regular_schedule_scenario_b(self):
        # 시나리오 B: 2025년(평년), base_sim_day = 100
        # 2025년 3월 첫 화요일인 3월 4일은 1월 1일 대비 +62일 경과
        # 따라서 시작 글로벌 sim_day = 100 + 62 = 162
        clubs_10 = self.clubs[:10]
        matches = generate_regular_schedule(clubs_10, 2025, 100)
        
        sim_days = {m.sim_day for m in matches}
        self.assertEqual(min(sim_days), 162)
        self.assertEqual(max(sim_days), 162 + 166)

    def test_generate_krown_elite_schedule(self):
        matches = generate_krown_elite_schedule(self.clubs)
        
        # 전체 경기 수 = 16 * 15 / 2 * 2 = 120 * 2 = 240 경기여야 함
        self.assertEqual(len(matches), 240)
        
        # sim_day가 1부터 30까지 있는지 확인
        sim_days = {m.sim_day for m in matches}
        self.assertEqual(len(sim_days), 30)
        
        # 모든 팀이 서로 상대팀과 홈 1경기, 원정 1경기씩 했는지 검증
        pair_matches = {}
        for m in matches:
            key = (m.home_club_id, m.away_club_id)
            pair_matches[key] = pair_matches.get(key, 0) + 1
            
        for c1 in self.clubs:
            for c2 in self.clubs:
                if c1.id != c2.id:
                    self.assertEqual(pair_matches.get((c1.id, c2.id), 0), 1)

    def test_generate_knockout_schedule_and_persistence(self):
        clubs_8 = self.clubs[:8]
        placeholders = generate_knockout_schedule(clubs_8)
        
        # 총 플레이스홀더 노드는 8강(4) + 4강(2) + 결승(1) = 7개여야 함
        self.assertEqual(len(placeholders), 7)
        
        # DB 영속화 테스트
        saved_placeholders = save_knockout_placeholders(self.session, placeholders)
        self.session.commit()
        
        # DB에서 다시 조회해서 검증
        db_placeholders = self.session.exec(select(MatchPlaceholder)).all()
        self.assertEqual(len(db_placeholders), 7)
        
        # 8강전 4개 노드 검증 (클럽 정보 채워져 있고, 부모는 없음)
        q_nodes = [p for p in db_placeholders if p.round == "ROUND_OF_8"]
        self.assertEqual(len(q_nodes), 4)
        for q in q_nodes:
            self.assertIsNotNone(q.home_club_id)
            self.assertIsNotNone(q.away_club_id)
            self.assertIsNone(q.home_parent_id)
            self.assertIsNone(q.away_parent_id)
            
        # 4강전 2개 노드 검증 (클럽 정보는 없고, 부모는 8강 노드)
        s_nodes = [p for p in db_placeholders if p.round == "SEMI_FINAL"]
        self.assertEqual(len(s_nodes), 2)
        for s in s_nodes:
            self.assertIsNone(s.home_club_id)
            self.assertIsNone(s.away_club_id)
            self.assertIsNotNone(s.home_parent_id)
            self.assertIsNotNone(s.away_parent_id)
            
        # 결승전 1개 노드 검증
        f_nodes = [p for p in db_placeholders if p.round == "FINAL"]
        self.assertEqual(len(f_nodes), 1)
        f = f_nodes[0]
        self.assertIsNone(f.home_club_id)
        self.assertIsNone(f.away_club_id)
        self.assertIsNotNone(f.home_parent_id)
        self.assertIsNotNone(f.away_parent_id)

if __name__ == "__main__":
    unittest.main()
