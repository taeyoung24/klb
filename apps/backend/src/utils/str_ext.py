import random

# Constants
LAST_NAMES = {
    '갈': 25, '강': 22, '경': 3, '고': 16, '공': 4, '곽': 7, '구': 5, '국': 4, '기': 4, '길': 1, '김': 243, 
    '나': 7, '남': 22, '내': 5, '노': 29,
    '단': 6, '대': 2, '도': 15, '돈': 2, '동': 1, 
    '류': 10,
    '마': 7, '만': 1, '명': 1, '모': 2, '문': 14, 
    '박': 19, '반': 7, '방': 14, '배': 17, '백': 11, '범': 13, '봉': 2, '부': 2, '빈': 3,
    '사': 6, '상': 1, '새': 1, '서': 15, '석': 9, '설': 5, '성': 3, '소': 4, '손': 15, '송': 21, '수': 2, '순': 9, '승': 4, '시': 5, '신': 11, '심': 4, 
    '아': 1, '안': 16, '야': 1, '양': 22, '어': 3, '여': 5, '연': 7, '영': 3, '오': 18, '옥': 1, '온': 1, '옹': 1, '왕': 4, '요': 1, '용': 1, '우': 3, '운': 2, '원': 4, '유': 31, '육': 1, '윤': 16, '이': 162, '임': 30, 
    '자': 3, '장': 81, '전': 40, '정': 81, '제': 4, '조': 34, '좌': 1, '주': 15, '지': 6, '진': 23, 
    '차': 4, '채': 5, '천': 5, '초': 5, '최': 75, '추': 3,
    '편': 2, '포': 3,
    '하': 11, '한': 19, '함': 1, '해': 1, '허': 8, '현': 1, '호': 18, '홍': 37, '화': 1, '황': 19
}
_LAST_NAMES_KEYS = list(LAST_NAMES.keys())
_LAST_NAMES_WEIGHTS = list(LAST_NAMES.values())

# TODO: 중복 제거 및 다양화 필요 (26. 8. 13. 안개비)
FIRST_SYLLABLES = [
    '민', '준', '현', '지', '도', '건', '예', '하', '주', '태',
    '성', '승', '재', '시', '영', '윤', '서', '동', '우', '대',
    '호', '유', '라', '찬', '범', '혁', '선', '경', '규', '진',
    '태', '연', '수', '인', '지', '솔', '하', '율', '도', '우',
    '광', '성', '현', '세', '아', '보', '주', '연', '태', '도',
    '소', '형',
]

SECOND_SYLLABLES = [
    '준', '호', '우', '훈', '호', '민', '우', '현', '진', '석',
    '재', '성', '혁', '현', '원', '율', '찬', '현', '성', '완',
    '범', '기', '담', '제', '훈', '호', '화', '애', '래', '거',
    '소', '형',
]

SINGLE_SYLLABLES = [
    '민', '준', '현', '호', '우', '진', '혁', '찬', '윤', '서',
    '태', '성', '재', '훈', '묵', '세', '제', '정', '군',
    '화', '연', '윤', '상'
],


POSITIONS = ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']

def generate_name() -> str:
    def has_consecutive_repeat(s: str) -> bool:
        for i in range(len(s) - 1):
            if s[i] == s[i + 1]:
                return True
        return False

    last = random.choices(_LAST_NAMES_KEYS, weights=_LAST_NAMES_WEIGHTS, k=1)[0]

    while True:
        # 외자 이름 (약 6%)
        if random.random() < 0.06:
            given = random.choice(SINGLE_SYLLABLES)[0]
        else:
            # 2글자 기본
            first = random.choice(FIRST_SYLLABLES)

            # first와 다른 음절만 후보로 사용
            second_candidates = [c for c in SECOND_SYLLABLES if c != first]
            if not second_candidates:
                second_candidates = SECOND_SYLLABLES
            second = random.choice(second_candidates)

            given = first + second

        full = last + given

        # 성+이름 전체에서 연속 두 글자 중복이 있으면 다시 생성
        if not has_consecutive_repeat(full):
            return full
