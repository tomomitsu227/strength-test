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
  data_analysis?: {
    extremeness_score?: number;
    extremeness_comment?: string;
    most_unique_trait?: string;
    uniqueness_comment?: string;
  };
}

export default function CreatorDiagnosisPage() {
  const [started, setStarted] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [questionsData, setQuestionsData] = useState<QuestionsData | null>(null);
  const [currentQuestion, setCurrentQuestion] = useState(0);
  const [answers, setAnswers] = useState<number[]>([]);
  const [userId, setUserId] = useState<string>('');
  const [result, setResult] = useState<ResultData | null>(null);
  const [isTransitioning, setIsTransitioning] = useState(false);

  useEffect(() => {
    axios.get(`${API_BASE}/questions`).then((res) => {
      setQuestionsData(res.data);
      // 質問数に合わせてanswers配列を初期化
      setAnswers(new Array(res.data.questions.length).fill(0));
    });
  }, []);

  const startTest = async () => {
    try {
      const res = await axios.post(`${API_BASE}/start`);
      setUserId(res.data.user_id);
      setStarted(true);
    } catch (e) {
      alert("診断を開始できませんでした。");
    }
  };

  const handleAnswer = (answer: number) => {
    if (isTransitioning) return;
    
    const newAnswers = [...answers];
    newAnswers[currentQuestion] = answer;
    setAnswers(newAnswers);
    
    setIsTransitioning(true);
    
    setTimeout(() => {
      if (currentQuestion < (questionsData?.questions.length || 0) - 1) {
        setCurrentQuestion(currentQuestion + 1);
      } else {
        submitAnswers(newAnswers);
      }
      setIsTransitioning(false);
    }, 200);
  };
  
  const submitAnswers = async (finalAnswers: number[]) => {
    try {
      const res = await axios.post(`${API_BASE}/submit`, {
        user_id: userId,
        answers: finalAnswers,
      });
      setResult(res.data);
      setCompleted(true);
    } catch (e) {
      alert("結果を送信できませんでした。");
    }
  };

  const handleDownloadPDF = async () => {
    // この関数は app.py 側の修正が必要
    alert('現在PDFダウンロード機能は調整中です。');
  };

  const restartTest = () => {
    setStarted(false);
    setCompleted(false);
    setResult(null);
    setCurrentQuestion(0);
    if(questionsData) {
      setAnswers(new Array(questionsData.questions.length).fill(0));
    }
    setUserId('');
  };


  if (!questionsData) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:from-gray-900 dark:to-gray-800">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
          <p className="text-gray-600 dark:text-gray-400">読み込み中...</p>
        </div>
      </div>
    );
  }

  // トップページ（診断開始前）
  if (!started) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex flex-col items-center justify-center p-6">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center w-full max-w-4xl"
        >
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            動画クリエイター特性診断
          </h1>
          <p className="text-lg md:text-xl text-gray-700 dark:text-gray-300 mb-12 max-w-3xl mx-auto">
            20の質問から、あなたのクリエイターとしての「核」となる強みと、才能が最も輝く創作スタイルを発見します。
          </p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl max-w-2xl mx-auto mb-12"
          >
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
              あなたの「本質」を見つけよう
            </h3>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">
             20の質問を通じて、あなたのクリエイターとしての強みや、最も輝ける創作スタイルを客観的に分析。一人で深く掘り下げるべきか、チームで輝くべきか、あなたの活動のヒントがここにあります。
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="text-center"
          >
            <button
              onClick={startTest}
              className="bg-red-600 hover:bg-red-700 text-white text-xl font-bold py-5 px-16 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300"
            >
              診断を始める
            </button>
            <p className="mt-6 text-sm text-gray-500 dark:text-gray-400">
              所要時間: 約3分
            </p>
          </motion.div>
        </motion.div>
      </div>
    );
  }

  // 質問画面
  if (!completed) {
    const q = questionsData.questions[currentQuestion];
    const progress = ((currentQuestion + 1) / questionsData.questions.length) * 100;

    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center px-4">
        <div className="max-w-3xl w-full">
          {/* プログレスバー */}
          <div className="mb-8">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm font-semibold text-gray-600 dark:text-gray-400">
                質問 {currentQuestion + 1} / {questionsData.questions.length}
              </span>
              <span className="text-sm font-semibold text-red-600">
                {Math.round(progress)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <motion.div
                className="bg-red-600 h-2 rounded-full"
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* 質問カード */}
          <AnimatePresence mode="wait">
            <motion.div
              key={currentQuestion}
              initial={{ opacity: 0, x: 50 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -50 }}
              transition={{ duration: 0.3 }}
              className="bg-white dark:bg-gray-800 rounded-2xl p-8 md:p-12 shadow-xl"
            >
              <div className="flex justify-center mb-6">
                <div className="flex items-center justify-center w-16 h-16 bg-red-600 text-white font-bold text-2xl rounded-full">
                  Q{currentQuestion + 1}
                </div>
              </div>

              <h2 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-white mb-8 leading-relaxed text-center">
                {q.q}
              </h2>

              <div className="space-y-4">
                {[
                  { value: 5, label: 'とても当てはまる' },
                  { value: 4, label: 'やや当てはまる' },
                  { value: 3, label: 'どちらとも言えない' },
                  { value: 2, label: 'あまり当てはまらない' },
                  { value: 1, label: '全く当てはまらない' }
                ].map((option) => (
                  <button
                    key={option.value}
                    onClick={() => handleAnswer(option.value)}
                    disabled={isTransitioning}
                    className={`w-full text-left p-4 rounded-xl border-2 transition-all duration-200 disabled:opacity-50 ${
                      answers[currentQuestion] === option.value
                        ? 'border-red-500 bg-red-50 dark:bg-red-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-red-300 dark:hover:border-red-700'
                    }`}
                  >
                     <span className="text-gray-700 dark:text-gray-300 font-medium text-lg">
                        {option.label}
                      </span>
                  </button>
                ))}
              </div>

              {currentQuestion > 0 && (
                <button
                  onClick={() => {
                    if (isTransitioning) return;
                    setIsTransitioning(true);
                    setCurrentQuestion(currentQuestion - 1);
                    setTimeout(() => setIsTransitioning(false), 200);
                  }}
                  disabled={isTransitioning}
                  className="mt-8 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 flex items-center disabled:opacity-50"
                >
                  <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                  前の質問に戻る
                </button>
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    );
  }

  // 結果表示画面
  if (completed && result) {
    const radarLabels = Object.keys(result.radar_scores);
    const radarData = {
      labels: radarLabels,
      datasets: [
        {
          label: 'あなたのスコア',
          data: radarLabels.map(label => result.radar_scores?.[label] || 0),
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          borderColor: '#EF4444',
          pointBackgroundColor: '#EF4444',
          pointBorderColor: '#fff',
          pointHoverBackgroundColor: '#fff',
          pointHoverBorderColor: '#EF4444'
        }
      ]
    };

    const radarOptions: any = {
      scales: {
        r: {
          min: 0,
          max: 10,
          ticks: {
            display: false,
            stepSize: 2
          },
          pointLabels: {
            font: { size: 14, family: '"Helvetica Neue", "Helvetica", "Arial", sans-serif' },
            color: '#374151'
          },
          grid: {
            color: '#E5E7EB'
          },
          angleLines: {
            color: '#E5E7EB'
          }
        }
      },
      plugins: {
        legend: { display: false }
      }
    };

    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-12 px-4">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-4">
              診断結果
            </h1>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              あなたのクリエイタータイプが判明しました
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8"
          >
            <div className="text-center">
              <p className="text-lg text-gray-500 dark:text-gray-400 mb-2">
                あなたのメインコアは
              </p>
              <h2 className="text-4xl md:text-5xl font-bold text-red-600 mb-3">
                {result.main_core_name}
              </h2>
              <p className="text-xl text-gray-700 dark:text-gray-300">
                {result.sub_core_title}
              </p>
            </div>
          </motion.div>
          
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8"
          >
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6 text-center">
              あなたの特性プロファイル
            </h3>
            <div className="max-w-lg mx-auto">
              <Radar data={radarData} options={radarOptions} />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="space-y-8 mb-8"
          >
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
               <h3 className="text-xl font-bold text-green-700 dark:text-green-400 mb-4">
                あなたに向いていること
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {result.suited_for || '…'}
              </p>
            </div>
            <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl">
              <h3 className="text-xl font-bold text-red-700 dark:text-red-400 mb-4">
                意識すると良い点
              </h3>
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">
                {result.not_suited_for || '…'}
              </p>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white dark:bg-gray-800 rounded-2xl p-8 shadow-xl mb-8"
          >
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
              分析結果のまとめ
            </h3>
            <p className="text-gray-700 dark:text-gray-300 leading-loose whitespace-pre-wrap">
              {result.synthesis || '…'}
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.7 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <button
              onClick={handleDownloadPDF}
              className="bg-red-600 hover:bg-red-700 text-white font-bold py-4 px-8 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300"
            >
              PDFでダウンロード (調整中)
            </button>
            <button
              onClick={restartTest}
              className="bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-800 dark:text-gray-200 font-bold py-4 px-8 rounded-full shadow-lg transform hover:scale-105 transition-all duration-300"
            >
              もう一度診断する
            </button>
          </motion.div>
        </div>
      </div>
    );
  }

  return null;
}