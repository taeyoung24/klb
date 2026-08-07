import random

# Constants
LAST_NAMES = [
    # 매우 흔한 성
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    '김', '이', '박', '최', '정', '강', '조', '윤', '장', '임',
    # 비교적 흔한 성
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',
    '홍', '고', '문', '양', '손', '배', '백', '허', '유', '남',
    '노', '심', '하', '곽', '성', '차', '주', '우', '구', '민',
    '진', '나', '엄', '방', '좌', '변', '예', '표', '현', '탁',
    '한', '오', '서', '신', '권', '황', '안', '송', '류', '전',
    '홍', '고', '문', '양', '손', '배', '백', '허', '유', '남',
    '노', '심', '하', '곽', '성', '차', '주', '우', '구', '민',
    '진', '나', '엄', '방', '좌', '변', '예', '표', '현', '탁',
    # 드물지만 실제 존재하는 성들 일부
    '여', '제', '마', '봉', '길', '기', '추', '설', '소', '우',
    '라', '채', '석', '반', '빈', '우', '엽', '우', '용', '표'
]

FIRST_SYLLABLES = [
    '민', '준', '현', '지', '도', '건', '예', '하', '주', '태',
    '성', '승', '재', '시', '영', '윤', '서', '동', '우', '대',
    '호', '유', '라', '찬', '범', '혁', '선', '경', '규', '진',
    '태', '연', '수', '인', '지', '솔', '하', '율', '도', '우',
    '광', '성', '현', '세', '아', '보', '주', '연', '태', '도'
]

SECOND_SYLLABLES = [
    '준', '호', '우', '훈', '호', '민', '우', '현', '진', '석',
    '재', '성', '혁', '현', '원', '율', '찬', '현', '성', '완',
    '범', '기', '담', '제', '훈', '호', '화', '애', '래'
]

SINGLE_SYLLABLES = [
    '민', '준', '현', '호', '우', '진', '혁', '찬', '윤', '서',
    '태', '성', '재', '훈'
]


POSITIONS = ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']

def generate_name() -> str:
    def has_consecutive_repeat(s: str) -> bool:
        for i in range(len(s) - 1):
            if s[i] == s[i + 1]:
                return True
        return False

    last = random.choice(LAST_NAMES)

    while True:
        # 외자 이름 (약 20%)
        if random.random() < 0.2:
            given = random.choice(SINGLE_SYLLABLES)
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
