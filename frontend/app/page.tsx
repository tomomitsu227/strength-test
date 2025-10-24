'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import axios from 'axios';
import Image from 'next/image';

import { Radar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js';
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE || 'http://localhost:5000/api';

interface Question {
  q: string;
}
interface QuestionsData {
  questions: Question[];
}
interface ResultData {
  user_id: string;
  main_core_name: string;
  sub_core_title: string;
  suited_for: string;
  not_suited_for: string;
  synthesis: string;
  radar_scores: { [key: string]: number };
}

const IconWrapper = ({ children }: { children: React.ReactNode }) => (
  <div className="flex items-center justify-center w-12 h-12 bg-red-100 dark:bg-gray-700 rounded-full mb-4">
    {children}
  </div>
);

export default function CreatorDiagnosisPage() {
  const [questionsData, setQuestionsData] = useState<QuestionsData>();
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [result, setResult] = useState<ResultData | null>(null);

  useEffect(() => {
    async function fetchQuestions() {
      const res = await axios.get(`${API_BASE}/questions`);
      setQuestionsData(res.data);
    }
    fetchQuestions();
  }, []);

  const handleAnswer = (answer: number) => {
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);

    if (currentQuestion < (questionsData?.questions.length || 0) - 1) {
      setCurrentQuestion(currentQuestion + 1);
    } else {
      submitAnswers(newAnswers);
    }
  };

  const submitAnswers = async (ans: number[]) => {
    const user_id = 'user-' + Math.random().toString(36).slice(2, 8);
    const res = await axios.post(`${API_BASE}/submit`, {
      user_id,
      answers: ans
    });
    setResult(res.data);
  };

  if (!questionsData) {
    return <div>読み込み中...</div>;
  }

  if (!result) {
    const q = questionsData.questions[currentQuestion];
    return (
      <div className="max-w-xl mx-auto p-6">
        <h2 className="text-2xl font-bold mb-6">動画クリエイター特性診断</h2>
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 rounded-full bg-red-500 text-white flex items-center justify-center text-xl font-bold">
            {currentQuestion + 1}
          </div>
          <div className="text-sm text-gray-500">/ 20</div>
        </div>
        <div className="mb-8 text-lg font-semibold">{q.q}</div>
        <div className="flex justify-center gap-4">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              className={`px-4 py-2 rounded-full border ${answers[currentQuestion] === n ? 'bg-red-500 text-white' : 'border-gray-300'}`}
              onClick={() => handleAnswer(n)}
            >
              {n}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // 7次元レーダーチャートラベル
  const radarLabels = [
    '独創性',
    '計画性',
    '社交性',
    '共感力',
    '精神的安定性',
    '創作スタイル',
    '協働適性'
  ];

  const radarData = {
    labels: radarLabels,
    datasets: [
      {
        label: 'あなたのスコア',
        data: radarLabels.map(label => result.radar_scores?.[label] || 0),
        backgroundColor: 'rgba(239,68,68,0.2)', // 赤系
        borderColor: '#EF4444',
        pointBackgroundColor: '#EF4444'
      }
    ]
  };

  const radarOptions = {
    scales: {
      r: {
        min: 0,
        max: 10,
        ticks: {
          stepSize: 2,
          color: '#374151'
        },
        pointLabels: {
          font: { size: 14, family: 'Noto Sans JP' },
          color: '#374151'
        },
        grid: {
          color: '#E5E7EB'
        }
      }
    },
    plugins: {
      legend: { display: false }
    }
  };

  return (
    <div className="max-w-xl mx-auto p-6">
      <h2 className="text-2xl font-bold mb-6">動画クリエイター特性診断</h2>
      <div className="mb-6">
        <div className="text-base mb-2 text-gray-600">
          {result.main_core_name}
        </div>
        <div className="font-bold text-xl mb-2">
          {result.sub_core_title}
        </div>
      </div>
      <div className="mb-8">
        <Radar data={radarData} options={radarOptions} />
      </div>
      <div className="mb-8">
        <h3 className="font-semibold text-lg mb-2 text-green-700">あなたに向いていること</h3>
        <div className="bg-green-100 border-l-4 border-green-500 p-4 mb-4">
          {result.suited_for}
        </div>
        <h3 className="font-semibold text-lg mb-2 text-red-700">意識すると良い点</h3>
        <div className="bg-red-100 border-l-4 border-red-500 p-4 mb-4">
          {result.not_suited_for}
        </div>
      </div>
      <div className="mb-8">
        {/* 総合分析（synthesis）10行程度に拡充 */}
        <h3 className="font-semibold text-lg mb-2 text-indigo-700">分析結果まとめ</h3>
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          {result.synthesis}
        </div>
      </div>
      {/* PDFダウンロードボタン等は既存コードのまま利用可 */}
    </div>
  );
}
