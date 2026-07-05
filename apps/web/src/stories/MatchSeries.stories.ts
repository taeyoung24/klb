import type { Meta, StoryObj } from '@storybook/react-vite';
import MatchSeries from '../components/MatchSeries/MatchSeries';

const meta = {
  title: 'Components/MatchSeries',
  component: MatchSeries,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof MatchSeries>;

export default meta;
type Story = StoryObj<typeof meta>;

// 사진 1: 데이터가 비어있는 기본 상태 (TBD)
export const UpperPlayInFinal: Story = {
  args: {
    stageTitle: 'Upper Play-In Final',
    upperSeedTitle: '5th Seed',
    upperTeamName: 'TBD',
    upperScoreSeries: [],
    lowerSeedTitle: 'Winner of Upper Play-In Round 2',
    lowerTeamName: 'TBD',
    lowerScoreSeries: [],
  },
};

// 사진 2: 경기가 완료된 다전제 (5판 3선승 등)
export const LowerPlayoffFinal: Story = {
  args: {
    stageTitle: 'Lower Playoff Final',
    upperSeedTitle: '1st Seed',
    upperTeamName: 'ARCHERS',
    // 실제 이미지 경로가 없으므로 Storybook 테스트용 플레이스홀더를 사용했습니다.
    upperTeamImage: 'https://via.placeholder.com/36/5b21b6/ffffff?text=A',
    upperScoreSeries: [5, 11, 4, 2, 4],
    lowerSeedTitle: '5th Seed',
    lowerTeamName: 'MELODIANS',
    lowerTeamImage: 'https://via.placeholder.com/36/ea580c/ffffff?text=M',
    lowerScoreSeries: [2, 6, 5, 4, 1],
  },
};

// 3판제로 진행된 경우 (점수 배열이 짧은 경우 홀수 길이에 맞추는 로직 테스트)
export const BestOfThree: Story = {
  args: {
    stageTitle: 'Semifinals',
    upperSeedTitle: '2nd Seed',
    upperTeamName: 'DRAGONS',
    upperScoreSeries: [10, 8],
    lowerSeedTitle: '3rd Seed',
    lowerTeamName: 'TIGERS',
    lowerScoreSeries: [5, 11],
  },
};
