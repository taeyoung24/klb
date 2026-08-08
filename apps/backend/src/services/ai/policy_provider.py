"""
services/ingame/decisions/base.py의 BaseDecisionEngine을 상속받아 NN 추론을 제공하는 구현체.
IngameContext 상태를 FeatureExtractor로 변환한 뒤 각 신경망(Net) 추론 결과를 시뮬레이터에 전달함.
신경망 정책 기반의 NNDecisionEngine을 통해 시뮬레이터와 AI 신경망 엔진을 유연하게 연결함.
"""
